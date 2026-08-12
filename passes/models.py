import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from routes.models import Route, Stop


class BusPass(models.Model):
    class ApplicantType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student Pass'
        PASSENGER = 'PASSENGER', 'Passenger Pass'

    class PassDuration(models.TextChoices):
        MONTHLY = '1', '1 Month (Monthly)'
        QUARTERLY = '3', '3 Months (Quarterly)'
        HALFYEARLY = '6', '6 Months (Half-Yearly)'
        ANNUAL = '12', '12 Months (Annual)'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'

    pass_number = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bus_passes'
    )
    applicant_type = models.CharField(max_length=20, choices=ApplicantType.choices, default=ApplicantType.STUDENT)
    applicant_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Route & Stop Details
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='passes')
    start_stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True, blank=True, related_name='pass_start_stops')
    end_stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True, blank=True, related_name='pass_end_stops')

    # Specific details
    duration_months = models.PositiveSmallIntegerField(default=1)
    college_name = models.CharField(max_length=200, blank=True, default='')
    student_id_number = models.CharField(max_length=100, blank=True, default='')
    id_proof_number = models.CharField(max_length=100, blank=True, default='')
    id_proof_document = models.FileField(upload_to='pass_documents/', blank=True, null=True)

    # Pricing & Status
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    original_fare = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bus Pass'
        verbose_name_plural = 'Bus Passes'
        ordering = ['-applied_at']

    def save(self, *args, **kwargs):
        if not self.pass_number:
            prefix = 'STU' if self.applicant_type == self.ApplicantType.STUDENT else 'PAS'
            self.pass_number = f"{prefix}-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pass_number} - {self.applicant_name} ({self.get_applicant_type_display()})"


class SpecialScheme(models.Model):
    class TargetAudience(models.TextChoices):
        ALL = 'ALL', 'All Commuters'
        STUDENT = 'STUDENT', 'Students Only'
        PASSENGER = 'PASSENGER', 'Regular Passengers'
        SENIOR = 'SENIOR', 'Senior Citizens'
        WOMEN = 'WOMEN', 'Women Passengers'

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    target_audience = models.CharField(max_length=20, choices=TargetAudience.choices, default=TargetAudience.ALL)
    description = models.TextField()
    discount_percentage = models.PositiveIntegerField(default=20, help_string="Percentage discount (e.g. 25 for 25% off)") if hasattr(models, 'help_string') else models.PositiveIntegerField(default=20)
    flat_discount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    badge_text = models.CharField(max_length=50, default='Special Scheme')
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Special Scheme'
        verbose_name_plural = 'Special Schemes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.code})"


class SchemeApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    application_number = models.CharField(max_length=50, unique=True, editable=False)
    scheme = models.ForeignKey(SpecialScheme, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheme_applications'
    )
    applicant_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    id_proof_number = models.CharField(max_length=100)
    preferred_route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheme_apps')
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Scheme Application'
        verbose_name_plural = 'Scheme Applications'
        ordering = ['-applied_at']

    def save(self, *args, **kwargs):
        if not self.application_number:
            self.application_number = f"SCH-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_number} - {self.applicant_name} for {self.scheme.title}"
