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

from django.contrib.auth.models import User
from calls.models import Call, CallQueue, CallTemplate
from calls.services.twilio_service import twilio_service
from ai_integration.services.ai_service import ai_service
from crm.models import Contact, ContactNote
from scheduling.models import Campaign, CampaignContact


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def autonomous_agent_call(self, contact_phone=None, contact_id=None, call_purpose='sales', context_data=None):
    """
    Initiate a fully autonomous AI agent call with dynamic agent selection
    
    Args:
        contact_phone: Phone number to call (for quick calls)
        contact_id: UUID of the contact to call (for CRM integration)
        call_purpose: Purpose of the call (sales, support, follow_up, appointment)
        context_data: Additional context for the AI agent
    """
    try:
        # Get contact by ID or phone
        if contact_id:
            contact = Contact.objects.get(id=contact_id)
            phone_number = contact.phone_number
        elif contact_phone:
            phone_number = contact_phone
            contact, created = Contact.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'first_name': 'Unknown',
                    'last_name': 'Contact',
                    'status': 'active'
                }
            )
        else:
            raise ValueError("Either contact_id or contact_phone must be provided")
        
        # Skip if contact is on do-not-call list
        if hasattr(contact, 'do_not_call') and contact.do_not_call:
            logger.info(f"Skipping call to {phone_number} - on do-not-call list")
            return {'status': 'skipped', 'reason': 'do_not_call'}
        
        # Select appropriate agent template based on purpose
        agent_template = select_agent_for_purpose(call_purpose)
        if not agent_template:
            logger.error(f"No agent template found for purpose: {call_purpose}")
            return {'status': 'failed', 'error': 'no_agent_template'}
        
        # Get agent name from template
        agent_name = agent_template.conversation_flow.get('agent_name', 'AI Agent')
        logger.info(f"🤖 {agent_name} initiating {call_purpose} call to {phone_number}")
        
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


def select_agent_for_purpose(call_purpose):
    """
    Select the best agent template based on call purpose
    
    Args:
        call_purpose: The purpose of the call
        
    Returns:
        CallTemplate: The best matching agent template
    """
    # Map purposes to template types
    purpose_to_template_type = {
        'sales': 'sales',
        'support': 'support', 
        'appointment': 'appointment',
        'follow_up': 'follow_up',
        'survey': 'survey',
        'reminder': 'appointment'
    }
    
    # Get template type for this purpose
    template_type = purpose_to_template_type.get(call_purpose, 'sales')
    
    # Try to find template by type
    template = CallTemplate.objects.filter(
        template_type=template_type,
        is_active=True
    ).first()
    
    if template:
        return template
    
    # Ultimate fallback - any active template
    return CallTemplate.objects.filter(is_active=True).first()


@shared_task(bind=True)
def dynamic_call_scheduler(self):
    """
    Dynamic call scheduler that automatically picks contacts and schedules calls
    
    This runs periodically and:
    1. Finds contacts that need to be called
    2. Determines the best time to call
    3. Selects appropriate agent
    4. Queues the call
    """
    try:
        logger.info("🔄 Running dynamic call scheduler...")
        
        # Get active campaigns
        active_campaigns = Campaign.objects.filter(status='active')
        
        scheduled_calls = 0
        
        for campaign in active_campaigns:
            # Get contacts for this campaign
            campaign_contacts = get_contacts_for_campaign(campaign)
            
            # Schedule calls based on campaign rules
            for contact in campaign_contacts:
                if should_call_contact(contact, campaign):
                    # Get admin user
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if not admin_user:
                        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
                
                    # Queue the call
                    queue_entry = CallQueue.objects.create(
                        contact=contact,
                        call_template=select_agent_for_purpose(campaign.campaign_type),
                        priority=get_call_priority(contact, campaign),
                        scheduled_time=get_optimal_call_time(contact),
                        max_attempts=3,
                        status='pending',
                        created_by=admin_user,
                        call_config={
                            'campaign_id': str(campaign.id),
                            'contact_name': f"{contact.first_name} {contact.last_name}",
                            'auto_scheduled': True,
                            'scheduler_run': timezone.now().isoformat()
                        }
                    )
                    
                    scheduled_calls += 1
                    logger.info(f"📅 Scheduled call: {contact.first_name} {contact.last_name}")
        
        logger.info(f"✅ Dynamic scheduler completed: {scheduled_calls} calls scheduled")
        return {'scheduled_calls': scheduled_calls}
        
    except Exception as e:
        logger.error(f"❌ Dynamic scheduler failed: {str(e)}")
        raise


def get_contacts_for_campaign(campaign):
    """Get contacts that should be included in this campaign"""
    
    # Get all active contacts
    contacts = Contact.objects.filter(status='active')
    
    # Filter based on campaign type
    if campaign.campaign_type == 'sales':
        # Sales: contacts without recent purchases (using lead source)
        contacts = contacts.filter(
            contact_type='lead'
        )
    elif campaign.campaign_type == 'follow_up':
        # Follow-up: contacts with recent interactions
        week_ago = timezone.now() - timedelta(days=7)
        contacts = contacts.filter(
            created_at__gte=week_ago
        )
    elif campaign.campaign_type == 'appointment_reminders':
        # Appointments: contacts that are customers
        contacts = contacts.filter(
            contact_type='customer'
        )
    
    # Exclude contacts already in this campaign
    existing_campaign_contacts = CampaignContact.objects.filter(
        campaign=campaign
    ).values_list('contact_id', flat=True)
    
    contacts = contacts.exclude(id__in=existing_campaign_contacts)
    
    # Limit based on campaign settings
    max_contacts = getattr(campaign, 'max_contacts_per_day', 50)
    return contacts[:max_contacts]


def should_call_contact(contact, campaign):
    """Determine if we should call this contact now"""
    
    current_time = timezone.now()
    
    # Check calling hours
    if campaign.allowed_calling_hours_start and campaign.allowed_calling_hours_end:
        current_hour = current_time.hour
        start_hour = campaign.allowed_calling_hours_start.hour
        end_hour = campaign.allowed_calling_hours_end.hour
        
        if not (start_hour <= current_hour <= end_hour):
            return False
    
    # Check days of week
    if campaign.allowed_days_of_week:
        current_weekday = current_time.weekday() + 1  # Django uses 1-7
        if current_weekday not in campaign.allowed_days_of_week:
            return False
    
    # Check if contact was called recently
    recent_calls = Call.objects.filter(
        contact=contact,
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    if recent_calls > 0:
        return False  # Don't call same contact twice in a day
    
    # Check campaign rate limits
    today_calls = Call.objects.filter(
        created_at__date=timezone.now().date(),
        call_metadata__campaign_id=str(campaign.id)
    ).count()
    
    if today_calls >= campaign.max_calls_per_day:
        return False
    
    return True


def get_call_priority(contact, campaign):
    """Calculate call priority based on contact and campaign data"""
    
    priority = 'normal'  # Default priority
    
    # Higher priority for VIP contacts
    if hasattr(contact, 'is_vip') and contact.is_vip:
        priority = 'high'
    
    # Higher priority for urgent campaigns
    if campaign.campaign_type == 'appointment_reminders':
        priority = 'urgent'
    
    # Lower priority for general sales
    if campaign.campaign_type == 'bulk_calls':
        priority = 'low'
    
    return priority


def get_optimal_call_time(contact):
    """Determine the best time to call this contact"""
    
    current_time = timezone.now()
    
    # Check contact preferences
    if hasattr(contact, 'ai_interaction_history') and contact.ai_interaction_history:
        preferred_time = contact.ai_interaction_history.get('preferred_time')
        
        if preferred_time == 'morning':
            # Schedule for 9-11 AM
            call_time = current_time.replace(hour=9, minute=0, second=0)
        elif preferred_time == 'afternoon':
            # Schedule for 2-4 PM
            call_time = current_time.replace(hour=14, minute=0, second=0)
        elif preferred_time == 'evening':
            # Schedule for 6-7 PM
            call_time = current_time.replace(hour=18, minute=0, second=0)
        else:
            # Default to 10 AM
            call_time = current_time.replace(hour=10, minute=0, second=0)
    else:
        # Default to 10 AM
        call_time = current_time.replace(hour=10, minute=0, second=0)
    
    # If time has passed today, schedule for tomorrow
    if call_time <= current_time:
        call_time += timedelta(days=1)
    
    return call_time


@shared_task(bind=True)
def process_call_queue(self):
    """
    Process pending calls in the queue
    
    This task:
    1. Finds calls that are ready to be made
    2. Initiates the autonomous agent call
    3. Updates queue status
    """
    try:
        logger.info("📞 Processing call queue...")
        
        # Get pending calls that are ready
        current_time = timezone.now()
        from django.db import models
        
        ready_calls = CallQueue.objects.filter(
            status='pending',
            scheduled_time__lte=current_time,
            attempt_count__lt=models.F('max_attempts')
        ).order_by('priority', 'scheduled_time')
        
        processed_calls = 0
        
        for queue_entry in ready_calls[:10]:  # Process max 10 calls at once
            try:
                # Get agent name from template
                agent_name = 'AI Agent'
                if queue_entry.call_template and queue_entry.call_template.conversation_flow:
                    agent_name = queue_entry.call_template.conversation_flow.get('agent_name', 'AI Agent')
                
                logger.info(f"🤖 {agent_name} making call to {queue_entry.contact.phone_number}")
                
                # Update queue entry
                queue_entry.status = 'in_progress'
                queue_entry.attempt_count += 1
                queue_entry.save()
                
                # Make the call
                result = autonomous_agent_call.delay(
                    contact_id=str(queue_entry.contact.id),
                    call_purpose=queue_entry.call_template.template_type if queue_entry.call_template else 'sales',
                    context_data={
                        'queue_id': str(queue_entry.id),
                        'agent_name': agent_name,
                        'template_id': str(queue_entry.call_template.id) if queue_entry.call_template else None
                    }
                )
                
                # Update with task ID
                queue_entry.call_config['task_id'] = result.id
                queue_entry.save()
                
                processed_calls += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to process queue entry {queue_entry.id}: {str(e)}")
                queue_entry.status = 'failed'
                queue_entry.call_config['error'] = str(e)
                queue_entry.save()
        
        logger.info(f"✅ Call queue processed: {processed_calls} calls initiated")
        return {'processed_calls': processed_calls}
        
    except Exception as e:
        logger.error(f"❌ Call queue processing failed: {str(e)}")
        raise
