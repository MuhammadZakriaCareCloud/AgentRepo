"""
URL configuration for ai_call_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication endpoints
    path('auth/', include('ai_call_system.auth_urls')),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # API Routes
    path('api/v1/crm/', include('crm.urls')),
    path('api/v1/calls/', include('calls.urls')),
    path('api/v1/ai/', include('ai_integration.urls')),
    path('api/v1/scheduling/', include('scheduling.urls')),
    
    # Twilio Webhooks
    path('webhooks/twilio/', include('calls.webhook_urls')),
    
    # Health check
    path('health/', include('ai_call_system.health_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
