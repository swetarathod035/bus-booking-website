from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_buses, name='search'),
    path('route/<int:route_id>/', views.route_detail, name='route_detail'),
    path('api/stops/', views.api_stops, name='api_stops'),
    path('api/schedule/<int:schedule_id>/seats/', views.api_schedule_seats, name='api_schedule_seats'),
]
