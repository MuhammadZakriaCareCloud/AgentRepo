"""
URL configuration for ai_call_system project - Development Version

Simplified URLs for initial development and testing.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_health(request):
    return JsonResponse({'status': 'healthy', 'service': 'AI Call System'})

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Simple health check
    path('health/', api_health, name='health-check'),
    path('api/health/', api_health, name='api-health-check'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
