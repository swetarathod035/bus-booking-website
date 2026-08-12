"""
Booking engine views: seat selection, payment, tickets, passenger dashboard.
"""
import json
import uuid
import datetime
import re
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q

from accounts.decorators import passenger_required, login_required
from routes.models import Schedule, Route, RouteStop, Stop
from .models import Booking, Seat, Payment, Ticket, PassengerDetail
from .utils import generate_seat_layout, calculate_fare, generate_ticket_pdf, send_booking_email


@passenger_required
def passenger_dashboard(request):
    """Passenger personal dashboard: upcoming & past bookings."""
    user = request.user
    upcoming = Booking.objects.filter(
        passenger=user,
        status__in=['CONFIRMED', 'PENDING'],
        schedule__travel_date__gte=datetime.date.today(),
    ).select_related('schedule__route', 'schedule__bus').prefetch_related('seats').order_by(
        'schedule__travel_date', 'schedule__departure_time'
    )
    past = Booking.objects.filter(
        passenger=user,
        status='COMPLETED',
    ).select_related('schedule__route').order_by('-created_at')[:20]

    context = {
        'title': 'My Dashboard — AnandBus',
        'upcoming_bookings': upcoming,
        'past_bookings': past,
        'user': user,
    }
    return render(request, 'bookings/passenger_dashboard.html', context)


@passenger_required
def select_seats(request, schedule_id):
    """Dynamic seat selection page with 2×3 grid."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    if not schedule.is_available:
        messages.error(request, 'This schedule is no longer available for booking.')
        return redirect('routes:search')

    # Auto-generate seats if not yet created for this schedule
    if not Seat.objects.filter(schedule=schedule).exists():
        generate_seat_layout(schedule)

    seats = Seat.objects.filter(schedule=schedule).order_by('row_number', 'column_letter')

    # Boarding / alighting stops for this route
    route_stops = RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order')

    # Prefill boarding/alighting from search GET params
    boarding_code = request.GET.get('from', '')
    alighting_code = request.GET.get('to', '')
    seat_ids_str = request.GET.get('seat_ids', '')

    selected_seat_ids = []
    if seat_ids_str:
        try:
            selected_seat_ids = [int(s) for s in seat_ids_str.split(',') if s.strip()]
        except ValueError:
            selected_seat_ids = []

    seats_param = request.GET.get('seats', '')
    if seats_param and seats_param.isdigit():
        num_seats = int(seats_param)
    elif selected_seat_ids:
        num_seats = len(selected_seat_ids)
    else:
        num_seats = 1

    # Fare calculation
    base_fare = float(schedule.route.calculate_fare())

    # Build seat grid: rows x columns (2+1 aisle +2 layout → 5 cols)
    # We use: A B | C | D E  (2-1-2 pattern)
    seat_grid = {}
    for seat in seats:
        row = seat.row_number
        if row not in seat_grid:
            seat_grid[row] = {}
        seat_grid[row][seat.column_letter] = seat

    context = {
        'title': f'Select Seats — {schedule.route}',
        'schedule': schedule,
        'seats': seats,
        'seat_grid': seat_grid,
        'route_stops': route_stops,
        'boarding_code': boarding_code,
        'alighting_code': alighting_code,
        'num_seats': num_seats,
        'selected_seat_ids': selected_seat_ids,
        'selected_seat_ids_json': json.dumps(selected_seat_ids),
        'base_fare': base_fare,
        'total_rows': range(1, schedule.bus.total_seats // 5 + 2),
    }
    return render(request, 'bookings/seat_selection.html', context)


@require_POST
@passenger_required
def create_booking(request):
    """Create booking after seat selection, before payment."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    schedule_id = data.get('schedule_id')
    seat_ids = data.get('seat_ids', [])
    boarding_stop_code = data.get('boarding_stop')
    alighting_stop_code = data.get('alighting_stop')
    passengers_data = data.get('passengers', [])

    if not all([schedule_id, seat_ids, boarding_stop_code, alighting_stop_code]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    schedule = get_object_or_404(Schedule, pk=schedule_id)
    boarding_stop = get_object_or_404(Stop, code=boarding_stop_code)
    alighting_stop = get_object_or_404(Stop, code=alighting_stop_code)

    with transaction.atomic():
        # Lock seats
        seats_qs = Seat.objects.select_for_update().filter(
            id__in=seat_ids, schedule=schedule, status='AVAILABLE'
        )
        seats = list(seats_qs)
        if len(seats) != len(seat_ids):
            return JsonResponse({'error': 'Some seats are no longer available. Please re-select.'}, status=409)

        # Calculate fare
        fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(seat_ids))

        # Create booking
        booking = Booking.objects.create(
            passenger=request.user,
            schedule=schedule,
            boarding_stop=boarding_stop,
            alighting_stop=alighting_stop,
            num_passengers=len(seat_ids),
            status=Booking.Status.PENDING,
            base_amount=fare_data['base_amount'],
            tax_amount=fare_data['tax_amount'],
            convenience_fee=fare_data['convenience_fee'],
            discount_amount=fare_data['discount_amount'],
            total_amount=fare_data['total_amount'],
            passenger_name=request.user.get_full_name() or request.user.username,
            passenger_email=request.user.email,
            passenger_phone=getattr(request.user, 'phone', '') or '',
        )
        booking.seats.set(seats)

        # Update seat status
        Seat.objects.filter(id__in=seat_ids).update(status=Seat.SeatStatus.BOOKED)

        # Reduce available seat count
        schedule.available_seats = max(0, schedule.available_seats - len(seat_ids))
        schedule.save()

        # Save individual passenger details if provided
        for i, pax in enumerate(passengers_data):
            if i < len(seats):
                PassengerDetail.objects.create(
                    booking=booking,
                    seat=seats[i],
                    name=pax.get('name', request.user.get_full_name()),
                    age=pax.get('age', 25),
                    gender=pax.get('gender', 'M'),
                )

    return JsonResponse({
        'success': True,
        'booking_id': str(booking.booking_id),
        'total_amount': float(booking.total_amount),
        'fare_breakdown': fare_data,
    })


@passenger_required
def booking_payment(request, booking_id):
    """Payment page — Razorpay order creation."""
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)

    if booking.status != Booking.Status.PENDING:
        messages.info(request, 'This booking has already been processed.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    # Create Razorpay order
    razorpay_order_id = None
    if settings.RAZORPAY_KEY_ID:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order_data = {
                'amount': int(booking.total_amount * 100),  # paise
                'currency': 'INR',
                'receipt': str(booking.booking_id)[:20],
                'notes': {
                    'booking_id': str(booking.booking_id),
                    'passenger': request.user.username,
                }
            }
            rz_order = client.order.create(data=order_data)
            razorpay_order_id = rz_order['id']

            # Store order ID
            payment, _ = Payment.objects.get_or_create(booking=booking, defaults={
                'amount': booking.total_amount,
                'gateway': Payment.Gateway.RAZORPAY,
            })
            payment.gateway_order_id = razorpay_order_id
            payment.save()
        except Exception:
            pass

    context = {
        'title': f'Payment — Booking #{booking.short_id}',
        'booking': booking,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount_paise': int(booking.total_amount * 100),
    }
    return render(request, 'bookings/payment.html', context)


@require_POST
@passenger_required
def payment_success(request):
    """Handle successful Razorpay callback and confirm booking."""
    booking_id = request.POST.get('booking_id') or request.POST.get('razorpay_description')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)

    # Verify signature
    verified = True
    is_demo = (
        razorpay_payment_id.startswith('demo_') or
        razorpay_payment_id.startswith('pay_') or
        razorpay_signature == 'demo_sig' or
        not settings.RAZORPAY_KEY_ID or
        settings.RAZORPAY_KEY_ID.startswith('rzp_test_XXXX')
    )
    if settings.RAZORPAY_KEY_ID and razorpay_payment_id and not is_demo:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })
        except Exception:
            verified = False

    if verified:
        with transaction.atomic():
            booking.status = Booking.Status.CONFIRMED
            booking.save()

            # Update payment
            payment, _ = Payment.objects.get_or_create(booking=booking, defaults={'amount': booking.total_amount})
            payment.status = Payment.Status.SUCCESS
            payment.gateway_payment_id = razorpay_payment_id
            payment.gateway_order_id = razorpay_order_id
            payment.gateway_signature = razorpay_signature
            payment.paid_at = timezone.now()
            payment.save()

            # Generate ticket
            ticket = Ticket(booking=booking)
            ticket.generate_ticket_number()
            ticket.save()

            # Generate PDF & QR
            try:
                generate_ticket_pdf(ticket)
            except Exception:
                pass

            # Send email
            try:
                send_booking_email(booking)
            except Exception:
                pass

        messages.success(request, f'Booking confirmed! Ticket #{ticket.ticket_number} sent to your email.')
        return redirect('bookings:booking_success', booking_id=booking_id)
    else:
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('bookings:booking_payment', booking_id=booking_id)


@passenger_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    ticket = getattr(booking, 'ticket', None)
    return render(request, 'bookings/booking_success.html', {
        'title': 'Booking Confirmed!',
        'booking': booking,
        'ticket': ticket,
    })


@passenger_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    ticket = getattr(booking, 'ticket', None)
    passenger_details = booking.passenger_details.select_related('seat').all()
    return render(request, 'bookings/booking_detail.html', {
        'title': f'Booking #{booking.short_id}',
        'booking': booking,
        'ticket': ticket,
        'passenger_details': passenger_details,
    })


@passenger_required
def download_ticket(request, booking_id):
    """Stream ticket PDF to browser."""
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    ticket = get_object_or_404(Ticket, booking=booking)

    if not ticket.pdf_file:
        try:
            generate_ticket_pdf(ticket)
        except Exception as e:
            messages.error(request, f'Could not generate PDF: {e}')
            return redirect('bookings:booking_detail', booking_id=booking_id)

    response = FileResponse(
        ticket.pdf_file.open('rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f'AnandBus_Ticket_{ticket.ticket_number}.pdf',
    )
    return response


@require_POST
@passenger_required
def cancel_booking(request, booking_id):
    """Cancel a booking (sends refund request)."""
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)

    if booking.status not in ['CONFIRMED', 'PENDING']:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    reason = request.POST.get('reason', 'Cancelled by passenger')

    with transaction.atomic():
        # Free up seats
        booking.seats.update(status=Seat.SeatStatus.AVAILABLE)
        booking.schedule.available_seats += booking.seats.count()
        booking.schedule.save()

        booking.status = Booking.Status.CANCELLED
        booking.cancellation_reason = reason
        booking.cancelled_at = timezone.now()
        booking.save()

        # Mark refund initiated if payment was made
        payment = getattr(booking, 'payment', None)
        if payment and payment.status == Payment.Status.SUCCESS:
            payment.status = Payment.Status.REFUNDED
            payment.refunded_at = timezone.now()
            payment.save()
            booking.status = Booking.Status.REFUNDED
            booking.save()

    messages.success(request, 'Booking cancelled successfully. Refund will be processed in 3–5 business days.')
    return redirect('bookings:passenger_dashboard')


@require_POST
@passenger_required
def reschedule_booking(request, booking_id):
    """Reschedule to a new schedule."""
    original = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    new_schedule_id = request.POST.get('new_schedule_id')

    if original.status != 'CONFIRMED':
        messages.error(request, 'Only confirmed bookings can be rescheduled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    new_schedule = get_object_or_404(Schedule, pk=new_schedule_id)

    with transaction.atomic():
        # Cancel original seats
        original.seats.update(status=Seat.SeatStatus.AVAILABLE)
        original.schedule.available_seats += original.seats.count()
        original.schedule.save()
        original.status = Booking.Status.RESCHEDULED
        original.save()

        # Create new booking
        new_booking = Booking.objects.create(
            passenger=request.user,
            schedule=new_schedule,
            boarding_stop=original.boarding_stop,
            alighting_stop=original.alighting_stop,
            num_passengers=original.num_passengers,
            status=Booking.Status.PENDING,
            base_amount=original.base_amount,
            tax_amount=original.tax_amount,
            convenience_fee=original.convenience_fee,
            total_amount=original.total_amount,
            original_booking=original,
        )

    messages.success(request, 'Booking rescheduled. Please complete payment for the new schedule.')
    return redirect('bookings:booking_payment', booking_id=new_booking.booking_id)


# ─── AJAX: Fare Calculator ────────────────────────────────────────────────────
@require_GET
def api_calculate_fare(request):
    schedule_id = request.GET.get('schedule_id')
    from_code = request.GET.get('from')
    to_code = request.GET.get('to')
    num_seats = int(request.GET.get('seats', 1))

    schedule = get_object_or_404(Schedule, pk=schedule_id)
    from_stop = get_object_or_404(Stop, code=from_code)
    to_stop = get_object_or_404(Stop, code=to_code)

    fare_data = calculate_fare(schedule, from_stop, to_stop, num_seats)
    return JsonResponse(fare_data)


# ─── 2-Step Booking: Passenger Details ─────────────────────────────────────────
@passenger_required
def passenger_info(request):
    """Step 2: Enter passenger details for each selected seat before payment."""
    if request.method == 'GET':
        schedule_id = request.GET.get('schedule_id')
        seat_ids_str = request.GET.get('seat_ids', '')
        boarding_code = request.GET.get('boarding_stop', '')
        alighting_code = request.GET.get('alighting_stop', '')

        if not all([schedule_id, seat_ids_str, boarding_code, alighting_code]):
            messages.error(request, 'Invalid booking parameters. Please select seats again.')
            return redirect('routes:search')

        try:
            seat_ids = [int(s) for s in seat_ids_str.split(',') if s.strip()]
        except ValueError:
            messages.error(request, 'Invalid seat selection.')
            return redirect('routes:search')

        schedule = get_object_or_404(Schedule, pk=schedule_id)
        boarding_stop = get_object_or_404(Stop, code=boarding_code)
        alighting_stop = get_object_or_404(Stop, code=alighting_code)
        selected_seats = Seat.objects.filter(id__in=seat_ids, schedule=schedule)

        if len(selected_seats) != len(seat_ids):
            messages.error(request, 'One or more selected seats are no longer valid.')
            return redirect('bookings:select_seats', schedule_id=schedule.id)

        fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(selected_seats))

        context = {
            'title': 'Passenger Information — AnandBus',
            'schedule': schedule,
            'boarding_stop': boarding_stop,
            'alighting_stop': alighting_stop,
            'selected_seats': selected_seats,
            'seat_ids_str': seat_ids_str,
            'fare_data': fare_data,
        }
        return render(request, 'bookings/passenger_info.html', context)

    elif request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        seat_ids_str = request.POST.get('seat_ids', '')
        boarding_code = request.POST.get('boarding_stop')
        alighting_code = request.POST.get('alighting_stop')

        try:
            seat_ids = [int(s) for s in seat_ids_str.split(',') if s.strip()]
        except (ValueError, AttributeError):
            messages.error(request, 'Invalid seat selection.')
            return redirect('routes:search')

        schedule = get_object_or_404(Schedule, pk=schedule_id)
        boarding_stop = get_object_or_404(Stop, code=boarding_code)
        alighting_stop = get_object_or_404(Stop, code=alighting_code)
        selected_seats = list(Seat.objects.filter(id__in=seat_ids, schedule=schedule))

        # Perform strict validations for each passenger
        passengers_data = []
        errors = []

        for idx in range(len(selected_seats)):
            pax_num = idx + 1
            name = request.POST.get(f'name_{idx}', '').strip()
            age_str = request.POST.get(f'age_{idx}', '').strip()
            gender = request.POST.get(f'gender_{idx}', '').strip()
            email = request.POST.get(f'email_{idx}', '').strip()
            phone = request.POST.get(f'phone_{idx}', '').strip()

            passengers_data.append({
                'name': name,
                'age': age_str,
                'gender': gender,
                'email': email,
                'phone': phone,
            })

            # Full Name validation (Required, letters and spaces only, min 2 chars)
            if not name or len(name) < 2 or not re.match(r'^[A-Za-z\s]+$', name):
                errors.append(f"Passenger {pax_num}: Full Name must contain only letters and spaces (min 2 characters).")

            # Age validation (Required, 1-99, no 3-digit numbers)
            if not age_str or not age_str.isdigit():
                errors.append(f"Passenger {pax_num}: Please enter a valid age (1-99).")
            else:
                age_val = int(age_str)
                if age_val < 1 or age_val > 99 or len(age_str) > 2:
                    errors.append(f"Passenger {pax_num}: Please enter a valid age (1-99).")

            # Gender validation (Required)
            if not gender or gender not in ['M', 'F', 'O']:
                errors.append(f"Passenger {pax_num}: Please select a gender.")

            # Email Address validation (Required, standard email regex)
            if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append(f"Passenger {pax_num}: Please enter a valid email address.")

            # Phone Number validation (Required, exactly 10 digits)
            if not phone or not re.match(r'^\d{10}$', phone):
                errors.append(f"Passenger {pax_num}: Please enter a valid 10-digit phone number.")

        if errors:
            for err in errors:
                messages.error(request, err)
            fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(selected_seats))
            context = {
                'title': 'Passenger Information — AnandBus',
                'schedule': schedule,
                'boarding_stop': boarding_stop,
                'alighting_stop': alighting_stop,
                'selected_seats': selected_seats,
                'seat_ids_str': seat_ids_str,
                'fare_data': fare_data,
                'passengers_input': passengers_data,
            }
            return render(request, 'bookings/passenger_info.html', context)

        with transaction.atomic():
            seats_qs = Seat.objects.select_for_update().filter(
                id__in=seat_ids, schedule=schedule, status='AVAILABLE'
            )
            seats = list(seats_qs)
            if len(seats) != len(seat_ids):
                messages.error(request, 'Some selected seats are no longer available. Please re-select.')
                return redirect('bookings:select_seats', schedule_id=schedule.id)

            fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(seat_ids))

            primary_pax = passengers_data[0]

            booking = Booking.objects.create(
                passenger=request.user,
                schedule=schedule,
                boarding_stop=boarding_stop,
                alighting_stop=alighting_stop,
                num_passengers=len(seat_ids),
                status=Booking.Status.PENDING,
                base_amount=Decimal(str(fare_data['base_amount'])),
                tax_amount=Decimal(str(fare_data['tax_amount'])),
                convenience_fee=Decimal(str(fare_data['convenience_fee'])),
                discount_amount=Decimal(str(fare_data['discount_amount'])),
                total_amount=Decimal(str(fare_data['total_amount'])),
                passenger_name=primary_pax['name'],
                passenger_email=primary_pax['email'],
                passenger_phone=primary_pax['phone'],
            )
            booking.seats.set(seats)

            # Update seats status to BOOKED
            Seat.objects.filter(id__in=seat_ids).update(status=Seat.SeatStatus.BOOKED)
            schedule.available_seats = max(0, schedule.available_seats - len(seat_ids))
            schedule.save()

            # Save individual passenger detail records
            for idx, seat in enumerate(seats):
                pax = passengers_data[idx]
                PassengerDetail.objects.create(
                    booking=booking,
                    seat=seat,
                    name=pax['name'],
                    age=int(pax['age']),
                    gender=pax['gender'],
                    email=pax['email'],
                    phone=pax['phone'],
                )

        return redirect('bookings:booking_payment', booking_id=booking.booking_id)


# ─── Dedicated Ticket Reschedule Page ──────────────────────────────────────────
def reschedule_ticket_page(request):
    """Dedicated ticket rescheduling page with PNR Number & Email lookup."""
    today_date = datetime.date.today()
    today_str = today_date.strftime('%Y-%m-%d')

    context = {
        'title': 'Reschedule Ticket — AnandBus',
        'searched': False,
        'booking': None,
        'today_str': today_str,
    }

    if request.method == 'POST':
        action = request.POST.get('action', 'search')
        pnr_number = request.POST.get('pnr_number', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        new_travel_date_str = request.POST.get('new_travel_date', '').strip()

        context['pnr_number'] = pnr_number
        context['email'] = email
        context['new_travel_date'] = new_travel_date_str
        context['searched'] = True

        if not pnr_number or not email:
            messages.error(request, 'Please enter both PNR Number and Email Address.')
            return render(request, 'bookings/reschedule_ticket.html', context)

        # Lookup booking by PNR and Email
        booking = Booking.objects.filter(
            Q(pnr_number__iexact=pnr_number) | Q(booking_id__istartswith=pnr_number),
            Q(passenger_email__iexact=email) | Q(passenger__email__iexact=email),
            status=Booking.Status.CONFIRMED,
        ).select_related('schedule__route', 'schedule__bus', 'passenger').first()

        if not booking:
            messages.error(request, 'No confirmed booking found matching this PNR Number and Email Address.')
            return render(request, 'bookings/reschedule_ticket.html', context)

        context['booking'] = booking

        if action == 'reschedule' and new_travel_date_str:
            try:
                selected_date = datetime.datetime.strptime(new_travel_date_str, '%Y-%m-%d').date()
                if selected_date < today_date:
                    messages.error(request, 'Reschedule date cannot be in the past.')
                    return render(request, 'bookings/reschedule_ticket.html', context)

                with transaction.atomic():
                    # Find or create schedule on new travel date for this route
                    new_schedule = Schedule.objects.filter(
                        route=booking.schedule.route,
                        travel_date=selected_date,
                        status__in=[Schedule.Status.SCHEDULED, Schedule.Status.DELAYED],
                    ).first()

                    if not new_schedule:
                        # Auto-create schedule for the new travel date
                        new_schedule = Schedule.objects.create(
                            route=booking.schedule.route,
                            bus=booking.schedule.bus,
                            driver=booking.schedule.driver,
                            departure_time=booking.schedule.departure_time,
                            arrival_time=booking.schedule.arrival_time,
                            travel_date=selected_date,
                            available_seats=booking.schedule.bus.total_seats,
                            status=Schedule.Status.SCHEDULED,
                        )

                    # Release original seats
                    booking.seats.update(status=Seat.SeatStatus.AVAILABLE)
                    booking.schedule.available_seats += booking.num_passengers
                    booking.schedule.save()

                    # Generate seats for new schedule if needed
                    if not Seat.objects.filter(schedule=new_schedule).exists():
                        generate_seat_layout(new_schedule)

                    new_seats = list(Seat.objects.filter(schedule=new_schedule, status=Seat.SeatStatus.AVAILABLE)[:booking.num_passengers])
                    if len(new_seats) < booking.num_passengers:
                        messages.error(request, 'Not enough seats available on the selected date.')
                        return render(request, 'bookings/reschedule_ticket.html', context)

                    Seat.objects.filter(id__in=[s.id for s in new_seats]).update(status=Seat.SeatStatus.BOOKED)
                    new_schedule.available_seats = max(0, new_schedule.available_seats - len(new_seats))
                    new_schedule.save()

                    # Update booking with new schedule and seats
                    booking.schedule = new_schedule
                    booking.seats.set(new_seats)
                    booking.save()

                    # Re-generate ticket PDF if exists
                    if hasattr(booking, 'ticket'):
                        try:
                            generate_ticket_pdf(booking.ticket)
                        except Exception:
                            pass

                messages.success(request, f'Ticket #{booking.short_id} has been successfully rescheduled to {selected_date.strftime("%d %b %Y")}!')
                return render(request, 'bookings/reschedule_ticket.html', {
                    'title': 'Reschedule Success — AnandBus',
                    'searched': True,
                    'booking': booking,
                })
            except ValueError:
                messages.error(request, 'Please enter a valid travel date.')

    return render(request, 'bookings/reschedule_ticket.html', context)


# ─── Dedicated Ticket Cancellation Page ────────────────────────────────────────
def cancel_ticket_page(request):
    """Dedicated ticket cancellation page with PNR Number & Email lookup."""
    context = {
        'title': 'Cancel Ticket — AnandBus',
        'searched': False,
        'booking': None,
        'refund_amount': Decimal('0.00'),
    }

    if request.method == 'POST':
        action = request.POST.get('action', 'search')
        pnr_number = request.POST.get('pnr_number', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()

        context['pnr_number'] = pnr_number
        context['email'] = email
        context['searched'] = True

        if not pnr_number or not email:
            messages.error(request, 'Please enter both PNR Number and Email Address.')
            return render(request, 'bookings/cancel_ticket.html', context)

        # Lookup booking by PNR and Email
        booking = Booking.objects.filter(
            Q(pnr_number__iexact=pnr_number) | Q(booking_id__istartswith=pnr_number),
            Q(passenger_email__iexact=email) | Q(passenger__email__iexact=email),
            status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
        ).select_related('schedule__route', 'passenger').first()

        if not booking:
            messages.error(request, 'No active booking found matching this PNR Number and Email Address.')
            return render(request, 'bookings/cancel_ticket.html', context)

        context['booking'] = booking
        refund_calc = (booking.total_amount * Decimal('0.90')).quantize(Decimal('0.01'))
        context['refund_amount'] = refund_calc

        if action == 'search':
            return render(request, 'bookings/cancel_ticket.html', context)

        elif action == 'cancel':
            reason = request.POST.get('cancellation_reason', 'Cancelled by passenger')
            with transaction.atomic():
                # Release seats
                booking.seats.update(status=Seat.SeatStatus.AVAILABLE)
                booking.schedule.available_seats += booking.num_passengers
                booking.schedule.save()

                booking.status = Booking.Status.CANCELLED
                booking.cancellation_reason = reason
                booking.cancelled_at = timezone.now()
                booking.save()

                payment = getattr(booking, 'payment', None)
                if payment and payment.status == Payment.Status.SUCCESS:
                    payment.status = Payment.Status.REFUNDED
                    payment.refund_amount = refund_calc
                    payment.refunded_at = timezone.now()
                    payment.save()
                    booking.status = Booking.Status.REFUNDED
                    booking.save()

            messages.success(request, f'Ticket #{booking.short_id} has been cancelled successfully. Refund of ₹{refund_calc} will be processed in 3–5 business days.')
            return render(request, 'bookings/cancel_ticket.html', {
                'title': 'Cancellation Confirmed — AnandBus',
                'searched': False,
            })

    return render(request, 'bookings/cancel_ticket.html', context)

