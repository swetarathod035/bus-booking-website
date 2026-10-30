import json, datetime, math
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from routes.models import Schedule, RouteStop
from bookings.models import Booking
from .models import BusLocation, STOP_COORDINATES


def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate direction bearing in degrees (0-360) between two coordinates."""
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    d_lon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    y = math.sin(d_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon)
    brng = math.degrees(math.atan2(y, x))
    return round((brng + 360) % 360, 1)


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two lat/lng pairs."""
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def live_tracking(request, schedule_id=None):
    """Live bus tracking map page with role-based bus selector & Google Maps integration."""
    user = request.user
    is_admin = user.is_authenticated and (
        user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN'
    )

    today = datetime.date.today()

    # Query active schedules
    all_schedules_qs = Schedule.objects.filter(
        status__in=['SCHEDULED', 'DEPARTED', 'AT_STOP', 'DELAYED'],
        travel_date__gte=today,
    ).select_related('route', 'bus', 'driver').order_by('travel_date', 'departure_time')

    if not all_schedules_qs.exists():
        all_schedules_qs = Schedule.objects.all().select_related('route', 'bus', 'driver').order_by('-travel_date', 'departure_time')[:15]

    search_q = request.GET.get('q', '').strip() or request.GET.get('booking_id', '').strip() or request.GET.get('bus_number', '').strip()

    schedule = None
    if schedule_id:
        schedule = Schedule.objects.filter(pk=schedule_id).select_related('route', 'bus', 'driver').first()

    # Handle explicit search query
    searched_schedule = None
    if search_q:
        matched_booking = Booking.objects.filter(
            Q(booking_id__icontains=search_q) | Q(id__icontains=search_q)
        ).select_related('schedule').first()
        if matched_booking and matched_booking.schedule:
            searched_schedule = matched_booking.schedule
        else:
            searched_schedule = Schedule.objects.filter(
                Q(bus__bus_number__icontains=search_q) |
                Q(bus__bus_name__icontains=search_q) |
                Q(route__route_number__icontains=search_q)
            ).select_related('route', 'bus', 'driver').first()

    if searched_schedule and not schedule_id:
        schedule = searched_schedule

    # Determine dropdown options based on User Role
    if is_admin:
        dropdown_schedules = list(all_schedules_qs)
    else:
        # For Passengers: Only show booked buses or currently tracked/searched bus
        passenger_schedules = []
        if user.is_authenticated:
            booked_schedules = Schedule.objects.filter(
                bookings__passenger=user,
                bookings__status__in=['CONFIRMED', 'PENDING', 'COMPLETED']
            ).select_related('route', 'bus', 'driver').distinct()
            passenger_schedules.extend(list(booked_schedules))

        if schedule and schedule not in passenger_schedules:
            passenger_schedules.append(schedule)

        if searched_schedule and searched_schedule not in passenger_schedules:
            passenger_schedules.append(searched_schedule)

        dropdown_schedules = passenger_schedules

    if not schedule:
        if dropdown_schedules:
            schedule = dropdown_schedules[0]
        elif is_admin and all_schedules_qs.exists():
            schedule = all_schedules_qs.first()
        elif all_schedules_qs.exists():
            schedule = all_schedules_qs.first()

    if not schedule:
        return render(request, 'tracking/live_tracking.html', {
            'title': 'Track My Bus — AnandBus',
            'error': 'No active bus schedule found for your request.',
            'all_schedules': [],
            'is_admin': is_admin,
            'search_query': search_q,
        })

    route_stops = RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order')

    now = datetime.datetime.now()
    route_path = []
    stops_data = []
    for idx, rs in enumerate(route_stops):
        stop = rs.stop
        coords = STOP_COORDINATES.get(stop.code)
        if not coords:
            coords = (float(stop.latitude or 22.5645), float(stop.longitude or 72.9289))
        route_path.append(list(coords))
        
        minutes_offset = rs.scheduled_minutes_from_start or (idx * 8)
        arrival_dt = datetime.datetime.combine(schedule.travel_date, schedule.departure_time) + datetime.timedelta(minutes=minutes_offset)
        
        stops_data.append({
            'code': stop.code,
            'name': stop.name,
            'lat': coords[0],
            'lng': coords[1],
            'order': rs.stop_order,
            'eta_minutes': minutes_offset,
            'arrival_time_str': arrival_dt.strftime('%I:%M %p'),
        })

    latest_location = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()

    # Occupancy status computation
    total_seats = schedule.bus.total_seats or 40
    avail_seats = schedule.available_seats
    occupied_seats = max(0, total_seats - avail_seats)
    occupancy_pct = min(100, int((occupied_seats / max(1, total_seats)) * 100))

    if occupancy_pct > 85 or avail_seats <= 5:
        occupancy_label = "Full Capacity (Standing Only)"
        occupancy_class = "danger"
    elif occupancy_pct > 50:
        occupancy_label = "Moderate Capacity"
        occupancy_class = "warning"
    else:
        occupancy_label = "Low Capacity (Seats Available)"
        occupancy_class = "success"

    # Determine coordinates for map embed
    map_lat = 22.5645
    map_lng = 72.9289
    if latest_location:
        map_lat = float(latest_location.latitude)
        map_lng = float(latest_location.longitude)
    elif stops_data:
        map_lat = stops_data[0]['lat']
        map_lng = stops_data[0]['lng']

    # Build all schedules list for client role switching
    all_schedules_list = []
    for sch in all_schedules_qs:
        loc = BusLocation.objects.filter(schedule=sch).order_by('-timestamp').first()
        r_stops = RouteStop.objects.filter(route=sch.route).select_related('stop').order_by('stop_order')
        f_stop = r_stops.first()
        s_lat = float(loc.latitude) if loc else (float(f_stop.stop.latitude) if f_stop and f_stop.stop.latitude else 22.5645)
        s_lng = float(loc.longitude) if loc else (float(f_stop.stop.longitude) if f_stop and f_stop.stop.longitude else 72.9289)
        all_schedules_list.append({
            'id': sch.id,
            'bus_number': sch.bus.bus_number,
            'bus_name': sch.bus.bus_name,
            'route_name': sch.route.route_name,
            'departure_time': sch.departure_time.strftime('%H:%M') if sch.departure_time else '',
            'lat': s_lat,
            'lng': s_lng,
        })

    context = {
        'title': f'Live Tracking — {schedule.bus.bus_name} ({schedule.route.route_name})',
        'schedule': schedule,
        'all_schedules': dropdown_schedules,
        'all_schedules_json': json.dumps(all_schedules_list),
        'is_admin': is_admin,
        'search_query': search_q,
        'map_lat': map_lat,
        'map_lng': map_lng,
        'route_path_json': json.dumps(route_path),
        'stops_json': json.dumps(stops_data),
        'latest_location': latest_location,
        'route_stops': route_stops,
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'occupancy_label': occupancy_label,
        'occupancy_class': occupancy_class,
        'occupancy_pct': occupancy_pct,
        'total_seats': total_seats,
        'available_seats': avail_seats,
    }
    return render(request, 'tracking/live_tracking.html', context)


@require_GET
def api_search_schedule(request):
    """
    Search endpoint for passengers & admins to find a schedule by Bus Number or Booking ID.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'found': False, 'message': 'Please enter a Bus Number or Booking ID.'})

    # 1. Match by Booking ID
    booking = Booking.objects.filter(
        Q(booking_id__icontains=query) | Q(id__icontains=query)
    ).select_related('schedule__bus', 'schedule__route').first()

    schedule = None
    if booking and booking.schedule:
        schedule = booking.schedule
    else:
        # 2. Match by Bus Number, Bus Name, or Route Number
        schedule = Schedule.objects.filter(
            Q(bus__bus_number__icontains=query) |
            Q(bus__bus_name__icontains=query) |
            Q(route__route_number__icontains=query)
        ).select_related('bus', 'route').order_by('-travel_date', 'departure_time').first()

    if schedule:
        latest_loc = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()
        route_stops = RouteStop.objects.filter(route=schedule.route).select_related('stop').order_by('stop_order')
        first_stop = route_stops.first() if route_stops.exists() else None
        
        lat = float(latest_loc.latitude) if latest_loc else (float(first_stop.stop.latitude) if first_stop and first_stop.stop.latitude else 22.5645)
        lng = float(latest_loc.longitude) if latest_loc else (float(first_stop.stop.longitude) if first_stop and first_stop.stop.longitude else 72.9289)

        return JsonResponse({
            'found': True,
            'schedule_id': schedule.id,
            'bus_number': schedule.bus.bus_number,
            'bus_name': schedule.bus.bus_name,
            'route_name': schedule.route.route_name,
            'lat': lat,
            'lng': lng,
            'redirect_url': f'/tracking/live/{schedule.id}/',
        })
    else:
        return JsonResponse({
            'found': False,
            'message': f"Bus Number or Booking ID '{query}' was not found or is currently inactive. Please double-check your bus number (e.g. GJ-18-T-0004)."
        })



STOP_LANDMARKS = {
    'ANAND_BUS_STAND': 'Anand Central GSRTC Depot & Amul Dairy Museum',
    'VV_NAGAR': 'Vallabh Vidyanagar University & Academic Hub',
    'BAKROL_PHATA': 'Bakrol Square & Commercial Hub',
    'MOGRI': 'Mogri Square',
    'KARAMSAD': 'Sardar Patel Ancestral House & Memorial',
    'VADTAL': 'Vadtal Swaminarayan Temple Gateway',
    'GAMDI': 'Gamdi Village Junction',
    'LAMBHVEL': 'Lambhvel Phata',
    'CHIKHODRA': 'Chikhodra Highway Crossing',
    'BORIAVI': 'Boriavi Junction',
    'SAMARKHA': 'Samarkha Lake View',
    'TOWN_HALL': 'Town Hall & Municipal Office',
    'RAILWAY_STATION': 'Anand Junction Railway Station',
    'CIVIL_HOSPITAL': 'Civil Hospital Medical Zone',
}


@require_GET
def api_bus_location(request, schedule_id):
    """AJAX polling endpoint for current bus GPS position with bearing, geofencing & stop ETAs."""
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    location = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()

    route_stops = list(RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order'))

    if not location:
        # Default to route start
        first_stop = route_stops[0] if route_stops else None
        coords = STOP_COORDINATES.get(first_stop.stop.code, (22.5645, 72.9289)) if first_stop else (22.5645, 72.9289)
        bus_lat, bus_lng = coords[0], coords[1]
        speed = 0.0
        heading = 0.0
        current_idx = 0
        eta_minutes = 0
        dist_remaining = float(schedule.route.distance_km)
    else:
        bus_lat = float(location.latitude)
        bus_lng = float(location.longitude)
        speed = float(location.speed_kmh)
        heading = float(location.heading)
        current_idx = min(location.current_stop_index, len(route_stops) - 1)
        eta_minutes = location.eta_minutes
        dist_remaining = float(location.distance_remaining_km)

    current_stop_name = route_stops[current_idx].stop.name if route_stops else 'En Route'
    next_stop_name = route_stops[current_idx + 1].stop.name if current_idx + 1 < len(route_stops) else 'Destination'

    # Compute dynamic stop-by-stop ETA & wall-clock arrival times
    base_time = datetime.datetime.now()
    stops_eta = []
    near_stop_event = None

    for idx, rs in enumerate(route_stops):
        s_coords = STOP_COORDINATES.get(rs.stop.code)
        if not s_coords:
            s_coords = (float(rs.stop.latitude or 22.5645), float(rs.stop.longitude or 72.9289))
        
        dist_m = haversine_distance_meters(bus_lat, bus_lng, s_coords[0], s_coords[1])
        
        # Geofencing check (100 - 200m radius)
        is_near = dist_m <= 200
        is_passed = idx < current_idx
        is_current = idx == current_idx

        if is_near and not near_stop_event:
            near_stop_event = {
                'stop_name': rs.stop.name,
                'distance_m': int(dist_m),
                'is_arrived': dist_m <= 100,
            }

        # Calculate estimated arrival clock time based on stop distance & average traffic speed (~35 km/h)
        est_min_from_now = max(0, int((dist_m / 1000.0) / 35.0 * 60.0)) if idx >= current_idx else 0
        clock_time = (base_time + datetime.timedelta(minutes=est_min_from_now)).strftime('%I:%M %p')

        landmark_text = STOP_LANDMARKS.get(rs.stop.code, f"{rs.stop.name} Major Stop")

        stops_eta.append({
            'code': rs.stop.code,
            'name': rs.stop.name,
            'landmark': landmark_text,
            'lat': s_coords[0],
            'lng': s_coords[1],
            'order': rs.stop_order,
            'dist_m': round(dist_m, 1),
            'dist_km': round(dist_m / 1000.0, 2),
            'est_min': est_min_from_now,
            'arrival_time_str': clock_time,
            'is_passed': is_passed,
            'is_current': is_current,
            'is_near': is_near,
        })

    # Occupancy Badge Calculation
    total_seats = schedule.bus.total_seats or 40
    avail_seats = schedule.available_seats
    occupied = max(0, total_seats - avail_seats)
    occupancy_pct = min(100, int((occupied / max(1, total_seats)) * 100))

    if occupancy_pct > 85 or avail_seats <= 5:
        occupancy_label = "Full Capacity"
        occupancy_class = "danger"
    elif occupancy_pct > 50:
        occupancy_label = "Moderate Capacity"
        occupancy_class = "warning"
    else:
        occupancy_label = "Low Capacity"
        occupancy_class = "success"

    return JsonResponse({
        'lat': bus_lat,
        'lng': bus_lng,
        'speed': speed,
        'heading': heading,
        'status': schedule.status,
        'status_display': schedule.get_status_display(),
        'current_stop': current_stop_name,
        'next_stop': next_stop_name,
        'eta_minutes': eta_minutes,
        'distance_covered': float(location.distance_covered_km) if location else 0.0,
        'distance_remaining': dist_remaining,
        'stop_index': current_idx,
        'timestamp': location.timestamp.isoformat() if location else timezone.now().isoformat(),
        'stops_eta': stops_eta,
        'geofence_event': near_stop_event,
        'occupancy': {
            'label': occupancy_label,
            'class': occupancy_class,
            'pct': occupancy_pct,
            'available_seats': avail_seats,
            'total_seats': total_seats,
        },
        'delay_info': {
            'is_delayed': schedule.status == 'DELAYED' or schedule.delay_minutes > 0,
            'delay_minutes': schedule.delay_minutes,
            'notes': schedule.notes or 'Route traffic congestion update',
        }
    })


@require_GET
def api_simulate_movement(request, schedule_id):
    """
    Simulates bus movement along the route path with heading angle calculation.
    """
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    route_stops = list(RouteStop.objects.filter(
        route=schedule.route
    ).select_related('stop').order_by('stop_order'))

    if not route_stops:
        return JsonResponse({'error': 'No stops found'}, status=400)

    latest = BusLocation.objects.filter(schedule=schedule).order_by('-timestamp').first()
    prev_idx = latest.current_stop_index if latest else 0
    current_idx = (prev_idx + 1) if latest else 0
    if current_idx >= len(route_stops):
        current_idx = 0  # Loop back for simulation

    prev_stop = route_stops[prev_idx].stop
    current_stop = route_stops[current_idx].stop

    prev_coords = STOP_COORDINATES.get(prev_stop.code, (22.5645, 72.9289))
    coords = STOP_COORDINATES.get(current_stop.code, (22.5645, 72.9289))

    heading = calculate_bearing(prev_coords[0], prev_coords[1], coords[0], coords[1])

    total_stops = len(route_stops)
    remaining_stops = total_stops - current_idx - 1
    distance_per_stop = float(schedule.route.distance_km) / max(total_stops - 1, 1)
    distance_covered = current_idx * distance_per_stop
    distance_remaining = max(0.0, remaining_stops * distance_per_stop)

    location = BusLocation.objects.create(
        schedule=schedule,
        latitude=coords[0],
        longitude=coords[1],
        speed_kmh=42.5,
        heading=heading,
        current_stop_index=current_idx,
        distance_covered_km=round(distance_covered, 2),
        distance_remaining_km=round(distance_remaining, 2),
        eta_minutes=remaining_stops * 6,
    )

    return JsonResponse({
        'success': True,
        'stop_name': current_stop.name,
        'lat': coords[0],
        'lng': coords[1],
        'heading': heading,
        'stop_index': current_idx,
        'distance_remaining': float(location.distance_remaining_km),
        'eta_minutes': location.eta_minutes,
    })

