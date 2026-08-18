"""
SuperAdmin dashboard and bus/driver/route management views.
"""
import json, datetime
from datetime import date, timedelta
from decimal import Decimal


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.decorators import superadmin_required
from .models import Bus, Driver
from routes.models import Route, Schedule, Stop, RouteStop
from bookings.models import Booking, Payment, Ticket


@superadmin_required
def admin_dashboard(request):
    """SuperAdmin main analytics dashboard."""
    today = date.today()
    this_month_start = today.replace(day=1)

    # KPI cards
    total_buses = Bus.objects.filter(status='ACTIVE').count()
    total_routes = Route.objects.filter(status='ACTIVE').count()
    today_schedules = Schedule.objects.filter(travel_date=today).count()
    total_bookings = Booking.objects.filter(status='CONFIRMED').count()

    # Revenue stats
    monthly_revenue = Payment.objects.filter(
        status='SUCCESS', paid_at__date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    today_revenue = Payment.objects.filter(
        status='SUCCESS', paid_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Chart data: last 7 days revenue
    revenue_chart = []
    labels = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = Payment.objects.filter(
            status='SUCCESS', paid_at__date=d
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_chart.append(float(rev))
        labels.append(d.strftime('%d %b'))

    # Recent bookings
    recent_bookings = Booking.objects.filter(
        status='CONFIRMED'
    ).select_related('passenger', 'schedule__route').order_by('-created_at')[:10]

    # Booking status pie
    booking_stats = Booking.objects.values('status').annotate(count=Count('id'))
    pie_labels = [b['status'] for b in booking_stats]
    pie_data = [b['count'] for b in booking_stats]

    # Driver Punctuality & Bus Cleanliness Ratings stats
    from bookings.models import RideRating
    from django.db.models import Avg
    rating_stats = RideRating.objects.aggregate(
        avg_punctuality=Avg('driver_punctuality'),
        avg_cleanliness=Avg('bus_cleanliness'),
        avg_staff=Avg('staff_behavior'),
        avg_overall=Avg('overall_rating'),
        total_reviews=Count('id')
    )
    recent_reviews = RideRating.objects.select_related('passenger', 'driver', 'bus', 'schedule__route').order_by('-created_at')[:6]

    context = {
        'title': 'Admin Dashboard — AnandBus',
        'total_buses': total_buses,
        'total_routes': total_routes,
        'today_schedules': today_schedules,
        'total_bookings': total_bookings,
        'monthly_revenue': monthly_revenue,
        'today_revenue': today_revenue,
        'revenue_chart': json.dumps(revenue_chart),
        'revenue_labels': json.dumps(labels),
        'pie_labels': json.dumps(pie_labels),
        'pie_data': json.dumps(pie_data),
        'recent_bookings': recent_bookings,
        'rating_stats': rating_stats,
        'recent_reviews': recent_reviews,
        'today': today,
    }
    return render(request, 'buses/admin_dashboard.html', context)



# ─── Bus CRUD ─────────────────────────────────────────────────────────────────
@superadmin_required
def bus_list(request):
    buses = Bus.objects.all().order_by('bus_number')
    return render(request, 'buses/bus_list.html', {'buses': buses, 'title': 'Manage Buses'})


@superadmin_required
def bus_create(request):
    from .forms import BusForm
    if request.method == 'POST':
        form = BusForm(request.POST, request.FILES)
        if form.is_valid():
            bus = form.save()
            messages.success(request, f'Bus {bus.bus_number} added successfully.')
            return redirect('buses:bus_list')
    else:
        form = BusForm()
    return render(request, 'buses/bus_form.html', {'form': form, 'title': 'Add New Bus', 'action': 'Add'})


@superadmin_required
def bus_edit(request, pk):
    from .forms import BusForm
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        form = BusForm(request.POST, request.FILES, instance=bus)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bus {bus.bus_number} updated.')
            return redirect('buses:bus_list')
    else:
        form = BusForm(instance=bus)
    return render(request, 'buses/bus_form.html', {'form': form, 'title': 'Edit Bus', 'action': 'Save', 'bus': bus})


@superadmin_required
def bus_toggle(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if bus.status == 'ACTIVE':
        bus.status = 'INACTIVE'
        messages.warning(request, f'Bus {bus.bus_number} disabled.')
    else:
        bus.status = 'ACTIVE'
        messages.success(request, f'Bus {bus.bus_number} enabled.')
    bus.save()
    return redirect('buses:bus_list')


@superadmin_required
def bus_delete(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        b_num = bus.bus_number
        bus.delete()
        messages.success(request, f'Bus {b_num} deleted successfully.')
    return redirect('buses:bus_list')


# ─── Driver CRUD ──────────────────────────────────────────────────────────────
@superadmin_required
def driver_list(request):
    drivers = Driver.objects.all().select_related('assigned_bus')
    return render(request, 'buses/driver_list.html', {'drivers': drivers, 'title': 'Manage Drivers'})


@superadmin_required
def driver_create(request):
    from .forms import DriverForm
    if request.method == 'POST':
        form = DriverForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save()
            messages.success(request, f'Driver {driver.name} added.')
            return redirect('buses:driver_list')
    else:
        form = DriverForm()
    return render(request, 'buses/driver_form.html', {'form': form, 'title': 'Add Driver', 'action': 'Add'})


@superadmin_required
def driver_edit(request, pk):
    from .forms import DriverForm
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f'Driver {driver.name} updated.')
            return redirect('buses:driver_list')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'buses/driver_form.html', {'form': form, 'title': 'Edit Driver', 'action': 'Save'})


@superadmin_required
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        d_name = driver.name
        driver.delete()
        messages.success(request, f'Driver {d_name} deleted successfully.')
    return redirect('buses:driver_list')


# ─── Route & Schedule Management ─────────────────────────────────────────────
@superadmin_required
def route_management(request):
    routes = Route.objects.all().select_related('source', 'destination')
    return render(request, 'buses/route_management.html', {'routes': routes, 'title': 'Manage Routes'})


@superadmin_required
def route_create(request):
    from .forms import RouteForm
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f'Route {route.route_number} added successfully.')
            return redirect('buses:route_management')
    else:
        form = RouteForm()
    return render(request, 'buses/route_form.html', {'form': form, 'title': 'Add New Route', 'action': 'Add'})


@superadmin_required
def route_edit(request, pk):
    from .forms import RouteForm
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f'Route {route.route_number} updated.')
            return redirect('buses:route_management')
    else:
        form = RouteForm(instance=route)
    return render(request, 'buses/route_form.html', {'form': form, 'title': 'Edit Route', 'action': 'Save', 'route': route})


@superadmin_required
def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        r_num = route.route_number
        route.delete()
        messages.success(request, f'Route {r_num} deleted successfully.')
    return redirect('buses:route_management')


@superadmin_required
def schedule_management(request):
    today = date.today()
    schedules = Schedule.objects.filter(
        travel_date__gte=today
    ).select_related('route', 'bus', 'driver').order_by('travel_date', 'departure_time')
    return render(request, 'buses/schedule_management.html', {
        'schedules': schedules, 'title': 'Manage Schedules'
    })


@superadmin_required
def schedule_create(request):
    from .forms import ScheduleForm
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            sch = form.save()
            from accounts.models import log_admin_action, AdminAuditLog
            log_admin_action(
                admin_user=request.user,
                action_type=AdminAuditLog.ActionType.SCHEDULE_CREATED,
                target_repr=f"Schedule #{sch.id} (Route {sch.route.route_number})",
                details=f"Created schedule on {sch.travel_date} (Dep: {sch.departure_time.strftime('%H:%M')}, Arr: {sch.arrival_time.strftime('%H:%M')}) using Bus {sch.bus.bus_number}.",
                request=request
            )
            messages.success(request, f'Schedule for route {sch.route.route_number} created.')
            return redirect('buses:schedule_management')
    else:
        form = ScheduleForm()
    return render(request, 'buses/schedule_form.html', {'form': form, 'title': 'Add Schedule', 'action': 'Add'})


@superadmin_required
def schedule_edit(request, pk):
    from .forms import ScheduleForm
    sch = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=sch)
        if form.is_valid():
            sch = form.save()
            from accounts.models import log_admin_action, AdminAuditLog
            log_admin_action(
                admin_user=request.user,
                action_type=AdminAuditLog.ActionType.SCHEDULE_UPDATED,
                target_repr=f"Schedule #{sch.id} (Route {sch.route.route_number})",
                details=f"Updated schedule parameters for travel date {sch.travel_date} (Dep: {sch.departure_time.strftime('%H:%M')}, Status: {sch.get_status_display()}).",
                request=request
            )
            messages.success(request, 'Schedule updated.')
            return redirect('buses:schedule_management')
    else:
        form = ScheduleForm(instance=sch)
    return render(request, 'buses/schedule_form.html', {'form': form, 'title': 'Edit Schedule', 'action': 'Save', 'schedule': sch})


@superadmin_required
def schedule_delete(request, pk):
    sch = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        sch_repr = f"Schedule #{sch.id} (Route {sch.route.route_number} on {sch.travel_date})"
        sch.delete()
        from accounts.models import log_admin_action, AdminAuditLog
        log_admin_action(
            admin_user=request.user,
            action_type=AdminAuditLog.ActionType.SCHEDULE_DELETED,
            target_repr=sch_repr,
            details=f"Deleted schedule permanently.",
            request=request
        )
        messages.success(request, 'Schedule deleted successfully.')
    return redirect('buses:schedule_management')



# ─── User Management & Roles Directory ─────────────────────────────────────────
@superadmin_required
def user_management(request):
    from accounts.models import CustomUser
    role_filter = request.GET.get('role', '')
    query = request.GET.get('q', '').strip()

    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Calculate counts per role
    total_users_count = CustomUser.objects.count()
    admin_count = CustomUser.objects.filter(role=CustomUser.Role.SUPER_ADMIN).count()
    conductor_count = CustomUser.objects.filter(role=CustomUser.Role.CONDUCTOR).count()
    passenger_count = CustomUser.objects.filter(role=CustomUser.Role.PASSENGER).count()

    if role_filter in dict(CustomUser.Role.choices):
        users = users.filter(role=role_filter)
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'buses/user_management.html', {
        'users': users,
        'title': 'Users & Roles Directory — AnandBus',
        'current_role': role_filter,
        'query': query,
        'role_choices': CustomUser.Role.choices,
        'total_users_count': total_users_count,
        'admin_count': admin_count,
        'conductor_count': conductor_count,
        'passenger_count': passenger_count,
    })


@superadmin_required
def user_create(request):
    from .forms import UserCreateForm
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('buses:user_management')
    else:
        form = UserCreateForm()
    return render(request, 'buses/user_form.html', {'form': form, 'title': 'Add New User', 'action': 'Add'})


@superadmin_required
def user_edit(request, user_id):
    from accounts.models import CustomUser
    from .forms import UserEditForm
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated.')
            return redirect('buses:user_management')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'buses/user_form.html', {'form': form, 'title': 'Edit User', 'action': 'Save', 'user_obj': user})


@superadmin_required
def promote_user(request, user_id):
    from accounts.models import CustomUser
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, pk=user_id)
        new_role = request.POST.get('role')
        if new_role in dict(CustomUser.Role.choices):
            old_role_display = user.get_role_display()
            user.role = new_role
            user.save()

            from accounts.models import log_admin_action, AdminAuditLog
            log_admin_action(
                admin_user=request.user,
                action_type=AdminAuditLog.ActionType.USER_PROMOTED,
                target_repr=f"User @{user.username}",
                details=f"Admin updated role for user {user.get_full_name() or user.username} from {old_role_display} to {user.get_role_display()}.",
                request=request
            )
            messages.success(request, f'Role for {user.username} updated to {user.get_role_display()}.')
    return redirect('buses:user_management')



@superadmin_required
def user_delete(request, user_id):
    from accounts.models import CustomUser
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'You cannot delete your own logged-in admin account.')
        else:
            uname = user.username
            user.delete()
            messages.success(request, f'User {uname} deleted successfully.')
    return redirect('buses:user_management')


# ─── Bus Stop CRUD ───────────────────────────────────────────────────────────
@superadmin_required
def stop_list(request):
    stops = Stop.objects.all().order_by('name')
    query = request.GET.get('q', '').strip()
    if query:
        stops = stops.filter(Q(name__icontains=query) | Q(code__icontains=query) | Q(address__icontains=query))
    return render(request, 'buses/stop_list.html', {'stops': stops, 'title': 'Manage Bus Stops', 'query': query})


@superadmin_required
def stop_create(request):
    from .forms import StopForm
    if request.method == 'POST':
        form = StopForm(request.POST, request.FILES)
        if form.is_valid():
            stop = form.save()
            messages.success(request, f'Bus stop {stop.name} added successfully.')
            return redirect('buses:stop_list')
    else:
        form = StopForm()
    return render(request, 'buses/stop_form.html', {'form': form, 'title': 'Add New Bus Stop', 'action': 'Add'})


@superadmin_required
def stop_edit(request, pk):
    from .forms import StopForm
    stop = get_object_or_404(Stop, pk=pk)
    if request.method == 'POST':
        form = StopForm(request.POST, request.FILES, instance=stop)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bus stop {stop.name} updated.')
            return redirect('buses:stop_list')
    else:
        form = StopForm(instance=stop)
    return render(request, 'buses/stop_form.html', {'form': form, 'title': 'Edit Bus Stop', 'action': 'Save', 'stop': stop})


@superadmin_required
def stop_delete(request, pk):
    stop = get_object_or_404(Stop, pk=pk)
    if request.method == 'POST':
        name = stop.name
        stop.delete()
        messages.success(request, f'Bus stop {name} deleted successfully.')
    return redirect('buses:stop_list')


# ─── Booking Admin CRUD ───────────────────────────────────────────────────────
@superadmin_required
def booking_admin_list(request):
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()
    bookings = Booking.objects.all().select_related('passenger', 'schedule__route').order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if query:
        bookings = bookings.filter(
            Q(booking_id__icontains=query) |
            Q(passenger__username__icontains=query) |
            Q(passenger__email__icontains=query) |
            Q(passenger_name__icontains=query)
        )
    return render(request, 'buses/booking_admin_list.html', {
        'bookings': bookings,
        'title': 'Manage Bookings',
        'current_status': status_filter,
        'query': query,
        'status_choices': Booking.Status.choices,
    })


@superadmin_required
def booking_admin_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Booking.Status.choices):
            booking.status = new_status
            booking.save()
            messages.success(request, f'Booking {booking.short_id} status updated to {booking.get_status_display()}.')
    return redirect('buses:booking_admin_list')


@superadmin_required
def booking_admin_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        bid = booking.short_id
        booking.delete()
        messages.success(request, f'Booking {bid} deleted successfully.')
    return redirect('buses:booking_admin_list')


# ─── Pass Verifier ────────────────────────────────────────────────────────────
def pass_verifier_page(request):
    """Pass verification interface replacing legacy pass_verifier.php."""
    from bookings.models import BusPass
    pass_number = request.GET.get('pass_number', '').strip().upper()
    bus_pass = None
    searched = False
    if pass_number:
        searched = True
        bus_pass = BusPass.objects.filter(pass_number=pass_number).select_related('passenger', 'scheme').first()

    return render(request, 'buses/pass_verifier.html', {
        'title': 'Pass Verifier — AnandBus',
        'pass_number': pass_number,
        'bus_pass': bus_pass,
        'searched': searched,
    })


# ─── Revenue Reports ──────────────────────────────────────────────────────────
@superadmin_required
def revenue_report(request):
    payments = Payment.objects.filter(
        status='SUCCESS'
    ).select_related('booking__passenger', 'booking__schedule__route').order_by('-paid_at')[:100]
    total = payments.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'buses/revenue_report.html', {
        'payments': payments, 'total': total, 'title': 'Revenue Report'
    })


@superadmin_required
def export_bookings_excel(request):
    """Export all bookings to Excel (.xlsx)."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Bookings'

    headers = ['Booking ID', 'Passenger', 'Email', 'Route', 'Date', 'Seats', 'Amount', 'Status', 'Booked On']
    header_fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    bookings = Booking.objects.select_related(
        'passenger', 'schedule__route'
    ).order_by('-created_at')

    for row_num, booking in enumerate(bookings, 2):
        seat_nums = ', '.join([s.seat_number for s in booking.seats.all()])
        ws.append([
            str(booking.booking_id)[:8].upper(),
            booking.passenger.get_full_name() or booking.passenger.username,
            booking.passenger.email,
            str(booking.schedule.route),
            str(booking.schedule.travel_date),
            seat_nums,
            float(booking.total_amount),
            booking.status,
            booking.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="anandbus_bookings.xlsx"'
    return response


# ─── Digital Conductor Duty Chart ──────────────────────────────────────────────
@superadmin_required
def duty_chart_view(request):
    """Digital Conductor & Driver Duty Chart Portal."""
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            target_date = datetime.date.today()
    else:
        target_date = datetime.date.today()

    schedules = Schedule.objects.filter(
        travel_date=target_date
    ).select_related('route', 'bus', 'driver').order_by('departure_time')

    # Fetch conductor profiles
    from accounts.models import ConductorProfile
    conductor_profiles = ConductorProfile.objects.select_related('user', 'assigned_bus').all()

    duty_roster = []
    for sch in schedules:
        assigned_conductor = None
        for cp in conductor_profiles:
            if cp.assigned_bus_id == sch.bus_id:
                assigned_conductor = cp.user.get_full_name() or cp.user.username
                break

        dep_hour = sch.departure_time.hour
        if dep_hour < 12:
            shift_name = "Morning Shift (06:00 - 14:00)"
        elif dep_hour < 18:
            shift_name = "Afternoon Shift (14:00 - 22:00)"
        else:
            shift_name = "Night Shift (22:00 - 06:00)"

        duty_roster.append({
            'schedule': sch,
            'bus': sch.bus,
            'driver': sch.driver,
            'conductor_name': assigned_conductor or "Ramesh Patel (Default Duty)",
            'route': sch.route,
            'departure_time': sch.departure_time,
            'arrival_time': sch.arrival_time,
            'shift': shift_name,
            'status': sch.get_status_display(),
            'status_code': sch.status,
        })

    return render(request, 'buses/duty_chart.html', {
        'title': 'Digital Conductor Duty Chart',
        'target_date': target_date,
        'duty_roster': duty_roster,
        'total_trips': len(duty_roster),
    })


# ─── Quick E-Ticket Verification ──────────────────────────────────────────────
def quick_verify_ticket_view(request):
    """Quick E-Ticket Verification for Conductors, Inspectors & Examiners."""
    from bookings.models import Ticket, Booking
    ticket_query = request.GET.get('ticket_id', '').strip().upper()
    ticket_result = None
    verification_status = None
    
    if ticket_query:
        t = Ticket.objects.filter(
            Q(ticket_number__iexact=ticket_query) |
            Q(booking__booking_id__startswith=ticket_query.lower())
        ).select_related('booking__passenger', 'booking__schedule__route', 'booking__schedule__bus').first()

        if t:
            ticket_result = t
            travel_date = t.booking.schedule.travel_date
            if travel_date < datetime.date.today():
                verification_status = 'EXPIRED'
            elif t.booking.status in ['CANCELLED', 'REFUNDED']:
                verification_status = 'CANCELLED'
            else:
                verification_status = 'VALID'
        else:
            verification_status = 'INVALID'

    return render(request, 'buses/quick_verify.html', {
        'title': 'Quick E-Ticket Verification',
        'ticket_query': ticket_query,
        'ticket_result': ticket_result,
        'verification_status': verification_status,
    })


# ─── AJAX: Toggle schedule status ────────────────────────────────────────────
@superadmin_required
def api_toggle_schedule_status(request, schedule_id):
    if request.method == 'POST':
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        valid = [s[0] for s in Schedule.Status.choices]
        if new_status in valid:
            old_status = schedule.status
            schedule.status = new_status
            schedule.save()

            from accounts.models import log_admin_action, AdminAuditLog
            log_admin_action(
                admin_user=request.user,
                action_type=AdminAuditLog.ActionType.SCHEDULE_STATUS_CHANGED,
                target_repr=f"Schedule #{schedule.id} ({schedule.route.route_number})",
                details=f"Status toggled from {old_status} to {new_status} for travel date {schedule.travel_date}.",
                request=request
            )
            return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'success': False}, status=400)


# ─── Admin Activity Audit Logs Portal ──────────────────────────────────────────
@superadmin_required
def admin_audit_logs(request):
    """SuperAdmin view to track and filter all administrative activity logs."""
    from accounts.models import AdminAuditLog, CustomUser

    action_filter = request.GET.get('action', '')
    user_filter   = request.GET.get('user', '')
    query         = request.GET.get('q', '').strip()

    audit_logs = AdminAuditLog.objects.select_related('admin_user').all()

    if action_filter:
        audit_logs = audit_logs.filter(action_type=action_filter)
    if user_filter and user_filter.isdigit():
        audit_logs = audit_logs.filter(admin_user_id=int(user_filter))
    if query:
        audit_logs = audit_logs.filter(
            Q(target_repr__icontains=query) |
            Q(details__icontains=query) |
            Q(admin_user__username__icontains=query) |
            Q(admin_user__first_name__icontains=query) |
            Q(admin_user__last_name__icontains=query)
        )

    admin_users = CustomUser.objects.filter(
        Q(role=CustomUser.Role.SUPER_ADMIN) | Q(is_staff=True) | Q(is_superuser=True)
    ).distinct()

    return render(request, 'buses/admin_audit_logs.html', {
        'title': 'Admin Activity Audit Logs — AnandBus',
        'audit_logs': audit_logs[:150],
        'action_choices': AdminAuditLog.ActionType.choices,
        'admin_users': admin_users,
        'current_action': action_filter,
        'current_user': user_filter,
        'query': query,
        'total_logs_count': AdminAuditLog.objects.count(),
    })












