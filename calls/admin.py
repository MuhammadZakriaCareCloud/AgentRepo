from django.contrib import admin
from .models import Call, CallConversation, CallTemplate, CallQueue

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['contact', 'call_type', 'status', 'duration', 'created_at']
    list_filter = ['call_type', 'status', 'ai_enabled', 'created_at']
    search_fields = ['contact__first_name', 'contact__last_name', 'twilio_call_sid']
    readonly_fields = ['id', 'created_at', 'twilio_call_sid']
    
    fieldsets = (
        ('Call Information', {
            'fields': ('contact', 'call_type', 'status', 'twilio_call_sid')
        }),
        ('Participants', {
            'fields': ('initiated_by', 'from_number', 'to_number')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'ended_at', 'duration')
        }),
        ('AI Integration', {
            'fields': ('ai_enabled', 'ai_conversation_id')
        }),
        ('Recording', {
            'fields': ('recording_url', 'recording_sid')
        }),
        ('Summary', {
            'fields': ('summary', 'notes', 'outcome', 'follow_up_required')
        })
    )

@admin.register(CallTemplate)
class CallTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'created_by', 'usage_count', 'is_active']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(CallQueue)
class CallQueueAdmin(admin.ModelAdmin):
    list_display = ['contact', 'status', 'priority', 'scheduled_time', 'attempt_count']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['contact__first_name', 'contact__last_name']
