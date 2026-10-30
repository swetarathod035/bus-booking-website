import json
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET

from .models import Route, Stop, Schedule, RouteStop, ANAND_STOPS


# ─── Anand Places for Carousel ────────────────────────────────────────────────
ANAND_PLACES = [
    {
        'id': 1,
        'name': 'Amul Dairy & Museum',
        'subtitle': 'Milk Capital of India',
        'description': 'Visit the legendary Amul cooperative dairy that revolutionized India\'s dairy industry. The interactive museum showcases the remarkable White Revolution story.',
        'image': 'images/places/amul.jpg',
        'stop': 'ANAND_BUS_STAND',
        'stop_name': 'Anand Bus Stand',
        'icon': '🥛',
        'tag': 'Heritage',
    },
    {
        'id': 2,
        'name': 'Sardar Vallabhbhai Patel Memorial',
        'subtitle': 'Karamsad — Birthplace of Iron Man',
        'description': 'Explore the ancestral home and memorial of India\'s first Deputy Prime Minister in the historic village of Karamsad.',
        'image': 'images/places/sardar.jpg',
        'stop': 'KARAMSAD',
        'stop_name': 'Karamsad Cross Roads',
        'icon': '🏛️',
        'tag': 'Historical',
    },
    {
        'id': 3,
        'name': 'Vallabh Vidyanagar',
        'subtitle': 'Educational Hub of Gujarat',
        'description': 'Walk through Gujarat\'s premier academic township featuring 100+ educational institutions, peaceful gardens, and vibrant student culture.',
        'image': 'images/places/vvnagar.jpg',
        'stop': 'VV_NAGAR',
        'stop_name': 'Vallabh Vidyanagar',
        'icon': '🎓',
        'tag': 'Education',
    },
    {
        'id': 4,
        'name': 'Swaminarayan Temple Vadtal',
        'subtitle': 'Divine Spiritual Abode',
        'description': 'One of the most sacred Swaminarayan temples in India, the Laxminarayan Dev Gadi at Vadtal draws thousands of devotees every day.',
        'image': 'images/places/vadtal_temple.jpg',
        'stop': 'VADTAL',
        'stop_name': 'Vadtal Temple Gateway',
        'icon': '🛕',
        'tag': 'Spiritual',
    },
    {
        'id': 5,
        'name': 'Ranchhodraiji Temple — Dakor Corridor',
        'subtitle': 'Sacred Pilgrimage Gateway',
        'description': 'The revered route to Dakor — home of Ranchhodraiji — passes through Anand district, connecting devotees to one of Gujarat\'s holiest shrines.',
        'image': 'images/places/dakor.jpg',
        'stop': 'BORIAVI',
        'stop_name': 'Boriavi',
        'icon': '🙏',
        'tag': 'Pilgrimage',
    },
    {
        'id': 6,
        'name': 'Floyde / Kanewal Lake',
        'subtitle': 'Scenic Natural Retreat',
        'description': 'A serene lake and nature reserve offering breathtaking sunsets, birdwatching, and peaceful walks away from the city bustle.',
        'image': 'images/places/kanewal_lake.jpg',
        'stop': 'SAMARKHA',
        'stop_name': 'Samarkha',
        'icon': '🏞️',
        'tag': 'Nature',
    },
]


def home(request):
    """Main home page with search, carousel, active routes list, and city info."""
    today = date.today()
    try:
        upcoming_schedules_count = Schedule.objects.filter(
            travel_date__gte=today,
            status__in=['SCHEDULED', 'DELAYED']
        ).count()
        active_routes_qs = Route.objects.filter(status='ACTIVE').select_related('source', 'destination')
        stops = list(Stop.objects.all().order_by('name'))

        routes_data = []
        for route in active_routes_qs:
            upcoming_sch = Schedule.objects.filter(
                route=route,
                travel_date__gte=today,
                status__in=['SCHEDULED', 'DELAYED'],
                available_seats__gt=0
            ).order_by('travel_date', 'departure_time').first()

            routes_data.append({
                'route': route,
                'upcoming_schedule': upcoming_sch,
                'fare': route.calculate_fare(),
            })
        active_routes_count = active_routes_qs.count()
    except Exception:
        upcoming_schedules_count = 0
        stops = []
        routes_data = []
        active_routes_count = 0

    tomorrow = today + timedelta(days=1)

    context = {
        'title': 'AnandBus — Your Smart City Bus Companion',
        'places': ANAND_PLACES,
        'stops': stops,
        'anand_stops': ANAND_STOPS,
        'active_routes': active_routes_count,
        'routes_data': routes_data,
        'upcoming_schedules': upcoming_schedules_count,
        'default_date': tomorrow.strftime('%Y-%m-%d'),
        'today': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'routes/home.html', context)


def ensure_schedules_for_date(travel_date):
    """Dynamically ensure active routes have schedules for the requested date."""
    from buses.models import Bus, Driver

    active_routes = Route.objects.filter(status='ACTIVE')
    if not active_routes.exists():
        return

    existing_route_ids = set(Schedule.objects.filter(travel_date=travel_date).values_list('route_id', flat=True))

    buses = list(Bus.objects.all())
    drivers = list(Driver.objects.all())

    if not buses:
        bus, _ = Bus.objects.get_or_create(
            bus_number='GJ-18-T-1001',
            defaults={'bus_name': 'Anand Express', 'bus_type': 'AC', 'total_seats': 40, 'has_gps': True}
        )
        buses = [bus]

    default_timings = [
        ('06:00:00', '07:15:00'),
        ('08:30:00', '09:45:00'),
        ('11:00:00', '12:15:00'),
        ('14:00:00', '15:15:00'),
        ('16:30:00', '17:45:00'),
        ('19:00:00', '20:15:00'),
    ]

    schedules_to_create = []
    for idx, route in enumerate(active_routes):
        if route.id not in existing_route_ids:
            bus = buses[idx % len(buses)]
            driver = drivers[idx % len(drivers)] if drivers else None
            for dep, arr in default_timings:
                schedules_to_create.append(Schedule(
                    route=route,
                    bus=bus,
                    driver=driver,
                    travel_date=travel_date,
                    departure_time=dep,
                    arrival_time=arr,
                    available_seats=bus.total_seats,
                    status='SCHEDULED',
                ))

    if schedules_to_create:
        Schedule.objects.bulk_create(schedules_to_create)


def search_buses(request):
    """Search available bus schedules with Crowd Density and Smart Connecting Route suggestions."""
    source_code = request.GET.get('source', '')
    dest_code = request.GET.get('destination', '')
    travel_date_str = request.GET.get('date', '')
    num_seats = int(request.GET.get('seats', 1))

    schedules = []
    connecting_routes = []
    source_stop = None
    dest_stop = None
    error = None

    if source_code and dest_code and travel_date_str:
        try:
            travel_date = date.fromisoformat(travel_date_str)
            if travel_date < date.today():
                error = "Please select today's or a future date."
            else:
                source_stop = Stop.objects.filter(code=source_code).first()
                dest_stop = Stop.objects.filter(code=dest_code).first()

                # Ensure active routes have schedules for this travel_date
                ensure_schedules_for_date(travel_date)

                # 1. Direct Routes matching source & destination stops
                source_route_ids = set(RouteStop.objects.filter(stop=source_stop).values_list('route_id', flat=True)) if source_stop else set()
                dest_route_ids = set(RouteStop.objects.filter(stop=dest_stop).values_list('route_id', flat=True)) if dest_stop else set()
                common_route_ids = list(source_route_ids.intersection(dest_route_ids))

                direct_routes = []
                if source_stop and dest_stop:
                    direct_routes = list(Route.objects.filter(
                        Q(source=source_stop, destination=dest_stop) | Q(source=dest_stop, destination=source_stop)
                    ).values_list('id', flat=True))

                valid_route_ids = list(set(common_route_ids + direct_routes))

                if valid_route_ids:
                    schedules = list(Schedule.objects.filter(
                        route_id__in=valid_route_ids,
                        travel_date=travel_date,
                        status__in=['SCHEDULED', 'DELAYED'],
                        available_seats__gte=num_seats,
                    ).select_related('route', 'bus', 'driver').order_by('departure_time'))

                # Attach Crowd Density Indicator to each direct schedule
                for sch in schedules:
                    total_seats = sch.bus.total_seats or 40
                    avail_seats = sch.available_seats
                    occ_pct = int(((total_seats - avail_seats) / max(1, total_seats)) * 100)
                    
                    if occ_pct > 85 or avail_seats <= 5:
                        sch.crowd_label = "High Capacity (Red)"
                        sch.crowd_class = "danger"
                        sch.crowd_icon = "fa-user-slash"
                    elif occ_pct > 50:
                        sch.crowd_label = "Moderate Capacity (Yellow)"
                        sch.crowd_class = "warning text-dark"
                        sch.crowd_icon = "fa-user-clock"
                    else:
                        sch.crowd_label = "Low Capacity (Green - Seats Available)"
                        sch.crowd_class = "success"
                        sch.crowd_icon = "fa-user-check"

                # 2. Smart Connecting Route Suggestion (if direct buses are few or 0)
                if len(schedules) < 2 and source_stop and dest_stop and source_stop.id != dest_stop.id:
                    # Major interchange hubs in Anand area
                    interchange_codes = ['ANAND_BUS_STAND', 'VV_NAGAR', 'KARAMSAD', 'TOWN_HALL']
                    interchange_stops = Stop.objects.filter(code__in=interchange_codes).exclude(id__in=[source_stop.id, dest_stop.id])

                    for hub in interchange_stops:
                        # Leg 1: Source -> Hub
                        leg1_routes = Route.objects.filter(
                            Q(source=source_stop, destination=hub) | Q(source=hub, destination=source_stop)
                        ).values_list('id', flat=True)
                        leg1_schedules = Schedule.objects.filter(
                            route_id__in=leg1_routes, travel_date=travel_date, status__in=['SCHEDULED', 'DELAYED'], available_seats__gte=num_seats
                        ).select_related('route', 'bus').order_by('departure_time')

                        # Leg 2: Hub -> Destination
                        leg2_routes = Route.objects.filter(
                            Q(source=hub, destination=dest_stop) | Q(source=dest_stop, destination=hub)
                        ).values_list('id', flat=True)
                        leg2_schedules = Schedule.objects.filter(
                            route_id__in=leg2_routes, travel_date=travel_date, status__in=['SCHEDULED', 'DELAYED'], available_seats__gte=num_seats
                        ).select_related('route', 'bus').order_by('departure_time')

                        for s1 in leg1_schedules:
                            for s2 in leg2_schedules:
                                # Ensure Leg 2 departs after Leg 1 arrives
                                if s2.departure_time > s1.arrival_time:
                                    t1_dt = datetime.datetime.combine(travel_date, s1.arrival_time)
                                    t2_dt = datetime.datetime.combine(travel_date, s2.departure_time)
                                    layover_mins = int((t2_dt - t1_dt).total_seconds() // 60)
                                    
                                    if 5 <= layover_mins <= 90:  # Reasonable transfer wait time
                                        total_fare = float(s1.route.calculate_fare()) + float(s2.route.calculate_fare())
                                        connecting_routes.append({
                                            'leg1': s1,
                                            'leg2': s2,
                                            'transfer_stop': hub.name,
                                            'layover_minutes': layover_mins,
                                            'total_fare': round(total_fare, 2),
                                        })
                                        if len(connecting_routes) >= 3:
                                            break
                            if len(connecting_routes) >= 3:
                                break
                        if len(connecting_routes) >= 3:
                            break

        except (ValueError, Exception) as e:
            error = str(e)

    stops = Stop.objects.all().order_by('name')
    context = {
        'title': 'Search Results — AnandBus',
        'schedules': schedules,
        'connecting_routes': connecting_routes,
        'source_stop': source_stop,
        'dest_stop': dest_stop,
        'source_code': source_code,
        'dest_code': dest_code,
        'travel_date': travel_date_str,
        'num_seats': num_seats,
        'stops': stops,
        'error': error,
    }
    return render(request, 'routes/search_results.html', context)


def route_detail(request, route_id):
    """Route detail with all stops and schedule."""
    route = get_object_or_404(Route, id=route_id)
    route_stops = RouteStop.objects.filter(route=route).select_related('stop').order_by('stop_order')
    today = date.today()
    upcoming = Schedule.objects.filter(
        route=route, travel_date__gte=today, status__in=['SCHEDULED']
    ).order_by('travel_date', 'departure_time')[:7]

    # Build GeoJSON path for Leaflet map
    coords = []
    for rs in route_stops:
        if rs.stop.coords:
            coords.append(rs.stop.coords)

    context = {
        'title': f'Route {route.route_number} — {route.route_name}',
        'route': route,
        'route_stops': route_stops,
        'upcoming_schedules': upcoming,
        'coords_json': json.dumps(coords),
    }
    return render(request, 'routes/route_detail.html', context)


@require_GET
def api_stops(request):
    """AJAX: return all stops as JSON."""
    stops = list(Stop.objects.values('code', 'name', 'latitude', 'longitude'))
    return JsonResponse({'stops': stops})


@require_GET
def api_schedule_seats(request, schedule_id):
    """AJAX: return seat availability for a schedule."""
    from bookings.models import Seat
    schedule = get_object_or_404(Schedule, id=schedule_id)
    seats = Seat.objects.filter(schedule=schedule).values(
        'id', 'seat_number', 'row_number', 'column_letter', 'seat_type', 'status', 'price_multiplier'
    )
    fare = float(schedule.route.calculate_fare())
    return JsonResponse({'seats': list(seats), 'base_fare': fare, 'schedule_id': schedule_id})
