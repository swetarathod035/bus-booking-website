from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required(login_url='/accounts/login/')
def role_redirect(request):
    """Redirect user to their role-specific dashboard."""
    return redirect(request.user.get_dashboard_url())


urlpatterns = [
    path('', role_redirect),
]
