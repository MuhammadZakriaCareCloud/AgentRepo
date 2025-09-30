"""
Agent Training API Views

API endpoints for managing agent training, conversation analysis,
and knowledge base operations.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta
import logging

from .models import AIConversation
from .training_models import (
    ConversationTrainingData,
    AgentKnowledgeBase,
    AgentTrainingSession,
    ConversationPattern,
    AgentPerformanceMetrics
)
from .training_services import AgentTrainingService, process_conversation_for_training_task
from .serializers import (
    ConversationTrainingDataSerializer,
    AgentKnowledgeBaseSerializer,
    AgentTrainingSessionSerializer,
    ConversationPatternSerializer,
    AgentPerformanceMetricsSerializer
)

logger = logging.getLogger(__name__)


class ConversationTrainingDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversation training data
    """
    queryset = ConversationTrainingData.objects.all()
    serializer_class = ConversationTrainingDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(conversation_category=category)
        
        # Filter by outcome
        outcome = self.request.query_params.get('outcome')
        if outcome:
            queryset = queryset.filter(outcome=outcome)
        
        # Filter by success score range
        min_score = self.request.query_params.get('min_success_score')
        if min_score:
            try:
                queryset = queryset.filter(success_score__gte=float(min_score))
            except ValueError:
                pass
        
        # Filter by quality
        high_quality = self.request.query_params.get('high_quality')
        if high_quality and high_quality.lower() == 'true':
            queryset = queryset.filter(is_high_quality=True)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def process_conversation(self, request):
        """
        Process a specific conversation for training
        """
        try:
            conversation_id = request.data.get('conversation_id')
            call_id = request.data.get('call_id')
            
            if not conversation_id:
                return Response(
                    {'error': 'conversation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if conversation exists
            try:
                ai_conversation = AIConversation.objects.get(id=conversation_id)
            except AIConversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Process in background
            task = process_conversation_for_training_task.delay(conversation_id, call_id)
            
            return Response({
                'success': True,
                'message': 'Conversation processing started',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}")
            return Response(
                {'error': 'Failed to process conversation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_process(self, request):
        """
        Process multiple conversations for training
        """
        try:
            conversation_ids = request.data.get('conversation_ids', [])
            
            if not conversation_ids or not isinstance(conversation_ids, list):
                return Response(
                    {'error': 'conversation_ids list is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate conversations exist
            existing_conversations = AIConversation.objects.filter(
                id__in=conversation_ids
            ).values_list('id', flat=True)
            
            valid_ids = [str(id) for id in existing_conversations]
            invalid_ids = [id for id in conversation_ids if id not in valid_ids]
            
            # Start processing tasks for valid conversations
            task_ids = []
            for conversation_id in valid_ids:
                task = process_conversation_for_training_task.delay(conversation_id)
                task_ids.append(task.id)
            
            return Response({
                'success': True,
                'message': f'Processing started for {len(valid_ids)} conversations',
                'task_ids': task_ids,
                'processed_count': len(valid_ids),
                'invalid_ids': invalid_ids
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Error in bulk processing: {str(e)}")
            return Response(
                {'error': 'Failed to start bulk processing'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get analytics on training data
        """
        try:
            queryset = self.get_queryset()
            
            analytics = {
                'total_conversations': queryset.count(),
                'by_category': {},
                'by_outcome': {},
                'average_success_score': 0,
                'high_quality_count': queryset.filter(is_high_quality=True).count(),
                'processed_count': queryset.filter(processed_for_training=True).count(),
            }
            
            # Category breakdown
            category_stats = queryset.values('conversation_category').annotate(
                count=Count('id'),
                avg_score=Avg('success_score')
            )
            for stat in category_stats:
                analytics['by_category'][stat['conversation_category']] = {
                    'count': stat['count'],
                    'average_score': round(stat['avg_score'] or 0, 2)
                }
            
            # Outcome breakdown
            outcome_stats = queryset.values('outcome').annotate(count=Count('id'))
            for stat in outcome_stats:
                analytics['by_outcome'][stat['outcome']] = stat['count']
            
            # Overall average success score
            avg_score = queryset.aggregate(avg=Avg('success_score'))['avg']
            analytics['average_success_score'] = round(avg_score or 0, 2)
            
            return Response(analytics, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating analytics: {str(e)}")
            return Response(
                {'error': 'Failed to generate analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_high_quality(self, request, pk=None):
        """
        Mark a training data entry as high quality
        """
        try:
            training_data = self.get_object()
            training_data.is_high_quality = True
            training_data.reviewed_by_human = True
            training_data.reviewer = request.user
            training_data.save(update_fields=['is_high_quality', 'reviewed_by_human', 'reviewer'])
            
            return Response({
                'success': True,
                'message': 'Marked as high quality'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error marking high quality: {str(e)}")
            return Response(
                {'error': 'Failed to update quality flag'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgentKnowledgeBaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing agent knowledge base
    """
    queryset = AgentKnowledgeBase.objects.filter(is_active=True)
    serializer_class = AgentKnowledgeBaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by knowledge type
        knowledge_type = self.request.query_params.get('type')
        if knowledge_type:
            queryset = queryset.filter(knowledge_type=knowledge_type)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Search in title and content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(tags__contains=[search])
            )
        
        return queryset.order_by('-success_rate', '-usage_count')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def update_from_training_data(self, request):
        """
        Update knowledge base from training data
        """
        try:
            training_service = AgentTrainingService()
            entries_created = training_service.create_knowledge_from_training_data()
            
            return Response({
                'success': True,
                'message': f'Knowledge base updated with {entries_created} new entries',
                'entries_created': entries_created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            return Response(
                {'error': 'Failed to update knowledge base'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search_by_intent(self, request):
        """
        Search knowledge base by user intent
        """
        try:
            intent = request.query_params.get('intent')
            if not intent:
                return Response(
                    {'error': 'intent parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Search in trigger phrases and content
            knowledge_entries = self.get_queryset().filter(
                Q(trigger_phrases__contains=[intent]) |
                Q(content__icontains=intent) |
                Q(title__icontains=intent)
            ).order_by('-success_rate')[:10]
            
            serializer = self.get_serializer(knowledge_entries, many=True)
            return Response({
                'success': True,
                'intent': intent,
                'matches': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error searching by intent: {str(e)}")
            return Response(
                {'error': 'Failed to search knowledge base'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def record_usage(self, request, pk=None):
        """
        Record usage of a knowledge entry
        """
        try:
            knowledge_entry = self.get_object()
            success = request.data.get('success', True)
            satisfaction_score = request.data.get('satisfaction_score')
            
            # Update usage count
            knowledge_entry.usage_count += 1
            
            # Update success rate (simple moving average)
            if success:
                knowledge_entry.success_rate = (
                    (knowledge_entry.success_rate * (knowledge_entry.usage_count - 1) + 1.0) /
                    knowledge_entry.usage_count
                )
            else:
                knowledge_entry.success_rate = (
                    (knowledge_entry.success_rate * (knowledge_entry.usage_count - 1) + 0.0) /
                    knowledge_entry.usage_count
                )
            
            # Update satisfaction score if provided
            if satisfaction_score is not None:
                try:
                    score = float(satisfaction_score)
                    if 0 <= score <= 5:  # Assuming 1-5 scale
                        current_avg = knowledge_entry.average_user_satisfaction or 0
                        knowledge_entry.average_user_satisfaction = (
                            (current_avg * (knowledge_entry.usage_count - 1) + score) /
                            knowledge_entry.usage_count
                        )
                except (ValueError, TypeError):
                    pass
            
            knowledge_entry.save(update_fields=[
                'usage_count', 'success_rate', 'average_user_satisfaction'
            ])
            
            return Response({
                'success': True,
                'message': 'Usage recorded successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            return Response(
                {'error': 'Failed to record usage'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgentTrainingSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing agent training sessions
    """
    queryset = AgentTrainingSession.objects.all()
    serializer_class = AgentTrainingSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start_training(self, request):
        """
        Start a new training session
        """
        try:
            training_type = request.data.get('training_type', 'incremental')
            training_parameters = request.data.get('training_parameters', {})
            
            # Create training session
            training_session = AgentTrainingSession.objects.create(
                training_type=training_type,
                training_parameters=training_parameters,
                created_by=request.user,
                status='pending'
            )
            
            # Add training data
            training_data_ids = request.data.get('training_data_ids', [])
            if training_data_ids:
                training_data = ConversationTrainingData.objects.filter(
                    id__in=training_data_ids
                )
                training_session.training_data_used.set(training_data)
            
            # Start training process (in production, this would trigger ML training)
            training_session.status = 'in_progress'
            training_session.started_at = timezone.now()
            training_session.save(update_fields=['status', 'started_at'])
            
            return Response({
                'success': True,
                'training_session_id': str(training_session.id),
                'message': 'Training session started'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting training: {str(e)}")
            return Response(
                {'error': 'Failed to start training session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationPatternViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing conversation patterns (read-only)
    """
    queryset = ConversationPattern.objects.filter(is_active=True)
    serializer_class = ConversationPatternSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        pattern_type = self.request.query_params.get('type')
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        
        return queryset.order_by('-success_rate')
    
    @action(detail=False, methods=['get'])
    def top_patterns(self, request):
        """
        Get top performing conversation patterns
        """
        try:
            limit = int(request.query_params.get('limit', 10))
            pattern_type = request.query_params.get('type')
            
            queryset = self.get_queryset()
            if pattern_type:
                queryset = queryset.filter(pattern_type=pattern_type)
            
            top_patterns = queryset.order_by('-success_rate')[:limit]
            serializer = self.get_serializer(top_patterns, many=True)
            
            return Response({
                'success': True,
                'patterns': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting top patterns: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve top patterns'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgentPerformanceMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing agent performance metrics (read-only)
    """
    queryset = AgentPerformanceMetrics.objects.all()
    serializer_class = AgentPerformanceMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by time period
        period_type = self.request.query_params.get('period')
        if period_type:
            queryset = queryset.filter(period_type=period_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)
        
        return queryset.order_by('-period_start')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get performance summary
        """
        try:
            # Get metrics for the last 30 days
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            metrics = self.get_queryset().filter(
                period_start__gte=start_date,
                period_end__lte=end_date
            )
            
            if not metrics.exists():
                return Response({
                    'success': True,
                    'message': 'No metrics available for the specified period',
                    'summary': {}
                }, status=status.HTTP_200_OK)
            
            # Calculate summary statistics
            summary = {
                'total_conversations': metrics.aggregate(
                    total=Count('total_conversations')
                )['total'] or 0,
                'average_success_rate': metrics.aggregate(
                    avg=Avg('success_rate')
                )['avg'] or 0,
                'average_conversation_length': metrics.aggregate(
                    avg=Avg('average_conversation_length')
                )['avg'] or 0,
                'average_response_time': metrics.aggregate(
                    avg=Avg('average_response_time')
                )['avg'] or 0,
                'total_cost': metrics.aggregate(
                    total=Avg('estimated_cost')
                )['total'] or 0,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
            }
            
            # Round floating point values
            for key, value in summary.items():
                if isinstance(value, float):
                    summary[key] = round(value, 2)
            
            return Response({
                'success': True,
                'summary': summary
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {str(e)}")
            return Response(
                {'error': 'Failed to generate performance summary'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
