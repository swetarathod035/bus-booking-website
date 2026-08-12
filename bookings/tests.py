import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from routes.models import Stop, Route, RouteStop, Schedule
from buses.models import Bus
from bookings.models import Booking, Seat, Payment, Ticket, PassengerDetail


class BookingsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.passenger = CustomUser.objects.create_user(
            username='pax_booking',
            email='paxbook@example.com',
            password='Password123!',
            role=CustomUser.Role.PASSENGER,
        )
        self.stop1 = Stop.objects.create(code='S1', name='Stop 1', latitude=22.56, longitude=72.92)
        self.stop2 = Stop.objects.create(code='S2', name='Stop 2', latitude=22.57, longitude=72.93)
        self.route = Route.objects.create(
            route_number='R200',
            route_name='Booking Route',
            source=self.stop1,
            destination=self.stop2,
            distance_km=15.0,
            base_fare=15.0,
            fare_per_km=1.5,
        )
        RouteStop.objects.create(route=self.route, stop=self.stop1, stop_order=1, distance_from_source=0)
        RouteStop.objects.create(route=self.route, stop=self.stop2, stop_order=2, distance_from_source=15.0)

        self.bus = Bus.objects.create(bus_number='GJ-18-B-0002', bus_name='Booking Bus', total_seats=40)
        self.schedule = Schedule.objects.create(
            route=self.route,
            bus=self.bus,
            travel_date=datetime.date.today(),
            departure_time='10:00',
            arrival_time='11:30',
            available_seats=40,
        )

    def test_passenger_dashboard(self):
        self.client.force_login(self.passenger)
        response = self.client.get(reverse('bookings:passenger_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_seat_selection_view(self):
        self.client.force_login(self.passenger)
        response = self.client.get(reverse('bookings:select_seats', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Seat.objects.filter(schedule=self.schedule).exists())

    def test_passenger_info_validation_invalid_age(self):
        """Test passenger_info rejects 3-digit age with proper error message."""
        self.client.force_login(self.passenger)
        self.client.get(reverse('bookings:select_seats', args=[self.schedule.id]))
        seat = Seat.objects.filter(schedule=self.schedule, status='AVAILABLE').first()

        post_data = {
            'schedule_id': self.schedule.id,
            'seat_ids': str(seat.id),
            'boarding_stop': 'S1',
            'alighting_stop': 'S2',
            'name_0': 'John Doe',
            'age_0': '105',  # 3-digit age -> Invalid!
            'gender_0': 'M',
            'email_0': 'john@example.com',
            'phone_0': '9876543210',
        }
        response = self.client.post(reverse('bookings:passenger_info'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid age (1-99)')

    def test_passenger_info_valid_submission(self):
        """Test valid passenger info submission creates booking and passenger details."""
        self.client.force_login(self.passenger)
        self.client.get(reverse('bookings:select_seats', args=[self.schedule.id]))
        seat = Seat.objects.filter(schedule=self.schedule, status='AVAILABLE').first()

        post_data = {
            'schedule_id': self.schedule.id,
            'seat_ids': str(seat.id),
            'boarding_stop': 'S1',
            'alighting_stop': 'S2',
            'name_0': 'Jane Doe',
            'age_0': '28',
            'gender_0': 'F',
            'email_0': 'jane@example.com',
            'phone_0': '9876543210',
        }
        response = self.client.post(reverse('bookings:passenger_info'), post_data)
        self.assertEqual(response.status_code, 302)

        booking = Booking.objects.get(passenger=self.passenger, passenger_email='jane@example.com')
        self.assertEqual(booking.passenger_name, 'Jane Doe')
        self.assertEqual(booking.passenger_phone, '9876543210')

        pax_detail = PassengerDetail.objects.get(booking=booking)
        self.assertEqual(pax_detail.name, 'Jane Doe')
        self.assertEqual(pax_detail.age, 28)
        self.assertEqual(pax_detail.gender, 'F')
        self.assertEqual(pax_detail.email, 'jane@example.com')
        self.assertEqual(pax_detail.phone, '9876543210')

    def test_date_only_reschedule_flow(self):
        """Test date-only reschedule flow on reschedule ticket page."""
        self.client.force_login(self.passenger)
        self.client.get(reverse('bookings:select_seats', args=[self.schedule.id]))
        seat = Seat.objects.filter(schedule=self.schedule, status='AVAILABLE').first()

        # Create confirmed booking
        booking = Booking.objects.create(
            passenger=self.passenger,
            schedule=self.schedule,
            boarding_stop=self.stop1,
            alighting_stop=self.stop2,
            num_passengers=1,
            status=Booking.Status.CONFIRMED,
            passenger_name='Jane Doe',
            passenger_email='reschedule@example.com',
        )
        booking.seats.set([seat])

        # Future schedule on a new date
        next_week = datetime.date.today() + datetime.timedelta(days=7)
        future_sch = Schedule.objects.create(
            route=self.route,
            bus=self.bus,
            travel_date=next_week,
            departure_time='14:00',
            arrival_time='15:30',
            available_seats=40,
        )

        # Step 1: Search by PNR & Email
        res1 = self.client.post(reverse('bookings:reschedule_ticket_page'), {
            'action': 'search',
            'pnr_number': booking.short_id,
            'email': 'reschedule@example.com',
        })
        self.assertEqual(res1.status_code, 200)

        # Step 2: Directly submit date reschedule
        res2 = self.client.post(reverse('bookings:reschedule_ticket_page'), {
            'action': 'reschedule',
            'pnr_number': booking.short_id,
            'email': 'reschedule@example.com',
            'new_travel_date': next_week.strftime('%Y-%m-%d'),
        })
        self.assertEqual(res2.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.schedule.travel_date, next_week)
