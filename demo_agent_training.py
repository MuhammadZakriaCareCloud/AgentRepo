#!/usr/bin/env python
"""
Demo script for AI Agent Training System

This script demonstrates:
1. Processing conversations for training
2. Creating knowledge base entries
3. Agent learning from successful conversations
4. Performance analytics and metrics
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_call_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from ai_integration.models import AIProvider, AIConversation, AIMessage
from ai_integration.training_models import (
    ConversationTrainingData,
    AgentKnowledgeBase,
    AgentTrainingSession,
    ConversationPattern,
    AgentPerformanceMetrics
)
from ai_integration.training_services import AgentTrainingService
from calls.models import Call, CallConversation
from crm.models import Contact


def create_sample_data():
    """Create sample conversation data for training"""
    print("Creating sample data...")
    
    # Create a user if not exists
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        user.set_password('admin')
        user.save()
        print(f"Created admin user")
    
    # Create AI provider if not exists
    ai_provider, created = AIProvider.objects.get_or_create(
        name='OpenAI GPT-3.5',
        defaults={
            'provider_type': 'openai',
            'api_key': 'sk-test-key',
            'default_model': 'gpt-3.5-turbo',
            'available_models': ['gpt-3.5-turbo', 'gpt-4'],
            'max_tokens': 2000,
            'is_active': True
        }
    )
    if created:
        print(f"Created AI provider: {ai_provider.name}")
    
    # Create sample contacts
    contact1, created = Contact.objects.get_or_create(
        phone_number='+1234567890',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
    )
    
    contact2, created = Contact.objects.get_or_create(
        phone_number='+1234567891',
        defaults={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com'
        }
    )
    
    # Create sample conversations
    conversations = []
    
    # Successful sales conversation
    conv1 = AIConversation.objects.create(
        conversation_type='call',
        status='completed',
        contact_phone=contact1.phone_number,
        user=user,
        ai_provider=ai_provider,
        model_used='gpt-3.5-turbo',
        system_prompt='You are a helpful sales assistant.',
        message_count=6,
        total_tokens_used=450,
        conversation_metadata={'call_type': 'sales', 'outcome': 'successful'}
    )
    
    # Add messages to conversation 1
    messages1 = [
        {'role': 'user', 'content': 'Hi, I\'m interested in your product pricing.', 'tokens': 50},
        {'role': 'assistant', 'content': 'Hello! I\'d be happy to help you with pricing information. What specific product are you interested in?', 'tokens': 75},
        {'role': 'user', 'content': 'I need a CRM solution for my small business.', 'tokens': 45},
        {'role': 'assistant', 'content': 'Great! Our CRM solution is perfect for small businesses. We have packages starting at $29/month. Would you like me to schedule a demo?', 'tokens': 80},
        {'role': 'user', 'content': 'Yes, that sounds good. Can we schedule for next week?', 'tokens': 40},
        {'role': 'assistant', 'content': 'Absolutely! I\'ll have someone from our team reach out to schedule a convenient time. Thank you for your interest!', 'tokens': 60}
    ]
    
    for i, msg_data in enumerate(messages1):
        AIMessage.objects.create(
            conversation=conv1,
            role=msg_data['role'],
            content=msg_data['content'],
            tokens_used=msg_data['tokens'],
            model_used='gpt-3.5-turbo' if msg_data['role'] == 'assistant' else None,
            processing_time_ms=1200 if msg_data['role'] == 'assistant' else None
        )
    
    conversations.append(conv1)
    
    # Customer support conversation
    conv2 = AIConversation.objects.create(
        conversation_type='call',
        status='completed',
        contact_phone=contact2.phone_number,
        user=user,
        ai_provider=ai_provider,
        model_used='gpt-3.5-turbo',
        system_prompt='You are a helpful customer support assistant.',
        message_count=8,
        total_tokens_used=520,
        conversation_metadata={'call_type': 'support', 'outcome': 'resolved'}
    )
    
    # Add messages to conversation 2
    messages2 = [
        {'role': 'user', 'content': 'I\'m having trouble logging into my account.', 'tokens': 45},
        {'role': 'assistant', 'content': 'I\'m sorry to hear you\'re having login issues. Let me help you with that. Can you tell me what error message you\'re seeing?', 'tokens': 85},
        {'role': 'user', 'content': 'It says "Invalid credentials" but I\'m sure my password is correct.', 'tokens': 55},
        {'role': 'assistant', 'content': 'That can be frustrating. Let\'s try a password reset. I\'ll send you a reset link to your registered email address.', 'tokens': 75},
        {'role': 'user', 'content': 'Okay, I received the email and reset my password.', 'tokens': 40},
        {'role': 'assistant', 'content': 'Great! Now try logging in with your new password. Are you able to access your account?', 'tokens': 70},
        {'role': 'user', 'content': 'Yes, it works now! Thank you so much for your help.', 'tokens': 45},
        {'role': 'assistant', 'content': 'You\'re welcome! I\'m glad we could resolve that quickly. Is there anything else I can help you with today?', 'tokens': 75}
    ]
    
    for i, msg_data in enumerate(messages2):
        AIMessage.objects.create(
            conversation=conv2,
            role=msg_data['role'],
            content=msg_data['content'],
            tokens_used=msg_data['tokens'],
            model_used='gpt-3.5-turbo' if msg_data['role'] == 'assistant' else None,
            processing_time_ms=1100 if msg_data['role'] == 'assistant' else None
        )
    
    conversations.append(conv2)
    
    # Partially successful conversation
    conv3 = AIConversation.objects.create(
        conversation_type='call',
        status='completed',
        contact_phone='+1234567892',
        ai_provider=ai_provider,
        model_used='gpt-3.5-turbo',
        system_prompt='You are a helpful appointment booking assistant.',
        message_count=4,
        total_tokens_used=280,
        conversation_metadata={'call_type': 'appointment', 'outcome': 'partial'}
    )
    
    # Add messages to conversation 3
    messages3 = [
        {'role': 'user', 'content': 'I need to book an appointment but I\'m not sure about my availability.', 'tokens': 60},
        {'role': 'assistant', 'content': 'I understand. What service would you like to book an appointment for?', 'tokens': 55},
        {'role': 'user', 'content': 'A consultation, but I need to check my calendar first.', 'tokens': 50},
        {'role': 'assistant', 'content': 'No problem! Feel free to call back when you have your calendar handy. We have availability throughout the week.', 'tokens': 85}
    ]
    
    for i, msg_data in enumerate(messages3):
        AIMessage.objects.create(
            conversation=conv3,
            role=msg_data['role'],
            content=msg_data['content'],
            tokens_used=msg_data['tokens'],
            model_used='gpt-3.5-turbo' if msg_data['role'] == 'assistant' else None,
            processing_time_ms=1000 if msg_data['role'] == 'assistant' else None
        )
    
    conversations.append(conv3)
    
    print(f"Created {len(conversations)} sample conversations")
    return conversations, ai_provider


def demonstrate_training_system():
    """Demonstrate the complete agent training system"""
    print("\n" + "="*60)
    print("AI AGENT TRAINING SYSTEM DEMONSTRATION")
    print("="*60)
    
    # Create sample data
    conversations, ai_provider = create_sample_data()
    
    # Initialize training service
    training_service = AgentTrainingService()
    
    print("\n1. PROCESSING CONVERSATIONS FOR TRAINING")
    print("-" * 40)
    
    training_data_entries = []
    for conv in conversations:
        print(f"Processing conversation {conv.id}...")
        try:
            training_data = training_service.process_conversation_for_training(conv)
            training_data_entries.append(training_data)
            
            print(f"  ✓ Category: {training_data.conversation_category}")
            print(f"  ✓ Outcome: {training_data.outcome}")
            print(f"  ✓ Success Score: {training_data.success_score:.2f}")
            print(f"  ✓ Key Phrases: {training_data.key_phrases}")
            print(f"  ✓ User Intents: {training_data.user_intents}")
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    print(f"Created {len(training_data_entries)} training data entries")
    
    print("\n2. MARKING HIGH-QUALITY CONVERSATIONS")
    print("-" * 40)
    
    # Mark successful conversations as high quality
    high_quality_count = 0
    for training_data in training_data_entries:
        if training_data.success_score >= 0.7:
            training_data.is_high_quality = True
            training_data.reviewed_by_human = True
            training_data.save(update_fields=['is_high_quality', 'reviewed_by_human'])
            high_quality_count += 1
            print(f"  ✓ Marked conversation {training_data.ai_conversation.id} as high quality")
    
    print(f"Marked {high_quality_count} conversations as high quality")
    
    print("\n3. CREATING KNOWLEDGE BASE FROM TRAINING DATA")
    print("-" * 40)
    
    knowledge_entries_created = training_service.create_knowledge_from_training_data()
    print(f"Created {knowledge_entries_created} knowledge base entries")
    
    # Display created knowledge entries
    knowledge_entries = AgentKnowledgeBase.objects.all().order_by('-success_rate')
    for entry in knowledge_entries:
        print(f"\n  📚 {entry.title}")
        print(f"     Type: {entry.knowledge_type}")
        print(f"     Category: {entry.category}")
        print(f"     Success Rate: {entry.success_rate:.2%}")
        print(f"     Trigger Phrases: {entry.trigger_phrases}")
        print(f"     Content: {entry.content[:100]}...")
    
    print("\n4. CREATING TRAINING SESSION")
    print("-" * 40)
    
    # Create a training session
    user = User.objects.first()
    training_session = AgentTrainingSession.objects.create(
        training_type='incremental',
        training_parameters={
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 10
        },
        status='completed',
        conversations_processed=len(training_data_entries),
        knowledge_entries_created=knowledge_entries_created,
        created_by=user,
        started_at=timezone.now() - timedelta(hours=1),
        completed_at=timezone.now(),
        duration_seconds=3600,
        training_metrics={
            'accuracy': 0.92,
            'loss': 0.15,
            'improvement': 0.08
        },
        performance_improvements={
            'response_quality': 0.12,
            'success_rate': 0.08,
            'user_satisfaction': 0.15
        }
    )
    
    # Add training data to session
    training_session.training_data_used.set(training_data_entries)
    
    print(f"  ✓ Created training session: {training_session.id}")
    print(f"  ✓ Status: {training_session.status}")
    print(f"  ✓ Conversations processed: {training_session.conversations_processed}")
    print(f"  ✓ Duration: {training_session.duration_seconds} seconds")
    print(f"  ✓ Accuracy: {training_session.training_metrics.get('accuracy', 0):.2%}")
    
    print("\n5. GENERATING PERFORMANCE METRICS")
    print("-" * 40)
    
    # Create performance metrics
    performance_metrics = AgentPerformanceMetrics.objects.create(
        period_type='daily',
        period_start=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0),
        period_end=timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999),
        agent_version='v1.2.0',
        ai_provider=ai_provider,
        total_conversations=len(conversations),
        successful_conversations=len([td for td in training_data_entries if td.outcome == 'successful']),
        success_rate=len([td for td in training_data_entries if td.outcome == 'successful']) / len(conversations),
        average_conversation_length=sum(conv.message_count for conv in conversations) / len(conversations),
        average_response_time=1.15,  # seconds
        user_satisfaction_score=4.2,
        outcomes_breakdown={
            'successful': len([td for td in training_data_entries if td.outcome == 'successful']),
            'partially_successful': len([td for td in training_data_entries if td.outcome == 'partially_successful']),
            'unsuccessful': len([td for td in training_data_entries if td.outcome == 'unsuccessful'])
        },
        new_patterns_learned=2,
        knowledge_base_updates=knowledge_entries_created,
        total_tokens_used=sum(conv.total_tokens_used for conv in conversations),
        estimated_cost=0.012  # Estimated cost in USD
    )
    
    print(f"  ✓ Period: {performance_metrics.period_type}")
    print(f"  ✓ Total Conversations: {performance_metrics.total_conversations}")
    print(f"  ✓ Success Rate: {performance_metrics.success_rate:.2%}")
    print(f"  ✓ Avg Conversation Length: {performance_metrics.average_conversation_length:.1f} turns")
    print(f"  ✓ User Satisfaction: {performance_metrics.user_satisfaction_score}/5.0")
    print(f"  ✓ Total Tokens Used: {performance_metrics.total_tokens_used}")
    print(f"  ✓ Estimated Cost: ${performance_metrics.estimated_cost:.3f}")
    
    print("\n6. TRAINING DATA ANALYTICS")
    print("-" * 40)
    
    # Display analytics
    total_training_data = ConversationTrainingData.objects.count()
    high_quality_data = ConversationTrainingData.objects.filter(is_high_quality=True).count()
    avg_success_score = sum(td.success_score for td in training_data_entries) / len(training_data_entries)
    
    print(f"  📊 Total Training Conversations: {total_training_data}")
    print(f"  📊 High-Quality Conversations: {high_quality_data}")
    print(f"  📊 Average Success Score: {avg_success_score:.2f}")
    
    # Category breakdown
    from collections import Counter
    categories = Counter(td.conversation_category for td in training_data_entries)
    outcomes = Counter(td.outcome for td in training_data_entries)
    
    print(f"  📊 Categories: {dict(categories)}")
    print(f"  📊 Outcomes: {dict(outcomes)}")
    
    print("\n7. KNOWLEDGE BASE SUMMARY")
    print("-" * 40)
    
    total_knowledge = AgentKnowledgeBase.objects.count()
    active_knowledge = AgentKnowledgeBase.objects.filter(is_active=True).count()
    high_success_knowledge = AgentKnowledgeBase.objects.filter(success_rate__gte=0.8).count()
    
    print(f"  🧠 Total Knowledge Entries: {total_knowledge}")
    print(f"  🧠 Active Entries: {active_knowledge}")
    print(f"  🧠 High-Success Entries (≥80%): {high_success_knowledge}")
    
    if knowledge_entries:
        avg_success_rate = sum(entry.success_rate for entry in knowledge_entries) / len(knowledge_entries)
        print(f"  🧠 Average Success Rate: {avg_success_rate:.2%}")
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE!")
    print("="*60)
    print("\nThe agent training system has successfully:")
    print("✅ Processed conversations and extracted training insights")
    print("✅ Created knowledge base entries from successful interactions")
    print("✅ Generated performance metrics and analytics")
    print("✅ Established a foundation for continuous learning")
    print("\nNext steps:")
    print("🔄 Conversations will be automatically processed as they occur")
    print("🧠 Knowledge base will continuously grow and improve")
    print("📈 Performance metrics will track agent improvement over time")
    print("🎯 Agents will use learned knowledge for better responses")
    
    return {
        'training_data_count': len(training_data_entries),
        'knowledge_entries_count': knowledge_entries_created,
        'performance_metrics': performance_metrics,
        'training_session': training_session
    }


if __name__ == "__main__":
    results = demonstrate_training_system()
    print(f"\n🎉 Demo completed with {results['training_data_count']} training entries and {results['knowledge_entries_count']} knowledge entries!")
