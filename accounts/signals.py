from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, PassengerProfile, ConductorProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create role-specific profile on user creation."""
    if created:
        if instance.role == CustomUser.Role.PASSENGER:
            PassengerProfile.objects.get_or_create(user=instance)
        elif instance.role == CustomUser.Role.CONDUCTOR:
            # Employee ID auto-generated
            emp_id = f"EMP{instance.pk:04d}"
            ConductorProfile.objects.get_or_create(user=instance, defaults={'employee_id': emp_id})
