from rest_framework import serializers
from .models import AIProvider, AIConversation, AIMessage, AIPromptTemplate, AIAnalytics
from .training_models import (
    ConversationTrainingData,
    AgentKnowledgeBase,
    AgentTrainingSession,
    ConversationPattern,
    AgentPerformanceMetrics
)


class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = '__all__'


class AIConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversation
        fields = '__all__'


class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = '__all__'


class AIPromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPromptTemplate
        fields = '__all__'


class AIAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnalytics
        fields = '__all__'

class ConversationTrainingDataSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation training data
    """
    ai_conversation_id = serializers.UUIDField(source='ai_conversation.id', read_only=True)
    call_id = serializers.UUIDField(source='call.id', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    
    class Meta:
        model = ConversationTrainingData
        fields = [
            'id', 'ai_conversation_id', 'call_id', 'conversation_category',
            'outcome', 'success_score', 'conversation_summary', 'key_phrases',
            'user_intents', 'agent_responses', 'conversation_turns',
            'average_response_time', 'user_satisfaction_score',
            'what_worked_well', 'areas_for_improvement', 'recommended_responses',
            'created_at', 'updated_at', 'processed_for_training',
            'training_weight', 'is_high_quality', 'reviewed_by_human',
            'reviewer_name'
        ]
        read_only_fields = [
            'id', 'ai_conversation_id', 'call_id', 'created_at', 'updated_at',
            'reviewer_name'
        ]


class AgentKnowledgeBaseSerializer(serializers.ModelSerializer):
    """
    Serializer for agent knowledge base entries
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    derived_conversations_count = serializers.IntegerField(
        source='derived_from_conversations.count', read_only=True
    )
    
    class Meta:
        model = AgentKnowledgeBase
        fields = [
            'id', 'knowledge_type', 'category', 'tags', 'title', 'content',
            'context', 'trigger_phrases', 'success_contexts', 'usage_count',
            'success_rate', 'average_user_satisfaction', 'created_at',
            'updated_at', 'created_by_name', 'is_active', 'confidence_score',
            'derived_conversations_count'
        ]
        read_only_fields = [
            'id', 'usage_count', 'success_rate', 'average_user_satisfaction',
            'created_at', 'updated_at', 'created_by_name', 'derived_conversations_count'
        ]


class AgentTrainingSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for agent training sessions
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    training_data_count = serializers.IntegerField(
        source='training_data_used.count', read_only=True
    )
    
    class Meta:
        model = AgentTrainingSession
        fields = [
            'id', 'training_type', 'training_parameters', 'model_version',
            'status', 'training_metrics', 'performance_improvements',
            'conversations_processed', 'knowledge_entries_created',
            'knowledge_entries_updated', 'started_at', 'completed_at',
            'duration_seconds', 'created_by_name', 'created_at', 'notes',
            'training_data_count'
        ]
        read_only_fields = [
            'id', 'status', 'training_metrics', 'performance_improvements',
            'conversations_processed', 'knowledge_entries_created',
            'knowledge_entries_updated', 'started_at', 'completed_at',
            'duration_seconds', 'created_by_name', 'created_at', 'training_data_count'
        ]


class ConversationPatternSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation patterns
    """
    source_conversations_count = serializers.IntegerField(
        source='source_conversations.count', read_only=True
    )
    
    class Meta:
        model = ConversationPattern
        fields = [
            'id', 'pattern_type', 'pattern_name', 'description',
            'trigger_conditions', 'conversation_flow', 'expected_responses',
            'success_rate', 'usage_count', 'average_conversation_length',
            'created_at', 'updated_at', 'is_active', 'source_conversations_count'
        ]
        read_only_fields = [
            'id', 'success_rate', 'usage_count', 'average_conversation_length',
            'created_at', 'updated_at', 'source_conversations_count'
        ]


class AgentPerformanceMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for agent performance metrics
    """
    ai_provider_name = serializers.CharField(source='ai_provider.name', read_only=True)
    
    class Meta:
        model = AgentPerformanceMetrics
        fields = [
            'id', 'period_type', 'period_start', 'period_end', 'agent_version',
            'ai_provider_name', 'total_conversations', 'successful_conversations',
            'success_rate', 'average_conversation_length', 'average_response_time',
            'user_satisfaction_score', 'outcomes_breakdown', 'new_patterns_learned',
            'knowledge_base_updates', 'total_tokens_used', 'estimated_cost',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'ai_provider_name']