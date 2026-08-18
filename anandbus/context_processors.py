from django.conf import settings
from accounts.models import Notification


def site_settings(request):
    """Inject global site settings and in-app user notifications into every template context."""
    user_notifications = []
    unread_notification_count = 0

    if request.user.is_authenticated:
        user_notifications = list(Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:8])
        
        unread_notification_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'AnandBus'),
        'SITE_TAGLINE': getattr(settings, 'SITE_TAGLINE', 'Your Smart City Bus Companion'),
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'STRIPE_PUBLIC_KEY': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        'user_notifications': user_notifications,
        'unread_notification_count': unread_notification_count,
    }

