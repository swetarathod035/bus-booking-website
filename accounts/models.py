from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Extended User model with role-based access control.
    Roles: SUPER_ADMIN, CONDUCTOR, PASSENGER
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
        CONDUCTOR = 'CONDUCTOR', _('Conductor')
        PASSENGER = 'PASSENGER', _('Passenger')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PASSENGER,
        db_index=True,
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    # ─── Role Helpers ────────────────────────────────────────────────────────
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN or self.is_superuser

    @property
    def is_conductor(self):
        return self.role == self.Role.CONDUCTOR

    @property
    def is_passenger(self):
        return self.role == self.Role.PASSENGER

    def get_dashboard_url(self):
        from django.urls import reverse
        if self.is_super_admin:
            return reverse('buses:admin_dashboard')
        elif self.is_conductor:
            return reverse('conductor:dashboard')
        else:
            return reverse('bookings:passenger_dashboard')


class ConductorProfile(models.Model):
    """Extra profile fields for conductors."""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='conductor_profile',
        limit_choices_to={'role': CustomUser.Role.CONDUCTOR},
    )
    employee_id = models.CharField(max_length=20, unique=True)
    license_number = models.CharField(max_length=30, blank=True)
    assigned_bus = models.ForeignKey(
        'buses.Bus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conductors',
    )
    joining_date = models.DateField(blank=True, null=True)
    is_active_duty = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Conductor Profile'

    def __str__(self):
        return f"Conductor: {self.user.get_full_name()} ({self.employee_id})"


class PassengerProfile(models.Model):
    """Extra profile data for passengers."""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='passenger_profile',
        limit_choices_to={'role': CustomUser.Role.PASSENGER},
    )
    preferred_payment = models.CharField(max_length=20, default='razorpay')
    loyalty_points = models.PositiveIntegerField(default=0)
    emergency_contact = models.CharField(max_length=15, blank=True)
    special_needs = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Passenger Profile'

    def __str__(self):
        return f"Passenger: {self.user.get_full_name() or self.user.username}"


class Notification(models.Model):
    """In-App User Notification model for dashboard alerts, email, and SMS/WhatsApp."""

    class NotificationType(models.TextChoices):
        BOOKING_CONFIRMED = 'BOOKING_CONFIRMED', _('Booking Confirmed')
        BOOKING_RESCHEDULED = 'BOOKING_RESCHEDULED', _('Booking Rescheduled')
        BOOKING_CANCELLED = 'BOOKING_CANCELLED', _('Booking Cancelled')
        PASS_APPROVED = 'PASS_APPROVED', _('Pass Approved')
        PASS_SUBMITTED = 'PASS_SUBMITTED', _('Pass Submitted')
        BUS_DELAY = 'BUS_DELAY', _('Bus Service Delay')
        GENERAL = 'GENERAL', _('General Alert')

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title} for {self.user.username}"


class AdminAuditLog(models.Model):
    """System Audit Log for tracking administrator actions."""

    class ActionType(models.TextChoices):
        PASS_APPROVED = 'PASS_APPROVED', _('Pass Approved')
        PASS_REJECTED = 'PASS_REJECTED', _('Pass Rejected')
        SCHEME_APP_UPDATED = 'SCHEME_APP_UPDATED', _('Scheme Application Status Updated')
        SCHEDULE_CREATED = 'SCHEDULE_CREATED', _('Schedule Created')
        SCHEDULE_UPDATED = 'SCHEDULE_UPDATED', _('Schedule Updated')
        SCHEDULE_DELETED = 'SCHEDULE_DELETED', _('Schedule Deleted')
        SCHEDULE_STATUS_CHANGED = 'SCHEDULE_STATUS_CHANGED', _('Schedule Status Changed')
        USER_PROMOTED = 'USER_PROMOTED', _('User Role Updated')
        GENERAL_ADMIN_ACTION = 'GENERAL_ADMIN_ACTION', _('General Admin Action')

    admin_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='admin_audit_logs',
    )
    action_type = models.CharField(
        max_length=40,
        choices=ActionType.choices,
        default=ActionType.GENERAL_ADMIN_ACTION,
        db_index=True,
    )
    target_repr = models.CharField(max_length=255)
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.get_action_type_display()}] by {self.admin_user.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


def log_admin_action(admin_user, action_type, target_repr, details="", request=None):
    """Helper utility function to record admin activity logs."""
    if not admin_user or not admin_user.is_authenticated:
        return None

    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

    return AdminAuditLog.objects.create(
        admin_user=admin_user,
        action_type=action_type,
        target_repr=target_repr,
        details=details,
        ip_address=ip,
    )


