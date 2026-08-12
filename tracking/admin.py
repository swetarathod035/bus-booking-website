from django.contrib import admin
from .models import BusLocation


@admin.register(BusLocation)
class BusLocationAdmin(admin.ModelAdmin):
    list_display = ['schedule', 'latitude', 'longitude', 'speed_kmh', 'eta_minutes', 'timestamp']
    list_filter = ['schedule__status']
    date_hierarchy = 'timestamp'
