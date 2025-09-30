from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Call, CallConversation, CallTemplate, CallQueue
from .serializers import CallSerializer, CallConversationSerializer, CallTemplateSerializer, CallQueueSerializer
from .tasks import process_outbound_call

class CallViewSet(viewsets.ModelViewSet):
    """ViewSet for managing calls"""
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    filterset_fields = ['call_type', 'status', 'contact', 'ai_enabled']
    search_fields = ['contact__first_name', 'contact__last_name', 'twilio_call_sid']
    ordering_fields = ['created_at', 'duration']
    ordering = ['-created_at']

class CallConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for call conversations"""
    queryset = CallConversation.objects.all()
    serializer_class = CallConversationSerializer
    filterset_fields = ['call', 'speaker_type']
    ordering = ['timestamp']

class CallTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for call templates"""
    queryset = CallTemplate.objects.all()
    serializer_class = CallTemplateSerializer
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']

class CallQueueViewSet(viewsets.ModelViewSet):
    """ViewSet for call queue"""
    queryset = CallQueue.objects.all()
    serializer_class = CallQueueSerializer
    filterset_fields = ['status', 'priority']
    ordering = ['priority', 'scheduled_time']

class InitiateCallView(APIView):
    """API endpoint to initiate an outbound call"""
    
    def post(self, request):
        contact_id = request.data.get('contact_id')
        template_id = request.data.get('template_id')
        priority = request.data.get('priority', 'normal')
        scheduled_time = request.data.get('scheduled_time')
        
        if not contact_id:
            return Response(
                {'error': 'contact_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from crm.models import Contact
            contact = Contact.objects.get(id=contact_id)
            
            # Create queue item
            queue_item = CallQueue.objects.create(
                contact=contact,
                call_template_id=template_id,
                priority=priority,
                scheduled_time=scheduled_time,
                created_by=request.user
            )
            
            # Process immediately if no scheduled time
            if not scheduled_time:
                task = process_outbound_call.delay(str(queue_item.id))
                return Response({
                    'message': 'Call initiated',
                    'queue_item_id': str(queue_item.id),
                    'task_id': task.id
                })
            else:
                return Response({
                    'message': 'Call scheduled',
                    'queue_item_id': str(queue_item.id)
                })
                
        except Contact.DoesNotExist:
            return Response(
                {'error': 'Contact not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BulkCallView(APIView):
    """API endpoint for bulk calling"""
    
    def post(self, request):
        contact_ids = request.data.get('contact_ids', [])
        template_id = request.data.get('template_id')
        priority = request.data.get('priority', 'normal')
        
        if not contact_ids:
            return Response(
                {'error': 'contact_ids is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from crm.models import Contact
            contacts = Contact.objects.filter(id__in=contact_ids)
            
            created_items = []
            for contact in contacts:
                queue_item = CallQueue.objects.create(
                    contact=contact,
                    call_template_id=template_id,
                    priority=priority,
                    created_by=request.user
                )
                created_items.append(str(queue_item.id))
            
            return Response({
                'message': f'Created {len(created_items)} call queue items',
                'queue_item_ids': created_items
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EndCallView(APIView):
    """API endpoint to end an active call"""
    
    def post(self, request, call_id):
        try:
            call = get_object_or_404(Call, id=call_id)
            
            if call.status not in ['initiated', 'ringing', 'in_progress']:
                return Response(
                    {'error': 'Call is not active'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # End call via Twilio if we have a SID
            if call.twilio_call_sid:
                from .services.twilio_service import twilio_service
                success = twilio_service.end_call(call.twilio_call_sid)
                if not success:
                    return Response(
                        {'error': 'Failed to end call via Twilio'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            call.status = 'completed'
            call.ended_at = timezone.now()
            call.save()
            
            return Response({'message': 'Call ended successfully'})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AddCallNoteView(APIView):
    """API endpoint to add a note to a call"""
    
    def post(self, request, call_id):
        try:
            call = get_object_or_404(Call, id=call_id)
            note = request.data.get('note')
            
            if not note:
                return Response(
                    {'error': 'note is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if call.notes:
                call.notes += f"\n\n{note}"
            else:
                call.notes = note
            
            call.save()
            
            return Response({'message': 'Note added successfully'})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProcessQueueView(APIView):
    """API endpoint to manually process the call queue"""
    
    def post(self, request):
        try:
            from .tasks import bulk_process_call_queue
            result = bulk_process_call_queue.delay()
            
            return Response({
                'message': 'Queue processing initiated',
                'task_id': result.id
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class QueueStatsView(APIView):
    """API endpoint for queue statistics"""
    
    def get(self, request):
        try:
            stats = {
                'pending': CallQueue.objects.filter(status='pending').count(),
                'in_progress': CallQueue.objects.filter(status='in_progress').count(),
                'completed': CallQueue.objects.filter(status='completed').count(),
                'failed': CallQueue.objects.filter(status='failed').count(),
                'cancelled': CallQueue.objects.filter(status='cancelled').count(),
            }
            
            return Response(stats)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CallDashboardView(APIView):
    """API endpoint for call dashboard data"""
    
    def get(self, request):
        try:
            from django.db.models import Count, Avg
            from datetime import timedelta
            from django.utils import timezone
            
            # Get date range
            days = int(request.GET.get('days', 7))
            start_date = timezone.now() - timedelta(days=days)
            
            # Call statistics
            total_calls = Call.objects.filter(created_at__gte=start_date).count()
            completed_calls = Call.objects.filter(
                created_at__gte=start_date, 
                status='completed'
            ).count()
            
            # Call type breakdown
            call_types = Call.objects.filter(created_at__gte=start_date).values('call_type').annotate(
                count=Count('id')
            )
            
            # Average call duration
            avg_duration = Call.objects.filter(
                created_at__gte=start_date,
                duration__isnull=False
            ).aggregate(avg_duration=Avg('duration'))
            
            return Response({
                'period_days': days,
                'total_calls': total_calls,
                'completed_calls': completed_calls,
                'success_rate': (completed_calls / total_calls * 100) if total_calls > 0 else 0,
                'call_types': list(call_types),
                'avg_duration_seconds': avg_duration['avg_duration'].total_seconds() if avg_duration['avg_duration'] else 0
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CallPerformanceView(APIView):
    """API endpoint for call performance metrics"""
    
    def get(self, request):
        try:
            from django.db.models import Count, Q
            from datetime import timedelta
            from django.utils import timezone
            
            # Get date range
            days = int(request.GET.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Performance metrics
            performance_data = Call.objects.filter(
                created_at__gte=start_date
            ).aggregate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                failed=Count('id', filter=Q(status='failed')),
                no_answer=Count('id', filter=Q(status='no_answer')),
                busy=Count('id', filter=Q(status='busy'))
            )
            
            return Response(performance_data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
