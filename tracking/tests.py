import datetime
from django.test import TestCase, Client
from django.urls import reverse
from routes.models import Stop, Route, RouteStop, Schedule
from buses.models import Bus
from tracking.models import BusLocation


class TrackingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.stop1 = Stop.objects.create(code='TS1', name='Track Stop 1', latitude=22.5645, longitude=72.9289)
        self.stop2 = Stop.objects.create(code='TS2', name='Track Stop 2', latitude=22.5530, longitude=72.9215)
        self.route = Route.objects.create(
            route_number='R400',
            route_name='Tracking Route',
            source=self.stop1,
            destination=self.stop2,
            distance_km=8.5,
            base_fare=12.0,
            fare_per_km=1.2,
        )
        RouteStop.objects.create(route=self.route, stop=self.stop1, stop_order=1, distance_from_source=0)
        RouteStop.objects.create(route=self.route, stop=self.stop2, stop_order=2, distance_from_source=8.5)

        self.bus = Bus.objects.create(bus_number='GJ-18-T-0004', bus_name='Track Bus', total_seats=40)
        self.schedule = Schedule.objects.create(
            route=self.route,
            bus=self.bus,
            travel_date=datetime.date.today(),
            departure_time='06:00',
            arrival_time='07:00',
            available_seats=40,
        )

    def test_live_tracking_page(self):
        response = self.client.get(reverse('tracking:live', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)

    def test_api_bus_location(self):
        response = self.client.get(reverse('tracking:api_location', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('lat', data)
        self.assertIn('lng', data)

    def test_api_simulate_movement(self):
        response = self.client.get(reverse('tracking:api_simulate', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(BusLocation.objects.filter(schedule=self.schedule).exists())

    def test_api_search_schedule_by_bus_number(self):
        response = self.client.get(reverse('tracking:api_search') + '?q=GJ-18-T-0004')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['schedule_id'], self.schedule.id)
        self.assertEqual(data['bus_number'], 'GJ-18-T-0004')

    def test_api_search_schedule_not_found(self):
        response = self.client.get(reverse('tracking:api_search') + '?q=NON_EXISTENT_BUS_999')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['found'])

    def test_role_based_live_tracking(self):
        # Unauthenticated / Passenger access
        response = self.client.get(reverse('tracking:live', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_admin'])


