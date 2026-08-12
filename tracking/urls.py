from django.urls import path
from . import views

app_name = 'tracking'

urlpatterns = [
    path('live/<int:schedule_id>/', views.live_tracking, name='live'),
    path('api/location/<int:schedule_id>/', views.api_bus_location, name='api_location'),
    path('api/simulate/<int:schedule_id>/', views.api_simulate_movement, name='api_simulate'),
]
