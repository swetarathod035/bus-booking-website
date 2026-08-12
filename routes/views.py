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
    upcoming_schedules_count = Schedule.objects.filter(
        travel_date__gte=today,
        status__in=['SCHEDULED', 'DELAYED']
    ).count()
    active_routes_qs = Route.objects.filter(status='ACTIVE').select_related('source', 'destination')
    stops = Stop.objects.all().order_by('name')

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

    tomorrow = today + timedelta(days=1)

    context = {
        'title': 'AnandBus — Your Smart City Bus Companion',
        'places': ANAND_PLACES,
        'stops': stops,
        'anand_stops': ANAND_STOPS,
        'active_routes': active_routes_qs.count(),
        'routes_data': routes_data,
        'upcoming_schedules': upcoming_schedules_count,
        'default_date': tomorrow.strftime('%Y-%m-%d'),
        'today': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'routes/home.html', context)


def search_buses(request):
    """Search available bus schedules."""
    source_code = request.GET.get('source', '')
    dest_code = request.GET.get('destination', '')
    travel_date_str = request.GET.get('date', '')
    num_seats = int(request.GET.get('seats', 1))

    schedules = []
    source_stop = None
    dest_stop = None
    error = None

    if source_code and dest_code and travel_date_str:
        try:
            travel_date = date.fromisoformat(travel_date_str)
            if travel_date < date.today():
                error = "Please select today's or a future date."
            else:
                source_stop = get_object_or_404(Stop, code=source_code)
                dest_stop = get_object_or_404(Stop, code=dest_code)

                # Find routes that include both stops in order
                source_route_stops = RouteStop.objects.filter(stop=source_stop).values_list('route', 'stop_order')
                dest_route_stops = RouteStop.objects.filter(stop=dest_stop).values_list('route', 'stop_order')

                valid_route_ids = []
                for (r_id, s_order) in source_route_stops:
                    for (r_id2, d_order) in dest_route_stops:
                        if r_id == r_id2 and s_order < d_order:
                            valid_route_ids.append(r_id)

                schedules = Schedule.objects.filter(
                    route_id__in=valid_route_ids,
                    travel_date=travel_date,
                    status__in=['SCHEDULED', 'DELAYED'],
                    available_seats__gte=num_seats,
                ).select_related('route', 'bus', 'driver').order_by('departure_time')

        except (ValueError, Exception) as e:
            error = str(e)

    stops = Stop.objects.all().order_by('name')
    context = {
        'title': 'Search Results — AnandBus',
        'schedules': schedules,
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
