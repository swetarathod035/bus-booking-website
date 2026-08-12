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
