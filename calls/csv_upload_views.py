"""
CSV Upload Management for Outbound Calls
Handles bulk contact import and knowledge base integration
"""
import csv
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import uuid
from datetime import datetime

from crm.models import Contact, ContactNote
from calls.models import CallTemplate, CallQueue
from scheduling.models import Campaign, CampaignContact
from ai_integration.models import AIPromptTemplate
from django.contrib.auth.models import User

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv_contacts(request):
    """
    Upload CSV file with contacts for outbound calling
    
    Expected CSV columns:
    - first_name, last_name, phone_number, email
    - company, job_title, lead_source
    - preferred_time, language, timezone
    - custom_field_1, custom_field_2, notes
    """
    
    if 'csv_file' not in request.FILES:
        return Response({
            'success': False,
            'error': 'No CSV file uploaded'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['csv_file']
    
    # Validate file type
    if not csv_file.name.endswith('.csv'):
        return Response({
            'success': False,
            'error': 'File must be a CSV format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(decoded_file)
        
        created_contacts = []
        updated_contacts = []
        errors = []
        
        # Get campaign info from request
        campaign_name = request.data.get('campaign_name', 'CSV Upload Campaign')
        agent_preference = request.data.get('agent_preference', 'Ali Khan')  # Default agent
        call_priority = request.data.get('priority', 'normal')
        
        # Create or get campaign
        campaign, created = Campaign.objects.get_or_create(
            name=campaign_name,
            defaults={
                'campaign_type': 'bulk_calls',
                'status': 'active',
                'description': f'Campaign created from CSV upload - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'start_date': datetime.now(),
                'allowed_calling_hours_start': '09:00:00',
                'allowed_calling_hours_end': '18:00:00',
                'allowed_days_of_week': [1, 2, 3, 4, 5],
                'max_calls_per_hour': 30,
                'max_calls_per_day': 200,
                'created_by': request.user
            }
        )
        
        row_number = 1
        for row in csv_reader:
            row_number += 1
            
            try:
                # Required fields
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                phone_number = row.get('phone_number', '').strip()
                
                if not phone_number:
                    errors.append(f"Row {row_number}: Phone number is required")
                    continue
                
                # Ensure phone number format
                if not phone_number.startswith('+'):
                    phone_number = '+92' + phone_number.lstrip('0')
                
                # Create or update contact
                contact, created = Contact.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={
                        'first_name': first_name or 'Unknown',
                        'last_name': last_name or 'Contact',
                        'email': row.get('email', '').strip(),
                        'company': row.get('company', '').strip(),
                        'job_title': row.get('job_title', '').strip(),
                        'lead_source': row.get('lead_source', 'csv_upload'),
                        'contact_type': 'lead',
                        'status': 'active',
                        'ai_interaction_history': {
                            'preferred_time': row.get('preferred_time', 'morning'),
                            'language': row.get('language', 'urdu'),
                            'timezone': row.get('timezone', 'Asia/Karachi'),
                            'custom_field_1': row.get('custom_field_1', ''),
                            'custom_field_2': row.get('custom_field_2', ''),
                            'csv_upload_date': datetime.now().isoformat(),
                            'campaign_name': campaign_name
                        }
                    }
                )
                
                if created:
                    created_contacts.append(contact)
                else:
                    # Update existing contact with new info
                    if row.get('email'):
                        contact.email = row.get('email').strip()
                    if row.get('company'):
                        contact.company = row.get('company').strip()
                    if row.get('job_title'):
                        contact.job_title = row.get('job_title').strip()
                    
                    # Update AI interaction history
                    contact.ai_interaction_history.update({
                        'preferred_time': row.get('preferred_time', contact.ai_interaction_history.get('preferred_time', 'morning')),
                        'language': row.get('language', contact.ai_interaction_history.get('language', 'urdu')),
                        'last_csv_update': datetime.now().isoformat()
                    })
                    contact.save()
                    updated_contacts.append(contact)
                
                # Add notes if provided
                notes = row.get('notes', '').strip()
                if notes:
                    ContactNote.objects.create(
                        contact=contact,
                        title="CSV Upload Note",
                        content=notes,
                        created_by=request.user,
                        note_type='general'
                    )
                
                # Add to campaign
                CampaignContact.objects.get_or_create(
                    campaign=campaign,
                    contact=contact,
                    defaults={
                        'status': 'pending',
                        'assigned_agent': request.user,
                        'priority': call_priority,
                        'metadata': {
                            'source': 'csv_upload',
                            'agent_preference': agent_preference,
                            'upload_timestamp': datetime.now().isoformat()
                        }
                    }
                )
                
            except Exception as e:
                errors.append(f"Row {row_number}: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'CSV upload completed',
            'data': {
                'campaign_id': str(campaign.id),
                'campaign_name': campaign.name,
                'created_contacts': len(created_contacts),
                'updated_contacts': len(updated_contacts),
                'total_processed': len(created_contacts) + len(updated_contacts),
                'errors': errors,
                'error_count': len(errors)
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to process CSV: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_knowledge_base_from_csv(request):
    """
    Create knowledge base from CSV for AI agents
    
    Expected CSV columns:
    - topic, question, answer, category
    - agent_name, context, priority
    - tags, effective_date, expiry_date
    """
    
    if 'csv_file' not in request.FILES:
        return Response({
            'success': False,
            'error': 'No CSV file uploaded'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['csv_file']
    
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(decoded_file)
        
        created_templates = []
        errors = []
        
        row_number = 1
        for row in csv_reader:
            row_number += 1
            
            try:
                topic = row.get('topic', '').strip()
                question = row.get('question', '').strip()
                answer = row.get('answer', '').strip()
                category = row.get('category', 'general').strip()
                
                if not topic or not answer:
                    errors.append(f"Row {row_number}: Topic and Answer are required")
                    continue
                
                # Create AI prompt template
                template_name = f"Knowledge Base: {topic}"
                
                prompt_template, created = AIPromptTemplate.objects.get_or_create(
                    name=template_name,
                    defaults={
                        'category': category,
                        'description': f"Knowledge base entry for {topic}",
                        'system_prompt': f"""
You are an AI agent with knowledge about: {topic}

Context: {row.get('context', '')}

When asked about "{question or topic}", respond with:
{answer}

Additional Information:
- Priority: {row.get('priority', 'normal')}
- Tags: {row.get('tags', '')}
- Agent: {row.get('agent_name', 'Any Agent')}

Always be helpful, accurate, and professional in your responses.
                        """.strip(),
                        'initial_message': f"I can help you with information about {topic}.",
                        'ai_parameters': {
                            'temperature': 0.3,  # More consistent for knowledge base
                            'max_tokens': 1000,
                            'topic': topic,
                            'category': category,
                            'priority': row.get('priority', 'normal'),
                            'tags': row.get('tags', '').split(','),
                            'agent_preference': row.get('agent_name', 'any'),
                            'effective_date': row.get('effective_date', ''),
                            'expiry_date': row.get('expiry_date', '')
                        },
                        'template_variables': [
                            'topic', 'question', 'answer', 'context'
                        ],
                        'created_by': request.user,
                        'is_active': True
                    }
                )
                
                if created:
                    created_templates.append(template_name)
                
            except Exception as e:
                errors.append(f"Row {row_number}: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Knowledge base created from CSV',
            'data': {
                'created_templates': len(created_templates),
                'template_names': created_templates,
                'errors': errors,
                'error_count': len(errors)
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to process knowledge base CSV: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def queue_calls_from_campaign(request, campaign_id):
    """
    Queue outbound calls for a specific campaign
    """
    
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        # Get agent preference
        agent_name = request.data.get('agent_name', 'Ali Khan')
        
        # Find appropriate call template
        call_template = CallTemplate.objects.filter(
            conversation_flow__agent_name__icontains=agent_name,
            is_active=True
        ).first()
        
        if not call_template:
            call_template = CallTemplate.objects.filter(
                template_type='sales',
                is_active=True
            ).first()
        
        # Get campaign contacts
        campaign_contacts = CampaignContact.objects.filter(
            campaign=campaign,
            status='pending'
        )
        
        queued_calls = []
        
        for campaign_contact in campaign_contacts:
            # Create call queue entry
            queue_entry, created = CallQueue.objects.get_or_create(
                contact=campaign_contact.contact,
                status='pending',
                defaults={
                    'call_template': call_template,
                    'priority': campaign_contact.priority,
                    'max_attempts': 3,
                    'scheduled_time': datetime.now(),
                    'created_by': request.user,
                    'call_config': {
                        'campaign_id': str(campaign.id),
                        'campaign_name': campaign.name,
                        'agent_name': agent_name,
                        'contact_name': f"{campaign_contact.contact.first_name} {campaign_contact.contact.last_name}",
                        'knowledge_base_enabled': True,
                        'csv_source': True
                    }
                }
            )
            
            if created:
                queued_calls.append({
                    'contact_name': f"{campaign_contact.contact.first_name} {campaign_contact.contact.last_name}",
                    'phone_number': campaign_contact.contact.phone_number,
                    'agent_name': agent_name
                })
        
        return Response({
            'success': True,
            'message': f'Calls queued for campaign: {campaign.name}',
            'data': {
                'campaign_id': str(campaign.id),
                'campaign_name': campaign.name,
                'agent_name': agent_name,
                'queued_calls': len(queued_calls),
                'calls': queued_calls
            }
        }, status=status.HTTP_200_OK)
        
    except Campaign.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_campaign_status(request, campaign_id):
    """
    Get status of a campaign and its calls
    """
    
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        # Get campaign contacts
        total_contacts = CampaignContact.objects.filter(campaign=campaign).count()
        pending_contacts = CampaignContact.objects.filter(campaign=campaign, status='pending').count()
        completed_contacts = CampaignContact.objects.filter(campaign=campaign, status='completed').count()
        
        # Get queue status
        queued_calls = CallQueue.objects.filter(call_config__campaign_id=str(campaign.id))
        pending_calls = queued_calls.filter(status='pending').count()
        in_progress_calls = queued_calls.filter(status='in_progress').count()
        completed_calls = queued_calls.filter(status='completed').count()
        failed_calls = queued_calls.filter(status='failed').count()
        
        return Response({
            'success': True,
            'data': {
                'campaign': {
                    'id': str(campaign.id),
                    'name': campaign.name,
                    'type': campaign.campaign_type,
                    'status': campaign.status,
                    'created_at': campaign.created_at,
                    'start_date': campaign.start_date
                },
                'contacts': {
                    'total': total_contacts,
                    'pending': pending_contacts,
                    'completed': completed_contacts
                },
                'calls': {
                    'pending': pending_calls,
                    'in_progress': in_progress_calls,
                    'completed': completed_calls,
                    'failed': failed_calls,
                    'total_queued': queued_calls.count()
                },
                'progress': {
                    'completion_rate': f"{(completed_calls / max(total_contacts, 1)) * 100:.1f}%",
                    'success_rate': f"{(completed_calls / max(completed_calls + failed_calls, 1)) * 100:.1f}%"
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Campaign.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
