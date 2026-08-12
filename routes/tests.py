import datetime
from django.test import TestCase, Client
from django.urls import reverse
from routes.models import Stop, Route, RouteStop, Schedule
from buses.models import Bus


class RoutesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.stop1 = Stop.objects.create(code='S1', name='Stop 1', latitude=22.56, longitude=72.92)
        self.stop2 = Stop.objects.create(code='S2', name='Stop 2', latitude=22.57, longitude=72.93)
        self.route = Route.objects.create(
            route_number='R100',
            route_name='Test Route',
            source=self.stop1,
            destination=self.stop2,
            distance_km=10.0,
            base_fare=12.0,
            fare_per_km=1.2,
        )
        RouteStop.objects.create(route=self.route, stop=self.stop1, stop_order=1, distance_from_source=0)
        RouteStop.objects.create(route=self.route, stop=self.stop2, stop_order=2, distance_from_source=10.0)

        self.bus = Bus.objects.create(bus_number='GJ-18-R-0001', bus_name='Route Bus', total_seats=40)
        self.schedule = Schedule.objects.create(
            route=self.route,
            bus=self.bus,
            travel_date=datetime.date.today(),
            departure_time='09:00',
            arrival_time='10:00',
            available_seats=40,
        )

    def test_home_view(self):
        response = self.client.get(reverse('routes:home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('stops', response.context)

    def test_search_buses_view(self):
        response = self.client.get(reverse('routes:search'), {
            'source': 'S1',
            'destination': 'S2',
            'date': datetime.date.today().isoformat(),
            'seats': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.schedule, response.context['schedules'])

    def test_route_detail_view(self):
        response = self.client.get(reverse('routes:route_detail', args=[self.route.id]))
        self.assertEqual(response.status_code, 200)

    def test_api_stops(self):
        response = self.client.get(reverse('routes:api_stops'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['stops']) >= 2)

