"""
Conductor portal views.
- Trip status control
- Seat / passenger manifest
- Offline ticket sales
- QR verification
"""
import json
import uuid
import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from accounts.decorators import conductor_required
from routes.models import Schedule, Stop, RouteStop
from bookings.models import Booking, Seat, Ticket
from .models import TripLog, OfflineTicket


@conductor_required
def dashboard(request):
    """Conductor main dashboard — today's assigned trips."""
    user = request.user
    today = datetime.date.today()

    # Get bus assigned to this conductor
    assigned_bus = None
    try:
        assigned_bus = user.conductor_profile.assigned_bus
    except Exception:
        pass

    if assigned_bus:
        schedules = Schedule.objects.filter(
            bus=assigned_bus,
            travel_date=today,
        ).select_related('route', 'bus', 'driver').order_by('departure_time')
    else:
        schedules = Schedule.objects.filter(
            travel_date=today,
        ).select_related('route', 'bus', 'driver').order_by('departure_time')

    context = {
        'title': 'Conductor Dashboard',
        'schedules': schedules,
        'today': today,
        'assigned_bus': assigned_bus,
    }
    return render(request, 'conductor/dashboard.html', context)


@conductor_required
def trip_detail(request, schedule_id):
    """Detailed trip view: passenger manifest, seat status, trip controls."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    seats = Seat.objects.filter(schedule=schedule).order_by('row_number', 'column_letter')
    bookings = Booking.objects.filter(
        schedule=schedule, status__in=['CONFIRMED']
    ).select_related('passenger').prefetch_related('seats')

    trip_logs = TripLog.objects.filter(schedule=schedule).order_by('-timestamp')[:20]
    route_stops = RouteStop.objects.filter(route=schedule.route).select_related('stop').order_by('stop_order')

    # Build seat grid
    seat_grid = {}
    for seat in seats:
        row = seat.row_number
        if row not in seat_grid:
            seat_grid[row] = {}
        seat_grid[row][seat.column_letter] = seat

    offline_tickets = OfflineTicket.objects.filter(schedule=schedule).order_by('-issued_at')

    context = {
        'title': f'Trip — {schedule.route} | {schedule.travel_date}',
        'schedule': schedule,
        'seats': seats,
        'seat_grid': seat_grid,
        'bookings': bookings,
        'trip_logs': trip_logs,
        'route_stops': route_stops,
        'offline_tickets': offline_tickets,
        'status_choices': Schedule.Status.choices,
    }
    return render(request, 'conductor/trip_detail.html', context)


@require_POST
@conductor_required
def update_trip_status(request, schedule_id):
    """Update live trip status and log event."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    data = json.loads(request.body)

    new_status = data.get('status')
    stop_id = data.get('stop_id')
    delay_minutes = int(data.get('delay_minutes', 0))
    message_text = data.get('message', '')

    valid_statuses = [s[0] for s in Schedule.Status.choices]
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    schedule.status = new_status
    schedule.delay_minutes = delay_minutes
    if stop_id:
        try:
            schedule.current_stop_id = stop_id
        except Exception:
            pass
    schedule.save()

    # Create trip log
    event_map = {
        'DEPARTED': TripLog.EventType.TRIP_START,
        'AT_STOP': TripLog.EventType.AT_STOP,
        'DELAYED': TripLog.EventType.DELAY_REPORTED,
        'COMPLETED': TripLog.EventType.TRIP_COMPLETE,
    }
    event_type = event_map.get(new_status, TripLog.EventType.AT_STOP)

    TripLog.objects.create(
        schedule=schedule,
        conductor=request.user,
        event_type=event_type,
        stop_id=stop_id,
        delay_minutes=delay_minutes,
        message=message_text,
    )

    return JsonResponse({'success': True, 'status': new_status, 'status_display': schedule.get_status_display()})


@require_POST
@conductor_required
def update_seat_status(request, seat_id):
    """Conductor manually updates a seat status."""
    seat = get_object_or_404(Seat, pk=seat_id)
    data = json.loads(request.body)
    new_status = data.get('status')

    allowed = ['AVAILABLE', 'BLOCKED', 'RESERVED_LADIES', 'RESERVED_DISABLED']
    if new_status not in allowed:
        return JsonResponse({'error': 'Invalid seat status'}, status=400)

    seat.status = new_status
    seat.save()
    return JsonResponse({'success': True, 'seat_number': seat.seat_number, 'status': new_status})


@conductor_required
def verify_ticket(request):
    """QR Code / ticket number verification page."""
    context = {'title': 'Verify Ticket'}
    if request.method == 'POST':
        ticket_number = request.POST.get('ticket_number', '').strip().upper()
        booking_id = request.POST.get('booking_id', '').strip()

        ticket = None
        if ticket_number:
            ticket = Ticket.objects.filter(ticket_number=ticket_number).first()
        elif booking_id:
            try:
                ticket = Ticket.objects.filter(booking__booking_id=booking_id).first()
            except Exception:
                pass

        if ticket:
            # Mark as verified
            ticket.is_verified = True
            ticket.verified_at = timezone.now()
            ticket.verified_by = request.user
            ticket.save()
            context['ticket'] = ticket
            context['booking'] = ticket.booking
            context['verified'] = True
            messages.success(request, f'✅ Ticket {ticket.ticket_number} verified successfully!')
        else:
            context['error'] = 'Ticket not found. Please check the number.'
            messages.error(request, 'Ticket not found.')

    return render(request, 'conductor/verify_ticket.html', context)


@conductor_required
def issue_offline_ticket(request, schedule_id):
    """Issue cash ticket offline."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    route_stops = RouteStop.objects.filter(route=schedule.route).select_related('stop').order_by('stop_order')

    if request.method == 'POST':
        boarding_code = request.POST.get('boarding_stop')
        alighting_code = request.POST.get('alighting_stop')
        seat_nums = request.POST.get('seat_numbers', '')
        passenger_count = int(request.POST.get('passenger_count', 1))
        amount = Decimal(request.POST.get('amount', '0'))

        boarding = get_object_or_404(Stop, code=boarding_code)
        alighting = get_object_or_404(Stop, code=alighting_code)

        ticket_num = f"OT-{datetime.date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        OfflineTicket.objects.create(
            schedule=schedule,
            conductor=request.user,
            boarding_stop=boarding,
            alighting_stop=alighting,
            seat_numbers=seat_nums,
            passenger_count=passenger_count,
            amount_collected=amount,
            ticket_number=ticket_num,
        )

        # Update schedule revenue
        schedule.total_fare_collected += amount
        schedule.save()

        messages.success(request, f'Offline ticket {ticket_num} issued for ₹{amount}.')
        return redirect('conductor:trip_detail', schedule_id=schedule_id)

    context = {
        'title': 'Issue Offline Ticket',
        'schedule': schedule,
        'route_stops': route_stops,
    }
    return render(request, 'conductor/offline_ticket.html', context)


@conductor_required
def passenger_manifest(request, schedule_id):
    """Full passenger manifest for a trip."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    bookings = Booking.objects.filter(
        schedule=schedule, status='CONFIRMED'
    ).select_related('passenger').prefetch_related('seats', 'passenger_details')

    context = {
        'title': f'Passenger Manifest — {schedule}',
        'schedule': schedule,
        'bookings': bookings,
    }
    return render(request, 'conductor/manifest.html', context)


@require_GET
@conductor_required
def api_verify_qr(request):
    """AJAX QR scan verification."""
    ticket_number = request.GET.get('ticket', '').strip().upper()
    ticket = Ticket.objects.filter(ticket_number=ticket_number).select_related('booking').first()
    if ticket:
        return JsonResponse({
            'valid': True,
            'ticket_number': ticket.ticket_number,
            'passenger': ticket.booking.passenger_name,
            'route': str(ticket.booking.schedule.route),
            'date': str(ticket.booking.schedule.travel_date),
            'seats': [s.seat_number for s in ticket.booking.seats.all()],
            'already_verified': ticket.is_verified,
        })
    return JsonResponse({'valid': False, 'message': 'Ticket not found'})
