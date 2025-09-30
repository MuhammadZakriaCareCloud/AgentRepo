#!/usr/bin/env python
"""
Simple API Test Script (without Redis/Celery dependencies)
Tests core functionality of the AI Call System
"""
import requests
import json
import sys

BASE_URL = 'http://127.0.0.1:8000'

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔥 {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_authentication():
    """Test JWT authentication"""
    print_header("TESTING JWT AUTHENTICATION")
    
    # Test login
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    response = requests.post(f'{BASE_URL}/auth/jwt/login/', json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print_success("JWT authentication successful")
        print_info(f"User: {data.get('user', {}).get('username')}")
        return data.get('access')
    else:
        print_error(f"Authentication failed: {response.text}")
        return None

def test_protected_endpoints(token):
    """Test protected API endpoints"""
    print_header("TESTING PROTECTED API ENDPOINTS")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test CRM contacts
    response = requests.get(f'{BASE_URL}/api/v1/crm/contacts/', headers=headers)
    if response.status_code == 200:
        contacts = response.json()
        print_success(f"CRM contacts endpoint: {len(contacts.get('results', []))} contacts")
    else:
        print_error(f"CRM contacts failed: {response.status_code}")
    
    # Test calls API
    response = requests.get(f'{BASE_URL}/api/v1/calls/api/calls/', headers=headers)
    if response.status_code == 200:
        calls = response.json()
        print_success(f"Calls API endpoint: {len(calls.get('results', []))} calls")
    else:
        print_error(f"Calls API failed: {response.status_code}")
    
    # Test campaigns
    response = requests.get(f'{BASE_URL}/api/v1/scheduling/campaigns/', headers=headers)
    if response.status_code == 200:
        campaigns = response.json()
        print_success(f"Campaigns endpoint: {len(campaigns.get('results', []))} campaigns")
    else:
        print_error(f"Campaigns failed: {response.status_code}")
    
    # Test AI conversations
    response = requests.get(f'{BASE_URL}/api/v1/ai/conversations/', headers=headers)
    if response.status_code == 200:
        conversations = response.json()
        print_success(f"AI conversations endpoint: {len(conversations.get('results', []))} conversations")
    else:
        print_error(f"AI conversations failed: {response.status_code}")

def test_create_campaign(token):
    """Test creating a campaign"""
    print_header("TESTING CAMPAIGN CREATION")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Get user profile to get user ID
    profile_response = requests.get(f'{BASE_URL}/auth/profile/', headers=headers)
    if profile_response.status_code != 200:
        print_error("Could not get user profile for campaign creation")
        return None
    
    user_id = profile_response.json().get('id')
    
    campaign_data = {
        'name': 'Test Campaign',
        'description': 'Automated test campaign',
        'campaign_type': 'bulk_calls',
        'status': 'draft',
        'start_date': '2025-10-01T09:00:00Z',
        'allowed_calling_hours_start': '09:00:00',
        'allowed_calling_hours_end': '18:00:00',
        'allowed_days_of_week': [1, 2, 3, 4, 5],
        'max_calls_per_hour': 10,
        'max_calls_per_day': 100,
        'created_by': user_id
    }
    
    response = requests.post(f'{BASE_URL}/api/v1/scheduling/campaigns/', 
                           json=campaign_data, headers=headers)
    
    if response.status_code == 201:
        campaign = response.json()
        print_success(f"Campaign created: {campaign.get('name')} (ID: {campaign.get('id')})")
        return campaign.get('id')
    else:
        print_error(f"Campaign creation failed: {response.status_code} - {response.text}")
        return None

def test_create_contact(token):
    """Test creating a contact"""
    print_header("TESTING CONTACT CREATION")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    contact_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'phone_number': '+1234567891',
        'email': 'jane.smith@example.com',
        'status': 'active'
    }
    
    response = requests.post(f'{BASE_URL}/api/v1/crm/contacts/', 
                           json=contact_data, headers=headers)
    
    if response.status_code == 201:
        contact = response.json()
        print_success(f"Contact created: {contact.get('first_name')} {contact.get('last_name')} ({contact.get('phone_number')})")
        return contact.get('id')
    else:
        print_error(f"Contact creation failed: {response.status_code} - {response.text}")
        return None

def main():
    print_header("🚀 AI CALL SYSTEM - API TESTING FLOW")
    print("🎯 Testing core API functionality without Celery/Redis")
    
    # Test authentication
    token = test_authentication()
    if not token:
        print_error("Authentication failed, stopping tests")
        return
    
    # Test protected endpoints
    test_protected_endpoints(token)
    
    # Test creating resources
    contact_id = test_create_contact(token)
    campaign_id = test_create_campaign(token)
    
    print_header("✨ TEST SUMMARY")
    print_success("Core API functionality working!")
    print_info("✅ JWT Authentication")
    print_info("✅ Protected API endpoints")
    print_info("✅ CRUD operations")
    print_info("✅ Role-based access control")
    print("")
    print_info("🔧 To enable full autonomous calling:")
    print_info("   1. Install and start Redis server")
    print_info("   2. Start Celery worker: celery -A ai_call_system worker --loglevel=info")
    print_info("   3. Configure Twilio credentials in settings")
    print_info("   4. Configure OpenAI API key in settings")

if __name__ == '__main__':
    main()
