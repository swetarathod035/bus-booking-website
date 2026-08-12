from django.contrib import admin
from .models import Seat, Booking, PassengerDetail, Payment, Ticket


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['short_id', 'passenger', 'schedule', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['booking_id', 'passenger__username', 'passenger__email']
    readonly_fields = ['booking_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'gateway', 'status', 'amount', 'paid_at']
    list_filter = ['gateway', 'status']
    search_fields = ['gateway_payment_id', 'gateway_order_id']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'booking', 'is_verified', 'issued_at']
    search_fields = ['ticket_number']
    list_filter = ['is_verified']
