import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from routes.models import Stop, Route, RouteStop, Schedule
from buses.models import Bus
from conductor.models import TripLog, OfflineTicket


class ConductorTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.conductor = CustomUser.objects.create_user(
            username='conductor_test',
            email='cond@example.com',
            password='Password123!',
            role=CustomUser.Role.CONDUCTOR,
        )
        self.stop1 = Stop.objects.create(code='CS1', name='Cond Stop 1', latitude=22.56, longitude=72.92)
        self.stop2 = Stop.objects.create(code='CS2', name='Cond Stop 2', latitude=22.57, longitude=72.93)
        self.route = Route.objects.create(
            route_number='R300',
            route_name='Conductor Route',
            source=self.stop1,
            destination=self.stop2,
            distance_km=12.0,
            base_fare=10.0,
            fare_per_km=1.0,
        )
        RouteStop.objects.create(route=self.route, stop=self.stop1, stop_order=1, distance_from_source=0)
        RouteStop.objects.create(route=self.route, stop=self.stop2, stop_order=2, distance_from_source=12.0)

        self.bus = Bus.objects.create(bus_number='GJ-18-C-0003', bus_name='Cond Bus', total_seats=40)
        self.schedule = Schedule.objects.create(
            route=self.route,
            bus=self.bus,
            travel_date=datetime.date.today(),
            departure_time='08:00',
            arrival_time='09:00',
            available_seats=40,
        )

    def test_conductor_dashboard(self):
        self.client.force_login(self.conductor)
        response = self.client.get(reverse('conductor:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_trip_detail(self):
        self.client.force_login(self.conductor)
        response = self.client.get(reverse('conductor:trip_detail', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)

    def test_update_trip_status(self):
        self.client.force_login(self.conductor)
        payload = {'status': 'DEPARTED', 'delay_minutes': 0, 'message': 'Departed'}
        response = self.client.post(
            reverse('conductor:update_trip_status', args=[self.schedule.id]),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.status, 'DEPARTED')

    def test_issue_offline_ticket(self):
        self.client.force_login(self.conductor)
        response = self.client.post(reverse('conductor:issue_offline_ticket', args=[self.schedule.id]), {
            'boarding_stop': 'CS1',
            'alighting_stop': 'CS2',
            'seat_numbers': 'A1',
            'passenger_count': 1,
            'amount': '22.00',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(OfflineTicket.objects.filter(schedule=self.schedule).exists())

