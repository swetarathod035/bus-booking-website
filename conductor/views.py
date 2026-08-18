"""
Conductor portal — full operational access:
- Dashboard with assigned trips
- Trip status control & seat management
- Passenger manifest & data scan (pass + ticket)
- Offline ticket issuance
- QR code / ticket verification
- Add bus & schedule (operational, not financial)
- View bus real-time status (on-time / delayed)
"""
import json, uuid, datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Q

from accounts.decorators import conductor_required, superadmin_required
from routes.models import Schedule, Stop, RouteStop, Route
from bookings.models import Booking, Seat, Ticket, BusPass, PassUsageLog
from .models import TripLog, OfflineTicket


# ─── Dashboard ────────────────────────────────────────────────────────────────
@conductor_required
def dashboard(request):
    user  = request.user
    today = datetime.date.today()

    assigned_bus = None
    try:
        assigned_bus = user.conductor_profile.assigned_bus
    except Exception:
        pass

    if assigned_bus:
        schedules = Schedule.objects.filter(bus=assigned_bus, travel_date=today
                    ).select_related('route', 'bus', 'driver').order_by('departure_time')
    else:
        schedules = Schedule.objects.filter(travel_date=today
                    ).select_related('route', 'bus', 'driver').order_by('departure_time')

    # Pending bus pass applications (conductor can see, not approve)
    pending_passes = BusPass.objects.filter(status='PENDING').count()

    context = {
        'title': 'Conductor Dashboard',
        'schedules': schedules,
        'today': today,
        'assigned_bus': assigned_bus,
        'pending_passes': pending_passes,
    }
    return render(request, 'conductor/dashboard.html', context)


# ─── Trip Detail ──────────────────────────────────────────────────────────────
@conductor_required
def trip_detail(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    seats    = Seat.objects.filter(schedule=schedule).order_by('row_number', 'column_letter')
    bookings = Booking.objects.filter(schedule=schedule, status='CONFIRMED'
               ).select_related('passenger').prefetch_related('seats', 'passenger_details')

    trip_logs   = TripLog.objects.filter(schedule=schedule).order_by('-timestamp')[:20]
    route_stops = RouteStop.objects.filter(route=schedule.route).select_related('stop').order_by('stop_order')
    offline_tix = OfflineTicket.objects.filter(schedule=schedule).order_by('-issued_at')

    seat_grid = {}
    for seat in seats:
        row = seat.row_number
        seat_grid.setdefault(row, {})[seat.column_letter] = seat

    context = {
        'title': f'Trip — {schedule.route} | {schedule.travel_date}',
        'schedule': schedule,
        'seats': seats,
        'seat_grid': seat_grid,
        'bookings': bookings,
        'trip_logs': trip_logs,
        'route_stops': route_stops,
        'offline_tickets': offline_tix,
        'status_choices': Schedule.Status.choices,
    }
    return render(request, 'conductor/trip_detail.html', context)


# ─── Update Trip Status ────────────────────────────────────────────────────────
@require_POST
@conductor_required
def update_trip_status(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    data = json.loads(request.body)

    new_status     = data.get('status')
    stop_id        = data.get('stop_id')
    delay_minutes  = int(data.get('delay_minutes', 0))
    message_text   = data.get('message', '')

    valid_statuses = [s[0] for s in Schedule.Status.choices]
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    schedule.status        = new_status
    schedule.delay_minutes = delay_minutes
    if stop_id:
        try:
            schedule.current_stop_id = int(stop_id)
        except Exception:
            pass
    schedule.save()

    event_map = {
        'DEPARTED': TripLog.EventType.TRIP_START,
        'AT_STOP':  TripLog.EventType.AT_STOP,
        'DELAYED':  TripLog.EventType.DELAY_REPORTED,
        'COMPLETED':TripLog.EventType.TRIP_COMPLETE,
    }
    TripLog.objects.create(
        schedule=schedule,
        conductor=request.user,
        event_type=event_map.get(new_status, TripLog.EventType.AT_STOP),
        stop_id=stop_id,
        delay_minutes=delay_minutes,
        message=message_text,
    )
    return JsonResponse({'success': True, 'status': new_status, 'status_display': schedule.get_status_display()})


# ─── Update Seat Status ────────────────────────────────────────────────────────
@require_POST
@conductor_required
def update_seat_status(request, seat_id):
    seat = get_object_or_404(Seat, pk=seat_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    allowed = ['AVAILABLE', 'BLOCKED', 'RESERVED_LADIES', 'RESERVED_DISABLED']
    if new_status not in allowed:
        return JsonResponse({'error': 'Invalid seat status'}, status=400)
    seat.status = new_status
    seat.save()
    return JsonResponse({'success': True, 'seat_number': seat.seat_number, 'status': new_status})


# ─── Verify Ticket ────────────────────────────────────────────────────────────
@conductor_required
def verify_ticket(request):
    context = {'title': 'Verify Ticket / Pass'}
    if request.method == 'POST':
        ticket_number = request.POST.get('ticket_number', '').strip().upper()
        booking_id    = request.POST.get('booking_id', '').strip()

        ticket = None
        if ticket_number:
            ticket = Ticket.objects.filter(ticket_number=ticket_number).select_related(
                'booking__passenger', 'booking__schedule__route'
            ).first()
        elif booking_id:
            try:
                ticket = Ticket.objects.filter(booking__booking_id=booking_id).first()
            except Exception:
                pass

        if ticket:
            ticket.is_verified = True
            ticket.verified_at = timezone.now()
            ticket.verified_by = request.user
            ticket.save()
            context['ticket']   = ticket
            context['booking']  = ticket.booking
            context['verified'] = True

            # Load passenger details for scan
            pax_details = ticket.booking.passenger_details.select_related('seat').all()
            context['passenger_details'] = pax_details

            # Check if passenger has active pass
            try:
                active_pass = BusPass.objects.filter(
                    passenger=ticket.booking.passenger, status='ACTIVE'
                ).select_related('scheme').first()
                context['passenger_pass'] = active_pass
            except Exception:
                context['passenger_pass'] = None

            messages.success(request, f'Ticket {ticket.ticket_number} verified!')
        else:
            context['error'] = 'Ticket not found. Check the number or scan QR.'
            messages.error(request, 'Ticket not found.')

    return render(request, 'conductor/verify_ticket.html', context)


# ─── Passenger / Pass Scan ────────────────────────────────────────────────────
@conductor_required
def scan_passenger(request):
    """Conductor scans a passenger by pass number, phone, or booking ID to see their data."""
    context = {'title': 'Scan Passenger Data'}
    query   = request.GET.get('q', '').strip()

    if query:
        # Try ticket number
        ticket = Ticket.objects.filter(
            Q(ticket_number__iexact=query) |
            Q(booking__booking_id__startswith=query.lower())
        ).select_related('booking__passenger', 'booking__schedule__route').first()

        # Try pass number
        bus_pass = BusPass.objects.filter(pass_number__iexact=query).select_related(
            'passenger', 'scheme'
        ).first()

        # Try phone number
        from accounts.models import CustomUser
        user_by_phone = None
        if not ticket and not bus_pass:
            user_by_phone = CustomUser.objects.filter(phone=query).first()

        if ticket:
            context['ticket']  = ticket
            context['booking'] = ticket.booking
            context['result_type'] = 'ticket'
            # Check for pass
            try:
                context['passenger_pass'] = BusPass.objects.filter(
                    passenger=ticket.booking.passenger, status='ACTIVE'
                ).select_related('scheme').first()
            except Exception:
                pass
        elif bus_pass:
            context['bus_pass']    = bus_pass
            context['result_type'] = 'pass'
        elif user_by_phone:
            context['found_user']  = user_by_phone
            context['result_type'] = 'user'
            try:
                context['passenger_pass'] = BusPass.objects.filter(
                    passenger=user_by_phone, status='ACTIVE'
                ).select_related('scheme').first()
                context['recent_bookings'] = Booking.objects.filter(
                    passenger=user_by_phone
                ).select_related('schedule__route').order_by('-created_at')[:5]
            except Exception:
                pass
        else:
            context['not_found'] = True

        context['query'] = query

    return render(request, 'conductor/scan_passenger.html', context)


# ─── Issue Offline Ticket ─────────────────────────────────────────────────────
@conductor_required
def issue_offline_ticket(request, schedule_id):
    schedule    = get_object_or_404(Schedule, pk=schedule_id)
    route_stops = RouteStop.objects.filter(route=schedule.route).select_related('stop').order_by('stop_order')

    if request.method == 'POST':
        boarding_code    = request.POST.get('boarding_stop')
        alighting_code   = request.POST.get('alighting_stop')
        seat_nums        = request.POST.get('seat_numbers', '')
        passenger_count  = int(request.POST.get('passenger_count', 1))
        amount           = Decimal(request.POST.get('amount', '0'))

        boarding  = get_object_or_404(Stop, code=boarding_code)
        alighting = get_object_or_404(Stop, code=alighting_code)

        ticket_num = f"OT-{datetime.date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        OfflineTicket.objects.create(
            schedule=schedule, conductor=request.user,
            boarding_stop=boarding, alighting_stop=alighting,
            seat_numbers=seat_nums, passenger_count=passenger_count,
            amount_collected=amount, ticket_number=ticket_num,
        )
        schedule.total_fare_collected += amount
        schedule.save()
        messages.success(request, f'Offline ticket {ticket_num} issued for ₹{amount}.')
        return redirect('conductor:trip_detail', schedule_id=schedule_id)

    return render(request, 'conductor/offline_ticket.html', {
        'title': 'Issue Offline Ticket',
        'schedule': schedule,
        'route_stops': route_stops,
    })


# ─── Passenger Manifest ───────────────────────────────────────────────────────
@conductor_required
def passenger_manifest(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    bookings = Booking.objects.filter(schedule=schedule, status='CONFIRMED'
               ).select_related('passenger').prefetch_related('seats', 'passenger_details')
    return render(request, 'conductor/manifest.html', {
        'title': f'Passenger Manifest — {schedule}',
        'schedule': schedule,
        'bookings': bookings,
    })


# ─── Conductor: Add Bus & Schedule RBAC Restriction ────────────────────────────
@conductor_required
def conductor_add_bus(request):
    """RBAC restriction: Bus creation is restricted strictly to SuperAdmin."""
    messages.error(request, "Access Restricted: Only SuperAdmin can add buses and manage fleet.")
    return redirect('conductor:dashboard')


@conductor_required
def conductor_add_schedule(request):
    """RBAC restriction: Schedule creation is restricted strictly to SuperAdmin."""
    messages.error(request, "Access Restricted: Only SuperAdmin can add schedules and route timetables.")
    return redirect('conductor:dashboard')


# ─── AJAX: Single-Click Passenger Check-in Toggle ─────────────────────────────
@require_POST
@conductor_required
def toggle_passenger_checkin(request):
    """Single-click toggle for passenger manifest check-in status."""
    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')
        ticket = get_object_or_404(Ticket, pk=ticket_id)

        ticket.is_verified = not ticket.is_verified
        ticket.verified_at = timezone.now() if ticket.is_verified else None
        ticket.verified_by = request.user if ticket.is_verified else None
        ticket.save()

        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'is_verified': ticket.is_verified,
            'verified_at': ticket.verified_at.strftime('%H:%M:%S') if ticket.verified_at else '',
            'message': 'Passenger checked in' if ticket.is_verified else 'Check-in reverted'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─── AJAX: Conductor Emergency SOS & Breakdown Alert ──────────────────────────
@require_POST
@conductor_required
def trigger_emergency_sos(request):
    """Conductor triggers SOS Emergency / Breakdown alert to Central Admin Control Room."""
    try:
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        event_type  = data.get('event_type', 'EMERGENCY')  # EMERGENCY or BREAKDOWN
        alert_msg   = data.get('message', '').strip()

        schedule = get_object_or_404(Schedule, pk=schedule_id)

        evt_choice = TripLog.EventType.EMERGENCY if event_type == 'EMERGENCY' else TripLog.EventType.BREAKDOWN

        # Log event in TripLog
        trip_log = TripLog.objects.create(
            schedule=schedule,
            conductor=request.user,
            event_type=evt_choice,
            message=alert_msg or f"Conductor reported {event_type} on Bus {schedule.bus.bus_number}",
        )

        # Notify SuperAdmins
        from accounts.models import CustomUser, Notification
        from accounts.utils import create_notification
        admins = CustomUser.objects.filter(Q(role=CustomUser.Role.SUPER_ADMIN) | Q(is_superuser=True)).distinct()
        
        for admin in admins:
            create_notification(
                user=admin,
                title=f"🚨 CONTROL ROOM ALERT: {event_type} — Bus #{schedule.bus.bus_number}",
                message=f"Urgent: Conductor {request.user.get_full_name() or request.user.username} triggered {event_type} alert on Route {schedule.route.route_number}. Details: {trip_log.message}",
                notification_type=Notification.NotificationType.GENERAL,
                link=f"/buses/admin/duty-chart/",
                send_email=True,
                send_sms=True
            )

        return JsonResponse({
            'success': True,
            'event_type': event_type,
            'message': f"🚨 Emergency {event_type} alert broadcasted to Central Admin Control Room!",
            'timestamp': trip_log.timestamp.strftime('%H:%M:%S')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



# ─── AJAX: Verify QR ──────────────────────────────────────────────────────────
@require_GET
@conductor_required
def api_verify_qr(request):
    ticket_number = request.GET.get('ticket', '').strip().upper()
    ticket = Ticket.objects.filter(ticket_number=ticket_number).select_related('booking').first()
    if ticket:
        # Also check for active pass
        try:
            active_pass = BusPass.objects.filter(
                passenger=ticket.booking.passenger, status='ACTIVE'
            ).select_related('scheme').first()
            pass_info = {
                'has_pass': True,
                'pass_number': active_pass.pass_number,
                'scheme': active_pass.scheme.name,
                'valid_until': str(active_pass.valid_until),
            } if active_pass else {'has_pass': False}
        except Exception:
            pass_info = {'has_pass': False}

        return JsonResponse({
            'valid': True,
            'ticket_number': ticket.ticket_number,
            'passenger': ticket.booking.passenger_name,
            'route': str(ticket.booking.schedule.route),
            'date': str(ticket.booking.schedule.travel_date),
            'seats': [s.seat_number for s in ticket.booking.seats.all()],
            'already_verified': ticket.is_verified,
            'pass_info': pass_info,
        })
    return JsonResponse({'valid': False, 'message': 'Ticket not found'})
