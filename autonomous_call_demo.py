#!/usr/bin/env python
"""
Autonomous AI Agent Call Demo

This script demonstrates how to trigger fully autonomous AI agent calls
that handle entire conversations without human intervention.

The AI agent can:
1. Make outbound calls automatically
2. Handle conversations based on predefined objectives
3. Make decisions during the call
4. Schedule follow-up actions
5. Update CRM records automatically
"""

import os
import django
import sys
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_call_system.settings_dev')
django.setup()

from calls.autonomous_agent import (
    autonomous_agent_call,
    trigger_sales_outreach_call,
    trigger_follow_up_call,
    trigger_support_call,
    process_autonomous_call_result
)
from crm.models import Contact
from calls.models import Call, CallQueue, CallTemplate
from scheduling.models import Campaign, CampaignContact
from django.utils import timezone


def demo_single_autonomous_call():
    """Demonstrate a single autonomous AI agent call"""
    print("\n=== Single Autonomous AI Agent Call Demo ===")
    
    # Get or create a test contact
    contact, created = Contact.objects.get_or_create(
        phone_number='+1234567890',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'company': 'Tech Innovations Inc',
            'job_title': 'IT Director',
            'contact_type': 'lead',
            'lead_source': 'website'
        }
    )
    
    if created:
        print(f"✓ Created test contact: {contact.full_name}")
    else:
        print(f"✓ Using existing contact: {contact.full_name}")
    
    # Trigger autonomous sales outreach call
    print("\n--- Triggering Autonomous Sales Call ---")
    
    # Context data for the AI agent
    call_context = {
        'product_interest': 'Cloud Infrastructure Solutions',
        'budget_range': '$10k-50k',
        'timeline': 'Q2 2024',
        'pain_points': ['scalability', 'security', 'cost_optimization'],
        'decision_maker': True,
        'previous_vendor': 'AWS'
    }
    
    # Trigger the autonomous call
    task_result = trigger_sales_outreach_call(
        contact_id=str(contact.id),
        context=call_context
    )
    
    print(f"✓ Autonomous call task triggered: {task_result.id}")
    print(f"✓ Call purpose: Sales Outreach")
    print(f"✓ Contact: {contact.full_name} ({contact.phone_number})")
    print(f"✓ Context: {call_context}")
    
    return task_result, contact


def demo_campaign_autonomous_calls():
    """Demonstrate autonomous calls for an entire campaign"""
    print("\n=== Campaign Autonomous Calls Demo ===")
    
    # Create test contacts for campaign
    campaign_contacts = [
        {
            'phone_number': '+1234567891',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'company': 'StartupCorp',
            'job_title': 'CEO',
            'email': 'alice@startupcorp.com'
        },
        {
            'phone_number': '+1234567892',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'company': 'Enterprise Solutions',
            'job_title': 'CTO',
            'email': 'bob@enterprise.com'
        },
        {
            'phone_number': '+1234567893',
            'first_name': 'Carol',
            'last_name': 'Davis',
            'company': 'Growth Industries',
            'job_title': 'VP Technology',
            'email': 'carol@growth.com'
        }
    ]
    
    contacts = []
    for contact_data in campaign_contacts:
        contact, created = Contact.objects.get_or_create(
            phone_number=contact_data['phone_number'],
            defaults={
                **contact_data,
                'contact_type': 'lead',
                'lead_source': 'campaign'
            }
        )
        contacts.append(contact)
        if created:
            print(f"✓ Created campaign contact: {contact.full_name}")
    
    # Create campaign
    campaign, created = Campaign.objects.get_or_create(
        name='Q1 2024 Product Launch Campaign',
        defaults={
            'description': 'Autonomous AI agent outreach for new product launch',
            'campaign_type': 'sales',
            'status': 'active',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by_id': 1
        }
    )
    
    if created:
        print(f"✓ Created campaign: {campaign.name}")
    
    # Schedule autonomous calls for each contact
    print("\n--- Scheduling Autonomous Campaign Calls ---")
    
    call_contexts = [
        {
            'product_focus': 'AI-Powered Analytics',
            'use_case': 'startup_growth',
            'budget_consideration': 'cost_conscious'
        },
        {
            'product_focus': 'Enterprise Security Suite',
            'use_case': 'enterprise_security',
            'budget_consideration': 'budget_flexible'
        },
        {
            'product_focus': 'Scalability Solutions',
            'use_case': 'rapid_scaling',
            'budget_consideration': 'growth_focused'
        }
    ]
    
    for i, contact in enumerate(contacts):
        # Create campaign contact relationship
        CampaignContact.objects.get_or_create(
            campaign=campaign,
            contact=contact,
            defaults={'status': 'pending'}
        )
        
        # Schedule autonomous call with staggered timing
        call_time = timezone.now() + timedelta(minutes=i * 5)  # 5 minutes apart
        
        # Trigger autonomous call
        task_result = autonomous_agent_call.apply_async(
            args=[str(contact.id), 'sales_outreach', call_contexts[i]],
            eta=call_time
        )
        
        print(f"✓ Scheduled autonomous call for {contact.full_name}")
        print(f"  - Scheduled time: {call_time}")
        print(f"  - Task ID: {task_result.id}")
        print(f"  - Context: {call_contexts[i]}")
    
    return campaign, contacts


def demo_follow_up_sequence():
    """Demonstrate autonomous follow-up call sequence"""
    print("\n=== Autonomous Follow-up Sequence Demo ===")
    
    # Get a contact for follow-up
    contact = Contact.objects.filter(
        ai_interaction_history__isnull=False
    ).first()
    
    if not contact:
        # Create a contact with interaction history
        contact = Contact.objects.create(
            first_name='David',
            last_name='Wilson',
            phone_number='+1234567894',
            email='david@techcorp.com',
            company='TechCorp',
            job_title='Director of Operations',
            contact_type='qualified_lead',
            ai_interaction_history={
                'interactions': [
                    {
                        'date': '2024-01-15T10:00:00Z',
                        'type': 'initial_call',
                        'outcome': 'interested',
                        'interest_level': 'medium',
                        'concerns': ['pricing', 'implementation_time'],
                        'next_action': 'send_info'
                    }
                ]
            }
        )
        print(f"✓ Created contact with interaction history: {contact.full_name}")
    
    # Trigger follow-up call sequence
    print("\n--- Triggering Follow-up Call Sequence ---")
    
    follow_up_context = {
        'previous_interaction': {
            'outcome': 'interested_but_concerned',
            'concerns': ['pricing', 'implementation_time'],
            'materials_sent': ['pricing_sheet', 'implementation_guide'],
            'follow_up_reason': 'address_pricing_concerns'
        },
        'new_information': {
            'discount_available': '15% early adopter discount',
            'implementation_support': 'Free 30-day implementation support',
            'case_study': 'Similar company achieved 40% cost savings'
        }
    }
    
    # Trigger immediate follow-up call
    task_result = trigger_follow_up_call(
        contact_id=str(contact.id),
        previous_interaction=follow_up_context['previous_interaction'],
        context=follow_up_context
    )
    
    print(f"✓ Follow-up call triggered for {contact.full_name}")
    print(f"✓ Task ID: {task_result.id}")
    print(f"✓ Follow-up context: {follow_up_context}")
    
    return task_result, contact


def demo_support_autonomous_call():
    """Demonstrate autonomous customer support call"""
    print("\n=== Autonomous Customer Support Call Demo ===")
    
    # Get or create customer contact
    customer, created = Contact.objects.get_or_create(
        phone_number='+1234567895',
        defaults={
            'first_name': 'Emma',
            'last_name': 'Thompson',
            'email': 'emma@customer.com',
            'company': 'Customer Corp',
            'contact_type': 'customer',
            'lead_source': 'existing_customer'
        }
    )
    
    if created:
        print(f"✓ Created customer contact: {customer.full_name}")
    
    # Support call context
    support_context = {
        'issue_type': 'technical_issue',
        'issue_description': 'API integration not working correctly',
        'severity': 'medium',
        'customer_tier': 'premium',
        'previous_tickets': ['TICK-001', 'TICK-002'],
        'escalation_available': True
    }
    
    # Trigger autonomous support call
    task_result = trigger_support_call(
        contact_id=str(customer.id),
        issue_type='technical_issue',
        context=support_context
    )
    
    print(f"✓ Autonomous support call triggered for {customer.full_name}")
    print(f"✓ Task ID: {task_result.id}")
    print(f"✓ Issue type: {support_context['issue_type']}")
    print(f"✓ Support context: {support_context}")
    
    return task_result, customer


def demo_call_result_processing():
    """Demonstrate how autonomous call results are processed"""
    print("\n=== Autonomous Call Result Processing Demo ===")
    
    # Simulate a completed call
    contact = Contact.objects.first()
    call = Call.objects.create(
        call_type='outbound',
        contact=contact,
        from_number='+1234567890',
        to_number=contact.phone_number,
        ai_enabled=True,
        status='completed',
        started_at=timezone.now() - timedelta(minutes=5),
        ended_at=timezone.now()
    )
    
    # Simulate conversation outcome
    conversation_outcome = {
        'conversation_flow': [
            {'speaker': 'agent', 'message': 'Hi, this is Alex from TechSolutions...'},
            {'speaker': 'human', 'message': 'Oh hi, yes I remember requesting information'},
            {'speaker': 'agent', 'message': 'Great! I wanted to follow up on your interest in our cloud solutions...'},
            {'speaker': 'human', 'message': 'Yes, I\'m interested but concerned about the pricing'},
            {'speaker': 'agent', 'message': 'I understand. Let me share some options that might work better for your budget...'},
            {'speaker': 'human', 'message': 'That sounds interesting. Can you send me more details?'},
            {'speaker': 'agent', 'message': 'Absolutely! I\'ll send you a customized proposal. When would be a good time for a demo?'},
            {'speaker': 'human', 'message': 'How about next Tuesday afternoon?'},
            {'speaker': 'agent', 'message': 'Perfect! I\'ll schedule that and send you the details.'}
        ],
        'call_summary': 'Successful call with interested prospect. Pricing concerns addressed, demo scheduled.',
        'outcome': 'positive',
        'next_steps': ['send_proposal', 'schedule_demo']
    }
    
    # Process the autonomous call result
    result = process_autonomous_call_result.delay(
        call_id=str(call.id),
        conversation_outcome=conversation_outcome
    )
    
    print(f"✓ Processing autonomous call result")
    print(f"✓ Call ID: {call.id}")
    print(f"✓ Contact: {contact.full_name}")
    print(f"✓ Processing task ID: {result.id}")
    print(f"✓ Conversation outcome: {conversation_outcome['outcome']}")
    
    return result, call


def demo_bulk_autonomous_calls():
    """Demonstrate bulk autonomous calls with different purposes"""
    print("\n=== Bulk Autonomous Calls Demo ===")
    
    # Define different call scenarios
    call_scenarios = [
        {
            'purpose': 'sales_outreach',
            'contact_type': 'lead',
            'context': {'product_interest': 'Enterprise Suite'},
            'delay_minutes': 0
        },
        {
            'purpose': 'follow_up',
            'contact_type': 'qualified_lead',
            'context': {'follow_up_reason': 'proposal_follow_up'},
            'delay_minutes': 2
        },
        {
            'purpose': 'customer_support',
            'contact_type': 'customer',
            'context': {'issue_type': 'billing_inquiry'},
            'delay_minutes': 4
        },
        {
            'purpose': 'appointment_booking',
            'contact_type': 'prospect',
            'context': {'appointment_type': 'product_demo'},
            'delay_minutes': 6
        }
    ]
    
    print(f"✓ Scheduling {len(call_scenarios)} autonomous calls with different purposes")
    
    triggered_tasks = []
    
    for i, scenario in enumerate(call_scenarios):
        # Get or create contact for this scenario
        contact, created = Contact.objects.get_or_create(
            phone_number=f'+123456780{i}',
            defaults={
                'first_name': f'Contact{i+1}',
                'last_name': 'AutoTest',
                'email': f'contact{i+1}@autotest.com',
                'company': f'Company {i+1}',
                'contact_type': scenario['contact_type']
            }
        )
        
        # Schedule the call with delay
        call_time = timezone.now() + timedelta(minutes=scenario['delay_minutes'])
        
        task_result = autonomous_agent_call.apply_async(
            args=[str(contact.id), scenario['purpose'], scenario['context']],
            eta=call_time
        )
        
        triggered_tasks.append({
            'task_id': task_result.id,
            'contact': contact,
            'purpose': scenario['purpose'],
            'scheduled_time': call_time
        })
        
        print(f"✓ Scheduled {scenario['purpose']} call for {contact.full_name}")
        print(f"  - Task ID: {task_result.id}")
        print(f"  - Scheduled: {call_time}")
        print(f"  - Context: {scenario['context']}")
    
    return triggered_tasks


def main():
    """Run all autonomous call demos"""
    print("🤖 AI Autonomous Agent Call System Demo")
    print("=" * 50)
    
    print("\nThis demo shows how the AI agent can call users completely autonomously:")
    print("✓ No human intervention required")
    print("✓ AI handles entire conversation")
    print("✓ Makes decisions based on responses")
    print("✓ Schedules follow-up actions automatically")
    print("✓ Updates CRM records automatically")
    
    try:
        # Demo 1: Single autonomous call
        demo_single_autonomous_call()
        
        # Demo 2: Campaign autonomous calls
        demo_campaign_autonomous_calls()
        
        # Demo 3: Follow-up sequence
        demo_follow_up_sequence()
        
        # Demo 4: Support call
        demo_support_autonomous_call()
        
        # Demo 5: Call result processing
        demo_call_result_processing()
        
        # Demo 6: Bulk autonomous calls
        demo_bulk_autonomous_calls()
        
        print("\n" + "=" * 50)
        print("✅ All autonomous call demos completed successfully!")
        print("\n🔧 Next Steps for Production:")
        print("1. Configure real Twilio account with phone numbers")
        print("2. Set up OpenAI API keys")
        print("3. Configure webhook URLs in production")
        print("4. Start Celery workers to process calls")
        print("5. Monitor call logs and results")
        
        print("\n📋 How to Trigger Autonomous Calls:")
        print("# Single call:")
        print("from calls.autonomous_agent import trigger_sales_outreach_call")
        print("task = trigger_sales_outreach_call(contact_id, context)")
        print("\n# Campaign calls:")
        print("# Use the Campaign model and schedule calls in bulk")
        print("\n# Programmatic triggers:")
        print("# Integrate with webhooks, cron jobs, or user actions")
        
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
