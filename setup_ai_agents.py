#!/usr/bin/env python
"""
AI Agent Call System - Complete Setup Script
Configures the agent with name, templates, and dynamic call scheduling
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_call_system.settings')
django.setup()

from django.contrib.auth.models import User
from calls.models imp        print(f"🤖 AVAILABLE AGENTS:")
        for template in templates:
            agent_name = template.conversation_flow.get('agent_name', 'Unknown')
            call_type = template.conversation_flow.get('call_type', 'outbound')
            print(f"   • {agent_name} - {template.template_type} ({call_type})")Call, CallTemplate, CallQueue
from crm.models import Contact
from scheduling.models import Campaign, CampaignContact
from ai_integration.models import AIProvider, AIPromptTemplate
import uuid

def setup_ai_agent():
    """Setup AI Agent with name and capabilities"""
    
    print("🤖 Setting up AI Agent...")
    
    # Create AI Provider
    ai_provider, created = AIProvider.objects.get_or_create(
        name="Primary AI Agent",
        defaults={
            'provider_type': 'openai',
            'api_key': 'your-openai-key-here',
            'default_model': 'gpt-4',
            'available_models': ['gpt-4', 'gpt-3.5-turbo'],
            'max_tokens': 4000,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created AI Provider: {ai_provider.name}")
    else:
        print(f"✅ Using existing AI Provider: {ai_provider.name}")
    
    return ai_provider

def create_agent_templates():
    """Create call templates for different scenarios"""
    
    print("📋 Creating Agent Call Templates...")
    
    templates = [
        {
            'name': 'Sales Agent - Ali Khan',
            'agent_name': 'Ali Khan',
            'call_type': 'outbound',
            'purpose': 'sales',
            'script': """
Hello, this is Ali Khan from [COMPANY_NAME]. 
I'm calling because we have an exclusive offer for customers like you.
We're offering a 30% discount on our premium services this month.
Would you be interested in hearing more about how this can benefit you?
            """.strip(),
            'ai_instructions': """
You are Ali Khan, a professional sales agent. Be friendly, confident, and persuasive.
- Always introduce yourself clearly
- Listen to customer concerns
- Highlight benefits, not just features
- Handle objections professionally
- Always try to close or get a callback time
- Keep calls under 5 minutes unless customer is very interested
            """.strip()
        },
        {
            'name': 'Support Agent - Sara Ahmed',
            'agent_name': 'Sara Ahmed',
            'call_type': 'inbound',
            'purpose': 'support',
            'script': """
Hello, this is Sara Ahmed from customer support.
Thank you for calling. How can I assist you today?
I'm here to help resolve any issues you might have.
            """.strip(),
            'ai_instructions': """
You are Sara Ahmed, a helpful customer support agent. Be patient, empathetic, and solution-focused.
- Always be polite and professional
- Listen carefully to customer problems
- Ask clarifying questions when needed
- Provide step-by-step solutions
- Escalate complex issues when necessary
- Always confirm customer satisfaction before ending
            """.strip()
        },
        {
            'name': 'Appointment Agent - Hassan Ali',
            'agent_name': 'Hassan Ali',
            'call_type': 'outbound',
            'purpose': 'appointment',
            'script': """
Hello, this is Hassan Ali calling to schedule your appointment.
I have a few time slots available this week.
Would you prefer morning or afternoon appointments?
            """.strip(),
            'ai_instructions': """
You are Hassan Ali, an efficient appointment scheduling agent. Be organized and accommodating.
- Check customer availability
- Offer multiple time options
- Confirm all appointment details
- Send confirmation if needed
- Be flexible with rescheduling
- Keep detailed notes about preferences
            """.strip()
        },
        {
            'name': 'Follow-up Agent - Fatima Sheikh',
            'agent_name': 'Fatima Sheikh',
            'call_type': 'outbound',
            'purpose': 'follow_up',
            'script': """
Hello, this is Fatima Sheikh calling for a follow-up.
I wanted to check how everything is going with your recent purchase/service.
Do you have any questions or need any assistance?
            """.strip(),
            'ai_instructions': """
You are Fatima Sheikh, a caring follow-up agent. Be attentive and supportive.
- Check customer satisfaction
- Address any concerns promptly
- Offer additional help or services
- Build long-term relationships
- Take feedback seriously
- Schedule future follow-ups if needed
            """.strip()
        }
    ]
    
    created_templates = []
    
    for template_data in templates:
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        
        template, created = CallTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={
                'template_type': template_data['purpose'],
                'description': f"AI Agent: {template_data['agent_name']} for {template_data['purpose']} calls",
                'initial_greeting': template_data['script'],
                'conversation_flow': {
                    'agent_name': template_data['agent_name'],
                    'instructions': template_data['ai_instructions'],
                    'call_type': template_data['call_type'],
                    'language': 'en-US',
                    'voice': 'female' if template_data['agent_name'] in ['Sara Ahmed', 'Fatima Sheikh'] else 'male'
                },
                'closing_message': f"Thank you for your time. This is {template_data['agent_name']} signing off. Have a great day!",
                'ai_voice': 'nova' if template_data['agent_name'] in ['Sara Ahmed', 'Fatima Sheikh'] else 'onyx',
                'ai_temperature': 0.7,
                'max_tokens': 500,
                'created_by': admin_user,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created template: {template.name}")
        else:
            print(f"✅ Using existing template: {template.name}")
            
        created_templates.append(template)
    
    return created_templates

def setup_dynamic_scheduler():
    """Setup dynamic call scheduler"""
    
    print("⏰ Setting up Dynamic Call Scheduler...")
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        username='ai_scheduler',
        defaults={
            'email': 'scheduler@aiagent.com',
            'first_name': 'AI',
            'last_name': 'Scheduler',
            'is_staff': True
        }
    )
    
    if created:
        admin_user.set_password('scheduler123')
        admin_user.save()
        print(f"✅ Created scheduler user: {admin_user.username}")
    else:
        print(f"✅ Using existing scheduler user: {admin_user.username}")
    
    # Create dynamic campaigns
    campaigns = [
        {
            'name': 'Dynamic Sales Outreach',
            'campaign_type': 'bulk_calls',
            'status': 'active',
            'description': 'Automatically picks contacts and makes sales calls'
        },
        {
            'name': 'Customer Follow-up Campaign',
            'campaign_type': 'follow_up',
            'status': 'active', 
            'description': 'Follows up with recent customers'
        },
        {
            'name': 'Appointment Reminders',
            'campaign_type': 'appointment_reminders',
            'status': 'active',
            'description': 'Automatically calls for appointment confirmations'
        }
    ]
    
    created_campaigns = []
    
    for campaign_data in campaigns:
        campaign, created = Campaign.objects.get_or_create(
            name=campaign_data['name'],
            defaults={
                'campaign_type': campaign_data['campaign_type'],
                'status': campaign_data['status'],
                'description': campaign_data['description'],
                'start_date': '2025-10-01T09:00:00Z',
                'allowed_calling_hours_start': '09:00:00',
                'allowed_calling_hours_end': '18:00:00',
                'allowed_days_of_week': [1, 2, 3, 4, 5],  # Mon-Fri
                'max_calls_per_hour': 20,
                'max_calls_per_day': 100,
                'created_by': admin_user
            }
        )
        
        if created:
            print(f"✅ Created campaign: {campaign.name}")
        else:
            print(f"✅ Using existing campaign: {campaign.name}")
            
        created_campaigns.append(campaign)
    
    return created_campaigns

def create_sample_contacts():
    """Create sample contacts for testing"""
    
    print("👥 Creating Sample Contacts...")
    
    sample_contacts = [
        {'first_name': 'Ahmed', 'last_name': 'Hassan', 'phone_number': '+923001234567', 'email': 'ahmed@example.com'},
        {'first_name': 'Ayesha', 'last_name': 'Khan', 'phone_number': '+923001234568', 'email': 'ayesha@example.com'},
        {'first_name': 'Muhammad', 'last_name': 'Ali', 'phone_number': '+923001234569', 'email': 'muhammad@example.com'},
        {'first_name': 'Fatima', 'last_name': 'Sheikh', 'phone_number': '+923001234570', 'email': 'fatima@example.com'},
        {'first_name': 'Hassan', 'last_name': 'Ahmad', 'phone_number': '+923001234571', 'email': 'hassan@example.com'},
    ]
    
    created_contacts = []
    
    for contact_data in sample_contacts:
        contact, created = Contact.objects.get_or_create(
            phone_number=contact_data['phone_number'],
            defaults={
                'first_name': contact_data['first_name'],
                'last_name': contact_data['last_name'],
                'email': contact_data['email'],
                'status': 'active',
                'lead_source': 'system_generated',
                'ai_interaction_history': {
                    'preferred_time': 'morning',
                    'language': 'urdu',
                    'timezone': 'Asia/Karachi'
                }
            }
        )
        
        if created:
            print(f"✅ Created contact: {contact.first_name} {contact.last_name}")
        else:
            print(f"✅ Using existing contact: {contact.first_name} {contact.last_name}")
            
        created_contacts.append(contact)
    
    return created_contacts

def setup_call_queue():
    """Setup automatic call queue with dynamic scheduling"""
    
    print("📞 Setting up Call Queue...")
    
    # Get templates and contacts
    templates = CallTemplate.objects.filter(is_active=True)
    contacts = Contact.objects.filter(status='active')[:5]  # First 5 contacts
    
    if not templates.exists():
        print("❌ No templates found! Run create_agent_templates() first")
        return []
    
    if not contacts.exists():
        print("❌ No contacts found! Run create_sample_contacts() first")
        return []
    
    # Create queue entries for different scenarios
    queue_entries = []
    
    for i, contact in enumerate(contacts):
        # Rotate through different agents/templates
        template = templates[i % templates.count()]
        
        # Get admin user for queue creation
        admin_user = User.objects.get(username='admin')
        
        queue_entry, created = CallQueue.objects.get_or_create(
            contact=contact,
            status='pending',
            defaults={
                'call_template': template,
                'priority': 'normal',
                'max_attempts': 3,
                'scheduled_time': '2025-10-01T10:00:00Z',
                'created_by': admin_user,
                'call_config': {
                    'contact_name': f"{contact.first_name} {contact.last_name}",
                    'agent_name': agent_name,
                    'call_purpose': template.template_type,
                    'auto_scheduled': True
                }
            }
        )
        
        if created:
            agent_name = template.conversation_flow.get('agent_name', 'Agent')
            print(f"✅ Queued call: {agent_name} → {contact.first_name} {contact.last_name}")
        else:
            print(f"✅ Call already queued: {contact.first_name} {contact.last_name}")
            
        queue_entries.append(queue_entry)
    
    return queue_entries

def main():
    """Main setup function"""
    
    print("🚀 AI AGENT CALL SYSTEM - COMPLETE SETUP")
    print("=" * 60)
    
    try:
        # Setup components
        ai_provider = setup_ai_agent()
        templates = create_agent_templates()
        campaigns = setup_dynamic_scheduler()
        contacts = create_sample_contacts()
        queue_entries = setup_call_queue()
        
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETE!")
        print("=" * 60)
        
        print(f"✅ AI Provider: {ai_provider.name}")
        print(f"✅ Call Templates: {len(templates)} agents configured")
        print(f"✅ Campaigns: {len(campaigns)} dynamic campaigns")
        print(f"✅ Contacts: {len(contacts)} sample contacts")
        print(f"✅ Queue Entries: {len(queue_entries)} calls ready")
        
        print("\n🤖 AVAILABLE AGENTS:")
        for template in templates:
            agent_name = template.metadata.get('agent_name', 'Unknown')
            print(f"   • {agent_name} - {template.purpose} ({template.call_type})")
        
        print("\n📞 HOW IT WORKS:")
        print("1. Scheduler automatically picks contacts from CRM")
        print("2. Assigns appropriate agent based on call purpose")
        print("3. Queues calls with proper timing")
        print("4. Agent makes calls using their specific template")
        print("5. Handles both inbound and outbound calls")
        print("6. Tracks all interactions and outcomes")
        
        print("\n🎯 TO START CALLING:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Start Celery worker: celery -A ai_call_system worker")
        print("3. Check admin panel: http://127.0.0.1:8000/admin")
        print("4. View call queue: /api/v1/calls/api/call-queue/")
        
        print("\n✨ Your AI agents are ready to make autonomous calls!")
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
