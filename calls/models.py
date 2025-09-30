from django.db import models
from django.contrib.auth.models import User
from crm.models import Contact
import uuid

class Call(models.Model):
    """
    Main call model for tracking all calls
    """
    CALL_TYPES = (
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    )
    
    CALL_STATUS = (
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('busy', 'Busy'),
        ('no_answer', 'No Answer'),
        ('voicemail', 'Voicemail'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Call identification
    twilio_call_sid = models.CharField(max_length=100, unique=True, null=True, blank=True)
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)
    
    # Participants
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='calls')
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Phone numbers
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    
    # Call details
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')
    duration = models.DurationField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # AI Integration
    ai_enabled = models.BooleanField(default=True)
    ai_conversation_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Recording
    recording_url = models.URLField(null=True, blank=True)
    recording_sid = models.CharField(max_length=100, null=True, blank=True)
    
    # Call metadata
    call_metadata = models.JSONField(default=dict, blank=True)
    
    # Summary and notes
    summary = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Call outcome
    outcome = models.CharField(max_length=100, null=True, blank=True)
    follow_up_required = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'calls'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['twilio_call_sid']),
            models.Index(fields=['contact']),
            models.Index(fields=['call_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.call_type.capitalize()} call to {self.contact.full_name} ({self.status})"


class CallConversation(models.Model):
    """
    AI conversation details for calls
    """
    SPEAKER_TYPES = (
        ('ai', 'AI Assistant'),
        ('human', 'Human'),
        ('system', 'System'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='conversations')
    
    # Message details
    speaker_type = models.CharField(max_length=20, choices=SPEAKER_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # AI metadata
    ai_model_used = models.CharField(max_length=50, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    intent = models.CharField(max_length=100, null=True, blank=True)
    entities = models.JSONField(default=dict, blank=True)
    
    # Audio metadata
    audio_duration = models.FloatField(null=True, blank=True)
    audio_url = models.URLField(null=True, blank=True)
    
    class Meta:
        db_table = 'call_conversations'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.speaker_type} - {self.message[:50]}..."


class CallTemplate(models.Model):
    """
    Templates for AI call scripts
    """
    TEMPLATE_TYPES = (
        ('sales', 'Sales Call'),
        ('support', 'Customer Support'),
        ('survey', 'Survey'),
        ('appointment', 'Appointment Booking'),
        ('follow_up', 'Follow Up'),
        ('custom', 'Custom'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    description = models.TextField(null=True, blank=True)
    
    # AI Script configuration
    initial_greeting = models.TextField()
    conversation_flow = models.JSONField(default=dict)
    closing_message = models.TextField()
    
    # AI parameters
    ai_voice = models.CharField(max_length=50, default='alloy')
    ai_temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=500)
    
    # Usage tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'call_templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class CallQueue(models.Model):
    """
    Queue for managing outbound calls
    """
    QUEUE_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    call_template = models.ForeignKey(CallTemplate, on_delete=models.CASCADE, null=True, blank=True)
    
    # Queue management
    status = models.CharField(max_length=20, choices=QUEUE_STATUS, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    
    # Scheduling
    scheduled_time = models.DateTimeField(null=True, blank=True)
    max_attempts = models.IntegerField(default=3)
    attempt_count = models.IntegerField(default=0)
    
    # Configuration
    call_config = models.JSONField(default=dict, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Result tracking
    call = models.ForeignKey(Call, on_delete=models.SET_NULL, null=True, blank=True)
    result_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'call_queue'
        ordering = ['priority', 'scheduled_time', 'created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['contact']),
        ]
    
    def __str__(self):
        return f"Queue item for {self.contact.full_name} - {self.status}"
