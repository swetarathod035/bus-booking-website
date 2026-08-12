from django.contrib import admin
from .models import BusPass, SpecialScheme, SchemeApplication


@admin.register(BusPass)
class BusPassAdmin(admin.ModelAdmin):
    list_display = ['pass_number', 'applicant_name', 'applicant_type', 'route', 'duration_months', 'total_fare', 'status', 'applied_at']
    list_filter = ['applicant_type', 'status', 'duration_months', 'applied_at']
    search_fields = ['pass_number', 'applicant_name', 'email', 'phone', 'college_name', 'id_proof_number']
    readonly_fields = ['pass_number', 'applied_at', 'updated_at']
    ordering = ['-applied_at']
    actions = ['approve_passes', 'reject_passes']

    def approve_passes(self, request, queryset):
        rows_updated = queryset.update(status=BusPass.Status.APPROVED)
        self.message_user(request, f"{rows_updated} pass application(s) marked as APPROVED.")
    approve_passes.short_description = "Mark selected passes as APPROVED"

    def reject_passes(self, request, queryset):
        rows_updated = queryset.update(status=BusPass.Status.REJECTED)
        self.message_user(request, f"{rows_updated} pass application(s) marked as REJECTED.")
    reject_passes.short_description = "Mark selected passes as REJECTED"


@admin.register(SpecialScheme)
class SpecialSchemeAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'target_audience', 'discount_percentage', 'flat_discount', 'is_active', 'valid_until', 'created_at']
    list_filter = ['target_audience', 'is_active', 'created_at']
    search_fields = ['title', 'code', 'description']
    ordering = ['-created_at']


@admin.register(SchemeApplication)
class SchemeApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_number', 'scheme', 'applicant_name', 'email', 'phone', 'preferred_route', 'status', 'applied_at']
    list_filter = ['status', 'scheme', 'applied_at']
    search_fields = ['application_number', 'applicant_name', 'email', 'phone', 'id_proof_number']
    readonly_fields = ['application_number', 'applied_at']
    ordering = ['-applied_at']
    actions = ['approve_scheme_apps', 'reject_scheme_apps']

    def approve_scheme_apps(self, request, queryset):
        rows_updated = queryset.update(status=SchemeApplication.Status.APPROVED)
        self.message_user(request, f"{rows_updated} scheme application(s) approved.")
    approve_scheme_apps.short_description = "Approve selected scheme applications"

    def reject_scheme_apps(self, request, queryset):
        rows_updated = queryset.update(status=SchemeApplication.Status.REJECTED)
        self.message_user(request, f"{rows_updated} scheme application(s) rejected.")
    reject_scheme_apps.short_description = "Reject selected scheme applications"
