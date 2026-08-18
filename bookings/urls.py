from django.urls import path
from . import views
from . import pass_views

app_name = 'bookings'

urlpatterns = [
    # Passenger dashboard
    path('dashboard/', views.passenger_dashboard, name='passenger_dashboard'),

    # Booking flow: Seats → Passenger Details → Payment → Success
    path('seats/<int:schedule_id>/', views.select_seats, name='select_seats'),
    path('passenger-details/', views.passenger_info, name='passenger_info'),
    path('create/', views.create_booking, name='create_booking'),
    path('pay/<uuid:booking_id>/', views.booking_payment, name='booking_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('success/<uuid:booking_id>/', views.booking_success, name='booking_success'),
    path('<uuid:booking_id>/', views.booking_detail, name='booking_detail'),
    path('<uuid:booking_id>/download/', views.download_ticket, name='download_ticket'),

    # Cancel / Reschedule / Rating
    path('reschedule-ticket/', views.reschedule_ticket_page, name='reschedule_ticket_page'),
    path('cancel-ticket/', views.cancel_ticket_page, name='cancel_ticket_page'),
    path('<uuid:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('<uuid:booking_id>/reschedule/', views.reschedule_booking, name='reschedule_booking'),
    path('<uuid:booking_id>/rate/', views.submit_ride_rating, name='submit_ride_rating'),


    # AJAX
    path('api/fare/', views.api_calculate_fare, name='api_calculate_fare'),

    # ── Bus Pass system ───────────────────────────────────────────────────────
    path('passes/', pass_views.pass_schemes_list, name='pass_schemes_list'),
    path('passes/mine/', pass_views.my_passes, name='my_passes'),
    path('passes/apply/<int:scheme_id>/', pass_views.apply_for_pass, name='apply_for_pass'),

    # Admin pass management
    path('passes/admin/', pass_views.admin_pass_list, name='admin_pass_list'),
    path('passes/admin/<int:pass_id>/approve/', pass_views.admin_approve_pass, name='admin_approve_pass'),
    path('passes/schemes/', pass_views.admin_scheme_list, name='admin_scheme_list'),
    path('passes/schemes/add/', pass_views.admin_scheme_create, name='admin_scheme_create'),
    path('passes/schemes/<int:scheme_id>/edit/', pass_views.admin_scheme_edit, name='admin_scheme_edit'),

    # Conductor scan pass (AJAX)
    path('passes/scan/', pass_views.conductor_scan_pass, name='conductor_scan_pass'),
]
