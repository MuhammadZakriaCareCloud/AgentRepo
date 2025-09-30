from celery import shared_task
from django.utils import timezone
from calls.models import Call, CallQueue
from calls.services.twilio_service import twilio_service
from ai_integration.services.ai_service import ai_service
from crm.models import Contact
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_outbound_call(self, queue_item_id):
    """
    Process an outbound call from the queue
    """
    try:
        queue_item = CallQueue.objects.get(id=queue_item_id)
        
        # Check if contact allows calls
        if queue_item.contact.do_not_call:
            queue_item.status = 'cancelled'
            queue_item.result_notes = 'Contact is on do-not-call list'
            queue_item.save()
            return {'status': 'cancelled', 'reason': 'do_not_call'}
        
        # Update queue item status
        queue_item.status = 'in_progress'
        queue_item.attempt_count += 1
        queue_item.save()
        
        # Create call record
        call = Call.objects.create(
            call_type='outbound',
            contact=queue_item.contact,
            initiated_by=queue_item.created_by,
            from_number=twilio_service.from_number,
            to_number=queue_item.contact.phone_number,
            ai_enabled=True
        )
        
        # Generate webhook URL for this call
        webhook_url = f"https://yourdomain.com/webhooks/twilio/voice/?call_id={call.id}"
        
        # Initiate the call via Twilio
        result = twilio_service.initiate_call(
            to_number=queue_item.contact.phone_number,
            webhook_url=webhook_url,
            call_data={
                'call_id': str(call.id),
                'template_id': str(queue_item.call_template.id) if queue_item.call_template else None,
                'contact_id': str(queue_item.contact.id)
            }
        )
        
        if result['success']:
            # Update call with Twilio SID
            call.twilio_call_sid = result['call_sid']
            call.status = 'initiated'
            call.started_at = timezone.now()
            call.save()
            
            # Update queue item
            queue_item.call = call
            queue_item.status = 'completed'
            queue_item.result_notes = f"Call initiated successfully: {result['call_sid']}"
            queue_item.save()
            
            logger.info(f"Outbound call initiated: {result['call_sid']} to {queue_item.contact.phone_number}")
            
            return {
                'status': 'success',
                'call_sid': result['call_sid'],
                'call_id': str(call.id)
            }
        else:
            # Handle failure
            call.status = 'failed'
            call.save()
            
            if queue_item.attempt_count < queue_item.max_attempts:
                queue_item.status = 'pending'
                queue_item.result_notes = f"Attempt {queue_item.attempt_count} failed: {result['error']}"
                queue_item.save()
                
                # Retry after delay
                self.retry(countdown=300)  # Retry after 5 minutes
            else:
                queue_item.status = 'failed'
                queue_item.result_notes = f"Max attempts reached. Last error: {result['error']}"
                queue_item.save()
            
            return {
                'status': 'failed',
                'error': result['error']
            }
            
    except Exception as e:
        logger.error(f"Error processing outbound call {queue_item_id}: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60)
        return {'status': 'error', 'error': str(e)}

@shared_task
def bulk_process_call_queue():
    """
    Process pending items in the call queue
    """
    pending_items = CallQueue.objects.filter(
        status='pending',
        scheduled_time__lte=timezone.now()
    ).order_by('priority', 'scheduled_time')[:10]  # Process 10 at a time
    
    results = []
    for item in pending_items:
        result = process_outbound_call.delay(str(item.id))
        results.append({
            'queue_item_id': str(item.id),
            'task_id': result.id
        })
    
    return {
        'processed_items': len(results),
        'results': results
    }

@shared_task
def process_ai_conversation(call_id, user_input, conversation_id=None):
    """
    Process AI conversation for a call
    """
    try:
        call = Call.objects.get(id=call_id)
        
        # Create or get AI conversation
        if conversation_id:
            conversation = ai_service.get_conversation(conversation_id)
        else:
            conversation = ai_service.create_conversation(
                conversation_type='call',
                contact_phone=call.contact.phone_number,
                system_prompt=_get_call_system_prompt(call)
            )
            call.ai_conversation_id = str(conversation.id)
            call.save()
        
        # Generate AI response
        response = ai_service.generate_response(conversation, user_input)
        
        if response['success']:
            # Log the conversation
            from calls.models import CallConversation
            CallConversation.objects.create(
                call=call,
                speaker_type='human',
                message=user_input
            )
            CallConversation.objects.create(
                call=call,
                speaker_type='ai',
                message=response['response'],
                ai_model_used=response.get('model_used'),
                confidence_score=0.95  # Placeholder
            )
            
            return {
                'status': 'success',
                'response': response['response'],
                'conversation_id': str(conversation.id)
            }
        else:
            return {
                'status': 'error',
                'error': response['error']
            }
            
    except Exception as e:
        logger.error(f"Error processing AI conversation for call {call_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@shared_task
def generate_call_summary(call_id):
    """
    Generate summary for completed call
    """
    try:
        call = Call.objects.get(id=call_id)
        
        if call.ai_conversation_id:
            conversation = ai_service.get_conversation(call.ai_conversation_id)
            summary = ai_service.summarize_conversation(conversation)
            
            call.summary = summary
            call.save()
            
            # Update contact's last contacted time
            call.contact.last_contacted = call.ended_at or timezone.now()
            call.contact.save()
            
            return {
                'status': 'success',
                'summary': summary
            }
        else:
            return {
                'status': 'error',
                'error': 'No AI conversation found for call'
            }
            
    except Exception as e:
        logger.error(f"Error generating call summary for call {call_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@shared_task
def cleanup_old_conversations():
    """
    Clean up old AI conversations and call records
    """
    from datetime import timedelta
    from ai_integration.models import AIConversation
    
    # Delete conversations older than 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    
    old_conversations = AIConversation.objects.filter(
        completed_at__lt=cutoff_date,
        status='completed'
    )
    
    deleted_count = old_conversations.count()
    old_conversations.delete()
    
    logger.info(f"Cleaned up {deleted_count} old conversations")
    
    return {
        'status': 'success',
        'deleted_conversations': deleted_count
    }

@shared_task
def sync_call_recordings():
    """
    Sync call recordings from Twilio
    """
    from datetime import timedelta
    
    # Get calls from last 24 hours that might have recordings
    recent_calls = Call.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24),
        status='completed',
        recording_url__isnull=True,
        twilio_call_sid__isnull=False
    )
    
    synced_count = 0
    for call in recent_calls:
        recordings = twilio_service.get_recordings(call.twilio_call_sid)
        if recordings:
            # Use the first recording
            recording = recordings[0]
            call.recording_url = recording['media_url']
            call.recording_sid = recording['sid']
            call.save()
            synced_count += 1
    
    logger.info(f"Synced {synced_count} call recordings")
    
    return {
        'status': 'success',
        'synced_recordings': synced_count
    }

def _get_call_system_prompt(call):
    """
    Generate system prompt for call based on call template or default
    """
    if call.call_template:
        return call.call_template.initial_greeting
    
    return f"""You are a professional AI assistant representing our company. You are speaking with {call.contact.first_name} {call.contact.last_name}.

Key information about this contact:
- Name: {call.contact.full_name}
- Company: {call.contact.company or 'Not provided'}
- Previous interactions: {call.contact.ai_interaction_history}

Guidelines:
1. Be professional and friendly
2. Listen actively to their needs
3. Provide helpful information
4. Keep responses concise for phone conversation
5. Ask clarifying questions when needed
6. End the call appropriately when business is complete

Remember this is a phone call, so keep responses conversational and not too long."""
