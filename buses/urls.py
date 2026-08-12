from django.urls import path
from . import views

app_name = 'buses'

urlpatterns = [
    # Admin Dashboard
    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    # Bus management
    path('admin/buses/', views.bus_list, name='bus_list'),
    path('admin/buses/add/', views.bus_create, name='bus_create'),
    path('admin/buses/<int:pk>/edit/', views.bus_edit, name='bus_edit'),
    path('admin/buses/<int:pk>/toggle/', views.bus_toggle, name='bus_toggle'),

    # Driver management
    path('admin/drivers/', views.driver_list, name='driver_list'),
    path('admin/drivers/add/', views.driver_create, name='driver_create'),
    path('admin/drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),

    # Routes & Schedules
    path('admin/routes/', views.route_management, name='route_management'),
    path('admin/schedules/', views.schedule_management, name='schedule_management'),

    # Users
    path('admin/users/', views.user_management, name='user_management'),
    path('admin/users/<int:user_id>/promote/', views.promote_user, name='promote_user'),

    # Revenue
    path('admin/revenue/', views.revenue_report, name='revenue_report'),
    path('admin/export/bookings/', views.export_bookings_excel, name='export_bookings'),

    # AJAX
    path('api/schedule/<int:schedule_id>/status/', views.api_toggle_schedule_status, name='api_schedule_status'),
]
