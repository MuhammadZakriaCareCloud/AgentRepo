from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AIConversation, AIMessage, AIAnalytics


class AIConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI conversations"""
    queryset = AIConversation.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class AIConversationSerializer(serializers.ModelSerializer):
            class Meta:
                model = AIConversation
                fields = '__all__'
        
        return AIConversationSerializer


class AIMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI messages"""
    queryset = AIMessage.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class AIMessageSerializer(serializers.ModelSerializer):
            class Meta:
                model = AIMessage
                fields = '__all__'
        
        return AIMessageSerializer


class AIAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI analytics"""
    queryset = AIAnalytics.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-analysis_date']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class AIAnalyticsSerializer(serializers.ModelSerializer):
            class Meta:
                model = AIAnalytics
                fields = '__all__'
        
        return AIAnalyticsSerializer
