from django.contrib import admin
from .models import TripLog, OfflineTicket


@admin.register(TripLog)
class TripLogAdmin(admin.ModelAdmin):
    list_display = ['schedule', 'conductor', 'event_type', 'stop', 'timestamp']
    list_filter = ['event_type']


@admin.register(OfflineTicket)
class OfflineTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'schedule', 'conductor', 'passenger_count', 'amount_collected', 'issued_at']
