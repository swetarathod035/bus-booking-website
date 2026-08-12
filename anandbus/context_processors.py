from django.conf import settings


def site_settings(request):
    """Inject global site settings into every template context."""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'AnandBus'),
        'SITE_TAGLINE': getattr(settings, 'SITE_TAGLINE', 'Your Smart City Bus Companion'),
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'STRIPE_PUBLIC_KEY': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
    }
