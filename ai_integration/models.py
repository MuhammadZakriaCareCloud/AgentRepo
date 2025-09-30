from django.db import models
from django.contrib.auth.models import User
import uuid

class AIProvider(models.Model):
    """
    Configuration for different AI providers
    """
    PROVIDER_TYPES = (
        ('openai', 'OpenAI'),
        ('azure_openai', 'Azure OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google AI'),
        ('custom', 'Custom Provider'),
    )
    
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    api_key = models.CharField(max_length=500)
    api_endpoint = models.URLField(null=True, blank=True)
    
    # Configuration
    default_model = models.CharField(max_length=100)
    available_models = models.JSONField(default=list)
    max_tokens = models.IntegerField(default=4000)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_providers'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.provider_type})"


class AIConversation(models.Model):
    """
    Track AI conversations across different contexts
    """
    CONVERSATION_TYPES = (
        ('call', 'Phone Call'),
        ('chat', 'Chat'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('error', 'Error'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Context
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # AI Configuration
    ai_provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE)
    model_used = models.CharField(max_length=100)
    system_prompt = models.TextField()
    
    # Conversation tracking
    message_count = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    
    # Metadata
    conversation_metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_conversations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact_phone']),
            models.Index(fields=['status']),
            models.Index(fields=['conversation_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.conversation_type} conversation - {self.status}"


class AIMessage(models.Model):
    """
    Individual messages within AI conversations
    """
    ROLE_CHOICES = (
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # AI metadata
    tokens_used = models.IntegerField(default=0)
    model_used = models.CharField(max_length=100, null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Additional context
    function_call = models.JSONField(null=True, blank=True)
    tool_calls = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIPromptTemplate(models.Model):
    """
    Reusable prompt templates for different scenarios
    """
    TEMPLATE_CATEGORIES = (
        ('sales', 'Sales'),
        ('support', 'Customer Support'),
        ('appointment', 'Appointment Booking'),
        ('survey', 'Survey'),
        ('follow_up', 'Follow Up'),
        ('general', 'General'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES)
    description = models.TextField(null=True, blank=True)
    
    # Template content
    system_prompt = models.TextField()
    initial_message = models.TextField(null=True, blank=True)
    
    # Configuration
    ai_parameters = models.JSONField(default=dict, blank=True)  # temperature, max_tokens, etc.
    
    # Variables that can be injected
    template_variables = models.JSONField(default=list, blank=True)
    
    # Usage tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ai_prompt_templates'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class AIAnalytics(models.Model):
    """
    Analytics and performance tracking for AI interactions
    """
    METRIC_TYPES = (
        ('token_usage', 'Token Usage'),
        ('response_time', 'Response Time'),
        ('conversation_length', 'Conversation Length'),
        ('success_rate', 'Success Rate'),
        ('cost', 'Cost'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True)  # For hourly metrics
    
    # Metric details
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    metric_value = models.FloatField()
    
    # Context
    ai_provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, null=True, blank=True)
    model_used = models.CharField(max_length=100, null=True, blank=True)
    conversation_type = models.CharField(max_length=20, null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_analytics'
        ordering = ['-date', '-hour']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['metric_type']),
            models.Index(fields=['ai_provider']),
        ]
        unique_together = ['date', 'hour', 'metric_type', 'ai_provider', 'model_used']
    
    def __str__(self):
        return f"{self.metric_type} - {self.metric_value} ({self.date})"
