from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'providers', views.AIProviderViewSet)
router.register(r'conversations', views.AIConversationViewSet)
router.register(r'messages', views.AIMessageViewSet)
router.register(r'templates', views.AIPromptTemplateViewSet)
router.register(r'analytics', views.AIAnalyticsViewSet)

app_name = 'ai_integration'

urlpatterns = [
    path('', include(router.urls)),
    
    # AI Interaction endpoints
    path('chat/', views.AIChartView.as_view(), name='ai-chat'),
    path('generate-response/', views.GenerateAIResponseView.as_view(), name='generate-response'),
    path('process-call-audio/', views.ProcessCallAudioView.as_view(), name='process-call-audio'),
    
    # Template management
    path('templates/render/', views.RenderTemplateView.as_view(), name='render-template'),
    path('templates/test/', views.TestTemplateView.as_view(), name='test-template'),
    
    # Analytics and monitoring
    path('analytics/dashboard/', views.AIDashboardView.as_view(), name='ai-dashboard'),
    path('analytics/usage/', views.AIUsageView.as_view(), name='ai-usage'),
    path('analytics/performance/', views.AIPerformanceView.as_view(), name='ai-performance'),
    
    # Model management
    path('models/available/', views.AvailableModelsView.as_view(), name='available-models'),
    path('models/test/', views.TestModelView.as_view(), name='test-model'),
]
