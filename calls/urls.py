from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

# API Router for autonomous calls
api_router = DefaultRouter()
api_router.register(r'calls', api_views.CallViewSet)
api_router.register(r'call-queue', api_views.CallQueueViewSet)

# Regular router for other endpoints
router = DefaultRouter()
router.register(r'conversations', views.CallConversationViewSet)
router.register(r'templates', views.CallTemplateViewSet)

app_name = 'calls'

urlpatterns = [
    # API endpoints for autonomous calls
    path('api/', include(api_router.urls)),
    
    # Regular endpoints
    path('', include(router.urls)),
    
    # CSV Upload endpoints
    path('csv/', include('calls.csv_urls')),
]
