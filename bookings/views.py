"""
Booking engine views: seat selection, payment, tickets, passenger dashboard.
"""
import json, uuid, datetime, re
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count

from accounts.decorators import passenger_required, login_required
from routes.models import Schedule, Route, RouteStop, Stop
from .models import Booking, Seat, Payment, Ticket, PassengerDetail, BusPass, RideRating
from .utils import generate_seat_layout, calculate_fare, generate_ticket_pdf, send_booking_email


# ─── Passenger Dashboard ──────────────────────────────────────────────────────
@passenger_required
def passenger_dashboard(request):
    user  = request.user
    today = datetime.date.today()

    upcoming = Booking.objects.filter(
        passenger=user,
        status__in=['CONFIRMED', 'PENDING'],
        schedule__travel_date__gte=today,
    ).select_related('schedule__route', 'schedule__bus').prefetch_related('seats').order_by(
        'schedule__travel_date', 'schedule__departure_time'
    )

    past = Booking.objects.filter(
        passenger=user,
    ).filter(
        Q(status__in=['COMPLETED', 'CANCELLED', 'REFUNDED']) | Q(schedule__travel_date__lt=today)
    ).select_related('schedule__route', 'schedule__bus', 'schedule__driver', 'ride_rating').order_by('-created_at')[:20]


    # ── Linear graph: bookings per day for last 14 days ──────────────────────
    graph_labels = []
    graph_data   = []
    for i in range(13, -1, -1):
        d = today - datetime.timedelta(days=i)
        count = Booking.objects.filter(
            passenger=user,
            created_at__date=d,
        ).count()
        graph_labels.append(d.strftime('%d %b'))
        graph_data.append(count)

    # Active booked buses live tracking data
    booked_buses_data = []
    from tracking.models import BusLocation, STOP_COORDINATES
    for b in upcoming:
        sch = b.schedule
        loc = BusLocation.objects.filter(schedule=sch).order_by('-timestamp').first()
        route_stops = RouteStop.objects.filter(route=sch.route).select_related('stop').order_by('stop_order')
        stops_list = []
        for rs in route_stops:
            coords = STOP_COORDINATES.get(rs.stop.code, (float(rs.stop.latitude or 22.5645), float(rs.stop.longitude or 72.9289)))
            stops_list.append({
                'name': rs.stop.name,
                'code': rs.stop.code,
                'lat': coords[0],
                'lng': coords[1],
            })

        default_lat = float(loc.latitude) if loc else (stops_list[0]['lat'] if stops_list else 22.5645)
        default_lng = float(loc.longitude) if loc else (stops_list[0]['lng'] if stops_list else 72.9289)

        booked_buses_data.append({
            'booking_id': str(b.booking_id),
            'short_id': b.short_id,
            'schedule_id': sch.id,
            'bus_number': sch.bus.bus_number,
            'bus_name': sch.bus.bus_name,
            'route_name': sch.route.route_name,
            'departure_time': sch.departure_time.strftime('%H:%M'),
            'travel_date': sch.travel_date.strftime('%Y-%m-%d'),
            'status': sch.get_status_display(),
            'lat': default_lat,
            'lng': default_lng,
            'speed': float(loc.speed_kmh) if loc else 38.0,
            'eta': loc.eta_minutes if loc else 12,
            'stops': stops_list,
        })

    active_passes = BusPass.objects.filter(
        passenger=user,
        status=BusPass.Status.ACTIVE,
        valid_until__gte=today
    ).select_related('scheme')

    # Student Pass Renewal Alert check (expires within 5 days / 3-day urgency alert)
    renewal_alert = None
    show_renewal_modal = False
    for p in active_passes:
        days_left = (p.valid_until - today).days
        if 0 <= days_left <= 5:
            renewal_alert = {
                'pass_number': p.pass_number,
                'scheme_name': p.scheme.title if p.scheme else 'Student Bus Pass',
                'days_left': days_left,
                'valid_until': p.valid_until,
            }
            if days_left <= 3:
                show_renewal_modal = True
                # Trigger In-App Notification & Email Alert
                from accounts.utils import create_notification
                from accounts.models import Notification
                create_notification(
                    user=user,
                    title=f"🚨 Student Pass Renewal Alert! #{p.pass_number}",
                    message=f"Urgent: Your {p.scheme.title if p.scheme else 'Student Bus Pass'} (#{p.pass_number}) expires in {days_left} day{'s' if days_left != 1 else ''} on {p.valid_until.strftime('%d %b %Y')}. Renew now to maintain uninterrupted student travel benefits.",
                    notification_type=Notification.NotificationType.GENERAL,
                    link="/passes/student-pass/",
                    send_email=True,
                    send_sms=True
                )
            break

    # Carbon Footprint Saver metric computation
    confirmed_bookings = Booking.objects.filter(
        passenger=user,
        status__in=['CONFIRMED', 'COMPLETED']
    ).select_related('schedule__route')

    total_km_traveled = 0.0
    for b in confirmed_bookings:
        dist = float(b.schedule.route.distance_km or 15.0)
        total_km_traveled += dist * b.num_passengers

    co2_saved_kg = round(total_km_traveled * 0.090, 1)  # ~90g CO2 saved per km per pax vs personal vehicle
    trees_equivalent = round(co2_saved_kg / 20.0, 1)     # ~20kg CO2 per tree/year

    context = {
        'title': 'My Dashboard — AnandBus',
        'upcoming_bookings': upcoming,
        'past_bookings': past,
        'user': user,
        'graph_labels': json.dumps(graph_labels),
        'graph_data': json.dumps(graph_data),
        'total_bookings': Booking.objects.filter(passenger=user).count(),
        'active_passes': active_passes,
        'renewal_alert': renewal_alert,
        'show_renewal_modal': show_renewal_modal,
        'eco_stats': {
            'total_km': round(total_km_traveled, 1),
            'co2_saved_kg': co2_saved_kg,
            'trees_equivalent': trees_equivalent,
        },
        'booked_buses_json': json.dumps(booked_buses_data),
    }
    return render(request, 'bookings/passenger_dashboard.html', context)


# ─── Seat Selection ───────────────────────────────────────────────────────────
@passenger_required
def select_seats(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    if not schedule.is_available:
        messages.error(request, 'This schedule is no longer available for booking.')
        return redirect('routes:search')

    if not Seat.objects.filter(schedule=schedule).exists():
        generate_seat_layout(schedule)

    seats       = Seat.objects.filter(schedule=schedule).order_by('row_number', 'column_letter')
    route_stops = RouteStop.objects.filter(route=schedule.route).select_related('stop').order_by('stop_order')

    boarding_code  = request.GET.get('from', '')
    alighting_code = request.GET.get('to', '')
    seat_ids_str   = request.GET.get('seat_ids', '')
    selected_seat_ids = []
    if seat_ids_str:
        try:
            selected_seat_ids = [int(s) for s in seat_ids_str.split(',') if s.strip()]
        except ValueError:
            pass

    seats_param = request.GET.get('seats', '')
    num_seats   = int(seats_param) if (seats_param and seats_param.isdigit()) else (len(selected_seat_ids) or 1)

    base_fare = float(schedule.route.calculate_fare())
    seat_grid = {}
    for seat in seats:
        seat_grid.setdefault(seat.row_number, {})[seat.column_letter] = seat

    return render(request, 'bookings/seat_selection.html', {
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
    })


# ─── Passenger Info (Step 2) ──────────────────────────────────────────────────
@passenger_required
def passenger_info(request):
    """Step 2: Fill in passenger details, then POST → create booking → redirect to payment."""
    if request.method == 'GET':
        schedule_id    = request.GET.get('schedule_id')
        seat_ids_str   = request.GET.get('seat_ids', '')
        boarding_code  = request.GET.get('boarding_stop', '')
        alighting_code = request.GET.get('alighting_stop', '')

        if not all([schedule_id, seat_ids_str, boarding_code, alighting_code]):
            messages.error(request, 'Invalid booking parameters. Please select seats again.')
            return redirect('routes:search')

        try:
            seat_ids = [int(s) for s in seat_ids_str.split(',') if s.strip()]
        except ValueError:
            messages.error(request, 'Invalid seat selection.')
            return redirect('routes:search')

        schedule      = get_object_or_404(Schedule, pk=schedule_id)
        boarding_stop = get_object_or_404(Stop, code=boarding_code)
        alighting_stop= get_object_or_404(Stop, code=alighting_code)
        selected_seats = Seat.objects.filter(id__in=seat_ids, schedule=schedule)

        if selected_seats.count() != len(seat_ids):
            messages.error(request, 'One or more seats are no longer valid. Please re-select.')
            return redirect('bookings:select_seats', schedule_id=schedule.id)

        fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(selected_seats))

        return render(request, 'bookings/passenger_info.html', {
            'title': 'Passenger Information — AnandBus',
            'schedule': schedule,
            'boarding_stop': boarding_stop,
            'alighting_stop': alighting_stop,
            'selected_seats': selected_seats,
            'seat_ids_str': seat_ids_str,
            'fare_data': fare_data,
        })

    # POST: validate → create booking → redirect to payment
    schedule_id    = request.POST.get('schedule_id')
    seat_ids_str   = request.POST.get('seat_ids', '')
    boarding_code  = request.POST.get('boarding_stop')
    alighting_code = request.POST.get('alighting_stop')

    try:
        seat_ids = [int(s) for s in seat_ids_str.split(',') if s.strip()]
    except (ValueError, AttributeError):
        messages.error(request, 'Invalid seat selection.')
        return redirect('routes:search')

    schedule      = get_object_or_404(Schedule, pk=schedule_id)
    boarding_stop = get_object_or_404(Stop, code=boarding_code)
    alighting_stop= get_object_or_404(Stop, code=alighting_code)
    selected_seats = list(Seat.objects.filter(id__in=seat_ids, schedule=schedule))

    passengers_data = []
    errors = []
    for idx in range(len(selected_seats)):
        name   = request.POST.get(f'name_{idx}', '').strip()
        age_s  = request.POST.get(f'age_{idx}', '').strip()
        gender = request.POST.get(f'gender_{idx}', '').strip()
        email  = request.POST.get(f'email_{idx}', '').strip()
        phone  = request.POST.get(f'phone_{idx}', '').strip()

        passengers_data.append({'name': name, 'age': age_s, 'gender': gender, 'email': email, 'phone': phone})

        if not name or len(name) < 2 or not re.match(r'^[A-Za-z\s]+$', name):
            errors.append(f'Passenger {idx+1}: Name must contain only letters (min 2 chars).')
        if not age_s or not age_s.isdigit() or not (1 <= int(age_s) <= 99):
            errors.append(f'Passenger {idx+1}: Age must be 1–99.')
        if gender not in ('M', 'F', 'O'):
            errors.append(f'Passenger {idx+1}: Please select gender.')
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append(f'Passenger {idx+1}: Enter a valid email address.')
        if not phone or not re.match(r'^\d{10}$', phone):
            errors.append(f'Passenger {idx+1}: Enter a valid 10-digit phone number.')

    if errors:
        for err in errors:
            messages.error(request, err)
        fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(selected_seats))
        return render(request, 'bookings/passenger_info.html', {
            'title': 'Passenger Information — AnandBus',
            'schedule': schedule,
            'boarding_stop': boarding_stop,
            'alighting_stop': alighting_stop,
            'selected_seats': selected_seats,
            'seat_ids_str': seat_ids_str,
            'fare_data': fare_data,
            'passengers_input': passengers_data,
        })

    with transaction.atomic():
        seats_qs = Seat.objects.select_for_update().filter(id__in=seat_ids, schedule=schedule, status='AVAILABLE')
        seats    = list(seats_qs)
        if len(seats) != len(seat_ids):
            messages.error(request, 'Some seats are no longer available. Please re-select.')
            return redirect('bookings:select_seats', schedule_id=schedule.id)

        fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(seat_ids))
        primary   = passengers_data[0]

        booking = Booking.objects.create(
            passenger      = request.user,
            schedule       = schedule,
            boarding_stop  = boarding_stop,
            alighting_stop = alighting_stop,
            num_passengers = len(seat_ids),
            status         = Booking.Status.PENDING,
            base_amount    = Decimal(str(fare_data['base_amount'])),
            tax_amount     = Decimal(str(fare_data['tax_amount'])),
            convenience_fee= Decimal(str(fare_data['convenience_fee'])),
            discount_amount= Decimal(str(fare_data['discount_amount'])),
            total_amount   = Decimal(str(fare_data['total_amount'])),
            passenger_name = primary['name'],
            passenger_email= primary['email'],
            passenger_phone= primary['phone'],
        )
        booking.seats.set(seats)
        Seat.objects.filter(id__in=seat_ids).update(status=Seat.SeatStatus.BOOKED)
        schedule.available_seats = max(0, schedule.available_seats - len(seat_ids))
        schedule.save()

        for idx, seat in enumerate(seats):
            pax = passengers_data[idx]
            PassengerDetail.objects.create(
                booking=booking, seat=seat,
                name=pax['name'], age=int(pax['age']),
                gender=pax['gender'], email=pax['email'], phone=pax['phone'],
            )

    # ✅ Redirect directly to payment page
    return redirect('bookings:booking_payment', booking_id=booking.booking_id)


# ─── Create Booking (AJAX) ────────────────────────────────────────────────────
@require_POST
@passenger_required
def create_booking(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    schedule_id      = data.get('schedule_id')
    seat_ids         = data.get('seat_ids', [])
    boarding_code    = data.get('boarding_stop')
    alighting_code   = data.get('alighting_stop')
    passengers_data  = data.get('passengers', [])

    if not all([schedule_id, seat_ids, boarding_code, alighting_code]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    schedule      = get_object_or_404(Schedule, pk=schedule_id)
    boarding_stop = get_object_or_404(Stop, code=boarding_code)
    alighting_stop= get_object_or_404(Stop, code=alighting_code)

    with transaction.atomic():
        seats_qs = Seat.objects.select_for_update().filter(id__in=seat_ids, schedule=schedule, status='AVAILABLE')
        seats    = list(seats_qs)
        if len(seats) != len(seat_ids):
            return JsonResponse({'error': 'Some seats are no longer available.'}, status=409)

        fare_data = calculate_fare(schedule, boarding_stop, alighting_stop, len(seat_ids))

        booking = Booking.objects.create(
            passenger=request.user, schedule=schedule,
            boarding_stop=boarding_stop, alighting_stop=alighting_stop,
            num_passengers=len(seat_ids), status=Booking.Status.PENDING,
            base_amount=fare_data['base_amount'], tax_amount=fare_data['tax_amount'],
            convenience_fee=fare_data['convenience_fee'], discount_amount=fare_data['discount_amount'],
            total_amount=fare_data['total_amount'],
            passenger_name=request.user.get_full_name() or request.user.username,
            passenger_email=request.user.email,
            passenger_phone=getattr(request.user, 'phone', '') or '',
        )
        booking.seats.set(seats)
        Seat.objects.filter(id__in=seat_ids).update(status=Seat.SeatStatus.BOOKED)
        schedule.available_seats = max(0, schedule.available_seats - len(seat_ids))
        schedule.save()

        for i, pax in enumerate(passengers_data):
            if i < len(seats):
                PassengerDetail.objects.create(
                    booking=booking, seat=seats[i],
                    name=pax.get('name', request.user.get_full_name()),
                    age=pax.get('age', 25), gender=pax.get('gender', 'M'),
                )

    return JsonResponse({
        'success': True,
        'booking_id': str(booking.booking_id),
        'total_amount': float(booking.total_amount),
        'fare_breakdown': fare_data,
    })


# ─── Payment Page ─────────────────────────────────────────────────────────────
@passenger_required
def booking_payment(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)

    if booking.status != Booking.Status.PENDING:
        messages.info(request, 'This booking has already been processed.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    razorpay_order_id = None
    if settings.RAZORPAY_KEY_ID and not settings.RAZORPAY_KEY_ID.startswith('rzp_test_XXXX'):
        try:
            import razorpay
            client    = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            rz_order  = client.order.create({'amount': int(booking.total_amount * 100), 'currency': 'INR',
                                              'receipt': str(booking.booking_id)[:20]})
            razorpay_order_id = rz_order['id']
            payment, _ = Payment.objects.get_or_create(booking=booking,
                          defaults={'amount': booking.total_amount, 'gateway': Payment.Gateway.RAZORPAY})
            payment.gateway_order_id = razorpay_order_id
            payment.save()
        except Exception:
            pass

    return render(request, 'bookings/payment.html', {
        'title': f'Payment — Booking #{booking.short_id}',
        'booking': booking,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount_paise': int(booking.total_amount * 100),
    })


# ─── Payment Success ───────────────────────────────────────────────────────────
@require_POST
@passenger_required
def payment_success(request):
    booking_id         = request.POST.get('booking_id')
    razorpay_payment_id= request.POST.get('razorpay_payment_id', '')
    razorpay_order_id  = request.POST.get('razorpay_order_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    booking  = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    is_demo  = (razorpay_signature == 'demo_sig' or razorpay_payment_id.startswith('demo_')
                or not settings.RAZORPAY_KEY_ID
                or settings.RAZORPAY_KEY_ID.startswith('rzp_test_XXXX'))
    verified = True

    if not is_demo and settings.RAZORPAY_KEY_ID:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id':  razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature':  razorpay_signature,
            })
        except Exception:
            verified = False

    if verified:
        with transaction.atomic():
            booking.status = Booking.Status.CONFIRMED
            booking.save()

            payment, _ = Payment.objects.get_or_create(booking=booking,
                          defaults={'amount': booking.total_amount})
            payment.status             = Payment.Status.SUCCESS
            payment.gateway_payment_id = razorpay_payment_id
            payment.gateway_order_id   = razorpay_order_id
            payment.gateway_signature  = razorpay_signature
            payment.paid_at            = timezone.now()
            payment.save()

            ticket = Ticket(booking=booking)
            ticket.generate_ticket_number()
            ticket.save()
            try:
                generate_ticket_pdf(ticket)
            except Exception:
                pass
            try:
                send_booking_email(booking)
            except Exception:
                pass

            # In-App Notification + Email + SMS/WhatsApp Alert
            from accounts.utils import create_notification
            from accounts.models import Notification
            create_notification(
                user=booking.passenger,
                title=f"🎉 Booking Confirmed #{booking.short_id}",
                message=f"Your trip on {booking.schedule.route.route_name} for {booking.schedule.travel_date} ({booking.schedule.departure_time.strftime('%H:%M')}) is confirmed. PNR: {booking.short_id}.",
                notification_type=Notification.NotificationType.BOOKING_CONFIRMED,
                link=f"/bookings/detail/{booking.booking_id}/"
            )

        messages.success(request, f'Booking confirmed! Ticket #{ticket.ticket_number} sent to your email.')
        return redirect('bookings:booking_success', booking_id=booking_id)
    else:
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('bookings:booking_payment', booking_id=booking_id)


# ─── Booking Success ──────────────────────────────────────────────────────────
@passenger_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    ticket  = getattr(booking, 'ticket', None)
    return render(request, 'bookings/booking_success.html', {
        'title': 'Booking Confirmed!', 'booking': booking, 'ticket': ticket,
    })


# ─── Booking Detail ───────────────────────────────────────────────────────────
@passenger_required
def booking_detail(request, booking_id):
    booking         = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    ticket          = getattr(booking, 'ticket', None)
    passenger_details = booking.passenger_details.select_related('seat').all()
    return render(request, 'bookings/booking_detail.html', {
        'title': f'Booking #{booking.short_id}',
        'booking': booking, 'ticket': ticket, 'passenger_details': passenger_details,
    })


# ─── Download Ticket ──────────────────────────────────────────────────────────
@passenger_required
def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    ticket  = get_object_or_404(Ticket, booking=booking)
    if not ticket.pdf_file:
        try:
            generate_ticket_pdf(ticket)
        except Exception as e:
            messages.error(request, f'Could not generate PDF: {e}')
            return redirect('bookings:booking_detail', booking_id=booking_id)
    return FileResponse(ticket.pdf_file.open('rb'), content_type='application/pdf',
                        as_attachment=True, filename=f'AnandBus_{ticket.ticket_number}.pdf')


# ─── Cancel Booking ───────────────────────────────────────────────────────────
@require_POST
@passenger_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    if booking.status not in ['CONFIRMED', 'PENDING']:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    reason = request.POST.get('reason', 'Cancelled by passenger')
    with transaction.atomic():
        booking.seats.update(status=Seat.SeatStatus.AVAILABLE)
        booking.schedule.available_seats += booking.seats.count()
        booking.schedule.save()
        booking.status             = Booking.Status.CANCELLED
        booking.cancellation_reason= reason
        booking.cancelled_at       = timezone.now()
        booking.save()

        payment = getattr(booking, 'payment', None)
        if payment and payment.status == Payment.Status.SUCCESS:
            payment.status     = Payment.Status.REFUNDED
            payment.refunded_at= timezone.now()
            payment.save()
            booking.status = Booking.Status.REFUNDED
            booking.save()

    from accounts.utils import create_notification
    from accounts.models import Notification
    create_notification(
        user=booking.passenger,
        title=f"⚠️ Booking Cancelled #{booking.short_id}",
        message=f"Your booking for {booking.schedule.route.route_name} on {booking.schedule.travel_date} has been cancelled. Refund will reflect in 3-5 days.",
        notification_type=Notification.NotificationType.BOOKING_CANCELLED,
        link="/bookings/dashboard/"
    )

    messages.success(request, 'Booking cancelled. Refund in 3–5 business days.')
    return redirect('bookings:passenger_dashboard')


# ─── Reschedule Booking ────────────────────────────────────────────────────────
@require_POST
@passenger_required
def reschedule_booking(request, booking_id):
    original       = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)
    new_schedule_id= request.POST.get('new_schedule_id')
    if original.status != 'CONFIRMED':
        messages.error(request, 'Only confirmed bookings can be rescheduled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    new_schedule = get_object_or_404(Schedule, pk=new_schedule_id)
    with transaction.atomic():
        original.seats.update(status=Seat.SeatStatus.AVAILABLE)
        original.schedule.available_seats += original.seats.count()
        original.schedule.save()
        original.status = Booking.Status.RESCHEDULED
        original.save()

        new_booking = Booking.objects.create(
            passenger=request.user, schedule=new_schedule,
            boarding_stop=original.boarding_stop, alighting_stop=original.alighting_stop,
            num_passengers=original.num_passengers, status=Booking.Status.PENDING,
            base_amount=original.base_amount, tax_amount=original.tax_amount,
            convenience_fee=original.convenience_fee, total_amount=original.total_amount,
            original_booking=original,
        )

    messages.success(request, 'Booking rescheduled. Please complete payment.')
    return redirect('bookings:booking_payment', booking_id=new_booking.booking_id)


# ─── Public Cancel/Reschedule pages ──────────────────────────────────────────
def reschedule_ticket_page(request):
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    context = {'title': 'Reschedule Ticket', 'searched': False, 'today_str': today_str}

    if request.method == 'POST':
        action      = request.POST.get('action', 'search')
        pnr         = request.POST.get('pnr_number', '').strip().upper()
        email       = request.POST.get('email', '').strip().lower()
        new_date_str= request.POST.get('new_travel_date', '')

        context.update({'pnr_number': pnr, 'email': email, 'new_travel_date': new_date_str, 'searched': True})

        if not pnr or not email:
            messages.error(request, 'Please enter both PNR Number and Email.')
            return render(request, 'bookings/reschedule_ticket.html', context)

        booking = Booking.objects.filter(
            Q(booking_id__startswith=pnr.lower()),
            Q(passenger_email__iexact=email) | Q(passenger__email__iexact=email),
            status=Booking.Status.CONFIRMED,
        ).select_related('schedule__route', 'schedule__bus').first()

        if not booking:
            messages.error(request, 'No confirmed booking found for this PNR and email.')
            return render(request, 'bookings/reschedule_ticket.html', context)

        context['booking'] = booking

        if action == 'reschedule' and new_date_str:
            try:
                new_date = datetime.datetime.strptime(new_date_str, '%Y-%m-%d').date()
                if new_date < datetime.date.today():
                    messages.error(request, 'Reschedule date cannot be in the past.')
                    return render(request, 'bookings/reschedule_ticket.html', context)

                with transaction.atomic():
                    new_schedule = Schedule.objects.filter(
                        route=booking.schedule.route, travel_date=new_date,
                        status__in=[Schedule.Status.SCHEDULED, Schedule.Status.DELAYED],
                    ).first() or Schedule.objects.create(
                        route=booking.schedule.route, bus=booking.schedule.bus,
                        driver=booking.schedule.driver,
                        departure_time=booking.schedule.departure_time,
                        arrival_time=booking.schedule.arrival_time, travel_date=new_date,
                        available_seats=booking.schedule.bus.total_seats,
                        status=Schedule.Status.SCHEDULED,
                    )

                    booking.seats.update(status=Seat.SeatStatus.AVAILABLE)
                    booking.schedule.available_seats += booking.num_passengers
                    booking.schedule.save()

                    if not Seat.objects.filter(schedule=new_schedule).exists():
                        generate_seat_layout(new_schedule)

                    new_seats = list(Seat.objects.filter(
                        schedule=new_schedule, status=Seat.SeatStatus.AVAILABLE
                    )[:booking.num_passengers])
                    if len(new_seats) < booking.num_passengers:
                        messages.error(request, 'Not enough available seats on the selected date.')
                        return render(request, 'bookings/reschedule_ticket.html', context)

                    Seat.objects.filter(id__in=[s.id for s in new_seats]).update(status=Seat.SeatStatus.BOOKED)
                    new_schedule.available_seats -= len(new_seats)
                    new_schedule.save()
                    booking.schedule = new_schedule
                    booking.seats.set(new_seats)
                    booking.save()

                messages.success(request, f'Ticket rescheduled to {new_date.strftime("%d %b %Y")}!')
            except ValueError:
                messages.error(request, 'Invalid date.')

    return render(request, 'bookings/reschedule_ticket.html', context)


def cancel_ticket_page(request):
    context = {'title': 'Cancel Ticket', 'searched': False}

    if request.method == 'POST':
        action = request.POST.get('action', 'search')
        pnr    = request.POST.get('pnr_number', '').strip().upper()
        email  = request.POST.get('email', '').strip().lower()
        context.update({'pnr_number': pnr, 'email': email, 'searched': True})

        if not pnr or not email:
            messages.error(request, 'Please enter both PNR Number and Email.')
            return render(request, 'bookings/cancel_ticket.html', context)

        booking = Booking.objects.filter(
            Q(booking_id__startswith=pnr.lower()),
            Q(passenger_email__iexact=email) | Q(passenger__email__iexact=email),
            status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
        ).select_related('schedule__route').first()

        if not booking:
            messages.error(request, 'No active booking found.')
            return render(request, 'bookings/cancel_ticket.html', context)

        refund = (booking.total_amount * Decimal('0.90')).quantize(Decimal('0.01'))
        context.update({'booking': booking, 'refund_amount': refund})

        if action == 'cancel':
            reason = request.POST.get('cancellation_reason', 'Cancelled by passenger')
            with transaction.atomic():
                booking.seats.update(status=Seat.SeatStatus.AVAILABLE)
                booking.schedule.available_seats += booking.num_passengers
                booking.schedule.save()
                booking.status             = Booking.Status.CANCELLED
                booking.cancellation_reason= reason
                booking.cancelled_at       = timezone.now()
                booking.save()

                payment = getattr(booking, 'payment', None)
                if payment and payment.status == Payment.Status.SUCCESS:
                    payment.status      = Payment.Status.REFUNDED
                    payment.refund_amount= refund
                    payment.refunded_at = timezone.now()
                    payment.save()
                    booking.status = Booking.Status.REFUNDED
                    booking.save()

            messages.success(request, f'Ticket cancelled. Refund of ₹{refund} in 3–5 business days.')
            return render(request, 'bookings/cancel_ticket.html', {'title': 'Cancellation Confirmed', 'searched': False})

    return render(request, 'bookings/cancel_ticket.html', context)


# ─── AJAX Fare Calculator ─────────────────────────────────────────────────────
@require_GET
def api_calculate_fare(request):
    schedule = get_object_or_404(Schedule, pk=request.GET.get('schedule_id'))
    from_stop= get_object_or_404(Stop, code=request.GET.get('from'))
    to_stop  = get_object_or_404(Stop, code=request.GET.get('to'))
    num_seats= int(request.GET.get('seats', 1))
    return JsonResponse(calculate_fare(schedule, from_stop, to_stop, num_seats))


# ─── Submit Ride Rating & Review ──────────────────────────────────────────────
@require_POST
@passenger_required
def submit_ride_rating(request, booking_id):
    """Passenger submits Driver Punctuality & Bus Cleanliness rating/feedback for a trip."""
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)

    if hasattr(booking, 'ride_rating'):
        messages.info(request, 'You have already submitted a rating for this trip. Thank you!')
        return redirect('bookings:passenger_dashboard')

    try:
        driver_punctuality = int(request.POST.get('driver_punctuality', 5))
        bus_cleanliness    = int(request.POST.get('bus_cleanliness', 5))
        staff_behavior     = int(request.POST.get('staff_behavior', 5))
        overall_rating     = int(request.POST.get('overall_rating', 5))
        comment            = request.POST.get('comment', '').strip()

        # Clamp ratings between 1 and 5
        driver_punctuality = max(1, min(5, driver_punctuality))
        bus_cleanliness    = max(1, min(5, bus_cleanliness))
        staff_behavior     = max(1, min(5, staff_behavior))
        overall_rating     = max(1, min(5, overall_rating))

        RideRating.objects.create(
            booking=booking,
            passenger=request.user,
            schedule=booking.schedule,
            driver=booking.schedule.driver,
            bus=booking.schedule.bus,
            driver_punctuality=driver_punctuality,
            bus_cleanliness=bus_cleanliness,
            staff_behavior=staff_behavior,
            overall_rating=overall_rating,
            comment=comment,
        )

        messages.success(request, '🌟 Thank you for rating your ride! Your feedback helps us maintain high quality service.')
    except Exception as e:
        messages.error(request, f'Failed to submit review: {e}')

    return redirect('bookings:passenger_dashboard')

