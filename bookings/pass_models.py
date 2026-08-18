"""
Bus Pass models — Student Pass, Monthly Pass, Special Schemes.
Separate file; imported into bookings/models.py via apps.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class PassScheme(models.Model):
    """Admin-defined pass schemes (monthly, student, senior, etc.)."""

    class SchemeType(models.TextChoices):
        MONTHLY      = 'MONTHLY',      _('Monthly Pass')
        STUDENT      = 'STUDENT',      _('Student Pass')
        SENIOR       = 'SENIOR',       _('Senior Citizen Pass')
        WOMEN        = 'WOMEN',        _('Ladies Special Pass')
        WORKER       = 'WORKER',       _('Daily Worker Pass')
        DIVYANGJAN   = 'DIVYANGJAN',   _('Divyangjan (Disabled) Pass')

    name            = models.CharField(max_length=100)
    scheme_type     = models.CharField(max_length=20, choices=SchemeType.choices, default=SchemeType.MONTHLY)
    description     = models.TextField(blank=True)
    validity_days   = models.PositiveSmallIntegerField(default=30, help_text="Pass valid for N days from activation")
    price           = models.DecimalField(max_digits=8, decimal_places=2)
    discount_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'),
                                           help_text="Percentage discount on each trip (0–100)")
    unlimited_trips = models.BooleanField(default=False, help_text="If True, unlimited trips within validity period")
    trip_limit      = models.PositiveSmallIntegerField(default=0, help_text="Max trips (0 = unlimited)")
    applicable_routes = models.ManyToManyField('routes.Route', blank=True,
                                                related_name='pass_schemes',
                                                help_text="Leave empty = applicable on all routes")
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pass Scheme'
        verbose_name_plural = 'Pass Schemes'
        ordering = ['scheme_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_scheme_type_display()}) — ₹{self.price}"

    @property
    def discount_multiplier(self):
        return Decimal('1.00') - (self.discount_pct / Decimal('100'))


class BusPass(models.Model):
    """An issued bus pass for a passenger."""

    class Status(models.TextChoices):
        ACTIVE    = 'ACTIVE',    _('Active')
        EXPIRED   = 'EXPIRED',   _('Expired')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        PENDING   = 'PENDING',   _('Pending Approval')

    pass_id         = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pass_number     = models.CharField(max_length=25, unique=True, db_index=True)
    passenger       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                         related_name='booking_bus_passes')
    scheme          = models.ForeignKey(PassScheme, on_delete=models.PROTECT, related_name='passes')
    status          = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    issued_date     = models.DateField(auto_now_add=True)
    valid_from      = models.DateField()
    valid_until     = models.DateField()
    trips_used      = models.PositiveSmallIntegerField(default=0)
    amount_paid     = models.DecimalField(max_digits=8, decimal_places=2)

    # ID proof for student/special passes
    id_proof_type   = models.CharField(max_length=30, blank=True,
                                        choices=[('STUDENT_ID', 'Student ID Card'),
                                                 ('AADHAR', 'Aadhar Card'),
                                                 ('PAN', 'PAN Card'),
                                                 ('COLLEGE_LETTER', 'College Verification Letter'),
                                                 ('GOVT_ID', 'Government ID')])
    id_proof_number = models.CharField(max_length=50, blank=True)
    institution_name= models.CharField(max_length=150, blank=True,
                                        help_text="School/College name for student passes")
    photo           = models.ImageField(upload_to='pass_photos/', blank=True, null=True)
    id_proof_doc    = models.FileField(upload_to='pass_docs/', blank=True, null=True)

    approved_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='approved_passes')
    approved_at     = models.DateTimeField(null=True, blank=True)
    rejection_reason= models.TextField(blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bus Pass'
        verbose_name_plural = 'Bus Passes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['passenger', 'status']),
            models.Index(fields=['pass_number']),
        ]

    def __str__(self):
        return f"Pass {self.pass_number} — {self.passenger.get_full_name()} ({self.scheme.get_scheme_type_display()})"

    @property
    def is_valid_today(self):
        import datetime
        today = datetime.date.today()
        return (self.status == self.Status.ACTIVE and
                self.valid_from <= today <= self.valid_until and
                (self.scheme.unlimited_trips or
                 self.scheme.trip_limit == 0 or
                 self.trips_used < self.scheme.trip_limit))

    @property
    def trips_remaining(self):
        if self.scheme.unlimited_trips or self.scheme.trip_limit == 0:
            return '∞'
        return max(0, self.scheme.trip_limit - self.trips_used)

    def generate_pass_number(self):
        import datetime
        type_code = self.scheme.scheme_type[:3].upper()
        date_str = self.issued_date.strftime('%y%m') if self.issued_date else datetime.date.today().strftime('%y%m')
        uid = str(self.pass_id).replace('-', '').upper()[:6]
        self.pass_number = f"AB-{type_code}-{date_str}-{uid}"
        return self.pass_number


class PassUsageLog(models.Model):
    """Log each trip made using a bus pass."""
    bus_pass    = models.ForeignKey(BusPass, on_delete=models.CASCADE, related_name='usage_logs')
    schedule    = models.ForeignKey('routes.Schedule', on_delete=models.SET_NULL, null=True,
                                    related_name='pass_usage_logs')
    boarding    = models.ForeignKey('routes.Stop', on_delete=models.SET_NULL, null=True,
                                    related_name='pass_boarding_logs')
    alighting   = models.ForeignKey('routes.Stop', on_delete=models.SET_NULL, null=True,
                                    related_name='pass_alighting_logs')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='pass_verifications')
    verified_at = models.DateTimeField(auto_now_add=True)
    fare_saved  = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Pass Usage Log'
        ordering = ['-verified_at']

    def __str__(self):
        return f"Pass {self.bus_pass.pass_number} used on {self.verified_at.date()}"
