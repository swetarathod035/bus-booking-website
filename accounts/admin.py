from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ConductorProfile, PassengerProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'get_full_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {'fields': ('role', 'phone', 'avatar', 'date_of_birth', 'address', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Profile', {'fields': ('role', 'phone', 'email', 'first_name', 'last_name')}),
    )


@admin.register(ConductorProfile)
class ConductorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'assigned_bus', 'is_active_duty']
    search_fields = ['user__username', 'employee_id']


@admin.register(PassengerProfile)
class PassengerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'loyalty_points', 'preferred_payment']
    search_fields = ['user__username', 'user__email']
