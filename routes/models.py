from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


# ─── All Anand Area Stops ─────────────────────────────────────────────────────
ANAND_STOPS = [
    ('ANAND_BUS_STAND', 'Anand Bus Stand (GSRTC Central)'),
    ('VV_NAGAR', 'Vallabh Vidyanagar (V.V. Nagar Circle)'),
    ('BAKROL_PHATA', 'Bakrol Phata / Bakrol Square'),
    ('MOGRI', 'Mogri'),
    ('KARAMSAD', 'Karamsad Cross Roads'),
    ('VADTAL', 'Vadtal Temple Gateway'),
    ('GAMDI', 'Gamdi'),
    ('LAMBHVEL', 'Lambhvel Phata'),
    ('CHIKHODRA', 'Chikhodra Square'),
    ('BORIAVI', 'Boriavi'),
    ('SAMARKHA', 'Samarkha'),
    ('JITODIA', 'Jitodia'),
    ('GANA', 'Gana'),
    ('ADAS', 'Adas'),
    ('ODE', 'Ode'),
    ('UMRETH_ROAD', 'Umreth Road'),
    ('TOWN_HALL', 'Town Hall Anand'),
    ('RAILWAY_STATION', 'Anand Railway Station Junction'),
    ('CIVIL_HOSPITAL', 'Civil Hospital Anand'),
    ('GIDC', 'Anand GIDC Industrial Zone'),
]


class Stop(models.Model):
    """A bus stop / location in Anand area."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    address = models.TextField(blank=True)
    is_major = models.BooleanField(default=False)
    image = models.ImageField(upload_to='stops/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Stop'
        verbose_name_plural = 'Stops'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def coords(self):
        if self.latitude and self.longitude:
            return [float(self.latitude), float(self.longitude)]
        return None


class Route(models.Model):
    """A bus route connecting multiple stops."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SEASONAL = 'SEASONAL', _('Seasonal')

    route_number = models.CharField(max_length=20, unique=True, db_index=True)
    route_name = models.CharField(max_length=200)
    source = models.ForeignKey(Stop, on_delete=models.PROTECT, related_name='routes_from')
    destination = models.ForeignKey(Stop, on_delete=models.PROTECT, related_name='routes_to')
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    base_fare = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('10.00'))
    fare_per_km = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.50'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
        ordering = ['route_number']

    def __str__(self):
        return f"Route {self.route_number}: {self.source} → {self.destination}"

    def calculate_fare(self, distance_km=None):
        """Calculate dynamic fare based on distance."""
        dist = distance_km or float(self.distance_km)
        fare = float(self.base_fare) + (dist * float(self.fare_per_km))
        return round(fare, 2)


class RouteStop(models.Model):
    """Ordered stops within a route (with intermediate stops)."""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_stops')
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='route_stops')
    stop_order = models.PositiveSmallIntegerField()
    distance_from_source = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    scheduled_minutes_from_start = models.PositiveSmallIntegerField(default=0)
    fare_from_source = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Route Stop'
        verbose_name_plural = 'Route Stops'
        ordering = ['route', 'stop_order']
        unique_together = ['route', 'stop_order']

    def __str__(self):
        return f"{self.route.route_number} - Stop #{self.stop_order}: {self.stop.name}"


class Schedule(models.Model):
    """A scheduled trip for a route + bus combination."""

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        DEPARTED = 'DEPARTED', _('Departed')
        AT_STOP = 'AT_STOP', _('At Stop')
        DELAYED = 'DELAYED', _('Delayed')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class DayType(models.TextChoices):
        DAILY = 'DAILY', _('Daily')
        WEEKDAYS = 'WEEKDAYS', _('Weekdays Only')
        WEEKENDS = 'WEEKENDS', _('Weekends Only')
        SPECIFIC = 'SPECIFIC', _('Specific Dates')

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    bus = models.ForeignKey('buses.Bus', on_delete=models.CASCADE, related_name='schedules')
    driver = models.ForeignKey(
        'buses.Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules'
    )
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    travel_date = models.DateField(db_index=True)
    day_type = models.CharField(max_length=20, choices=DayType.choices, default=DayType.DAILY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    current_stop = models.ForeignKey(
        Stop, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_schedules'
    )
    delay_minutes = models.SmallIntegerField(default=0)
    available_seats = models.PositiveSmallIntegerField(default=40)
    total_fare_collected = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        ordering = ['travel_date', 'departure_time']
        indexes = [
            models.Index(fields=['travel_date', 'status']),
            models.Index(fields=['route', 'travel_date']),
        ]

    def __str__(self):
        return f"{self.route} on {self.travel_date} at {self.departure_time}"

    @property
    def is_available(self):
        return self.status in [self.Status.SCHEDULED, self.Status.DELAYED] and self.available_seats > 0
