from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import BusPass, SpecialScheme, SchemeApplication
from .forms import StudentPassForm, PassengerPassForm, SpecialSchemeForm, SchemeApplicationForm
from routes.models import Route, Stop


def calculate_pass_fare(route, duration_months, is_student=False):
    """Calculate pass pricing based on base fare, distance, duration & student discount."""
    base_daily_fare = float(route.base_fare) if route else 25.0
    monthly_trip_count = 40  # Avg 2 trips/day * 20 working days
    base_monthly_cost = base_daily_fare * monthly_trip_count * int(duration_months)

    if is_student:
        # Student discounts: 1m=50%, 3m=60%, 6m=65%, 12m=70%
        discount_map = {1: 50, 3: 60, 6: 65, 12: 70}
        discount_pct = discount_map.get(int(duration_months), 50)
    else:
        # Passenger discounts: 1m=20%, 3m=30%, 6m=35%, 12m=40%
        discount_map = {1: 20, 3: 30, 6: 35, 12: 40}
        discount_pct = discount_map.get(int(duration_months), 20)

    discount_amount = (base_monthly_cost * discount_pct) / 100
    final_fare = base_monthly_cost - discount_amount
    return Decimal(str(round(base_monthly_cost, 2))), Decimal(str(round(final_fare, 2))), Decimal(str(discount_pct))


def student_pass_view(request):
    """Student Bus Pass application page."""
    routes = Route.objects.filter(status='ACTIVE')
    stops = Stop.objects.all()

    if request.method == 'POST':
        form = StudentPassForm(request.POST, request.FILES)
        if form.is_validated() if hasattr(form, 'is_validated') else form.is_valid():
            bus_pass = form.save(commit=False)
            bus_pass.applicant_type = BusPass.ApplicantType.STUDENT
            if request.user.is_authenticated:
                bus_pass.user = request.user

            # Fare & Validity calculation
            months = int(form.cleaned_data.get('duration_months', 1))
            orig_fare, final_fare, disc_pct = calculate_pass_fare(bus_pass.route, months, is_student=True)
            bus_pass.original_fare = orig_fare
            bus_pass.total_fare = final_fare
            bus_pass.discount_percentage = disc_pct
            bus_pass.valid_from = date.today()
            bus_pass.valid_to = date.today() + relativedelta(months=months)

            bus_pass.save()

            if request.user.is_authenticated:
                from accounts.utils import create_notification
                from accounts.models import Notification
                create_notification(
                    user=request.user,
                    title=f"🎫 Student Pass Application Submitted #{bus_pass.pass_number}",
                    message=f"Your Student Bus Pass application for route {bus_pass.route.route_name if bus_pass.route else 'All City Routes'} was submitted successfully and is pending verification.",
                    notification_type=Notification.NotificationType.PASS_SUBMITTED,
                    link="/passes/my-passes/"
                )

            messages.success(
                request,
                f"🎉 Student Bus Pass application submitted successfully! Your Pass Reference ID is {bus_pass.pass_number}. Status: Pending Verification."
            )
            return redirect('passes:my_passes')
        else:
            messages.error(request, "Please correct the highlighted errors in the form.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'applicant_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': getattr(request.user, 'phone_number', ''),
            }
        form = StudentPassForm(initial=initial_data)

    context = {
        'form': form,
        'routes': routes,
        'stops': stops,
        'page_title': 'Student Bus Pass Application — AnandBus',
    }
    return render(request, 'passes/student_pass.html', context)


def passenger_pass_view(request):
    """Passenger Commuter Bus Pass application page."""
    routes = Route.objects.filter(status='ACTIVE')
    stops = Stop.objects.all()

    if request.method == 'POST':
        form = PassengerPassForm(request.POST, request.FILES)
        if form.is_valid():
            bus_pass = form.save(commit=False)
            bus_pass.applicant_type = BusPass.ApplicantType.PASSENGER
            if request.user.is_authenticated:
                bus_pass.user = request.user

            # Fare & Validity calculation
            months = int(form.cleaned_data.get('duration_months', 1))
            orig_fare, final_fare, disc_pct = calculate_pass_fare(bus_pass.route, months, is_student=False)
            bus_pass.original_fare = orig_fare
            bus_pass.total_fare = final_fare
            bus_pass.discount_percentage = disc_pct
            bus_pass.valid_from = date.today()
            bus_pass.valid_to = date.today() + relativedelta(months=months)

            bus_pass.save()
            messages.success(
                request,
                f"🎉 Passenger Bus Pass application submitted! Pass ID: {bus_pass.pass_number}. Status: Pending Approval."
            )
            return redirect('passes:my_passes')
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'applicant_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': getattr(request.user, 'phone_number', ''),
            }
        form = PassengerPassForm(initial=initial_data)

    context = {
        'form': form,
        'routes': routes,
        'stops': stops,
        'page_title': 'Commuter Bus Pass — AnandBus',
    }
    return render(request, 'passes/passenger_pass.html', context)


def special_schemes_view(request):
    """Special Schemes listing page & application handling."""
    # Seed default sample schemes if none exist so users see rich initial schemes!
    if not SpecialScheme.objects.exists():
        SpecialScheme.objects.create(
            title='Senior Citizen Concession Scheme',
            code='SENIOR50',
            target_audience=SpecialScheme.TargetAudience.SENIOR,
            description='Enjoy 50% discount on all city and intra-district express routes for citizens aged 60 and above.',
            discount_percentage=50,
            badge_text='50% OFF Senior Care',
            is_active=True,
        )
        SpecialScheme.objects.create(
            title='Women Freedom Commute Scheme',
            code='WOMEN30',
            target_audience=SpecialScheme.TargetAudience.WOMEN,
            description='30% flat discount on monthly and quarterly passes for female passengers across Anand city.',
            discount_percentage=30,
            badge_text='30% Women Special',
            is_active=True,
        )
        SpecialScheme.objects.create(
            title='Student Higher Subsidy Scheme',
            code='STUHERO70',
            target_audience=SpecialScheme.TargetAudience.STUDENT,
            description='Special Government subsidized 70% discount for school and college students in Anand.',
            discount_percentage=70,
            badge_text='70% Mega Student Subsidy',
            is_active=True,
        )

    schemes = SpecialScheme.objects.filter(is_active=True)
    routes = Route.objects.filter(status='ACTIVE')

    if request.method == 'POST':
        scheme_id = request.POST.get('scheme_id')
        scheme = get_object_or_404(SpecialScheme, pk=scheme_id)
        app_form = SchemeApplicationForm(request.POST)

        if app_form.is_valid():
            app_inst = app_form.save(commit=False)
            app_inst.scheme = scheme
            if request.user.is_authenticated:
                app_inst.user = request.user
            app_inst.save()

            messages.success(
                request,
                f"✅ Applied successfully for scheme '{scheme.title}'! Application Ref: {app_inst.application_number}."
            )
            return redirect('passes:my_passes')
        else:
            messages.error(request, "Failed to submit scheme application. Please check form details.")

    context = {
        'schemes': schemes,
        'routes': routes,
        'app_form': SchemeApplicationForm(),
        'page_title': 'Special Bus Schemes & Subsidies — AnandBus',
    }
    return render(request, 'passes/special_schemes.html', context)


def my_passes_view(request):
    """View user pass applications and scheme applications."""
    if request.user.is_authenticated:
        user_passes = BusPass.objects.filter(user=request.user)
        user_schemes = SchemeApplication.objects.filter(user=request.user)
    else:
        user_passes = BusPass.objects.none()
        user_schemes = SchemeApplication.objects.none()

    context = {
        'user_passes': user_passes,
        'user_schemes': user_schemes,
        'page_title': 'My Pass & Scheme Applications — AnandBus',
    }
    return render(request, 'passes/my_passes.html', context)


def admin_manage_passes_view(request):
    """Admin panel to view, approve, or reject pass and scheme applications."""
    if not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'is_super_admin', False))):
        messages.error(request, "Access restricted to administrators.")
        return redirect('routes:home')

    status_filter = request.GET.get('status', 'ALL')

    # Handle quick status update POST requests
    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        item_id = request.POST.get('item_id')
        new_status = request.POST.get('new_status')

        if action_type == 'BUS_PASS':
            bpass = get_object_or_404(BusPass, pk=item_id)
            old_status = bpass.status
            bpass.status = new_status
            bpass.save()

            from accounts.models import log_admin_action, AdminAuditLog
            act_type = AdminAuditLog.ActionType.PASS_APPROVED if new_status == 'APPROVED' else AdminAuditLog.ActionType.PASS_REJECTED
            log_admin_action(
                admin_user=request.user,
                action_type=act_type,
                target_repr=f"Bus Pass #{bpass.pass_number}",
                details=f"Admin updated Bus Pass #{bpass.pass_number} status from {old_status} to {new_status} for applicant {bpass.applicant_name}.",
                request=request
            )

            if bpass.user:
                from accounts.utils import create_notification
                from accounts.models import Notification
                ntype = Notification.NotificationType.PASS_APPROVED if new_status == 'APPROVED' else Notification.NotificationType.GENERAL
                create_notification(
                    user=bpass.user,
                    title=f"🎫 Pass #{bpass.pass_number} Update: {bpass.get_status_display()}",
                    message=f"Your bus pass application #{bpass.pass_number} status has been updated to {bpass.get_status_display()}.",
                    notification_type=ntype,
                    link="/passes/my-passes/"
                )

            messages.success(request, f"Pass {bpass.pass_number} status updated to {bpass.get_status_display()}.")
        elif action_type == 'SCHEME_APP':
            sapp = get_object_or_404(SchemeApplication, pk=item_id)
            old_status = sapp.status
            sapp.status = new_status
            sapp.save()

            from accounts.models import log_admin_action, AdminAuditLog
            log_admin_action(
                admin_user=request.user,
                action_type=AdminAuditLog.ActionType.SCHEME_APP_UPDATED,
                target_repr=f"Scheme App #{sapp.application_number}",
                details=f"Admin updated Special Scheme application #{sapp.application_number} status from {old_status} to {new_status} for scheme '{sapp.scheme.title}'.",
                request=request
            )

            messages.success(request, f"Scheme Application {sapp.application_number} status updated to {sapp.get_status_display()}.")

        return redirect('passes:admin_manage_passes')


    passes_qs = BusPass.objects.all()
    schemes_qs = SchemeApplication.objects.all()

    if status_filter != 'ALL':
        passes_qs = passes_qs.filter(status=status_filter)
        schemes_qs = schemes_qs.filter(status=status_filter)

    total_passes_count = BusPass.objects.count()
    pending_passes_count = BusPass.objects.filter(status='PENDING').count()
    total_schemes_count = SpecialScheme.objects.count()

    context = {
        'passes': passes_qs,
        'scheme_apps': schemes_qs,
        'status_filter': status_filter,
        'total_passes_count': total_passes_count,
        'pending_passes_count': pending_passes_count,
        'total_schemes_count': total_schemes_count,
        'page_title': 'Admin — Manage Bus Passes & Schemes',
    }
    return render(request, 'passes/admin_manage_passes.html', context)


def admin_add_scheme_view(request):
    """Admin view to create new special schemes."""
    if not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'is_super_admin', False))):
        messages.error(request, "Access restricted to administrators.")
        return redirect('routes:home')

    if request.method == 'POST':
        form = SpecialSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save()
            messages.success(request, f"🎉 New Scheme '{scheme.title}' created successfully!")
            return redirect('passes:special_schemes')
        else:
            messages.error(request, "Failed to create scheme. Please correct form errors.")
    else:
        form = SpecialSchemeForm()

    context = {
        'form': form,
        'page_title': 'Add New Special Bus Scheme — Admin',
    }
    return render(request, 'passes/admin_add_scheme.html', context)
