from django.db import models
from django.utils.translation import gettext_lazy as _


class Bus(models.Model):
    """Physical bus entity."""

    class BusType(models.TextChoices):
        AC = 'AC', _('AC Bus')
        NON_AC = 'NON_AC', _('Non-AC Bus')
        MINI = 'MINI', _('Mini Bus')
        DELUXE = 'DELUXE', _('Deluxe Bus')

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        MAINTENANCE = 'MAINTENANCE', _('Under Maintenance')

    bus_number = models.CharField(max_length=20, unique=True, db_index=True)
    bus_name = models.CharField(max_length=100)
    bus_type = models.CharField(max_length=20, choices=BusType.choices, default=BusType.NON_AC)
    total_seats = models.PositiveSmallIntegerField(default=40)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    manufacturer = models.CharField(max_length=60, blank=True)
    model_year = models.PositiveSmallIntegerField(blank=True, null=True)
    registration_expiry = models.DateField(blank=True, null=True)
    insurance_expiry = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='buses/', blank=True, null=True)
    has_wifi = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    has_charging = models.BooleanField(default=False)
    has_gps = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'
        ordering = ['bus_number']

    def __str__(self):
        return f"{self.bus_number} - {self.bus_name}"

    @property
    def amenities_list(self):
        amenities = []
        if self.has_wifi:
            amenities.append('WiFi')
        if self.has_ac:
            amenities.append('AC')
        if self.has_charging:
            amenities.append('USB Charging')
        if self.has_gps:
            amenities.append('GPS Tracking')
        return amenities


class Driver(models.Model):
    """Bus driver entity."""

    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', _('Available')
        ON_DUTY = 'ON_DUTY', _('On Duty')
        OFF_DUTY = 'OFF_DUTY', _('Off Duty')
        ON_LEAVE = 'ON_LEAVE', _('On Leave')

    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    license_number = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to='drivers/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    assigned_bus = models.ForeignKey(
        Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers'
    )
    experience_years = models.PositiveSmallIntegerField(default=0)
    joining_date = models.DateField(blank=True, null=True)
    license_expiry = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.employee_id})"
