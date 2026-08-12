from django.db import models
from decimal import Decimal


class BusLocation(models.Model):
    """Simulated real-time GPS location of a bus on active trip."""
    schedule = models.ForeignKey(
        'routes.Schedule', on_delete=models.CASCADE, related_name='locations'
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    speed_kmh = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    heading = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # degrees
    current_stop_index = models.PositiveSmallIntegerField(default=0)
    distance_covered_km = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    distance_remaining_km = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    eta_minutes = models.SmallIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bus Location'
        verbose_name_plural = 'Bus Locations'
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
        indexes = [
            models.Index(fields=['schedule', 'timestamp']),
        ]

    def __str__(self):
        return f"Bus @ ({self.latitude}, {self.longitude}) for {self.schedule}"


# GPS coordinates for all Anand stops (pre-seeded)
STOP_COORDINATES = {
    'ANAND_BUS_STAND':   (22.5645, 72.9289),
    'VV_NAGAR':          (22.5530, 72.9215),
    'BAKROL_PHATA':      (22.5712, 72.9103),
    'MOGRI':             (22.5801, 72.8942),
    'KARAMSAD':          (22.5420, 72.9452),
    'VADTAL':            (22.4985, 72.9073),
    'GAMDI':             (22.5610, 72.9350),
    'LAMBHVEL':          (22.5780, 72.9520),
    'CHIKHODRA':         (22.5492, 72.9601),
    'BORIAVI':           (22.5340, 72.9710),
    'SAMARKHA':          (22.5210, 72.9830),
    'JITODIA':           (22.5890, 72.9150),
    'GANA':              (22.6010, 72.9250),
    'ADAS':              (22.4830, 72.9100),
    'ODE':               (22.6120, 72.9380),
    'UMRETH_ROAD':       (22.5660, 72.9420),
    'TOWN_HALL':         (22.5580, 72.9330),
    'RAILWAY_STATION':   (22.5720, 72.9410),
    'CIVIL_HOSPITAL':    (22.5595, 72.9278),
    'GIDC':              (22.5855, 72.9680),
}
