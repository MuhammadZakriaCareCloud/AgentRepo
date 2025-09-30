"""
URL configuration for AI Integration Training APIs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .training_views import (
    ConversationTrainingDataViewSet,
    AgentKnowledgeBaseViewSet,
    AgentTrainingSessionViewSet,
    ConversationPatternViewSet,
    AgentPerformanceMetricsViewSet
)

# Create router for training endpoints
training_router = DefaultRouter()
training_router.register(r'training-data', ConversationTrainingDataViewSet, basename='training-data')
training_router.register(r'knowledge-base', AgentKnowledgeBaseViewSet, basename='knowledge-base')
training_router.register(r'training-sessions', AgentTrainingSessionViewSet, basename='training-sessions')
training_router.register(r'conversation-patterns', ConversationPatternViewSet, basename='conversation-patterns')
training_router.register(r'performance-metrics', AgentPerformanceMetricsViewSet, basename='performance-metrics')

urlpatterns = [
    path('training/', include(training_router.urls)),
]
