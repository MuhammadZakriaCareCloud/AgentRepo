from django.contrib import admin

# Register your models here.

# Training models admin
from .training_models import (
    ConversationTrainingData,
    AgentKnowledgeBase,
    AgentTrainingSession,
    ConversationPattern,
    AgentPerformanceMetrics
)

@admin.register(ConversationTrainingData)
class ConversationTrainingDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_category', 'outcome', 'success_score', 'is_high_quality', 'processed_for_training', 'created_at']
    list_filter = ['conversation_category', 'outcome', 'is_high_quality', 'processed_for_training', 'reviewed_by_human']
    search_fields = ['conversation_summary', 'key_phrases']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ai_conversation', 'call', 'conversation_category', 'outcome', 'success_score')
        }),
        ('Analysis Data', {
            'fields': ('conversation_summary', 'key_phrases', 'user_intents', 'agent_responses', 'conversation_turns')
        }),
        ('Performance Metrics', {
            'fields': ('average_response_time', 'user_satisfaction_score', 'training_weight')
        }),
        ('Learning Insights', {
            'fields': ('what_worked_well', 'areas_for_improvement', 'recommended_responses')
        }),
        ('Quality Control', {
            'fields': ('is_high_quality', 'reviewed_by_human', 'reviewer', 'processed_for_training')
        }),
        ('Metadata', {
            'fields': ('contact_info', 'call_context', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AgentKnowledgeBase)
class AgentKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'knowledge_type', 'category', 'success_rate', 'usage_count', 'is_active', 'created_at']
    list_filter = ['knowledge_type', 'category', 'is_active', 'created_at']
    search_fields = ['title', 'content', 'tags']
    readonly_fields = ['id', 'usage_count', 'success_rate', 'average_user_satisfaction', 'created_at', 'updated_at']
    ordering = ['-success_rate', '-usage_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('knowledge_type', 'category', 'title', 'content', 'context')
        }),
        ('Usage Patterns', {
            'fields': ('trigger_phrases', 'success_contexts', 'tags')
        }),
        ('Performance', {
            'fields': ('usage_count', 'success_rate', 'average_user_satisfaction', 'confidence_score')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(AgentTrainingSession)
class AgentTrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'training_type', 'status', 'conversations_processed', 'knowledge_entries_created', 'created_at']
    list_filter = ['training_type', 'status', 'created_at']
    readonly_fields = ['id', 'conversations_processed', 'knowledge_entries_created', 'knowledge_entries_updated', 'started_at', 'completed_at', 'duration_seconds', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Training Configuration', {
            'fields': ('training_type', 'training_parameters', 'model_version')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at', 'duration_seconds')
        }),
        ('Results', {
            'fields': ('training_metrics', 'performance_improvements', 'conversations_processed', 'knowledge_entries_created', 'knowledge_entries_updated')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'notes')
        }),
    )


@admin.register(ConversationPattern)
class ConversationPatternAdmin(admin.ModelAdmin):
    list_display = ['pattern_name', 'pattern_type', 'success_rate', 'usage_count', 'is_active', 'created_at']
    list_filter = ['pattern_type', 'is_active', 'created_at']
    search_fields = ['pattern_name', 'description']
    readonly_fields = ['id', 'success_rate', 'usage_count', 'average_conversation_length', 'created_at', 'updated_at']
    ordering = ['-success_rate', '-usage_count']


@admin.register(AgentPerformanceMetrics)
class AgentPerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ['period_type', 'period_start', 'ai_provider', 'success_rate', 'total_conversations', 'created_at']
    list_filter = ['period_type', 'ai_provider', 'period_start']
    readonly_fields = ['id', 'created_at']
    ordering = ['-period_start']
    
    fieldsets = (
        ('Time Period', {
            'fields': ('period_type', 'period_start', 'period_end')
        }),
        ('Agent Info', {
            'fields': ('agent_version', 'ai_provider')
        }),
        ('Performance Metrics', {
            'fields': ('total_conversations', 'successful_conversations', 'success_rate', 'average_conversation_length', 'average_response_time', 'user_satisfaction_score')
        }),
        ('Learning Metrics', {
            'fields': ('new_patterns_learned', 'knowledge_base_updates')
        }),
        ('Cost Metrics', {
            'fields': ('total_tokens_used', 'estimated_cost')
        }),
        ('Breakdown', {
            'fields': ('outcomes_breakdown',),
            'classes': ('collapse',)
        }),
    )
