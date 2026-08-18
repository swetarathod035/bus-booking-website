from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ConductorProfile, PassengerProfile, AdminAuditLog


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


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'action_type', 'target_repr', 'timestamp', 'ip_address']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['admin_user__username', 'target_repr', 'details']
    readonly_fields = ['admin_user', 'action_type', 'target_repr', 'details', 'ip_address', 'timestamp']

