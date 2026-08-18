from django.urls import path
from . import views

app_name = 'tracking'

urlpatterns = [
    path('', views.live_tracking, name='index'),
    path('live/', views.live_tracking, name='live_index'),
    path('live/<int:schedule_id>/', views.live_tracking, name='live'),
    path('api/search/', views.api_search_schedule, name='api_search'),
    path('api/location/<int:schedule_id>/', views.api_bus_location, name='api_location'),
    path('api/simulate/<int:schedule_id>/', views.api_simulate_movement, name='api_simulate'),
]
