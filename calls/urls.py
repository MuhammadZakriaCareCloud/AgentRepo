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
    
    # Call management
    path('initiate/', views.InitiateCallView.as_view(), name='initiate-call'),
    path('bulk-call/', views.BulkCallView.as_view(), name='bulk-call'),
    path('<uuid:call_id>/end/', views.EndCallView.as_view(), name='end-call'),
    path('<uuid:call_id>/add-note/', views.AddCallNoteView.as_view(), name='add-call-note'),
    
    # Queue management
    path('queue/process/', views.ProcessQueueView.as_view(), name='process-queue'),
    path('queue/stats/', views.QueueStatsView.as_view(), name='queue-stats'),
    
    # Analytics
    path('analytics/dashboard/', views.CallDashboardView.as_view(), name='call-dashboard'),
    path('analytics/performance/', views.CallPerformanceView.as_view(), name='call-performance'),
]
