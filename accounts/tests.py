from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.passenger = CustomUser.objects.create_user(
            username='pax_test',
            email='pax@example.com',
            password='Password123!',
            first_name='Priya',
            last_name='Patel',
            role=CustomUser.Role.PASSENGER,
        )

    def test_user_creation(self):
        self.assertEqual(self.passenger.role, 'PASSENGER')
        self.assertEqual(self.passenger.get_dashboard_url(), '/bookings/dashboard/')

    def test_login_view(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

        response_post = self.client.post(reverse('accounts:login'), {
            'username': 'pax_test',
            'password': 'Password123!',
        })
        self.assertIn(response_post.status_code, [200, 302])

    def test_registration_view(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

        response_post = self.client.post(reverse('accounts:register'), {
            'username': 'new_user',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'Pass123456!',
            'password2': 'Pass123456!',
        })
        self.assertIn(response_post.status_code, [200, 302])
        self.assertTrue(CustomUser.objects.filter(username='new_user').exists())

    def test_profile_view(self):
        self.client.force_login(self.passenger)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

        response_post = self.client.post(reverse('accounts:profile'), {
            'first_name': 'PriyaUpdated',
            'last_name': 'Patel',
            'email': 'pax@example.com',
        })
        self.assertIn(response_post.status_code, [200, 302])
        self.passenger.refresh_from_db()
        self.assertEqual(self.passenger.first_name, 'PriyaUpdated')

    def test_logout_view(self):
        self.client.force_login(self.passenger)
        response = self.client.get(reverse('accounts:logout'))
        self.assertIn(response.status_code, [200, 302])

