"""
RBAC decorators and mixins for AnandBus.
Enforces role-based access control across all views.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages


def role_required(*roles):
    """
    Decorator that requires the user to have one of the specified roles.
    Unauthenticated users → login page.
    Wrong role → 403 Forbidden.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='/accounts/login/')
        def wrapper(request, *args, **kwargs):
            user = request.user
            user_role = getattr(user, 'role', None)
            # Superusers bypass all role checks
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            if user_role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator


def superadmin_required(view_func):
    """Only SUPER_ADMIN or superuser may access."""
    @wraps(view_func)
    @login_required(login_url='/accounts/login/')
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser or request.user.role == 'SUPER_ADMIN':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def conductor_required(view_func):
    """Only CONDUCTOR or SUPER_ADMIN may access."""
    @wraps(view_func)
    @login_required(login_url='/accounts/login/')
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.role in ('SUPER_ADMIN', 'CONDUCTOR'):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def passenger_required(view_func):
    """Only PASSENGER (or admin for testing) may access."""
    @wraps(view_func)
    @login_required(login_url='/accounts/login/')
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.role in ('SUPER_ADMIN', 'PASSENGER'):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


# ─── Class-Based View Mixins ──────────────────────────────────────────────────
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class SuperAdminMixin(LoginRequiredMixin):
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.role == 'SUPER_ADMIN'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ConductorMixin(LoginRequiredMixin):
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if not (user.is_superuser or user.role in ('SUPER_ADMIN', 'CONDUCTOR')):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PassengerMixin(LoginRequiredMixin):
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if not (user.is_superuser or user.role in ('SUPER_ADMIN', 'PASSENGER')):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
