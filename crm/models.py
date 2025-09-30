from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import uuid

class Contact(models.Model):
    """
    Contact model for CRM functionality
    """
    CONTACT_TYPES = (
        ('lead', 'Lead'),
        ('customer', 'Customer'),
        ('prospect', 'Prospect'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES, default='lead')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    company = models.CharField(max_length=200, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    # Address fields
    address_line1 = models.CharField(max_length=200, blank=True, null=True)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='US')
    
    # CRM fields
    lead_source = models.CharField(max_length=100, blank=True, null=True)
    assigned_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # AI preferences
    preferred_ai_voice = models.CharField(max_length=50, default='alloy')
    ai_interaction_history = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contacted = models.DateTimeField(null=True, blank=True)
    
    # Call preferences
    best_time_to_call = models.CharField(max_length=100, blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    do_not_call = models.BooleanField(default=False)
    
    # Custom fields (flexible JSON storage)
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'crm_contacts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['contact_type']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_agent']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def full_address(self):
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.zip_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])


class ContactTag(models.Model):
    """
    Tags for categorizing contacts
    """
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'crm_contact_tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ContactTagAssignment(models.Model):
    """
    Many-to-many relationship between contacts and tags
    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='tag_assignments')
    tag = models.ForeignKey(ContactTag, on_delete=models.CASCADE, related_name='contact_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'crm_contact_tag_assignments'
        unique_together = ['contact', 'tag']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.contact.full_name} - {self.tag.name}"


class ContactNote(models.Model):
    """
    Notes associated with contacts
    """
    NOTE_TYPES = (
        ('general', 'General'),
        ('call_summary', 'Call Summary'),
        ('meeting', 'Meeting'),
        ('email', 'Email'),
        ('task', 'Task'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='contact_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For follow-up tasks
    is_task = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'crm_contact_notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contact.full_name} - {self.title}"
