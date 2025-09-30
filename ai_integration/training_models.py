"""
Agent Training and Learning Models

This module contains models for storing and managing agent training data,
conversation learning, and performance analytics.
"""

from django.db import models
from django.contrib.auth.models import User
import uuid
import json


class ConversationTrainingData(models.Model):
    """
    Store conversation data for agent training and learning
    """
    OUTCOME_TYPES = (
        ('successful', 'Successful'),
        ('partially_successful', 'Partially Successful'),
        ('unsuccessful', 'Unsuccessful'),
        ('incomplete', 'Incomplete'),
        ('error', 'Error'),
    )
    
    CONVERSATION_CATEGORIES = (
        ('sales', 'Sales'),
        ('support', 'Customer Support'),
        ('appointment', 'Appointment Booking'),
        ('survey', 'Survey'),
        ('follow_up', 'Follow Up'),
        ('complaint', 'Complaint Handling'),
        ('information', 'Information Request'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to original conversation/call
    ai_conversation = models.ForeignKey(
        'AIConversation', 
        on_delete=models.CASCADE, 
        related_name='training_data'
    )
    call = models.ForeignKey(
        'calls.Call', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='training_data'
    )
    
    # Conversation metadata
    conversation_category = models.CharField(max_length=20, choices=CONVERSATION_CATEGORIES)
    outcome = models.CharField(max_length=20, choices=OUTCOME_TYPES)
    success_score = models.FloatField(default=0.0, help_text="0.0-1.0 success rating")
    
    # Training features extracted from conversation
    conversation_summary = models.TextField()
    key_phrases = models.JSONField(default=list, blank=True)  # Important phrases/keywords
    user_intents = models.JSONField(default=list, blank=True)  # Detected user intents
    agent_responses = models.JSONField(default=list, blank=True)  # Successful agent responses
    
    # Conversation flow analysis
    conversation_turns = models.IntegerField(default=0)
    average_response_time = models.FloatField(null=True, blank=True)  # in seconds
    user_satisfaction_score = models.FloatField(null=True, blank=True)  # if available
    
    # Learning annotations
    what_worked_well = models.TextField(null=True, blank=True)
    areas_for_improvement = models.TextField(null=True, blank=True)
    recommended_responses = models.JSONField(default=list, blank=True)
    
    # Context data
    contact_info = models.JSONField(default=dict, blank=True)  # Anonymized contact data
    call_context = models.JSONField(default=dict, blank=True)  # Call timing, type, etc.
    
    # Training metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_for_training = models.BooleanField(default=False)
    training_weight = models.FloatField(default=1.0)  # Importance weight for training
    
    # Quality flags
    is_high_quality = models.BooleanField(default=False)
    reviewed_by_human = models.BooleanField(default=False)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'conversation_training_data'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation_category']),
            models.Index(fields=['outcome']),
            models.Index(fields=['success_score']),
            models.Index(fields=['processed_for_training']),
            models.Index(fields=['is_high_quality']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"Training data: {self.conversation_category} - {self.outcome}"


class AgentKnowledgeBase(models.Model):
    """
    Structured knowledge base for AI agents built from training data
    """
    KNOWLEDGE_TYPES = (
        ('faq', 'FAQ'),
        ('response_pattern', 'Response Pattern'),
        ('objection_handling', 'Objection Handling'),
        ('conversation_flow', 'Conversation Flow'),
        ('product_info', 'Product Information'),
        ('policy', 'Policy/Procedure'),
        ('script', 'Script Template'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Knowledge classification
    knowledge_type = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES)
    category = models.CharField(max_length=50)  # sales, support, etc.
    tags = models.JSONField(default=list, blank=True)
    
    # Knowledge content
    title = models.CharField(max_length=200)
    content = models.TextField()
    context = models.TextField(null=True, blank=True)  # When to use this knowledge
    
    # Usage patterns learned from training data
    trigger_phrases = models.JSONField(default=list, blank=True)  # Phrases that should trigger this knowledge
    success_contexts = models.JSONField(default=list, blank=True)  # Contexts where this was successful
    
    # Performance metrics
    usage_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    average_user_satisfaction = models.FloatField(null=True, blank=True)
    
    # Source tracking
    derived_from_conversations = models.ManyToManyField(
        ConversationTrainingData, 
        blank=True,
        related_name='knowledge_entries'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Status
    is_active = models.BooleanField(default=True)
    confidence_score = models.FloatField(default=0.5)  # How confident we are in this knowledge
    
    class Meta:
        db_table = 'agent_knowledge_base'
        ordering = ['-success_rate', '-usage_count']
        indexes = [
            models.Index(fields=['knowledge_type']),
            models.Index(fields=['category']),
            models.Index(fields=['success_rate']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.knowledge_type})"


class AgentTrainingSession(models.Model):
    """
    Track agent training sessions and model updates
    """
    TRAINING_TYPES = (
        ('incremental', 'Incremental Learning'),
        ('batch', 'Batch Training'),
        ('fine_tuning', 'Fine Tuning'),
        ('knowledge_update', 'Knowledge Base Update'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Training configuration
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES)
    training_data_used = models.ManyToManyField(ConversationTrainingData, blank=True)
    
    # Parameters
    training_parameters = models.JSONField(default=dict, blank=True)
    model_version = models.CharField(max_length=50, null=True, blank=True)
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    training_metrics = models.JSONField(default=dict, blank=True)  # loss, accuracy, etc.
    performance_improvements = models.JSONField(default=dict, blank=True)
    
    # Training data statistics
    conversations_processed = models.IntegerField(default=0)
    knowledge_entries_created = models.IntegerField(default=0)
    knowledge_entries_updated = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'agent_training_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Training session {self.training_type} - {self.status}"


class ConversationPattern(models.Model):
    """
    Learned patterns from successful conversations
    """
    PATTERN_TYPES = (
        ('opening', 'Opening Pattern'),
        ('objection_handling', 'Objection Handling'),
        ('closing', 'Closing Pattern'),
        ('information_gathering', 'Information Gathering'),
        ('rapport_building', 'Rapport Building'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Pattern identification
    pattern_type = models.CharField(max_length=30, choices=PATTERN_TYPES)
    pattern_name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Pattern structure
    trigger_conditions = models.JSONField(default=dict, blank=True)  # When to use this pattern
    conversation_flow = models.JSONField(default=list, blank=True)  # Step-by-step flow
    expected_responses = models.JSONField(default=list, blank=True)  # Common user responses
    
    # Performance data
    success_rate = models.FloatField(default=0.0)
    usage_count = models.IntegerField(default=0)
    average_conversation_length = models.FloatField(null=True, blank=True)
    
    # Source conversations
    source_conversations = models.ManyToManyField(
        ConversationTrainingData,
        related_name='patterns',
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'conversation_patterns'
        ordering = ['-success_rate', '-usage_count']
    
    def __str__(self):
        return f"{self.pattern_name} ({self.pattern_type})"


class AgentPerformanceMetrics(models.Model):
    """
    Track agent performance over time
    """
    METRIC_PERIODS = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    period_type = models.CharField(max_length=10, choices=METRIC_PERIODS)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Agent identification
    agent_version = models.CharField(max_length=50, null=True, blank=True)
    ai_provider = models.ForeignKey('AIProvider', on_delete=models.CASCADE)
    
    # Performance metrics
    total_conversations = models.IntegerField(default=0)
    successful_conversations = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    
    average_conversation_length = models.FloatField(null=True, blank=True)
    average_response_time = models.FloatField(null=True, blank=True)
    user_satisfaction_score = models.FloatField(null=True, blank=True)
    
    # Conversation outcomes
    outcomes_breakdown = models.JSONField(default=dict, blank=True)
    
    # Learning metrics
    new_patterns_learned = models.IntegerField(default=0)
    knowledge_base_updates = models.IntegerField(default=0)
    
    # Cost metrics
    total_tokens_used = models.IntegerField(default=0)
    estimated_cost = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'agent_performance_metrics'
        ordering = ['-period_start']
        unique_together = ['period_type', 'period_start', 'ai_provider']
    
    def __str__(self):
        return f"Performance {self.period_type} - {self.success_rate:.2%} success"
