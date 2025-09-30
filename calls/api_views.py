from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Call, CallQueue, CallTemplate
from .serializers import CallSerializer, CallQueueSerializer
from .autonomous_agent import (
    autonomous_agent_call,
    trigger_sales_outreach_call,
    trigger_follow_up_call,
    trigger_support_call
)
from crm.models import Contact
from scheduling.models import Campaign, CampaignContact

logger = logging.getLogger(__name__)


class CallViewSet(viewsets.ModelViewSet):
    """ViewSet for managing calls"""
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Call.objects.all()
        
        # Filter by contact
        contact_id = self.request.query_params.get('contact_id')
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by AI enabled
        ai_enabled = self.request.query_params.get('ai_enabled')
        if ai_enabled is not None:
            queryset = queryset.filter(ai_enabled=ai_enabled.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def trigger_autonomous_call(self, request):
        """
        Trigger an autonomous AI agent call
        
        POST /api/calls/trigger_autonomous_call/
        {
            "contact_id": "uuid",
            "call_purpose": "sales_outreach|follow_up|customer_support|appointment_booking",
            "context": {
                "key": "value",
                ...
            },
            "scheduled_time": "2024-01-20T15:30:00Z" (optional)
        }
        """
        try:
            contact_id = request.data.get('contact_id')
            call_purpose = request.data.get('call_purpose', 'sales_outreach')
            context = request.data.get('context', {})
            scheduled_time_str = request.data.get('scheduled_time')
            
            if not contact_id:
                return Response({
                    'success': False,
                    'error': 'contact_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate contact exists
            contact = get_object_or_404(Contact, id=contact_id)
            
            # Validate call purpose
            valid_purposes = ['sales_outreach', 'follow_up', 'customer_support', 'appointment_booking', 'survey', 'renewal_reminder']
            if call_purpose not in valid_purposes:
                return Response({
                    'success': False,
                    'error': f'Invalid call_purpose. Must be one of: {", ".join(valid_purposes)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle scheduled time
            if scheduled_time_str:
                try:
                    from django.utils.dateparse import parse_datetime
                    scheduled_time = parse_datetime(scheduled_time_str)
                    if not scheduled_time:
                        raise ValueError("Invalid datetime format")
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid scheduled_time format. Use ISO format: 2024-01-20T15:30:00Z'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Schedule for future execution
                task_result = autonomous_agent_call.apply_async(
                    args=[contact_id, call_purpose, context],
                    eta=scheduled_time
                )
            else:
                # Execute immediately
                task_result = autonomous_agent_call.delay(contact_id, call_purpose, context)
            
            logger.info(f"Autonomous call triggered for {contact.full_name} - Purpose: {call_purpose}")
            
            return Response({
                'success': True,
                'message': f'Autonomous {call_purpose} call triggered for {contact.full_name}',
                'task_id': task_result.id,
                'contact': {
                    'id': str(contact.id),
                    'name': contact.full_name,
                    'phone': contact.phone_number
                },
                'call_purpose': call_purpose,
                'scheduled_time': scheduled_time_str if scheduled_time_str else 'immediate'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error triggering autonomous call: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def trigger_campaign_calls(self, request):
        """
        Trigger autonomous calls for an entire campaign
        
        POST /api/calls/trigger_campaign_calls/
        {
            "campaign_id": "uuid",
            "call_purpose": "sales_outreach",
            "context": {},
            "stagger_minutes": 5,
            "start_immediately": true
        }
        """
        try:
            campaign_id = request.data.get('campaign_id')
            call_purpose = request.data.get('call_purpose', 'sales_outreach')
            context = request.data.get('context', {})
            stagger_minutes = request.data.get('stagger_minutes', 5)
            start_immediately = request.data.get('start_immediately', True)
            
            if not campaign_id:
                return Response({
                    'success': False,
                    'error': 'campaign_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get campaign and contacts
            campaign = get_object_or_404(Campaign, id=campaign_id)
            campaign_contacts = CampaignContact.objects.filter(
                campaign=campaign,
                status__in=['pending', 'active']
            ).select_related('contact')
            
            if not campaign_contacts.exists():
                return Response({
                    'success': False,
                    'error': 'No active contacts found in campaign'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            triggered_calls = []
            base_time = timezone.now() if start_immediately else timezone.now() + timedelta(minutes=10)
            
            for i, campaign_contact in enumerate(campaign_contacts):
                contact = campaign_contact.contact
                
                # Skip if contact is on do-not-call list
                if contact.do_not_call:
                    continue
                
                # Calculate staggered time
                call_time = base_time + timedelta(minutes=i * stagger_minutes)
                
                # Add campaign context
                call_context = {
                    **context,
                    'campaign_id': str(campaign.id),
                    'campaign_name': campaign.name,
                    'campaign_type': campaign.campaign_type
                }
                
                # Schedule the call
                task_result = autonomous_agent_call.apply_async(
                    args=[str(contact.id), call_purpose, call_context],
                    eta=call_time
                )
                
                triggered_calls.append({
                    'task_id': task_result.id,
                    'contact_id': str(contact.id),
                    'contact_name': contact.full_name,
                    'contact_phone': contact.phone_number,
                    'scheduled_time': call_time.isoformat()
                })
                
                # Update campaign contact status
                campaign_contact.status = 'in_progress'
                campaign_contact.save()
            
            logger.info(f"Triggered {len(triggered_calls)} autonomous calls for campaign: {campaign.name}")
            
            return Response({
                'success': True,
                'message': f'Triggered {len(triggered_calls)} autonomous calls for campaign: {campaign.name}',
                'campaign': {
                    'id': str(campaign.id),
                    'name': campaign.name,
                    'type': campaign.campaign_type
                },
                'calls_triggered': len(triggered_calls),
                'call_purpose': call_purpose,
                'triggered_calls': triggered_calls
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error triggering campaign calls: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_autonomous_calls(self, request):
        """
        Trigger bulk autonomous calls for multiple contacts
        
        POST /api/calls/bulk_autonomous_calls/
        {
            "calls": [
                {
                    "contact_id": "uuid",
                    "call_purpose": "sales_outreach",
                    "context": {},
                    "delay_minutes": 0
                },
                ...
            ]
        }
        """
        try:
            calls_data = request.data.get('calls', [])
            
            if not calls_data:
                return Response({
                    'success': False,
                    'error': 'calls array is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            triggered_calls = []
            errors = []
            
            for i, call_data in enumerate(calls_data):
                try:
                    contact_id = call_data.get('contact_id')
                    call_purpose = call_data.get('call_purpose', 'sales_outreach')
                    context = call_data.get('context', {})
                    delay_minutes = call_data.get('delay_minutes', 0)
                    
                    if not contact_id:
                        errors.append(f"Call #{i+1}: contact_id is required")
                        continue
                    
                    # Validate contact exists
                    contact = Contact.objects.filter(id=contact_id).first()
                    if not contact:
                        errors.append(f"Call #{i+1}: Contact not found")
                        continue
                    
                    # Skip if on do-not-call list
                    if contact.do_not_call:
                        errors.append(f"Call #{i+1}: Contact {contact.full_name} is on do-not-call list")
                        continue
                    
                    # Schedule the call
                    call_time = timezone.now() + timedelta(minutes=delay_minutes)
                    task_result = autonomous_agent_call.apply_async(
                        args=[contact_id, call_purpose, context],
                        eta=call_time
                    )
                    
                    triggered_calls.append({
                        'task_id': task_result.id,
                        'contact_id': contact_id,
                        'contact_name': contact.full_name,
                        'contact_phone': contact.phone_number,
                        'call_purpose': call_purpose,
                        'scheduled_time': call_time.isoformat()
                    })
                    
                except Exception as e:
                    errors.append(f"Call #{i+1}: {str(e)}")
            
            logger.info(f"Bulk autonomous calls: {len(triggered_calls)} triggered, {len(errors)} errors")
            
            return Response({
                'success': len(triggered_calls) > 0,
                'message': f'Triggered {len(triggered_calls)} autonomous calls',
                'calls_triggered': len(triggered_calls),
                'errors_count': len(errors),
                'triggered_calls': triggered_calls,
                'errors': errors
            }, status=status.HTTP_200_OK if len(triggered_calls) > 0 else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in bulk autonomous calls: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def autonomous_call_status(self, request):
        """
        Get status of autonomous calls
        
        GET /api/calls/autonomous_call_status/?task_id=xxx&contact_id=yyy
        """
        try:
            task_id = request.query_params.get('task_id')
            contact_id = request.query_params.get('contact_id')
            
            if task_id:
                # Get status by task ID (requires Celery result backend)
                from celery.result import AsyncResult
                result = AsyncResult(task_id)
                
                return Response({
                    'task_id': task_id,
                    'status': result.status,
                    'result': result.result if result.ready() else None,
                    'successful': result.successful() if result.ready() else None
                })
            
            elif contact_id:
                # Get recent calls for contact
                contact = get_object_or_404(Contact, id=contact_id)
                recent_calls = Call.objects.filter(
                    contact=contact,
                    ai_enabled=True
                ).order_by('-created_at')[:5]
                
                calls_data = []
                for call in recent_calls:
                    calls_data.append({
                        'id': str(call.id),
                        'status': call.status,
                        'call_type': call.call_type,
                        'started_at': call.started_at,
                        'ended_at': call.ended_at,
                        'duration_seconds': call.duration_seconds,
                        'twilio_call_sid': call.twilio_call_sid
                    })
                
                return Response({
                    'contact': {
                        'id': str(contact.id),
                        'name': contact.full_name,
                        'phone': contact.phone_number
                    },
                    'recent_calls': calls_data
                })
            
            else:
                return Response({
                    'success': False,
                    'error': 'Either task_id or contact_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error getting autonomous call status: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CallQueueViewSet(viewsets.ModelViewSet):
    """ViewSet for managing call queue"""
    queryset = CallQueue.objects.all()
    serializer_class = CallQueueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CallQueue.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-priority', 'scheduled_time')
    
    @action(detail=False, methods=['post'])
    def schedule_autonomous_calls(self, request):
        """
        Schedule multiple autonomous calls in the queue
        
        POST /api/call-queue/schedule_autonomous_calls/
        {
            "calls": [
                {
                    "contact_id": "uuid",
                    "call_purpose": "sales_outreach",
                    "scheduled_time": "2024-01-20T15:30:00Z",
                    "priority": "high",
                    "context": {}
                },
                ...
            ]
        }
        """
        try:
            calls_data = request.data.get('calls', [])
            
            if not calls_data:
                return Response({
                    'success': False,
                    'error': 'calls array is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            scheduled_calls = []
            errors = []
            
            for i, call_data in enumerate(calls_data):
                try:
                    contact_id = call_data.get('contact_id')
                    call_purpose = call_data.get('call_purpose', 'sales_outreach')
                    scheduled_time_str = call_data.get('scheduled_time')
                    priority = call_data.get('priority', 'normal')
                    context = call_data.get('context', {})
                    
                    if not contact_id:
                        errors.append(f"Call #{i+1}: contact_id is required")
                        continue
                    
                    if not scheduled_time_str:
                        errors.append(f"Call #{i+1}: scheduled_time is required")
                        continue
                    
                    # Validate contact
                    contact = Contact.objects.filter(id=contact_id).first()
                    if not contact:
                        errors.append(f"Call #{i+1}: Contact not found")
                        continue
                    
                    # Parse scheduled time
                    from django.utils.dateparse import parse_datetime
                    scheduled_time = parse_datetime(scheduled_time_str)
                    if not scheduled_time:
                        errors.append(f"Call #{i+1}: Invalid scheduled_time format")
                        continue
                    
                    # Get or create call template
                    call_template, _ = CallTemplate.objects.get_or_create(
                        template_type=call_purpose,
                        defaults={
                            'name': f'Autonomous {call_purpose.title()} Template',
                            'description': f'Template for autonomous {call_purpose} calls',
                            'is_active': True
                        }
                    )
                    
                    # Create queue entry
                    queue_entry = CallQueue.objects.create(
                        contact=contact,
                        call_template=call_template,
                        priority=priority,
                        scheduled_time=scheduled_time,
                        created_by_id=request.user.id,
                        call_config={
                            'call_purpose': call_purpose,
                            'autonomous': True,
                            'context': context
                        }
                    )
                    
                    scheduled_calls.append({
                        'queue_id': str(queue_entry.id),
                        'contact_id': contact_id,
                        'contact_name': contact.full_name,
                        'call_purpose': call_purpose,
                        'scheduled_time': scheduled_time_str,
                        'priority': priority
                    })
                    
                except Exception as e:
                    errors.append(f"Call #{i+1}: {str(e)}")
            
            return Response({
                'success': len(scheduled_calls) > 0,
                'message': f'Scheduled {len(scheduled_calls)} autonomous calls in queue',
                'scheduled_calls': len(scheduled_calls),
                'errors_count': len(errors),
                'calls': scheduled_calls,
                'errors': errors
            }, status=status.HTTP_200_OK if len(scheduled_calls) > 0 else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error scheduling autonomous calls: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
