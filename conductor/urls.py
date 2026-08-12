from django.urls import path
from . import views

app_name = 'conductor'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('trip/<int:schedule_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:schedule_id>/status/', views.update_trip_status, name='update_trip_status'),
    path('trip/<int:schedule_id>/manifest/', views.passenger_manifest, name='passenger_manifest'),
    path('trip/<int:schedule_id>/offline-ticket/', views.issue_offline_ticket, name='issue_offline_ticket'),
    path('seat/<int:seat_id>/status/', views.update_seat_status, name='update_seat_status'),
    path('verify/', views.verify_ticket, name='verify_ticket'),
    path('api/verify-qr/', views.api_verify_qr, name='api_verify_qr'),
]
