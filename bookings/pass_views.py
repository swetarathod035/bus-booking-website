"""
Bus Pass views — apply, manage, view passes & schemes.
"""
import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from accounts.decorators import passenger_required, superadmin_required, conductor_required
from .models import PassScheme, BusPass, PassUsageLog


# ─── Passenger: View all schemes ─────────────────────────────────────────────
@passenger_required
def pass_schemes_list(request):
    """Passenger can browse all active pass schemes."""
    schemes = PassScheme.objects.filter(is_active=True).prefetch_related('applicable_routes')
    my_passes = BusPass.objects.filter(passenger=request.user).select_related('scheme').order_by('-created_at')
    return render(request, 'bookings/pass_schemes.html', {
        'title': 'Bus Passes & Special Schemes',
        'schemes': schemes,
        'my_passes': my_passes,
    })


# ─── Passenger: Apply for a pass ─────────────────────────────────────────────
@passenger_required
def apply_for_pass(request, scheme_id):
    """Passenger applies for a specific pass scheme."""
    scheme = get_object_or_404(PassScheme, id=scheme_id, is_active=True)

    if request.method == 'POST':
        id_proof_type   = request.POST.get('id_proof_type', '').strip()
        id_proof_number = request.POST.get('id_proof_number', '').strip()
        institution     = request.POST.get('institution_name', '').strip()
        photo           = request.FILES.get('photo')
        id_proof_doc    = request.FILES.get('id_proof_doc')

        # Validate for student/special passes
        errors = []
        if scheme.scheme_type == PassScheme.SchemeType.STUDENT:
            if not institution:
                errors.append('Institution/College name is required for Student Pass.')
            if not id_proof_number:
                errors.append('Student ID / Enrollment number is required.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'bookings/apply_pass.html', {
                'title': f'Apply — {scheme.name}',
                'scheme': scheme,
            })

        today = datetime.date.today()
        valid_until = today + datetime.timedelta(days=scheme.validity_days)

        bus_pass = BusPass(
            passenger       = request.user,
            scheme          = scheme,
            valid_from      = today,
            valid_until     = valid_until,
            amount_paid     = scheme.price,
            id_proof_type   = id_proof_type,
            id_proof_number = id_proof_number,
            institution_name = institution,
        )
        if photo:
            bus_pass.photo = photo
        if id_proof_doc:
            bus_pass.id_proof_doc = id_proof_doc

        bus_pass.save()
        bus_pass.generate_pass_number()
        bus_pass.save()

        messages.success(request,
            f'Application for {scheme.name} submitted (Pass #{bus_pass.pass_number}). '
            f'It will be activated after admin approval.'
        )
        return redirect('bookings:my_passes')

    return render(request, 'bookings/apply_pass.html', {
        'title': f'Apply for {scheme.name}',
        'scheme': scheme,
    })


# ─── Passenger: My passes ────────────────────────────────────────────────────
@passenger_required
def my_passes(request):
    passes = BusPass.objects.filter(passenger=request.user).select_related('scheme').order_by('-created_at')
    return render(request, 'bookings/my_passes.html', {
        'title': 'My Bus Passes',
        'passes': passes,
    })


# ─── Admin: Manage all passes ─────────────────────────────────────────────────
@superadmin_required
def admin_pass_list(request):
    passes = BusPass.objects.all().select_related('passenger', 'scheme').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        passes = passes.filter(status=status_filter)
    return render(request, 'buses/admin_pass_list.html', {
        'title': 'Bus Pass Applications',
        'passes': passes,
        'status_choices': BusPass.Status.choices,
        'current_status': status_filter,
    })


@require_POST
@superadmin_required
def admin_approve_pass(request, pass_id):
    bus_pass = get_object_or_404(BusPass, id=pass_id)
    action = request.POST.get('action')
    from accounts.models import log_admin_action, AdminAuditLog
    if action == 'approve':
        bus_pass.status = BusPass.Status.ACTIVE
        bus_pass.approved_by = request.user
        bus_pass.approved_at = timezone.now()
        bus_pass.save()

        log_admin_action(
            admin_user=request.user,
            action_type=AdminAuditLog.ActionType.PASS_APPROVED,
            target_repr=f"Bus Pass #{bus_pass.pass_number}",
            details=f"Admin approved bus pass #{bus_pass.pass_number} ({bus_pass.scheme.name}) for passenger {bus_pass.passenger.get_full_name() or bus_pass.passenger.username}.",
            request=request
        )
        messages.success(request, f'Pass {bus_pass.pass_number} approved and activated.')
    elif action == 'reject':
        bus_pass.status = BusPass.Status.REJECTED
        reason = request.POST.get('reason', 'Does not meet eligibility criteria.')
        bus_pass.rejection_reason = reason
        bus_pass.save()

        log_admin_action(
            admin_user=request.user,
            action_type=AdminAuditLog.ActionType.PASS_REJECTED,
            target_repr=f"Bus Pass #{bus_pass.pass_number}",
            details=f"Admin rejected bus pass #{bus_pass.pass_number} ({bus_pass.scheme.name}). Reason: {reason}",
            request=request
        )
        messages.warning(request, f'Pass {bus_pass.pass_number} rejected.')
    return redirect('bookings:admin_pass_list')



# ─── Admin: Manage pass schemes ───────────────────────────────────────────────
@superadmin_required
def admin_scheme_list(request):
    schemes = PassScheme.objects.all().order_by('scheme_type')
    return render(request, 'buses/admin_scheme_list.html', {
        'title': 'Pass Schemes Management',
        'schemes': schemes,
    })


@superadmin_required
def admin_scheme_create(request):
    from buses.forms import PassSchemeForm
    if request.method == 'POST':
        form = PassSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save()
            messages.success(request, f'Scheme "{scheme.name}" created.')
            return redirect('bookings:admin_scheme_list')
    else:
        form = PassSchemeForm()
    return render(request, 'buses/admin_scheme_form.html', {
        'title': 'Create Pass Scheme',
        'form': form,
        'action': 'Create',
    })


@superadmin_required
def admin_scheme_edit(request, scheme_id):
    from buses.forms import PassSchemeForm
    scheme = get_object_or_404(PassScheme, id=scheme_id)
    if request.method == 'POST':
        form = PassSchemeForm(request.POST, instance=scheme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scheme updated.')
            return redirect('bookings:admin_scheme_list')
    else:
        form = PassSchemeForm(instance=scheme)
    return render(request, 'buses/admin_scheme_form.html', {
        'title': 'Edit Pass Scheme',
        'form': form,
        'action': 'Save',
        'scheme': scheme,
    })


# ─── Conductor: Scan pass ────────────────────────────────────────────────────
@require_GET
@conductor_required
def conductor_scan_pass(request):
    """AJAX: Conductor scans a bus pass number or encrypted QR token to verify & log usage."""
    raw_input   = request.GET.get('pass', '').strip()
    schedule_id = request.GET.get('schedule_id', '')
    boarding    = request.GET.get('boarding', '')
    alighting   = request.GET.get('alighting', '')

    if not raw_input:
        return JsonResponse({'valid': False, 'message': 'Pass number or QR code token required'})

    # Support Encrypted QR Token verification
    if raw_input.startswith('ABTOKEN.'):
        from .utils import verify_secure_qr_token
        is_token_valid, result = verify_secure_qr_token(raw_input)
        if not is_token_valid:
            return JsonResponse({'valid': False, 'message': f'QR Verification Failed: {result}'})
        pass_number = result.get('pass', '').strip().upper()
    else:
        pass_number = raw_input.upper()

    bus_pass = BusPass.objects.filter(pass_number=pass_number).select_related(
        'passenger', 'scheme'
    ).first()

    if not bus_pass:
        return JsonResponse({'valid': False, 'message': 'Pass not found'})

    if not bus_pass.is_valid_today:
        return JsonResponse({
            'valid': False,
            'message': f'Pass is {bus_pass.get_status_display()} or expired. Valid until: {bus_pass.valid_until}',
            'pass_number': pass_number,
            'passenger': bus_pass.passenger.get_full_name(),
            'status': bus_pass.status,
        })

    # Log usage
    log_data = {
        'bus_pass': bus_pass,
        'verified_by': request.user,
    }
    if schedule_id:
        from routes.models import Schedule
        try:
            log_data['schedule'] = Schedule.objects.get(id=schedule_id)
        except Exception:
            pass

    from routes.models import Stop
    if boarding:
        try:
            log_data['boarding'] = Stop.objects.get(code=boarding)
        except Exception:
            pass
    if alighting:
        try:
            log_data['alighting'] = Stop.objects.get(code=alighting)
        except Exception:
            pass

    PassUsageLog.objects.create(**log_data)

    # Increment trips_used if limited
    if bus_pass.scheme.trip_limit > 0 and not bus_pass.scheme.unlimited_trips:
        bus_pass.trips_used += 1
        bus_pass.save()

    return JsonResponse({
        'valid': True,
        'message': 'PASS VALID',
        'pass_status_display': 'PASS VALID',
        'pass_number': bus_pass.pass_number,
        'passenger': bus_pass.passenger.get_full_name() or bus_pass.passenger.username,
        'passenger_phone': bus_pass.passenger.phone or '—',
        'pass_type': bus_pass.scheme.get_scheme_type_display(),
        'scheme_name': bus_pass.scheme.name,
        'institution': bus_pass.institution_name or '—',
        'valid_until': str(bus_pass.valid_until),
        'trips_used': bus_pass.trips_used,
        'trips_remaining': str(bus_pass.trips_remaining),
        'discount_pct': float(bus_pass.scheme.discount_pct),
    })


# ─── Admin: Trigger Expiry Alerts ─────────────────────────────────────────────
@superadmin_required
def trigger_pass_expiry_alerts(request):
    """Admin triggers automated email alerts for passes expiring within 3 days."""
    from .utils import send_pass_expiry_notifications
    count = send_pass_expiry_notifications(days_ahead=3)
    messages.success(request, f'Automated pass expiry alerts triggered! {count} email notifications sent.')
    return redirect('bookings:admin_pass_list')
