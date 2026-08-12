"""
Real-time simulated bus tracking with Leaflet.js.
"""
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from routes.models import Schedule, RouteStop
from .models import BusLocation, STOP_COORDINATES


def live_tracking(request, schedule_id):
    """Live bus tracking map page."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    route_stops = RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order')

    # Build route path for Leaflet polyline
    route_path = []
    stops_data = []
    for rs in route_stops:
        stop = rs.stop
        coords = STOP_COORDINATES.get(stop.code)
        if not coords:
            coords = (float(stop.latitude or 22.56), float(stop.longitude or 72.93))
        route_path.append(list(coords))
        stops_data.append({
            'code': stop.code,
            'name': stop.name,
            'lat': coords[0],
            'lng': coords[1],
            'order': rs.stop_order,
            'eta_minutes': rs.scheduled_minutes_from_start,
        })

    # Get latest bus location
    latest_location = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()

    context = {
        'title': f'Live Tracking — {schedule.route}',
        'schedule': schedule,
        'route_path_json': json.dumps(route_path),
        'stops_json': json.dumps(stops_data),
        'latest_location': latest_location,
        'route_stops': route_stops,
    }
    return render(request, 'tracking/live_tracking.html', context)


@require_GET
def api_bus_location(request, schedule_id):
    """AJAX polling endpoint for current bus GPS position."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    location = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()

    if not location:
        # Return first stop position as default
        first_stop = RouteStop.objects.filter(
            route=schedule.route
        ).select_related('stop').order_by('stop_order').first()

        if first_stop:
            coords = STOP_COORDINATES.get(first_stop.stop.code, (22.5645, 72.9289))
            return JsonResponse({
                'lat': coords[0], 'lng': coords[1],
                'speed': 0, 'status': schedule.status,
                'current_stop': str(first_stop.stop.name),
                'next_stop': None,
                'eta_minutes': 0,
                'distance_remaining': float(schedule.route.distance_km),
                'stop_index': 0,
            })

    route_stops = list(RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order'))

    current_idx = min(location.current_stop_index, len(route_stops) - 1)
    current_stop_name = route_stops[current_idx].stop.name if route_stops else 'Unknown'
    next_stop_name = route_stops[current_idx + 1].stop.name if current_idx + 1 < len(route_stops) else 'Destination'

    return JsonResponse({
        'lat': float(location.latitude),
        'lng': float(location.longitude),
        'speed': float(location.speed_kmh),
        'heading': float(location.heading),
        'status': schedule.status,
        'status_display': schedule.get_status_display(),
        'current_stop': current_stop_name,
        'next_stop': next_stop_name,
        'eta_minutes': location.eta_minutes,
        'distance_covered': float(location.distance_covered_km),
        'distance_remaining': float(location.distance_remaining_km),
        'stop_index': location.current_stop_index,
        'timestamp': location.timestamp.isoformat(),
    })


@require_GET
def api_simulate_movement(request, schedule_id):
    """
    Simulates bus movement along the route path.
    Advances the bus position by one stop each call (for demo purposes).
    In production this would be replaced by actual GPS feed.
    """
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    route_stops = list(RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order'))

    if not route_stops:
        return JsonResponse({'error': 'No stops found'}, status=400)

    latest = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()
    current_idx = (latest.current_stop_index + 1) if latest else 0
    current_idx = min(current_idx, len(route_stops) - 1)

    current_stop = route_stops[current_idx].stop
    coords = STOP_COORDINATES.get(current_stop.code, (22.5645, 72.9289))

    total_stops = len(route_stops)
    remaining_stops = total_stops - current_idx - 1
    distance_per_stop = float(schedule.route.distance_km) / max(total_stops - 1, 1)
    distance_covered = current_idx * distance_per_stop
    distance_remaining = remaining_stops * distance_per_stop

    location = BusLocation.objects.create(
        schedule=schedule,
        latitude=coords[0],
        longitude=coords[1],
        speed_kmh=35.0,
        current_stop_index=current_idx,
        distance_covered_km=round(distance_covered, 2),
        distance_remaining_km=round(distance_remaining, 2),
        eta_minutes=remaining_stops * 8,  # ~8 min per stop
    )

    return JsonResponse({
        'success': True,
        'stop_name': current_stop.name,
        'lat': coords[0],
        'lng': coords[1],
        'stop_index': current_idx,
        'distance_remaining': float(location.distance_remaining_km),
        'eta_minutes': location.eta_minutes,
    })
