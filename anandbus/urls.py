from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # Main app namespaces
    path('', include('routes.urls', namespace='routes')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('buses/', include('buses.urls', namespace='buses')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('conductor/', include('conductor.urls', namespace='conductor')),
    path('tracking/', include('tracking.urls', namespace='tracking')),
    path('passes/', include('passes.urls', namespace='passes')),
    # passes app merged into bookings — URLs available at /bookings/passes/

    # Redirect /dashboard/ based on role
    path('dashboard/', include('accounts.dashboard_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler403 = 'accounts.views.handler_403'
handler404 = 'accounts.views.handler_404'
handler500 = 'accounts.views.handler_500'
