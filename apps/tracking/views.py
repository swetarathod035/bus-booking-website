"""
AnandBus – Live bus tracking views
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
import math 
import random

from .models import LiveLocation, LocationHistory
from apps.buses.models import Bus, Schedule 


def tracking_map(request, bus_id=None):
    """Live tracking map page."""
    buses = Bus.objects.filter(status='active').prefetch_related('live_location')
    selected_bus = None
    if bus_id:
        selected_bus = get_object_or_404(Bus, pk=bus_id)
    return render(request, 'tracking/map.html', {
        'buses':        buses,
        'selected_bus': selected_bus,
    })


def bus_location_api(request, bus_id):
    """JSON endpoint – returns current location of a bus."""
    bus = get_object_or_404(Bus, pk=bus_id, status='active')
    try:
        loc = bus.live_location
        data = {
            'bus_number':   bus.bus_number,
            'bus_name':     bus.name,
            'lat':          loc.lat,
            'lng':          loc.lng,
            'speed':        loc.speed_kmph,
            'current_stop': str(loc.current_stop) if loc.current_stop else '—',
            'next_stop':    str(loc.next_stop) if loc.next_stop else '—',
            'eta_minutes':  loc.eta_minutes,
            'is_delayed':   loc.is_delayed,
            'last_updated': loc.last_updated.strftime('%I:%M %p'),
        }
    except LiveLocation.DoesNotExist:
        # Return simulated location for demo
        # Center of Anand city
        base_lat, base_lng = 22.5573, 72.9520
        data = {
            'bus_number':   bus.bus_number,
            'bus_name':     bus.name,
            'lat':          base_lat + random.uniform(-0.02, 0.02),
            'lng':          base_lng + random.uniform(-0.02, 0.02),
            'speed':        random.randint(15, 45),
            'current_stop': 'Anand Bus Stand',
            'next_stop':    'Vallabh Vidyanagar',
            'eta_minutes':  random.randint(3, 20),
            'is_delayed':   False,
            'last_updated': timezone.now().strftime('%I:%M %p'),
            'simulated':    True,
        }
    return JsonResponse(data)


def all_buses_location_api(request):
    """Returns locations of all active buses."""
    buses = Bus.objects.filter(status='active')
    result = []
    base_lat, base_lng = 22.5573, 72.9520
    for bus in buses:
        try:
            loc = bus.live_location
            result.append({
                'bus_id': bus.pk, 'bus_number': bus.bus_number, 'bus_name': bus.name,
                'lat': loc.lat, 'lng': loc.lng, 'last_updated': loc.last_updated.strftime('%H:%M'),
            })
        except LiveLocation.DoesNotExist:
            result.append({
                'bus_id': bus.pk, 'bus_number': bus.bus_number, 'bus_name': bus.name,
                'lat': base_lat + random.uniform(-0.05, 0.05),
                'lng': base_lng + random.uniform(-0.05, 0.05),
                'last_updated': timezone.now().strftime('%H:%M'),
                'simulated': True,
            })
    return JsonResponse({'buses': result})


@require_POST
def update_location(request, bus_id):
    """Admin/Driver endpoint to push a GPS update."""
    bus  = get_object_or_404(Bus, pk=bus_id)
    data = json.loads(request.body)
    loc, _ = LiveLocation.objects.get_or_create(bus=bus, defaults={'lat': 0, 'lng': 0})
    loc.lat        = data.get('lat', loc.lat)
    loc.lng        = data.get('lng', loc.lng)
    loc.speed_kmph = data.get('speed', 0)
    loc.save()
    LocationHistory.objects.create(bus=bus, lat=loc.lat, lng=loc.lng, speed_kmph=loc.speed_kmph)
    return JsonResponse({'status': 'ok'})

