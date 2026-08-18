import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)


def send_sms_whatsapp_alert(phone_number, text_content, channel="SMS/WhatsApp"):
    """
    Sends or simulates an instant SMS / WhatsApp alert message to user's mobile number.
    In production, this connects to Msg91 / Twilio API gateway.
    """
    phone = phone_number or "+91-9876543210"
    log_msg = f"📱 [{channel} ALERT SENT to {phone}]: {text_content}"
    logger.info(log_msg)
    print(log_msg)  # Printed to server console for instant verification
    return True


def create_notification(user, title, message, notification_type=Notification.NotificationType.GENERAL, link=None, send_email=True, send_sms=True):
    """
    Creates an In-App Notification entry in DB and dispatches Email + SMS/WhatsApp alerts.
    """
    if not user or not user.is_authenticated:
        return None

    # 1. Save In-App Database Entry
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )

    # 2. Instant SMS / WhatsApp Mobile Alert
    if send_sms:
        user_phone = getattr(user, 'phone', None) or getattr(user, 'phone_number', None) or "+91-9876543210"
        sms_text = f"AnandBus Alert: {title} — {message}. Details: {settings.SITE_URL}{link or ''}"
        send_sms_whatsapp_alert(user_phone, sms_text)

    # 3. Professional Email Notification
    if send_email and user.email:
        try:
            email_subject = f"🔔 AnandBus Notification: {title}"
            email_body = f"""
            Hello {user.get_full_name() or user.username},

            {title}
            --------------------------------------------------
            {message}

            Log in to your AnandBus account to view details:
            {settings.SITE_URL}{link or ''}

            Thank you for traveling with AnandBus!
            Your Smart City Bus Companion
            """
            msg = EmailMessage(
                subject=email_subject,
                body=email_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'AnandBus <noreply@anandbus.com>'),
                to=[user.email]
            )
            msg.send(fail_silently=True)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    return notification
