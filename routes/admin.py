from django.contrib import admin
from .models import Stop, Route, RouteStop, Schedule


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_major', 'latitude', 'longitude']
    search_fields = ['name', 'code']
    list_filter = ['is_major']


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    ordering = ['stop_order']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_number', 'route_name', 'source', 'destination', 'distance_km', 'base_fare', 'status']
    list_filter = ['status']
    search_fields = ['route_number', 'route_name']
    inlines = [RouteStopInline]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['route', 'bus', 'travel_date', 'departure_time', 'status', 'available_seats']
    list_filter = ['status', 'travel_date']
    search_fields = ['route__route_number', 'bus__bus_number']
    date_hierarchy = 'travel_date'
