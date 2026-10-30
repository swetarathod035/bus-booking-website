from django.core.management.base import BaseCommand
from bookings.utils import send_pass_expiry_notifications

class Command(BaseCommand):
    help = 'Sends automated email and SMS notification alerts to passengers whose bus passes expire within 3 days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Days ahead of expiry to target for notifications (default: 3).'
        )

    def handle(self, *args, **options):
        days = options['days']
        self.stdout.write(f'Checking active bus passes expiring within {days} days...')
        count = send_pass_expiry_notifications(days_ahead=days)
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {count} automated pass expiry alert notifications.'))
