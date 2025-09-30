from django.contrib import admin
from .models import Contact, ContactTag, ContactTagAssignment, ContactNote

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'email', 'contact_type', 'status', 'created_at']
    list_filter = ['contact_type', 'status', 'created_at', 'assigned_agent']
    search_fields = ['first_name', 'last_name', 'phone_number', 'email', 'company']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'email')
        }),
        ('Classification', {
            'fields': ('contact_type', 'status', 'assigned_agent')
        }),
        ('Company Information', {
            'fields': ('company', 'job_title')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'zip_code', 'country')
        }),
        ('Preferences', {
            'fields': ('best_time_to_call', 'timezone', 'do_not_call', 'preferred_ai_voice')
        }),
        ('Additional Information', {
            'fields': ('lead_source', 'notes', 'custom_fields')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_contacted'),
            'classes': ('collapse',)
        })
    )

@admin.register(ContactTag)
class ContactTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']

@admin.register(ContactNote)
class ContactNoteAdmin(admin.ModelAdmin):
    list_display = ['contact', 'title', 'note_type', 'created_by', 'created_at']
    list_filter = ['note_type', 'is_task', 'completed', 'created_at']
    search_fields = ['title', 'content', 'contact__first_name', 'contact__last_name']
