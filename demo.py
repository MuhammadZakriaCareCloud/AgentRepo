#!/usr/bin/env python
"""
AI Call System - Demo Script

This script demonstrates the capabilities of the AI Call System by:
1. Creating sample contacts
2. Setting up call templates
3. Showing API usage examples
4. Creating campaigns

Run this after setting up the system to see it in action.
"""

import os
import django
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_call_system.settings_dev')
django.setup()

from django.contrib.auth.models import User
from crm.models import Contact, ContactTag, ContactNote
from calls.models import CallTemplate, CallQueue
from scheduling.models import Campaign
from ai_integration.models import AIProvider, AIPromptTemplate

def create_sample_data():
    """Create sample data for demonstration"""
    
    print("🚀 Creating sample data for AI Call System Demo...")
    
    # 1. Create sample contacts
    print("\n👥 Creating sample contacts...")
    
    contacts_data = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890',
            'email': 'john.doe@example.com',
            'company': 'Tech Innovations Inc',
            'job_title': 'CTO',
            'contact_type': 'lead',
            'lead_source': 'Website'
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '+0987654321',
            'email': 'jane.smith@example.com',
            'company': 'Marketing Solutions LLC',
            'job_title': 'Marketing Director',
            'contact_type': 'customer',
            'lead_source': 'Referral'
        },
        {
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'phone_number': '+1122334455',
            'email': 'bob.johnson@example.com',
            'company': 'StartupCorp',
            'job_title': 'Founder',
            'contact_type': 'prospect',
            'lead_source': 'Cold Outreach'
        }
    ]
    
    contacts = []
    for contact_data in contacts_data:
        contact, created = Contact.objects.get_or_create(
            phone_number=contact_data['phone_number'],
            defaults=contact_data
        )
        if created:
            print(f"   ✓ Created contact: {contact.full_name}")
        contacts.append(contact)
    
    # 2. Create contact tags
    print("\n🏷️  Creating contact tags...")
    
    tags_data = [
        {'name': 'High Priority', 'color': '#ff0000'},
        {'name': 'Tech Industry', 'color': '#0066cc'},
        {'name': 'Decision Maker', 'color': '#00cc66'},
        {'name': 'Warm Lead', 'color': '#ffaa00'},
    ]
    
    tags = []
    for tag_data in tags_data:
        tag, created = ContactTag.objects.get_or_create(
            name=tag_data['name'],
            defaults=tag_data
        )
        if created:
            print(f"   ✓ Created tag: {tag.name}")
        tags.append(tag)
    
    # 3. Create AI provider
    print("\n🤖 Setting up AI provider...")
    
    ai_provider, created = AIProvider.objects.get_or_create(
        name='Default OpenAI',
        defaults={
            'provider_type': 'openai',
            'api_key': 'your-openai-api-key-here',
            'default_model': 'gpt-4',
            'available_models': ['gpt-4', 'gpt-3.5-turbo'],
            'max_tokens': 4000,
            'is_active': True
        }
    )
    if created:
        print("   ✓ Created AI provider configuration")
    
    # 4. Create AI prompt templates
    print("\n📝 Creating AI prompt templates...")
    
    # Get or create admin user
    admin_user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    templates_data = [
        {
            'name': 'Sales Outreach',
            'category': 'sales',
            'description': 'Template for initial sales outreach calls',
            'system_prompt': '''You are a professional sales representative making an outbound call. Your goals are to:
1. Introduce yourself and the company professionally
2. Understand the prospect's current challenges
3. Explain how our solution can help
4. Schedule a follow-up meeting if there's interest
5. Be respectful of their time

Keep responses conversational and under 30 seconds each.''',
            'initial_message': 'Hi {contact.first_name}, this is Sarah from TechSolutions. I hope I\'m not catching you at a bad time. I\'m calling because I noticed your company might benefit from our latest automation platform. Do you have a quick minute to chat?'
        },
        {
            'name': 'Customer Support',
            'category': 'support',
            'description': 'Template for customer support calls',
            'system_prompt': '''You are a helpful customer support representative. Your goals are to:
1. Listen carefully to the customer's issue
2. Provide clear, actionable solutions
3. Escalate to human support when necessary
4. Ensure customer satisfaction
5. Document the interaction properly

Be empathetic and solution-focused.''',
            'initial_message': 'Hello! Thank you for calling customer support. I\'m here to help you with any questions or issues you might have. How can I assist you today?'
        },
        {
            'name': 'Appointment Booking',
            'category': 'appointment',
            'description': 'Template for booking appointments and consultations',
            'system_prompt': '''You are an appointment booking specialist. Your goals are to:
1. Understand what type of service they need
2. Check availability in the calendar system
3. Book appropriate time slots
4. Confirm all details including contact information
5. Send calendar invitations

Be efficient and accurate with scheduling.''',
            'initial_message': 'Hi {contact.first_name}! I\'m calling to help you schedule your consultation. What type of service are you looking to book, and do you have any preferred dates or times?'
        }
    ]
    
    for template_data in templates_data:
        template, created = AIPromptTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={**template_data, 'created_by': admin_user}
        )
        if created:
            print(f"   ✓ Created AI template: {template.name}")
    
    # 5. Create call templates
    print("\n📞 Creating call templates...")
    
    call_templates_data = [
        {
            'name': 'Product Demo Outreach',
            'template_type': 'sales',
            'description': 'Template for reaching out to prospects for product demos',
            'initial_greeting': 'Hi {contact.first_name}, this is Alex from TechSolutions. I hope I\'m catching you at a good time. I\'m calling because I saw that {contact.company} might be interested in our new automation platform. Would you be open to a quick 15-minute demo this week?',
            'conversation_flow': {
                'opening': 'Introduce yourself and company',
                'qualification': 'Ask about current challenges and pain points',
                'value_prop': 'Explain how your solution addresses their needs',
                'scheduling': 'Propose specific times for a demo',
                'objection_handling': 'Address any concerns or objections',
                'closing': 'Confirm next steps or politely end call'
            },
            'closing_message': 'Thank you for your time, {contact.first_name}. I\'ll send you a calendar invitation for our demo. Looking forward to showing you how we can help {contact.company} save time and increase efficiency. Have a great day!'
        },
        {
            'name': 'Customer Check-in',
            'template_type': 'follow_up',
            'description': 'Template for checking in with existing customers',
            'initial_greeting': 'Hi {contact.first_name}, this is Sarah from customer success at TechSolutions. I hope you\'re doing well! I wanted to check in and see how things are going with our platform. Do you have a few minutes to chat?',
            'conversation_flow': {
                'check_in': 'Ask about their experience with the product',
                'satisfaction': 'Gauge satisfaction levels',
                'support_needs': 'Identify any support or training needs',
                'feedback': 'Collect feedback for product improvements',
                'upsell_opportunities': 'Identify expansion opportunities',
                'next_steps': 'Schedule follow-up if needed'
            },
            'closing_message': 'Thanks so much for the feedback, {contact.first_name}. It\'s great to hear that things are going well. I\'ll follow up on those items we discussed. Don\'t hesitate to reach out if you need anything!'
        }
    ]
    
    for template_data in call_templates_data:
        template, created = CallTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={**template_data, 'created_by': admin_user}
        )
        if created:
            print(f"   ✓ Created call template: {template.name}")
    
    # 6. Create a sample campaign
    print("\n🎯 Creating sample campaign...")
    
    from datetime import datetime, timedelta
    
    # Get the sales template
    sales_template = CallTemplate.objects.filter(template_type='sales').first()
    
    campaign, created = Campaign.objects.get_or_create(
        name='Q1 Product Demo Campaign',
        defaults={
            'description': 'Outreach campaign to generate product demo bookings for Q1',
            'campaign_type': 'bulk_calls',
            'call_template': sales_template,
            'start_date': datetime.now() + timedelta(hours=1),
            'end_date': datetime.now() + timedelta(days=30),
            'max_calls_per_hour': 5,
            'max_calls_per_day': 25,
            'allowed_days_of_week': [1, 2, 3, 4, 5],  # Monday to Friday
            'created_by': admin_user,
            'total_contacts': len(contacts)
        }
    )
    
    if created:
        print(f"   ✓ Created campaign: {campaign.name}")
        
        # Add contacts to campaign
        for contact in contacts:
            campaign.target_contacts.add(contact)
        
        print(f"   ✓ Added {len(contacts)} contacts to campaign")
    
    # 7. Create some sample notes
    print("\n📝 Creating sample contact notes...")
    
    notes_data = [
        {
            'contact': contacts[0],
            'title': 'Initial Outreach',
            'content': 'Made first contact. Interested in our automation platform. Mentioned they\'re currently using manual processes that take too much time.',
            'note_type': 'call_summary'
        },
        {
            'contact': contacts[1],
            'title': 'Demo Scheduled',
            'content': 'Great call! Scheduled product demo for next Tuesday at 2 PM. They\'re particularly interested in the reporting features.',
            'note_type': 'call_summary'
        }
    ]
    
    for note_data in notes_data:
        note, created = ContactNote.objects.get_or_create(
            contact=note_data['contact'],
            title=note_data['title'],
            defaults={**note_data, 'created_by': admin_user}
        )
        if created:
            print(f"   ✓ Created note: {note.title} for {note.contact.full_name}")
    
    print("\n✅ Sample data created successfully!")
    return contacts, call_templates_data, campaign

def show_api_examples():
    """Show example API calls"""
    
    print("\n\n🔌 API Usage Examples:")
    print("=" * 50)
    
    print("\n1. List all contacts:")
    print("   GET http://127.0.0.1:8000/api/v1/crm/contacts/")
    
    print("\n2. Create a new contact:")
    print("   POST http://127.0.0.1:8000/api/v1/crm/contacts/")
    print("   Content-Type: application/json")
    print("   {")
    print('     "first_name": "Alice",')
    print('     "last_name": "Wilson",')
    print('     "phone_number": "+1555123456",')
    print('     "email": "alice@example.com",')
    print('     "company": "Innovation Labs",')
    print('     "contact_type": "lead"')
    print("   }")
    
    print("\n3. Initiate an outbound call:")
    print("   POST http://127.0.0.1:8000/api/v1/calls/initiate/")
    print("   {")
    print('     "contact_id": "contact-uuid-here",')
    print('     "template_id": "template-uuid-here",')
    print('     "priority": "high"')
    print("   }")
    
    print("\n4. Get call analytics:")
    print("   GET http://127.0.0.1:8000/api/v1/calls/analytics/dashboard/?days=7")
    
    print("\n5. Create a bulk call campaign:")
    print("   POST http://127.0.0.1:8000/api/v1/scheduling/campaigns/")
    print("   {")
    print('     "name": "Summer Sales Campaign",')
    print('     "campaign_type": "bulk_calls",')
    print('     "start_date": "2024-06-01T09:00:00Z",')
    print('     "call_template": "template-uuid-here",')
    print('     "max_calls_per_hour": 10')
    print("   }")

def show_management_commands():
    """Show available management commands"""
    
    print("\n\n🛠️  Management Commands:")
    print("=" * 50)
    
    print("\n1. Import contacts from CSV:")
    print("   python manage.py import_contacts contacts.csv --skip-duplicates")
    
    print("\n2. Process call queue:")
    print("   python manage.py process_call_queue --limit 50")
    
    print("\n3. Run with full settings (after installing all dependencies):")
    print("   python manage.py runserver --settings=ai_call_system.settings")

def show_next_steps():
    """Show next steps for setup"""
    
    print("\n\n🚀 Next Steps:")
    print("=" * 50)
    
    print("\n1. 🔧 Complete Setup:")
    print("   • Install all dependencies: pip install -r requirements.txt")
    print("   • Set up Redis server for Celery")
    print("   • Configure .env file with your API keys")
    print("   • Set up PostgreSQL for production")
    
    print("\n2. 🔑 Get API Keys:")
    print("   • Twilio Account SID and Auth Token")
    print("   • OpenAI API Key")
    print("   • Configure webhook URLs in Twilio console")
    
    print("\n3. 🔥 Start Background Services:")
    print("   • Celery Worker: celery -A ai_call_system worker --loglevel=info")
    print("   • Celery Beat: celery -A ai_call_system beat --loglevel=info")
    
    print("\n4. 🧪 Test the System:")
    print("   • Access admin panel: http://127.0.0.1:8000/admin/")
    print("   • Test health check: http://127.0.0.1:8000/health/")
    print("   • Import sample contacts using management commands")
    print("   • Create test campaigns and monitor results")
    
    print("\n5. 📈 Monitor and Scale:")
    print("   • Set up logging and monitoring")
    print("   • Configure rate limiting for calls")
    print("   • Implement proper error handling")
    print("   • Set up backup and recovery procedures")

if __name__ == '__main__':
    print("🎉 AI Call System - Demo & Setup Guide")
    print("=" * 60)
    
    try:
        # Create sample data
        contacts, templates, campaign = create_sample_data()
        
        # Show API examples
        show_api_examples()
        
        # Show management commands
        show_management_commands()
        
        # Show next steps
        show_next_steps()
        
        print(f"\n\n✨ Demo completed successfully!")
        print(f"📊 Created: {Contact.objects.count()} contacts, {CallTemplate.objects.count()} call templates")
        print(f"🎯 Created: {Campaign.objects.count()} campaigns")
        print(f"🤖 Created: {AIPromptTemplate.objects.count()} AI templates")
        
        print(f"\n🌐 Django admin available at: http://127.0.0.1:8000/admin/")
        print(f"   Username: admin")
        print(f"   Password: [the password you set during setup]")
        
    except Exception as e:
        print(f"\n❌ Error during demo setup: {str(e)}")
        import traceback
        traceback.print_exc()
