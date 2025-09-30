"""
Autonomous AI Agent Calling System

This module implements fully automated AI agent calls that can:
1. Initiate calls automatically based on triggers
2. Handle entire conversations without human intervention
3. Make decisions and take actions based on conversation outcomes
4. Schedule follow-up calls automatically
5. Update CRM records based on call results
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
import json

from calls.models import Call, CallQueue, CallTemplate
from calls.services.twilio_service import twilio_service
from ai_integration.services.ai_service import ai_service
from crm.models import Contact, ContactNote
from scheduling.models import Campaign, CampaignContact


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def autonomous_agent_call(self, contact_id, call_purpose, context_data=None):
    """
    Initiate a fully autonomous AI agent call
    
    Args:
        contact_id: UUID of the contact to call
        call_purpose: Purpose of the call (sales, support, follow_up, etc.)
        context_data: Additional context for the AI agent
    """
    try:
        contact = Contact.objects.get(id=contact_id)
        
        # Skip if contact is on do-not-call list
        if contact.do_not_call:
            logger.info(f"Skipping call to {contact.full_name} - on do-not-call list")
            return {'status': 'skipped', 'reason': 'do_not_call'}
        
        # Create autonomous call record
        call = Call.objects.create(
            call_type='outbound',
            contact=contact,
            from_number=twilio_service.from_number,
            to_number=contact.phone_number,
            ai_enabled=True,
            status='initiated'
        )
        
        # Build AI agent context
        agent_context = _build_agent_context(contact, call_purpose, context_data)
        
        # Create AI conversation with autonomous agent prompt
        conversation = ai_service.create_conversation(
            conversation_type='call',
            contact_phone=contact.phone_number,
            system_prompt=agent_context['system_prompt']
        )
        
        call.ai_conversation_id = str(conversation.id)
        call.save()
        
        # Generate webhook URL for autonomous handling
        webhook_url = f"https://yourdomain.com/webhooks/twilio/autonomous-agent/?call_id={call.id}&purpose={call_purpose}"
        
        # Initiate the call
        result = twilio_service.initiate_call(
            to_number=contact.phone_number,
            webhook_url=webhook_url,
            call_data={
                'call_id': str(call.id),
                'autonomous': True,
                'purpose': call_purpose,
                'context': agent_context
            }
        )
        
        if result['success']:
            call.twilio_call_sid = result['call_sid']
            call.started_at = timezone.now()
            call.save()
            
            logger.info(f"Autonomous agent call initiated: {result['call_sid']} to {contact.full_name}")
            
            return {
                'status': 'success',
                'call_sid': result['call_sid'],
                'call_id': str(call.id)
            }
        else:
            call.status = 'failed'
            call.save()
            
            # Retry logic
            if self.request.retries < self.max_retries:
                self.retry(countdown=300)  # Retry after 5 minutes
            
            return {'status': 'failed', 'error': result['error']}
            
    except Exception as e:
        logger.error(f"Error in autonomous agent call: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60)
        return {'status': 'error', 'error': str(e)}


def _build_agent_context(contact, call_purpose, context_data=None):
    """Build comprehensive context for the autonomous AI agent"""
    
    # Base agent personality and capabilities
    base_context = {
        'agent_name': 'Alex',
        'company_name': 'TechSolutions',
        'agent_role': 'AI Sales Representative',
        'personality': 'professional, friendly, solution-focused'
    }
    
    # Contact-specific information
    contact_info = {
        'name': contact.full_name,
        'company': contact.company or 'their company',
        'title': contact.job_title or 'their role',
        'previous_interactions': contact.ai_interaction_history,
        'lead_source': contact.lead_source,
        'contact_type': contact.contact_type
    }
    
    # Purpose-specific system prompts
    purpose_prompts = {
        'sales_outreach': _get_sales_outreach_prompt(contact_info, context_data),
        'product_demo': _get_product_demo_prompt(contact_info, context_data),
        'follow_up': _get_follow_up_prompt(contact_info, context_data),
        'customer_support': _get_support_prompt(contact_info, context_data),
        'appointment_booking': _get_appointment_prompt(contact_info, context_data),
        'survey': _get_survey_prompt(contact_info, context_data),
        'renewal_reminder': _get_renewal_prompt(contact_info, context_data)
    }
    
    system_prompt = purpose_prompts.get(call_purpose, purpose_prompts['sales_outreach'])
    
    return {
        'system_prompt': system_prompt,
        'contact_info': contact_info,
        'call_purpose': call_purpose,
        'context_data': context_data or {}
    }


def _get_sales_outreach_prompt(contact_info, context_data):
    """Generate autonomous sales outreach prompt"""
    return f"""You are Alex, an AI sales representative from TechSolutions. You are making an autonomous outbound call to {contact_info['name']} at {contact_info['company']}.

CALL OBJECTIVE: Generate interest in our automation platform and schedule a product demo.

CONTACT CONTEXT:
- Name: {contact_info['name']}
- Company: {contact_info['company']}
- Title: {contact_info['title']}
- Lead Source: {contact_info['lead_source']}
- Contact Type: {contact_info['contact_type']}

CONVERSATION FLOW:
1. OPENING: Introduce yourself professionally and state purpose
2. QUALIFICATION: Ask about current challenges with manual processes
3. VALUE PROPOSITION: Explain how our platform saves time and increases efficiency
4. DEMO SCHEDULING: Propose specific times for a 15-minute demo
5. OBJECTION HANDLING: Address concerns professionally
6. CLOSING: Confirm next steps or politely end call

AUTONOMOUS DECISION MAKING:
- If they're interested: Schedule demo and create follow-up task
- If they're busy: Offer to call back at a better time
- If not interested: Thank them and mark as "not interested"
- If voicemail: Leave professional message and schedule callback

CONVERSATION STYLE:
- Keep responses under 30 seconds
- Be conversational, not scripted
- Listen actively and respond to their specific needs
- End call naturally when objective is met or clearly not interested

IMPORTANT: You are fully autonomous. Make decisions and take actions without requiring human approval."""


def _get_product_demo_prompt(contact_info, context_data):
    """Generate autonomous product demo prompt"""
    return f"""You are Alex from TechSolutions conducting an autonomous product demo call with {contact_info['name']}.

CALL OBJECTIVE: Conduct a compelling product demonstration and move toward closing the sale.

DEMO STRUCTURE:
1. AGENDA SETTING: Confirm their specific interests and time availability
2. DISCOVERY: Understand their current workflow and pain points
3. DEMONSTRATION: Show relevant features that solve their problems
4. BENEFITS FOCUS: Emphasize ROI and efficiency gains
5. TRIAL OFFER: Propose a free trial period
6. CLOSING: Ask for commitment or next steps

AUTONOMOUS ACTIONS:
- Adapt demo based on their responses
- Skip irrelevant features
- Focus on features that address their specific needs
- Make trial offers when appropriate
- Schedule implementation calls if they're ready to proceed

Keep the demo engaging and interactive. Ask questions throughout."""


def _get_follow_up_prompt(contact_info, context_data):
    """Generate autonomous follow-up prompt"""
    previous_interaction = context_data.get('previous_interaction', 'previous conversation')
    
    return f"""You are Alex from TechSolutions following up with {contact_info['name']} after {previous_interaction}.

CALL OBJECTIVE: Continue the sales process and move to the next stage.

FOLLOW-UP CONTEXT:
- Previous interaction: {previous_interaction}
- Follow-up reason: {context_data.get('follow_up_reason', 'general follow-up')}
- Next steps needed: {context_data.get('next_steps', 'determine next steps')}

CONVERSATION APPROACH:
1. REFERENCE PREVIOUS: Mention our last conversation
2. CHECK STATUS: Ask about any developments since we last spoke
3. ADDRESS CONCERNS: Handle any questions or objections that have arisen
4. ADVANCE SALE: Move to next appropriate step in sales process
5. CONFIRM NEXT STEPS: Set clear expectations for follow-up

AUTONOMOUS DECISIONS:
- If ready to proceed: Schedule next meeting or send proposal
- If still considering: Provide additional information and set follow-up
- If no longer interested: Update status and end professionally"""


def _get_support_prompt(contact_info, context_data):
    """Generate autonomous customer support prompt"""
    return f"""You are Alex from TechSolutions customer support calling {contact_info['name']} proactively.

CALL OBJECTIVE: Provide excellent customer service and resolve any issues.

SUPPORT CONTEXT:
- Issue type: {context_data.get('issue_type', 'general check-in')}
- Account status: {context_data.get('account_status', 'active')}
- Previous tickets: {context_data.get('previous_tickets', 'none recent')}

SUPPORT FLOW:
1. GREETING: Professional introduction and call purpose
2. ISSUE IDENTIFICATION: Understand their current challenges
3. TROUBLESHOOTING: Provide step-by-step solutions
4. ESCALATION: If needed, connect to human specialist
5. FOLLOW-UP: Schedule check-in if issue is complex
6. SATISFACTION: Confirm resolution and satisfaction

AUTONOMOUS CAPABILITIES:
- Provide common solutions immediately
- Access knowledge base information
- Schedule technical callbacks when needed
- Create support tickets automatically
- Escalate complex issues to human agents"""


@shared_task
def schedule_autonomous_campaign_calls(campaign_id):
    """
    Schedule autonomous calls for an entire campaign
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        # Get all pending contacts in the campaign
        pending_contacts = CampaignContact.objects.filter(
            campaign=campaign,
            status='pending'
        ).select_related('contact')
        
        scheduled_count = 0
        
        for campaign_contact in pending_contacts:
            # Check if contact allows calls
            if campaign_contact.contact.do_not_call:
                campaign_contact.status = 'skipped'
                campaign_contact.result_notes = 'On do-not-call list'
                campaign_contact.save()
                continue
            
            # Schedule autonomous call
            call_time = _calculate_optimal_call_time(
                campaign_contact.contact,
                campaign.allowed_calling_hours_start,
                campaign.allowed_calling_hours_end,
                campaign.allowed_days_of_week
            )
            
            # Determine call purpose based on campaign type
            call_purpose = _get_call_purpose_from_campaign(campaign)
            
            # Schedule the autonomous call
            autonomous_agent_call.apply_async(
                args=[
                    str(campaign_contact.contact.id),
                    call_purpose,
                    {
                        'campaign_id': str(campaign.id),
                        'campaign_name': campaign.name,
                        'campaign_type': campaign.campaign_type
                    }
                ],
                eta=call_time
            )
            
            # Update campaign contact
            campaign_contact.status = 'scheduled'
            campaign_contact.scheduled_time = call_time
            campaign_contact.save()
            
            scheduled_count += 1
        
        logger.info(f"Scheduled {scheduled_count} autonomous calls for campaign: {campaign.name}")
        
        return {
            'status': 'success',
            'scheduled_calls': scheduled_count,
            'campaign_name': campaign.name
        }
        
    except Exception as e:
        logger.error(f"Error scheduling autonomous campaign calls: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def _calculate_optimal_call_time(contact, start_hour, end_hour, allowed_days):
    """Calculate optimal time to call based on contact preferences and campaign rules"""
    from datetime import datetime, time
    import random
    
    # Start with current time
    call_time = timezone.now()
    
    # If contact has preferred calling time, try to honor it
    if contact.best_time_to_call:
        # Parse preferred time (implementation depends on format)
        # For now, use campaign defaults
        pass
    
    # Ensure call is within allowed hours
    if call_time.hour < start_hour.hour:
        call_time = call_time.replace(hour=start_hour.hour, minute=0)
    elif call_time.hour >= end_hour.hour:
        # Schedule for next allowed day
        call_time = call_time.replace(hour=start_hour.hour, minute=0) + timedelta(days=1)
    
    # Ensure call is on allowed day of week
    while call_time.weekday() + 1 not in allowed_days:  # weekday() returns 0-6, we need 1-7
        call_time += timedelta(days=1)
        call_time = call_time.replace(hour=start_hour.hour, minute=0)
    
    # Add some randomization to spread calls throughout the day
    random_minutes = random.randint(0, (end_hour.hour - start_hour.hour) * 60)
    call_time += timedelta(minutes=random_minutes)
    
    return call_time


def _get_call_purpose_from_campaign(campaign):
    """Determine call purpose based on campaign type"""
    purpose_mapping = {
        'bulk_calls': 'sales_outreach',
        'drip_campaign': 'follow_up',
        'appointment_reminders': 'appointment_booking',
        'follow_up': 'follow_up',
        'survey': 'survey'
    }
    
    return purpose_mapping.get(campaign.campaign_type, 'sales_outreach')


@shared_task
def process_autonomous_call_result(call_id, conversation_outcome):
    """
    Process the results of an autonomous call and take appropriate actions
    """
    try:
        call = Call.objects.get(id=call_id)
        
        # Analyze conversation outcome
        outcome_data = _analyze_call_outcome(conversation_outcome)
        
        # Update call record
        call.outcome = outcome_data['primary_outcome']
        call.summary = outcome_data['summary']
        call.follow_up_required = outcome_data['follow_up_needed']
        call.save()
        
        # Create contact note
        ContactNote.objects.create(
            contact=call.contact,
            title=f"Autonomous Call - {outcome_data['primary_outcome']}",
            content=outcome_data['detailed_summary'],
            note_type='call_summary',
            created_by_id=1  # System user
        )
        
        # Take autonomous actions based on outcome
        _take_autonomous_actions(call, outcome_data)
        
        # Update contact interaction history
        _update_contact_interaction_history(call.contact, outcome_data)
        
        logger.info(f"Processed autonomous call result for {call.contact.full_name}: {outcome_data['primary_outcome']}")
        
        return {
            'status': 'success',
            'outcome': outcome_data['primary_outcome'],
            'actions_taken': outcome_data.get('actions_taken', [])
        }
        
    except Exception as e:
        logger.error(f"Error processing autonomous call result: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def _analyze_call_outcome(conversation_outcome):
    """Analyze conversation outcome and determine next steps"""
    
    # Use AI to analyze the conversation
    analysis_prompt = f"""
    Analyze this call conversation outcome and provide structured analysis:
    
    Conversation: {conversation_outcome}
    
    Provide analysis in JSON format:
    {{
        "primary_outcome": "interested|not_interested|callback_requested|demo_scheduled|voicemail|no_answer",
        "interest_level": "high|medium|low|none",
        "follow_up_needed": true/false,
        "follow_up_timeframe": "immediate|1_day|1_week|1_month",
        "key_concerns": ["concern1", "concern2"],
        "next_best_action": "schedule_demo|send_info|callback|no_action",
        "summary": "brief summary",
        "detailed_summary": "detailed summary for CRM"
    }}
    """
    
    # This would use the AI service to analyze the conversation
    # For now, returning a sample structure
    return {
        'primary_outcome': 'interested',
        'interest_level': 'medium',
        'follow_up_needed': True,
        'follow_up_timeframe': '1_week',
        'key_concerns': ['pricing', 'implementation_time'],
        'next_best_action': 'send_info',
        'summary': 'Contact showed interest but has pricing concerns',
        'detailed_summary': 'Had a positive conversation. Contact is interested in our solution but needs to understand pricing better. They mentioned current budget constraints but may have flexibility in Q2. Requested detailed pricing information.',
        'actions_taken': []
    }


def _take_autonomous_actions(call, outcome_data):
    """Take autonomous actions based on call outcome"""
    
    actions_taken = []
    
    if outcome_data['next_best_action'] == 'schedule_demo':
        # Schedule a demo call
        demo_time = timezone.now() + timedelta(days=3)  # Schedule for 3 days later
        
        CallQueue.objects.create(
            contact=call.contact,
            call_template=CallTemplate.objects.filter(template_type='sales').first(),
            priority='high',
            scheduled_time=demo_time,
            created_by_id=1,  # System user
            call_config={'call_purpose': 'product_demo'}
        )
        
        actions_taken.append('Demo call scheduled')
    
    elif outcome_data['next_best_action'] == 'callback':
        # Schedule callback
        callback_days = {'immediate': 0, '1_day': 1, '1_week': 7, '1_month': 30}
        callback_time = timezone.now() + timedelta(days=callback_days.get(outcome_data['follow_up_timeframe'], 7))
        
        CallQueue.objects.create(
            contact=call.contact,
            call_template=CallTemplate.objects.filter(template_type='follow_up').first(),
            priority='normal',
            scheduled_time=callback_time,
            created_by_id=1,
            call_config={'call_purpose': 'follow_up', 'previous_outcome': outcome_data['primary_outcome']}
        )
        
        actions_taken.append('Follow-up call scheduled')
    
    elif outcome_data['next_best_action'] == 'send_info':
        # In a real implementation, this would trigger email sending
        actions_taken.append('Information packet queued for sending')
    
    # Update outcome data with actions taken
    outcome_data['actions_taken'] = actions_taken


def _update_contact_interaction_history(contact, outcome_data):
    """Update contact's AI interaction history"""
    
    if not contact.ai_interaction_history:
        contact.ai_interaction_history = {}
    
    # Add this interaction to history
    interaction_record = {
        'date': timezone.now().isoformat(),
        'type': 'autonomous_call',
        'outcome': outcome_data['primary_outcome'],
        'interest_level': outcome_data['interest_level'],
        'concerns': outcome_data.get('key_concerns', []),
        'next_action': outcome_data['next_best_action']
    }
    
    # Keep last 10 interactions
    if 'interactions' not in contact.ai_interaction_history:
        contact.ai_interaction_history['interactions'] = []
    
    contact.ai_interaction_history['interactions'].append(interaction_record)
    contact.ai_interaction_history['interactions'] = contact.ai_interaction_history['interactions'][-10:]
    
    # Update last contacted
    contact.last_contacted = timezone.now()
    contact.save()


# Convenience functions for triggering autonomous calls

def trigger_sales_outreach_call(contact_id, context=None):
    """Trigger an autonomous sales outreach call"""
    return autonomous_agent_call.delay(contact_id, 'sales_outreach', context)


def trigger_follow_up_call(contact_id, previous_interaction, context=None):
    """Trigger an autonomous follow-up call"""
    context = context or {}
    context['previous_interaction'] = previous_interaction
    return autonomous_agent_call.delay(contact_id, 'follow_up', context)


def trigger_support_call(contact_id, issue_type, context=None):
    """Trigger an autonomous customer support call"""
    context = context or {}
    context['issue_type'] = issue_type
    return autonomous_agent_call.delay(contact_id, 'customer_support', context)
