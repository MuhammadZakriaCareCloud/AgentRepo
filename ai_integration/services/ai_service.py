import openai
from django.conf import settings
from ai_integration.models import AIConversation, AIMessage, AIProvider
import logging
import time

logger = logging.getLogger(__name__)

class AIService:
    """
    Service class for AI integration
    """
    
    def __init__(self, provider_name='default'):
        self.provider = self._get_provider(provider_name)
        if self.provider.provider_type == 'openai':
            openai.api_key = self.provider.api_key
            if self.provider.api_endpoint:
                openai.api_base = self.provider.api_endpoint
    
    def _get_provider(self, provider_name):
        """Get AI provider configuration"""
        try:
            if provider_name == 'default':
                return AIProvider.objects.filter(is_active=True).first()
            return AIProvider.objects.get(name=provider_name, is_active=True)
        except AIProvider.DoesNotExist:
            # Create default provider if none exists
            return AIProvider.objects.create(
                name='Default OpenAI',
                provider_type='openai',
                api_key=settings.OPENAI_API_KEY,
                default_model=settings.OPENAI_MODEL,
                available_models=['gpt-4', 'gpt-3.5-turbo'],
                is_active=True
            )
    
    def create_conversation(self, conversation_type, contact_phone=None, user=None, system_prompt=None):
        """Create a new AI conversation"""
        if not system_prompt:
            system_prompt = self._get_default_system_prompt(conversation_type)
        
        conversation = AIConversation.objects.create(
            conversation_type=conversation_type,
            contact_phone=contact_phone,
            user=user,
            ai_provider=self.provider,
            model_used=self.provider.default_model,
            system_prompt=system_prompt
        )
        
        # Add system message
        AIMessage.objects.create(
            conversation=conversation,
            role='system',
            content=system_prompt
        )
        
        return conversation
    
    def add_message(self, conversation, role, content, **kwargs):
        """Add a message to the conversation"""
        message = AIMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            **kwargs
        )
        
        conversation.message_count += 1
        conversation.save()
        
        return message
    
    def generate_response(self, conversation, user_input, max_tokens=None, temperature=None):
        """Generate AI response for the conversation"""
        start_time = time.time()
        
        try:
            # Add user message
            self.add_message(conversation, 'user', user_input)
            
            # Get conversation history
            messages = self._get_conversation_messages(conversation)
            
            # Set parameters
            max_tokens = max_tokens or settings.AI_MAX_TOKENS
            temperature = temperature or settings.AI_TEMPERATURE
            
            # Generate response based on provider type
            if self.provider.provider_type == 'openai':
                response = self._generate_openai_response(
                    messages, max_tokens, temperature
                )
            else:
                raise ValueError(f"Unsupported provider type: {self.provider.provider_type}")
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Add AI response to conversation
            ai_message = self.add_message(
                conversation,
                'assistant',
                response['content'],
                tokens_used=response.get('tokens_used', 0),
                model_used=response.get('model_used'),
                processing_time_ms=processing_time
            )
            
            # Update conversation stats
            conversation.total_tokens_used += response.get('tokens_used', 0)
            conversation.save()
            
            return {
                'success': True,
                'response': response['content'],
                'message_id': ai_message.id,
                'tokens_used': response.get('tokens_used', 0),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_openai_response(self, messages, max_tokens, temperature):
        """Generate response using OpenAI API"""
        try:
            response = openai.ChatCompletion.create(
                model=self.provider.default_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model_used': response.model
            }
            
        except openai.error.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            return {
                'content': "I'm experiencing high demand right now. Please try again in a moment.",
                'tokens_used': 0,
                'model_used': self.provider.default_model
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _get_conversation_messages(self, conversation):
        """Get conversation messages in OpenAI format"""
        messages = []
        for msg in conversation.messages.all():
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        return messages
    
    def _get_default_system_prompt(self, conversation_type):
        """Get default system prompt based on conversation type"""
        prompts = {
            'call': """You are a professional AI assistant handling phone calls. You should:
1. Be polite and professional
2. Listen carefully to the caller's needs
3. Provide helpful and accurate information
4. Keep responses concise and clear
5. Ask clarifying questions when needed
6. End calls appropriately when the conversation is complete

Remember you are representing a business, so maintain a professional tone at all times.""",
            
            'chat': """You are a helpful AI assistant. You should:
1. Be friendly and helpful
2. Provide accurate information
3. Ask clarifying questions when needed
4. Keep responses concise but informative
5. Be respectful and professional""",
            
            'email': """You are an AI assistant helping to draft professional emails. You should:
1. Use appropriate business language
2. Structure emails clearly
3. Be concise but complete
4. Maintain a professional tone
5. Include relevant details""",
            
            'sms': """You are an AI assistant for SMS communication. You should:
1. Keep messages brief and to the point
2. Use clear, simple language
3. Include only essential information
4. Be friendly but professional"""
        }
        
        return prompts.get(conversation_type, prompts['chat'])
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"Analyze the sentiment of this text and respond with only 'positive', 'negative', or 'neutral':\n\n{text}",
                max_tokens=10,
                temperature=0
            )
            
            sentiment = response.choices[0].text.strip().lower()
            return sentiment if sentiment in ['positive', 'negative', 'neutral'] else 'neutral'
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {str(e)}")
            return 'neutral'
    
    def extract_intent(self, text, possible_intents=None):
        """Extract intent from user input"""
        if not possible_intents:
            possible_intents = [
                'information_request', 'complaint', 'compliment', 
                'appointment_booking', 'cancellation', 'support_request'
            ]
        
        try:
            intent_list = ', '.join(possible_intents)
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"What is the intent of this message? Choose from: {intent_list}\n\nMessage: {text}\n\nIntent:",
                max_tokens=20,
                temperature=0
            )
            
            intent = response.choices[0].text.strip().lower()
            return intent if intent in possible_intents else 'unknown'
            
        except Exception as e:
            logger.error(f"Failed to extract intent: {str(e)}")
            return 'unknown'
    
    def summarize_conversation(self, conversation):
        """Generate a summary of the conversation"""
        try:
            messages = conversation.messages.filter(role__in=['user', 'assistant']).order_by('created_at')
            conversation_text = '\n'.join([f"{msg.role}: {msg.content}" for msg in messages])
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"Summarize this conversation in 2-3 sentences:\n\n{conversation_text}\n\nSummary:",
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].text.strip()
            
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {str(e)}")
            return "Unable to generate summary"
    
    def get_conversation_analytics(self, conversation):
        """Get analytics for a conversation"""
        messages = conversation.messages.all()
        
        return {
            'total_messages': messages.count(),
            'user_messages': messages.filter(role='user').count(),
            'assistant_messages': messages.filter(role='assistant').count(),
            'total_tokens': conversation.total_tokens_used,
            'avg_response_time': messages.filter(role='assistant').aggregate(
                avg_time=models.Avg('processing_time_ms')
            )['avg_time'] or 0,
            'conversation_duration': (conversation.last_activity - conversation.created_at).total_seconds()
        }

# Singleton instance
ai_service = AIService()
