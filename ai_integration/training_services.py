"""
Agent Training Services

This module provides services for processing conversation data,
extracting training insights, and updating agent knowledge.
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg, Count, Q
from celery import shared_task

from .models import AIConversation, AIMessage
from .training_models import (
    ConversationTrainingData, 
    AgentKnowledgeBase, 
    AgentTrainingSession,
    ConversationPattern,
    AgentPerformanceMetrics
)
from calls.models import Call, CallConversation
from crm.models import Contact

logger = logging.getLogger(__name__)


class ConversationAnalyzer:
    """
    Analyze conversations to extract training insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_conversation(self, ai_conversation: AIConversation) -> Dict[str, Any]:
        """
        Analyze a completed conversation and extract training insights
        """
        try:
            messages = ai_conversation.messages.all().order_by('created_at')
            
            analysis = {
                'conversation_id': str(ai_conversation.id),
                'conversation_summary': self._generate_summary(messages),
                'key_phrases': self._extract_key_phrases(messages),
                'user_intents': self._detect_user_intents(messages),
                'agent_responses': self._analyze_agent_responses(messages),
                'conversation_flow': self._analyze_conversation_flow(messages),
                'success_metrics': self._calculate_success_metrics(ai_conversation, messages),
                'areas_for_improvement': self._identify_improvements(messages),
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing conversation {ai_conversation.id}: {str(e)}")
            return {}
    
    def _generate_summary(self, messages) -> str:
        """Generate a concise summary of the conversation"""
        try:
            # Extract key topics and outcomes
            user_messages = [msg.content for msg in messages if msg.role == 'user']
            assistant_messages = [msg.content for msg in messages if msg.role == 'assistant']
            
            if not user_messages or not assistant_messages:
                return "Incomplete conversation"
            
            # Simple extractive summary (in production, use more sophisticated NLP)
            summary_parts = []
            
            # Extract main topic from first few exchanges
            if len(user_messages) > 0:
                first_user_msg = user_messages[0][:100]
                summary_parts.append(f"User inquiry: {first_user_msg}")
            
            # Extract resolution or outcome from last few exchanges
            if len(assistant_messages) > 0:
                last_assistant_msg = assistant_messages[-1][:100]
                summary_parts.append(f"Agent response: {last_assistant_msg}")
            
            return ". ".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return "Unable to generate summary"
    
    def _extract_key_phrases(self, messages) -> List[str]:
        """Extract important phrases and keywords"""
        try:
            all_text = " ".join([msg.content for msg in messages])
            
            # Simple keyword extraction (in production, use NLP libraries like spaCy)
            keywords = []
            
            # Look for common business terms
            business_terms = [
                'appointment', 'meeting', 'schedule', 'booking', 'cancel',
                'price', 'cost', 'quote', 'estimate', 'payment',
                'support', 'help', 'issue', 'problem', 'question',
                'product', 'service', 'feature', 'demo', 'trial'
            ]
            
            for term in business_terms:
                if term.lower() in all_text.lower():
                    keywords.append(term)
            
            # Extract quoted phrases
            quoted_phrases = re.findall(r'"([^"]*)"', all_text)
            keywords.extend(quoted_phrases[:5])  # Limit to first 5 quotes
            
            return list(set(keywords))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error extracting key phrases: {str(e)}")
            return []
    
    def _detect_user_intents(self, messages) -> List[str]:
        """Detect user intents from conversation"""
        try:
            user_messages = [msg.content for msg in messages if msg.role == 'user']
            intents = []
            
            # Intent detection patterns (in production, use intent classification models)
            intent_patterns = {
                'booking': ['book', 'schedule', 'appointment', 'meeting'],
                'information': ['what', 'how', 'when', 'where', 'tell me'],
                'complaint': ['problem', 'issue', 'wrong', 'error', 'unhappy'],
                'cancellation': ['cancel', 'refund', 'return', 'stop'],
                'support': ['help', 'support', 'assistance', 'guidance'],
                'pricing': ['price', 'cost', 'fee', 'charge', 'expensive'],
            }
            
            for message in user_messages:
                message_lower = message.lower()
                for intent, patterns in intent_patterns.items():
                    if any(pattern in message_lower for pattern in patterns):
                        intents.append(intent)
            
            return list(set(intents))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error detecting user intents: {str(e)}")
            return []
    
    def _analyze_agent_responses(self, messages) -> List[Dict[str, Any]]:
        """Analyze agent responses for effectiveness"""
        try:
            agent_responses = []
            
            for i, message in enumerate(messages):
                if message.role == 'assistant':
                    response_data = {
                        'content': message.content,
                        'position': i,
                        'tokens_used': message.tokens_used,
                        'response_time': message.processing_time_ms,
                        'effectiveness_score': self._score_response_effectiveness(message, messages, i)
                    }
                    agent_responses.append(response_data)
            
            return agent_responses
            
        except Exception as e:
            self.logger.error(f"Error analyzing agent responses: {str(e)}")
            return []
    
    def _score_response_effectiveness(self, message, all_messages, position) -> float:
        """Score how effective an agent response was (0.0 - 1.0)"""
        try:
            score = 0.5  # Base score
            
            # Factors that increase effectiveness score
            if len(message.content) > 50:  # Detailed responses
                score += 0.1
            
            if '?' in message.content:  # Engaging questions
                score += 0.1
            
            # Look at user response to gauge effectiveness
            if position + 1 < len(all_messages):
                next_message = all_messages[position + 1]
                if next_message.role == 'user':
                    next_content = next_message.content.lower()
                    
                    # Positive indicators in user response
                    positive_words = ['yes', 'okay', 'sure', 'great', 'perfect', 'thanks']
                    if any(word in next_content for word in positive_words):
                        score += 0.2
                    
                    # Negative indicators
                    negative_words = ['no', 'but', 'however', 'confused', 'unclear']
                    if any(word in next_content for word in negative_words):
                        score -= 0.2
            
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            
        except Exception as e:
            self.logger.error(f"Error scoring response effectiveness: {str(e)}")
            return 0.5
    
    def _analyze_conversation_flow(self, messages) -> Dict[str, Any]:
        """Analyze the flow and structure of the conversation"""
        try:
            flow_analysis = {
                'total_turns': len(messages),
                'user_turns': len([m for m in messages if m.role == 'user']),
                'agent_turns': len([m for m in messages if m.role == 'assistant']),
                'average_response_length': 0,
                'conversation_phases': [],
            }
            
            if messages:
                total_length = sum(len(m.content) for m in messages)
                flow_analysis['average_response_length'] = total_length / len(messages)
            
            # Identify conversation phases (opening, middle, closing)
            if len(messages) >= 3:
                flow_analysis['conversation_phases'] = ['opening', 'development', 'closing']
            elif len(messages) >= 1:
                flow_analysis['conversation_phases'] = ['opening']
            
            return flow_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing conversation flow: {str(e)}")
            return {}
    
    def _calculate_success_metrics(self, conversation: AIConversation, messages) -> Dict[str, float]:
        """Calculate various success metrics for the conversation"""
        try:
            metrics = {
                'completion_score': 0.0,
                'engagement_score': 0.0,
                'efficiency_score': 0.0,
                'overall_success_score': 0.0,
            }
            
            # Completion score based on conversation status
            if conversation.status == 'completed':
                metrics['completion_score'] = 1.0
            elif conversation.status == 'active':
                metrics['completion_score'] = 0.5
            else:
                metrics['completion_score'] = 0.0
            
            # Engagement score based on message exchange
            user_messages = len([m for m in messages if m.role == 'user'])
            if user_messages >= 3:
                metrics['engagement_score'] = min(1.0, user_messages / 5)
            else:
                metrics['engagement_score'] = user_messages / 3
            
            # Efficiency score based on conversation length vs. resolution
            total_turns = len(messages)
            if total_turns <= 6:  # Quick resolution
                metrics['efficiency_score'] = 1.0
            elif total_turns <= 12:  # Reasonable length
                metrics['efficiency_score'] = 0.7
            else:  # Long conversation
                metrics['efficiency_score'] = 0.4
            
            # Overall success score (weighted average)
            metrics['overall_success_score'] = (
                metrics['completion_score'] * 0.4 +
                metrics['engagement_score'] * 0.3 +
                metrics['efficiency_score'] * 0.3
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating success metrics: {str(e)}")
            return {'overall_success_score': 0.0}
    
    def _identify_improvements(self, messages) -> List[str]:
        """Identify areas where the agent could improve"""
        try:
            improvements = []
            
            # Check for common issues
            agent_messages = [m for m in messages if m.role == 'assistant']
            
            # Too many short responses
            short_responses = [m for m in agent_messages if len(m.content) < 30]
            if len(short_responses) > len(agent_messages) * 0.5:
                improvements.append("Provide more detailed responses")
            
            # Lack of questions/engagement
            questions = [m for m in agent_messages if '?' in m.content]
            if len(questions) < 2 and len(agent_messages) > 3:
                improvements.append("Ask more engaging questions")
            
            # Repetitive responses
            contents = [m.content for m in agent_messages]
            if len(set(contents)) < len(contents) * 0.8:  # Less than 80% unique
                improvements.append("Avoid repetitive responses")
            
            return improvements
            
        except Exception as e:
            self.logger.error(f"Error identifying improvements: {str(e)}")
            return []


class AgentTrainingService:
    """
    Service for training agents from conversation data
    """
    
    def __init__(self):
        self.analyzer = ConversationAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    @transaction.atomic
    def process_conversation_for_training(self, ai_conversation: AIConversation, 
                                        call: Optional[Call] = None) -> ConversationTrainingData:
        """
        Process a completed conversation and create training data
        """
        try:
            # Analyze the conversation
            analysis = self.analyzer.analyze_conversation(ai_conversation)
            
            if not analysis:
                raise ValueError("Failed to analyze conversation")
            
            # Determine conversation category and outcome
            category = self._categorize_conversation(ai_conversation, analysis)
            outcome = self._determine_outcome(ai_conversation, analysis)
            
            # Create training data record
            training_data = ConversationTrainingData.objects.create(
                ai_conversation=ai_conversation,
                call=call,
                conversation_category=category,
                outcome=outcome,
                success_score=analysis.get('success_metrics', {}).get('overall_success_score', 0.0),
                conversation_summary=analysis.get('conversation_summary', ''),
                key_phrases=analysis.get('key_phrases', []),
                user_intents=analysis.get('user_intents', []),
                agent_responses=analysis.get('agent_responses', []),
                conversation_turns=analysis.get('conversation_flow', {}).get('total_turns', 0),
                average_response_time=self._calculate_avg_response_time(ai_conversation),
                what_worked_well=self._extract_what_worked_well(analysis),
                areas_for_improvement="; ".join(analysis.get('areas_for_improvement', [])),
                contact_info=self._extract_contact_info(ai_conversation),
                call_context=self._extract_call_context(call) if call else {},
            )
            
            self.logger.info(f"Created training data for conversation {ai_conversation.id}")
            return training_data
            
        except Exception as e:
            self.logger.error(f"Error processing conversation for training: {str(e)}")
            raise
    
    def _categorize_conversation(self, conversation: AIConversation, analysis: Dict) -> str:
        """Categorize the conversation based on intents and content"""
        try:
            intents = analysis.get('user_intents', [])
            
            # Map intents to categories
            if 'booking' in intents:
                return 'appointment'
            elif 'complaint' in intents:
                return 'complaint'
            elif 'support' in intents:
                return 'support'
            elif 'pricing' in intents:
                return 'sales'
            elif 'information' in intents:
                return 'information'
            else:
                return 'other'
                
        except Exception as e:
            self.logger.error(f"Error categorizing conversation: {str(e)}")
            return 'other'
    
    def _determine_outcome(self, conversation: AIConversation, analysis: Dict) -> str:
        """Determine the outcome of the conversation"""
        try:
            success_score = analysis.get('success_metrics', {}).get('overall_success_score', 0.0)
            
            if conversation.status == 'completed':
                if success_score >= 0.8:
                    return 'successful'
                elif success_score >= 0.6:
                    return 'partially_successful'
                else:
                    return 'unsuccessful'
            elif conversation.status == 'error':
                return 'error'
            else:
                return 'incomplete'
                
        except Exception as e:
            self.logger.error(f"Error determining outcome: {str(e)}")
            return 'incomplete'
    
    def _calculate_avg_response_time(self, conversation: AIConversation) -> Optional[float]:
        """Calculate average response time for agent messages"""
        try:
            agent_messages = conversation.messages.filter(
                role='assistant',
                processing_time_ms__isnull=False
            )
            
            if agent_messages.exists():
                avg_time = agent_messages.aggregate(
                    avg_time=Avg('processing_time_ms')
                )['avg_time']
                return avg_time / 1000.0 if avg_time else None  # Convert to seconds
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating avg response time: {str(e)}")
            return None
    
    def _extract_what_worked_well(self, analysis: Dict) -> str:
        """Extract what worked well in the conversation"""
        try:
            success_factors = []
            
            # High effectiveness responses
            agent_responses = analysis.get('agent_responses', [])
            effective_responses = [r for r in agent_responses if r.get('effectiveness_score', 0) > 0.7]
            
            if effective_responses:
                success_factors.append("Agent provided effective responses")
            
            # Good engagement
            success_score = analysis.get('success_metrics', {}).get('engagement_score', 0)
            if success_score > 0.7:
                success_factors.append("High user engagement")
            
            # Efficient resolution
            efficiency_score = analysis.get('success_metrics', {}).get('efficiency_score', 0)
            if efficiency_score > 0.8:
                success_factors.append("Efficient problem resolution")
            
            return "; ".join(success_factors) if success_factors else "Standard conversation flow"
            
        except Exception as e:
            self.logger.error(f"Error extracting success factors: {str(e)}")
            return ""
    
    def _extract_contact_info(self, conversation: AIConversation) -> Dict:
        """Extract anonymized contact information"""
        try:
            contact_info = {}
            
            if conversation.contact_phone:
                # Anonymize phone number (keep area code, mask rest)
                phone = conversation.contact_phone
                if len(phone) >= 7:
                    contact_info['area_code'] = phone[:3]
                    contact_info['phone_type'] = 'mobile' if phone.startswith(('6', '7', '8', '9')) else 'landline'
            
            return contact_info
            
        except Exception as e:
            self.logger.error(f"Error extracting contact info: {str(e)}")
            return {}
    
    def _extract_call_context(self, call: Call) -> Dict:
        """Extract call context information"""
        try:
            if not call:
                return {}
            
            context = {
                'call_type': call.call_type,
                'duration_seconds': call.duration.total_seconds() if call.duration else None,
                'time_of_day': call.created_at.hour if call.created_at else None,
                'day_of_week': call.created_at.weekday() if call.created_at else None,
                'outcome': call.outcome,
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error extracting call context: {str(e)}")
            return {}
    
    @transaction.atomic
    def create_knowledge_from_training_data(self, training_data_queryset=None) -> int:
        """
        Create or update knowledge base entries from training data
        """
        try:
            if training_data_queryset is None:
                # Process unprocessed high-quality training data
                training_data_queryset = ConversationTrainingData.objects.filter(
                    processed_for_training=False,
                    is_high_quality=True,
                    success_score__gte=0.7
                )
            
            knowledge_entries_created = 0
            
            for training_data in training_data_queryset:
                # Create FAQ entries from successful conversations
                if training_data.outcome == 'successful' and training_data.user_intents:
                    knowledge_entry = self._create_faq_entry(training_data)
                    if knowledge_entry:
                        knowledge_entries_created += 1
                
                # Create response patterns from effective agent responses
                effective_responses = [
                    r for r in training_data.agent_responses 
                    if r.get('effectiveness_score', 0) > 0.8
                ]
                
                for response in effective_responses:
                    pattern_entry = self._create_response_pattern(training_data, response)
                    if pattern_entry:
                        knowledge_entries_created += 1
                
                # Mark as processed
                training_data.processed_for_training = True
                training_data.save(update_fields=['processed_for_training'])
            
            self.logger.info(f"Created {knowledge_entries_created} knowledge entries")
            return knowledge_entries_created
            
        except Exception as e:
            self.logger.error(f"Error creating knowledge from training data: {str(e)}")
            return 0
    
    def _create_faq_entry(self, training_data: ConversationTrainingData) -> Optional[AgentKnowledgeBase]:
        """Create FAQ entry from successful conversation"""
        try:
            # Extract question from user intents and key phrases
            intents = training_data.user_intents
            key_phrases = training_data.key_phrases
            
            if not intents:
                return None
            
            # Generate title based on main intent
            main_intent = intents[0]
            title = f"How to handle {main_intent} requests"
            
            # Check if similar entry exists
            existing = AgentKnowledgeBase.objects.filter(
                knowledge_type='faq',
                category=training_data.conversation_category,
                title__icontains=main_intent
            ).first()
            
            if existing:
                # Update existing entry
                existing.usage_count += 1
                existing.success_rate = (existing.success_rate + training_data.success_score) / 2
                existing.trigger_phrases = list(set(existing.trigger_phrases + key_phrases))
                existing.save()
                return existing
            else:
                # Create new entry
                entry = AgentKnowledgeBase.objects.create(
                    knowledge_type='faq',
                    category=training_data.conversation_category,
                    title=title,
                    content=training_data.conversation_summary,
                    trigger_phrases=key_phrases,
                    success_rate=training_data.success_score,
                    usage_count=1,
                    confidence_score=training_data.success_score,
                    created_by_id=1  # System user
                )
                entry.derived_from_conversations.add(training_data)
                return entry
                
        except Exception as e:
            self.logger.error(f"Error creating FAQ entry: {str(e)}")
            return None
    
    def _create_response_pattern(self, training_data: ConversationTrainingData, 
                               response_data: Dict) -> Optional[AgentKnowledgeBase]:
        """Create response pattern from effective agent response"""
        try:
            response_content = response_data.get('content', '')
            effectiveness = response_data.get('effectiveness_score', 0)
            
            if not response_content or effectiveness < 0.8:
                return None
            
            # Create response pattern entry
            title = f"Effective response pattern for {training_data.conversation_category}"
            
            entry = AgentKnowledgeBase.objects.create(
                knowledge_type='response_pattern',
                category=training_data.conversation_category,
                title=title,
                content=response_content,
                context=f"Use when: {', '.join(training_data.user_intents)}",
                success_rate=effectiveness,
                usage_count=1,
                confidence_score=effectiveness,
                created_by_id=1  # System user
            )
            entry.derived_from_conversations.add(training_data)
            return entry
            
        except Exception as e:
            self.logger.error(f"Error creating response pattern: {str(e)}")
            return None


# Celery tasks for background processing
@shared_task(bind=True, max_retries=3)
def process_conversation_for_training_task(self, conversation_id: str, call_id: str = None):
    """
    Background task to process conversation for training
    """
    try:
        ai_conversation = AIConversation.objects.get(id=conversation_id)
        call = None
        if call_id:
            call = Call.objects.get(id=call_id)
        
        training_service = AgentTrainingService()
        training_data = training_service.process_conversation_for_training(ai_conversation, call)
        
        logger.info(f"Successfully processed conversation {conversation_id} for training")
        return {'success': True, 'training_data_id': str(training_data.id)}
        
    except Exception as e:
        logger.error(f"Error processing conversation for training: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60)
        raise


@shared_task(bind=True, max_retries=3)
def update_knowledge_base_task(self):
    """
    Background task to update knowledge base from training data
    """
    try:
        training_service = AgentTrainingService()
        entries_created = training_service.create_knowledge_from_training_data()
        
        logger.info(f"Updated knowledge base with {entries_created} new entries")
        return {'success': True, 'entries_created': entries_created}
        
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60)
        raise


@shared_task(bind=True, max_retries=3)
def generate_performance_metrics_task(self):
    """
    Background task to generate performance metrics
    """
    try:
        # This would implement comprehensive performance analysis
        # For now, just a placeholder
        logger.info("Performance metrics generation completed")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Error generating performance metrics: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60)
        raise
