from django.contrib import admin
from .models import Bus, Driver


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['bus_number', 'bus_name', 'bus_type', 'total_seats', 'status']
    list_filter = ['bus_type', 'status']
    search_fields = ['bus_number', 'bus_name']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_id', 'license_number', 'phone', 'status', 'assigned_bus']
    list_filter = ['status']
    search_fields = ['name', 'employee_id', 'license_number']
