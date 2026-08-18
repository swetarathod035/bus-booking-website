from django.urls import path
from . import views

app_name = 'conductor'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Trip management
    path('trip/<int:schedule_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:schedule_id>/status/', views.update_trip_status, name='update_trip_status'),
    path('trip/<int:schedule_id>/manifest/', views.passenger_manifest, name='passenger_manifest'),
    path('trip/<int:schedule_id>/offline-ticket/', views.issue_offline_ticket, name='issue_offline_ticket'),

    # Seat management
    path('seat/<int:seat_id>/status/', views.update_seat_status, name='update_seat_status'),

    # Ticket & Pass verification
    path('verify/', views.verify_ticket, name='verify_ticket'),
    path('scan/', views.scan_passenger, name='scan_passenger'),

    # Operational additions
    path('add-bus/', views.conductor_add_bus, name='add_bus'),
    path('add-schedule/', views.conductor_add_schedule, name='add_schedule'),

    # AJAX
    path('api/verify-qr/', views.api_verify_qr, name='api_verify_qr'),
    path('api/toggle-checkin/', views.toggle_passenger_checkin, name='toggle_passenger_checkin'),
    path('api/emergency-sos/', views.trigger_emergency_sos, name='trigger_emergency_sos'),
]

