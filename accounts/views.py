from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.views.generic import UpdateView
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy

from .forms import PassengerRegistrationForm, CustomLoginForm, ProfileUpdateForm
from .models import CustomUser
from .decorators import login_required


def register(request):
    """Passenger self-registration."""
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = PassengerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to AnandBus, {user.first_name}! Your account is ready.')
            return redirect('bookings:passenger_dashboard')
    else:
        form = PassengerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'title': 'Create Account'})


def user_login(request):
    """Login all roles — redirects to role-specific dashboard."""
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', user.get_dashboard_url())
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'title': 'Sign In'})


@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('routes:home')


@login_required
def profile_view(request):
    """View/edit own profile."""
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, 'accounts/profile.html', {'form': form, 'title': 'My Profile'})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form, 'title': 'Change Password'})


# ─── Error Handlers ───────────────────────────────────────────────────────────
def handler_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def handler_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def handler_500(request):
    return render(request, 'errors/500.html', status=500)
