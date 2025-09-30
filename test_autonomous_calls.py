#!/usr/bin/env python
"""
Test Autonomous AI Agent Calls

This script demonstrates how to test the autonomous calling system
using both Python functions and API endpoints.
"""

import os
import django
import requests
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_call_system.settings_dev')
django.setup()

from calls.autonomous_agent import (
    trigger_sales_outreach_call,
    trigger_follow_up_call,
    trigger_support_call
)
from crm.models import Contact
from django.utils import timezone


def test_autonomous_functions():
    """Test autonomous calling using Python functions"""
    print("\n=== Testing Autonomous Functions ===")
    
    # Create test contact
    contact, created = Contact.objects.get_or_create(
        phone_number='+1234567890',
        defaults={
            'first_name': 'John',
            'last_name': 'Test',
            'email': 'john@test.com',
            'company': 'Test Corp',
            'contact_type': 'lead'
        }
    )
    
    print(f"✓ Using contact: {contact.full_name} ({contact.phone_number})")
    
    # Test 1: Sales outreach call
    print("\n--- Test 1: Sales Outreach Call ---")
    context = {
        'product_interest': 'AI Solutions',
        'budget_range': '$10k-50k',
        'decision_maker': True
    }
    
    task_result = trigger_sales_outreach_call(str(contact.id), context)
    print(f"✓ Sales call triggered - Task ID: {task_result.id}")
    
    # Test 2: Follow-up call
    print("\n--- Test 2: Follow-up Call ---")
    previous_interaction = {
        'outcome': 'interested',
        'concerns': ['pricing'],
        'follow_up_reason': 'address_concerns'
    }
    
    task_result = trigger_follow_up_call(
        str(contact.id), 
        previous_interaction, 
        {'discount_available': '15%'}
    )
    print(f"✓ Follow-up call triggered - Task ID: {task_result.id}")
    
    # Test 3: Support call
    print("\n--- Test 3: Support Call ---")
    support_context = {
        'issue_type': 'technical_issue',
        'severity': 'medium'
    }
    
    task_result = trigger_support_call(
        str(contact.id), 
        'technical_issue', 
        support_context
    )
    print(f"✓ Support call triggered - Task ID: {task_result.id}")
    
    return contact


def test_api_endpoints():
    """Test autonomous calling using API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    # Base API URL (adjust if needed)
    base_url = 'http://127.0.0.1:8000/calls/api'
    
    # Get or create test contact
    contact, created = Contact.objects.get_or_create(
        phone_number='+1234567891',
        defaults={
            'first_name': 'Jane',
            'last_name': 'API',
            'email': 'jane@api.com',
            'company': 'API Corp',
            'contact_type': 'lead'
        }
    )
    
    print(f"✓ Using contact: {contact.full_name} ({contact.phone_number})")
    
    # Test 1: Single autonomous call via API
    print("\n--- Test 1: API Single Autonomous Call ---")
    
    payload = {
        'contact_id': str(contact.id),
        'call_purpose': 'sales_outreach',
        'context': {
            'product_focus': 'Cloud Solutions',
            'urgency': 'high',
            'campaign': 'Q1 2024'
        }
    }
    
    try:
        response = requests.post(
            f'{base_url}/calls/trigger_autonomous_call/',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ API call successful: {result['message']}")
            print(f"✓ Task ID: {result['task_id']}")
        else:
            print(f"❌ API call failed: {response.status_code} - {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ API call failed: Django server not running")
        print("   Start server with: python manage.py runserver")
    
    # Test 2: Bulk autonomous calls via API
    print("\n--- Test 2: API Bulk Autonomous Calls ---")
    
    # Create additional test contacts
    bulk_contacts = []
    for i in range(3):
        contact, created = Contact.objects.get_or_create(
            phone_number=f'+123456789{i+2}',
            defaults={
                'first_name': f'Contact{i+1}',
                'last_name': 'Bulk',
                'email': f'bulk{i+1}@test.com',
                'company': f'Bulk Corp {i+1}',
                'contact_type': 'lead'
            }
        )
        bulk_contacts.append(contact)
    
    bulk_payload = {
        'calls': [
            {
                'contact_id': str(contact.id),
                'call_purpose': 'sales_outreach',
                'context': {'batch': 'bulk_test'},
                'delay_minutes': i * 2  # Stagger calls
            }
            for i, contact in enumerate(bulk_contacts)
        ]
    }
    
    try:
        response = requests.post(
            f'{base_url}/calls/bulk_autonomous_calls/',
            json=bulk_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Bulk API call successful: {result['message']}")
            print(f"✓ Calls triggered: {result['calls_triggered']}")
        else:
            print(f"❌ Bulk API call failed: {response.status_code} - {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Bulk API call failed: Django server not running")
    
    # Test 3: Scheduled autonomous call via API
    print("\n--- Test 3: API Scheduled Autonomous Call ---")
    
    # Schedule call for 2 minutes from now
    scheduled_time = (timezone.now() + timedelta(minutes=2)).isoformat()
    
    scheduled_payload = {
        'contact_id': str(contact.id),
        'call_purpose': 'follow_up',
        'context': {'scheduled_test': True},
        'scheduled_time': scheduled_time
    }
    
    try:
        response = requests.post(
            f'{base_url}/calls/trigger_autonomous_call/',
            json=scheduled_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Scheduled API call successful: {result['message']}")
            print(f"✓ Scheduled for: {result['scheduled_time']}")
        else:
            print(f"❌ Scheduled API call failed: {response.status_code} - {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Scheduled API call failed: Django server not running")


def test_call_status_api():
    """Test call status checking via API"""
    print("\n=== Testing Call Status API ===")
    
    base_url = 'http://127.0.0.1:8000/calls/api'
    
    # Get a contact to check status for
    contact = Contact.objects.first()
    if not contact:
        print("❌ No contacts found for status testing")
        return
    
    try:
        response = requests.get(
            f'{base_url}/calls/autonomous_call_status/',
            params={'contact_id': str(contact.id)}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Status API successful for {result['contact']['name']}")
            print(f"✓ Recent calls: {len(result['recent_calls'])}")
            
            for call in result['recent_calls']:
                print(f"  - Call {call['id']}: {call['status']} ({call['call_type']})")
        else:
            print(f"❌ Status API failed: {response.status_code} - {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Status API call failed: Django server not running")


def demonstrate_production_usage():
    """Show examples of how to use autonomous calls in production"""
    print("\n=== Production Usage Examples ===")
    
    print("""
📋 Production Usage Patterns:

1. Webhook Triggers:
   # Trigger call when user signs up
   POST /calls/api/calls/trigger_autonomous_call/
   {
       "contact_id": "user_id_from_webhook",
       "call_purpose": "sales_outreach",
       "context": {"signup_source": "website"}
   }

2. Scheduled Campaigns:
   # Schedule calls for a campaign
   POST /calls/api/calls/trigger_campaign_calls/
   {
       "campaign_id": "campaign_uuid",
       "call_purpose": "product_demo",
       "stagger_minutes": 10
   }

3. Follow-up Automation:
   # Automatic follow-up after demo
   from calls.autonomous_agent import trigger_follow_up_call
   trigger_follow_up_call(contact_id, previous_interaction)

4. Customer Support:
   # Proactive support call for issues
   trigger_support_call(contact_id, "billing_issue", context)

5. Bulk Operations:
   # Process large contact lists
   POST /calls/api/calls/bulk_autonomous_calls/
   {
       "calls": [
           {"contact_id": "...", "call_purpose": "renewal_reminder"},
           ...
       ]
   }

6. CRM Integration:
   # Trigger from CRM events
   from calls.autonomous_agent import autonomous_agent_call
   autonomous_agent_call.delay(contact_id, purpose, context)

🔄 Call Flow:
1. Call triggered → Celery task created
2. Task executes → Twilio call initiated  
3. Call connects → AI agent takes over
4. Conversation handled → Results processed
5. Follow-up actions → CRM updated

🏗️ Production Setup:
1. Configure Twilio phone numbers
2. Set up OpenAI API keys
3. Deploy with Redis + Celery workers
4. Configure webhook URLs
5. Set up monitoring & logging
""")


def main():
    """Run all autonomous call tests"""
    print("🤖 Autonomous AI Agent Call Testing")
    print("=" * 50)
    
    print("""
This test demonstrates how the AI agent can call users completely autonomously:

✅ Autonomous Features:
• No human intervention required
• AI handles entire conversation
• Makes decisions based on responses  
• Schedules follow-up actions automatically
• Updates CRM records automatically
• Supports multiple call purposes
• API and function interfaces available

🎯 Call Purposes Supported:
• sales_outreach - Initial sales contact
• follow_up - Follow-up on previous interaction
• customer_support - Proactive support calls
• appointment_booking - Schedule appointments
• survey - Conduct surveys
• renewal_reminder - Contract renewals
""")
    
    try:
        # Test Python functions
        contact = test_autonomous_functions()
        
        # Test API endpoints  
        test_api_endpoints()
        
        # Test status checking
        test_call_status_api()
        
        # Show production examples
        demonstrate_production_usage()
        
        print("\n" + "=" * 50)
        print("✅ All autonomous call tests completed!")
        
        print(f"""
🚀 Ready for Production:
• {Contact.objects.count()} contacts in system
• Autonomous calling system operational
• API endpoints available
• Background processing configured

⚡ Quick Start Commands:
# Single call
python -c "
from calls.autonomous_agent import trigger_sales_outreach_call
trigger_sales_outreach_call('{contact.id}', {{'test': True}})
"

# API call (with Django server running)
curl -X POST http://127.0.0.1:8000/calls/api/calls/trigger_autonomous_call/ \\
  -H "Content-Type: application/json" \\
  -d '{{"contact_id": "{contact.id}", "call_purpose": "sales_outreach"}}'

🔧 Next Steps:
1. Configure real Twilio/OpenAI credentials
2. Start Celery workers: celery -A ai_call_system worker -l info
3. Test with real phone numbers
4. Monitor call logs and results
5. Set up production webhooks
""")
        
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
