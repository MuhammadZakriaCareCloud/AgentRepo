from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'conversations', views.AIConversationViewSet)
router.register(r'messages', views.AIMessageViewSet)
router.register(r'analytics', views.AIAnalyticsViewSet)

app_name = 'ai_integration'

urlpatterns = [
    path('', include(router.urls)),
]
