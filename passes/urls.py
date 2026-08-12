from django.urls import path
from . import views

app_name = 'passes'

urlpatterns = [
    path('student/', views.student_pass_view, name='student_pass'),
    path('passenger/', views.passenger_pass_view, name='passenger_pass'),
    path('schemes/', views.special_schemes_view, name='special_schemes'),
    path('my-passes/', views.my_passes_view, name='my_passes'),
    path('admin/manage/', views.admin_manage_passes_view, name='admin_manage_passes'),
    path('admin/add-scheme/', views.admin_add_scheme_view, name='admin_add_scheme'),
]
