from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class TripLog(models.Model):
    """Real-time trip log updated by conductor."""

    class EventType(models.TextChoices):
        TRIP_START = 'TRIP_START', _('Trip Started')
        AT_STOP = 'AT_STOP', _('At Stop')
        DEPARTED_STOP = 'DEPARTED_STOP', _('Departed Stop')
        DELAY_REPORTED = 'DELAY_REPORTED', _('Delay Reported')
        TRIP_COMPLETE = 'TRIP_COMPLETE', _('Trip Completed')
        BREAKDOWN = 'BREAKDOWN', _('Breakdown')
        EMERGENCY = 'EMERGENCY', _('Emergency')

    schedule = models.ForeignKey(
        'routes.Schedule', on_delete=models.CASCADE, related_name='trip_logs'
    )
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='trip_logs',
    )
    event_type = models.CharField(max_length=25, choices=EventType.choices)
    stop = models.ForeignKey(
        'routes.Stop', on_delete=models.SET_NULL, null=True, blank=True, related_name='trip_logs'
    )
    delay_minutes = models.SmallIntegerField(default=0)
    message = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trip Log'
        verbose_name_plural = 'Trip Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.schedule}"


class OfflineTicket(models.Model):
    """Tickets sold offline by conductor (cash payment)."""
    schedule = models.ForeignKey(
        'routes.Schedule', on_delete=models.CASCADE, related_name='offline_tickets'
    )
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offline_tickets_issued',
    )
    boarding_stop = models.ForeignKey(
        'routes.Stop', on_delete=models.PROTECT, related_name='offline_boarding'
    )
    alighting_stop = models.ForeignKey(
        'routes.Stop', on_delete=models.PROTECT, related_name='offline_alighting'
    )
    seat_numbers = models.CharField(max_length=100)  # comma-separated
    passenger_count = models.PositiveSmallIntegerField(default=1)
    amount_collected = models.DecimalField(max_digits=8, decimal_places=2)
    ticket_number = models.CharField(max_length=25, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Offline Ticket'
        verbose_name_plural = 'Offline Tickets'
        ordering = ['-issued_at']

    def __str__(self):
        return f"Offline Ticket {self.ticket_number}"
