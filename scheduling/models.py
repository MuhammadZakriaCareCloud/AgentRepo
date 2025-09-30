from django.db import models
from django.contrib.auth.models import User
from crm.models import Contact
from calls.models import CallTemplate
import uuid

class Campaign(models.Model):
    """
    Campaign for organizing bulk calls and scheduled activities
    """
    CAMPAIGN_TYPES = (
        ('bulk_calls', 'Bulk Calls'),
        ('drip_campaign', 'Drip Campaign'),
        ('appointment_reminders', 'Appointment Reminders'),
        ('follow_up', 'Follow Up Campaign'),
        ('survey', 'Survey Campaign'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    campaign_type = models.CharField(max_length=30, choices=CAMPAIGN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Campaign configuration
    call_template = models.ForeignKey(CallTemplate, on_delete=models.CASCADE, null=True, blank=True)
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Time constraints
    allowed_calling_hours_start = models.TimeField(default='09:00:00')
    allowed_calling_hours_end = models.TimeField(default='18:00:00')
    allowed_days_of_week = models.JSONField(default=list)  # [1,2,3,4,5] for Mon-Fri
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Rate limiting
    max_calls_per_hour = models.IntegerField(default=10)
    max_calls_per_day = models.IntegerField(default=100)
    
    # Target audience
    target_contacts = models.ManyToManyField(Contact, through='CampaignContact', blank=True)
    
    # Results tracking
    total_contacts = models.IntegerField(default=0)
    completed_calls = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    
    # Metadata
    campaign_metadata = models.JSONField(default=dict, blank=True)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['campaign_type']),
            models.Index(fields=['start_date']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.campaign_type})"


class CampaignContact(models.Model):
    """
    Many-to-many relationship between campaigns and contacts with additional data
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('opted_out', 'Opted Out'),
    )
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling
    scheduled_time = models.DateTimeField(null=True, blank=True)
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Retry logic
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Results
    call_result = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Custom data for this contact in this campaign
    custom_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_contacts'
        unique_together = ['campaign', 'contact']
        ordering = ['scheduled_time', 'created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.campaign.name} - {self.contact.full_name} ({self.status})"


class Schedule(models.Model):
    """
    General scheduling system for various tasks
    """
    SCHEDULE_TYPES = (
        ('one_time', 'One Time'),
        ('recurring', 'Recurring'),
        ('conditional', 'Conditional'),
    )
    
    RECURRENCE_TYPES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Task configuration
    task_name = models.CharField(max_length=100)  # Celery task name
    task_args = models.JSONField(default=list, blank=True)
    task_kwargs = models.JSONField(default=dict, blank=True)
    
    # Scheduling
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Recurrence settings
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_TYPES, null=True, blank=True)
    recurrence_interval = models.IntegerField(default=1)  # Every N days/weeks/months
    recurrence_rule = models.CharField(max_length=500, null=True, blank=True)  # Cron-like rule
    
    # Execution tracking
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    run_count = models.IntegerField(default=0)
    max_runs = models.IntegerField(null=True, blank=True)
    
    # Conditions
    conditions = models.JSONField(default=dict, blank=True)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedules'
        ordering = ['next_run', '-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['next_run']),
            models.Index(fields=['task_name']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.schedule_type}"


class ScheduleExecution(models.Model):
    """
    Track individual executions of scheduled tasks
    """
    EXECUTION_STATUS = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retried', 'Retried'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='executions')
    
    status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='pending')
    
    # Execution details
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Task tracking
    celery_task_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Results
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Retry logic
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'schedule_executions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['schedule', 'status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['celery_task_id']),
        ]
    
    def __str__(self):
        return f"{self.schedule.name} execution - {self.status}"


class CallTimeSlot(models.Model):
    """
    Available time slots for scheduling calls
    """
    SLOT_STATUS = (
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('booked', 'Booked'),
        ('unavailable', 'Unavailable'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time slot details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    
    # Availability
    status = models.CharField(max_length=20, choices=SLOT_STATUS, default='available')
    
    # Assignment
    assigned_agent = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Booking details
    booked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_slots')
    booking_notes = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'call_time_slots'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_agent']),
        ]
    
    def __str__(self):
        return f"Time slot {self.start_time} - {self.end_time} ({self.status})"
