from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AIProvider, AIConversation, AIMessage, AIAnalytics


class AIProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI Providers/Agents - Full CRUD Operations"""
    queryset = AIProvider.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class AIProviderSerializer(serializers.ModelSerializer):
            class Meta:
                model = AIProvider
                fields = [
                    'id', 'name', 'provider_type', 'api_key', 'api_endpoint',
                    'default_model', 'available_models', 'max_tokens', 
                    'is_active', 'created_at', 'updated_at'
                ]
                extra_kwargs = {
                    'api_key': {'write_only': True}  # Hide API key in responses
                }
        
        return AIProviderSerializer

    def get_queryset(self):
        """Filter agents based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by provider type
        provider_type = self.request.query_params.get('provider_type')
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


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
