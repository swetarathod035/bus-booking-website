from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/clear/', views.clear_notifications, name='clear_notifications'),
]

