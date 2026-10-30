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
    path('admin/buses/<int:pk>/delete/', views.bus_delete, name='bus_delete'),

    # Driver management
    path('admin/drivers/', views.driver_list, name='driver_list'),
    path('admin/drivers/add/', views.driver_create, name='driver_create'),
    path('admin/drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('admin/drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),

    # Bus Stops management
    path('admin/stops/', views.stop_list, name='stop_list'),
    path('admin/stops/add/', views.stop_create, name='stop_create'),
    path('admin/stops/<int:pk>/edit/', views.stop_edit, name='stop_edit'),
    path('admin/stops/<int:pk>/delete/', views.stop_delete, name='stop_delete'),

    # Routes
    path('admin/routes/', views.route_management, name='route_management'),
    path('admin/routes/add/', views.route_create, name='route_create'),
    path('admin/routes/<int:pk>/edit/', views.route_edit, name='route_edit'),
    path('admin/routes/<int:pk>/delete/', views.route_delete, name='route_delete'),

    # Schedules
    path('admin/schedules/', views.schedule_management, name='schedule_management'),
    path('admin/schedules/add/', views.schedule_create, name='schedule_create'),
    path('admin/schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('admin/schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    # Users
    path('admin/users/', views.user_management, name='user_management'),
    path('admin/users/add/', views.user_create, name='user_create'),
    path('admin/users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('admin/users/<int:user_id>/promote/', views.promote_user, name='promote_user'),
    path('admin/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('admin/users/<int:user_id>/toggle-block/', views.user_toggle_block, name='user_toggle_block'),

    # Bookings Admin Management
    path('admin/bookings/', views.booking_admin_list, name='booking_admin_list'),
    path('admin/bookings/<int:pk>/update/', views.booking_admin_update, name='booking_admin_update'),
    path('admin/bookings/<int:pk>/delete/', views.booking_admin_delete, name='booking_admin_delete'),

    # Pass Verifier
    path('verifier/', views.pass_verifier_page, name='pass_verifier'),

    # Duty Chart & Quick Ticket Verifier
    path('admin/duty-chart/', views.duty_chart_view, name='duty_chart'),
    path('admin/quick-verify/', views.quick_verify_ticket_view, name='quick_verify_ticket'),

    # Revenue & Audit & Export
    path('admin/revenue/', views.revenue_report, name='revenue_report'),
    path('admin/audit-logs/', views.admin_audit_logs, name='admin_audit_logs'),
    path('admin/export/bookings/', views.export_bookings_excel, name='export_bookings'),

    # AJAX
    path('api/schedule/<int:schedule_id>/status/', views.api_toggle_schedule_status, name='api_schedule_status'),
]

