"""
SuperAdmin dashboard and bus/driver/route management views.
"""
import json
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


# ─── Route & Schedule Management ─────────────────────────────────────────────
@superadmin_required
def route_management(request):
    routes = Route.objects.all().select_related('source', 'destination')
    return render(request, 'buses/route_management.html', {'routes': routes, 'title': 'Manage Routes'})


@superadmin_required
def schedule_management(request):
    today = date.today()
    schedules = Schedule.objects.filter(
        travel_date__gte=today
    ).select_related('route', 'bus', 'driver').order_by('travel_date', 'departure_time')
    return render(request, 'buses/schedule_management.html', {
        'schedules': schedules, 'title': 'Manage Schedules'
    })


# ─── User Management ──────────────────────────────────────────────────────────
@superadmin_required
def user_management(request):
    from accounts.models import CustomUser
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'buses/user_management.html', {'users': users, 'title': 'Manage Users'})


@superadmin_required
def promote_user(request, user_id):
    from accounts.models import CustomUser
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, pk=user_id)
        new_role = request.POST.get('role')
        if new_role in dict(CustomUser.Role.choices):
            user.role = new_role
            user.save()
            messages.success(request, f'{user.username} role updated to {new_role}.')
    return redirect('buses:user_management')


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

    # Auto-width columns
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


# ─── AJAX: Toggle schedule status ────────────────────────────────────────────
@superadmin_required
def api_toggle_schedule_status(request, schedule_id):
    if request.method == 'POST':
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        valid = [s[0] for s in Schedule.Status.choices]
        if new_status in valid:
            schedule.status = new_status
            schedule.save()
            return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'success': False}, status=400)
