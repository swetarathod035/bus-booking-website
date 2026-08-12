from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Passenger dashboard
    path('dashboard/', views.passenger_dashboard, name='passenger_dashboard'),

    # Booking flow
    path('seats/<int:schedule_id>/', views.select_seats, name='select_seats'),
    path('passenger-details/', views.passenger_info, name='passenger_info'),
    path('create/', views.create_booking, name='create_booking'),
    path('pay/<uuid:booking_id>/', views.booking_payment, name='booking_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('success/<uuid:booking_id>/', views.booking_success, name='booking_success'),
    path('<uuid:booking_id>/', views.booking_detail, name='booking_detail'),
    path('<uuid:booking_id>/download/', views.download_ticket, name='download_ticket'),

    # Public / Dedicated Reschedule & Cancellation pages
    path('reschedule-ticket/', views.reschedule_ticket_page, name='reschedule_ticket_page'),
    path('cancel-ticket/', views.cancel_ticket_page, name='cancel_ticket_page'),

    # Manage bookings
    path('<uuid:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('<uuid:booking_id>/reschedule/', views.reschedule_booking, name='reschedule_booking'),

    # AJAX
    path('api/fare/', views.api_calculate_fare, name='api_calculate_fare'),
]

