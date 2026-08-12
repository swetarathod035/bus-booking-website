from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from buses.models import Bus, Driver


class BusesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_superuser(
            username='admin_test',
            email='admin@example.com',
            password='AdminPassword123!',
            role=CustomUser.Role.SUPER_ADMIN,
        )
        self.bus = Bus.objects.create(
            bus_number='GJ-18-T-9999',
            bus_name='Test Bus',
            bus_type='AC',
            total_seats=40,
            has_wifi=True,
            has_ac=True,
        )

    def test_bus_creation_and_properties(self):
        self.assertEqual(self.bus.bus_number, 'GJ-18-T-9999')
        self.assertIn('WiFi', self.bus.amenities_list)

    def test_admin_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('buses:admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_bus_crud_views(self):
        self.client.force_login(self.admin)
        resp_list = self.client.get(reverse('buses:bus_list'))
        self.assertEqual(resp_list.status_code, 200)

        resp_create = self.client.post(reverse('buses:bus_create'), {
            'bus_number': 'GJ-18-T-8888',
            'bus_name': 'New Bus',
            'bus_type': 'NON_AC',
            'total_seats': 30,
            'status': 'ACTIVE',
        })
        self.assertIn(resp_create.status_code, [200, 302])
        self.assertTrue(Bus.objects.filter(bus_number='GJ-18-T-8888').exists())

        resp_toggle = self.client.get(reverse('buses:bus_toggle', args=[self.bus.pk]))
        self.assertIn(resp_toggle.status_code, [200, 302])
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.status, 'INACTIVE')

    def test_driver_crud_views(self):
        self.client.force_login(self.admin)
        resp_create = self.client.post(reverse('buses:driver_create'), {
            'employee_id': 'DRV999',
            'name': 'Ramesh Test',
            'license_number': 'GJ18-99999999',
            'phone': '9876543210',
            'status': 'AVAILABLE',
            'experience_years': 5,
        })
        self.assertIn(resp_create.status_code, [200, 302])
        self.assertTrue(Driver.objects.filter(employee_id='DRV999').exists())

