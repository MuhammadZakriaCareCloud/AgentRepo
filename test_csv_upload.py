#!/usr/bin/env python
"""
CSV Upload Test Script
Tests CSV upload functionality for contacts and knowledge base
"""
import requests
import json
import os

BASE_URL = 'http://127.0.0.1:8000'

def get_auth_token():
    """Get authentication token"""
    
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    response = requests.post(f'{BASE_URL}/auth/jwt/login/', json=login_data)
    
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"❌ Authentication failed: {response.text}")
        return None

def test_csv_contacts_upload(token):
    """Test CSV contacts upload"""
    
    print("📋 Testing CSV Contacts Upload...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Upload sample contacts CSV
    with open('sample_contacts.csv', 'rb') as csv_file:
        files = {'csv_file': csv_file}
        data = {
            'campaign_name': 'CSV Upload Test Campaign',
            'agent_preference': 'Ali Khan',
            'priority': 'high'
        }
        
        response = requests.post(
            f'{BASE_URL}/api/v1/calls/csv/upload-contacts/',
            headers=headers,
            files=files,
            data=data
        )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ CSV Upload Successful!")
        print(f"   📊 Campaign: {result['data']['campaign_name']}")
        print(f"   👥 Created Contacts: {result['data']['created_contacts']}")
        print(f"   🔄 Updated Contacts: {result['data']['updated_contacts']}")
        print(f"   ❌ Errors: {result['data']['error_count']}")
        
        if result['data']['errors']:
            print("   📝 Error Details:")
            for error in result['data']['errors']:
                print(f"      • {error}")
        
        return result['data']['campaign_id']
    else:
        print(f"❌ CSV Upload Failed: {response.status_code}")
        print(f"   📝 Error: {response.text}")
        return None

def test_knowledge_base_upload(token):
    """Test knowledge base CSV upload"""
    
    print("\n🧠 Testing Knowledge Base Upload...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Upload sample knowledge base CSV
    with open('sample_knowledge_base.csv', 'rb') as csv_file:
        files = {'csv_file': csv_file}
        
        response = requests.post(
            f'{BASE_URL}/api/v1/calls/csv/upload-knowledge/',
            headers=headers,
            files=files
        )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Knowledge Base Upload Successful!")
        print(f"   📚 Templates Created: {result['data']['created_templates']}")
        print(f"   ❌ Errors: {result['data']['error_count']}")
        
        print("   📖 Knowledge Topics:")
        for template in result['data']['template_names']:
            print(f"      • {template}")
        
        return True
    else:
        print(f"❌ Knowledge Base Upload Failed: {response.status_code}")
        print(f"   📝 Error: {response.text}")
        return False

def test_queue_campaign_calls(token, campaign_id):
    """Test queuing calls for campaign"""
    
    print(f"\n📞 Testing Campaign Call Queueing...")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    data = {
        'agent_name': 'Ali Khan'
    }
    
    response = requests.post(
        f'{BASE_URL}/api/v1/calls/csv/campaign/{campaign_id}/queue-calls/',
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Calls Queued Successfully!")
        print(f"   📊 Campaign: {result['data']['campaign_name']}")
        print(f"   🤖 Agent: {result['data']['agent_name']}")
        print(f"   📞 Queued Calls: {result['data']['queued_calls']}")
        
        print("   📋 Call List:")
        for call in result['data']['calls']:
            print(f"      • {call['agent_name']} → {call['contact_name']} ({call['phone_number']})")
        
        return True
    else:
        print(f"❌ Call Queueing Failed: {response.status_code}")
        print(f"   📝 Error: {response.text}")
        return False

def test_campaign_status(token, campaign_id):
    """Test campaign status check"""
    
    print(f"\n📊 Testing Campaign Status...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(
        f'{BASE_URL}/api/v1/calls/csv/campaign/{campaign_id}/status/',
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Campaign Status Retrieved!")
        print(f"   📊 Campaign: {result['data']['campaign']['name']}")
        print(f"   📅 Created: {result['data']['campaign']['created_at']}")
        print(f"   📈 Status: {result['data']['campaign']['status']}")
        
        print(f"   👥 Contacts:")
        print(f"      • Total: {result['data']['contacts']['total']}")
        print(f"      • Pending: {result['data']['contacts']['pending']}")
        print(f"      • Completed: {result['data']['contacts']['completed']}")
        
        print(f"   📞 Calls:")
        print(f"      • Pending: {result['data']['calls']['pending']}")
        print(f"      • In Progress: {result['data']['calls']['in_progress']}")
        print(f"      • Completed: {result['data']['calls']['completed']}")
        print(f"      • Failed: {result['data']['calls']['failed']}")
        
        print(f"   📈 Progress:")
        print(f"      • Completion Rate: {result['data']['progress']['completion_rate']}")
        print(f"      • Success Rate: {result['data']['progress']['success_rate']}")
        
        return True
    else:
        print(f"❌ Status Check Failed: {response.status_code}")
        print(f"   📝 Error: {response.text}")
        return False

def main():
    """Main test function"""
    
    print("🚀 CSV UPLOAD & KNOWLEDGE BASE TEST")
    print("=" * 60)
    
    # Check if CSV files exist
    if not os.path.exists('sample_contacts.csv'):
        print("❌ sample_contacts.csv not found!")
        return
    
    if not os.path.exists('sample_knowledge_base.csv'):
        print("❌ sample_knowledge_base.csv not found!")
        return
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed, stopping tests")
        return
    
    print("✅ Authentication successful")
    
    # Test CSV contacts upload
    campaign_id = test_csv_contacts_upload(token)
    
    if campaign_id:
        # Test knowledge base upload
        kb_success = test_knowledge_base_upload(token)
        
        # Test campaign call queueing
        queue_success = test_queue_campaign_calls(token, campaign_id)
        
        # Test campaign status
        status_success = test_campaign_status(token, campaign_id)
        
        print("\n" + "=" * 60)
        print("🎉 CSV UPLOAD TEST SUMMARY")
        print("=" * 60)
        print(f"✅ CSV Contacts Upload: {'SUCCESS' if campaign_id else 'FAILED'}")
        print(f"✅ Knowledge Base Upload: {'SUCCESS' if kb_success else 'FAILED'}")
        print(f"✅ Call Queue Creation: {'SUCCESS' if queue_success else 'FAILED'}")
        print(f"✅ Campaign Status Check: {'SUCCESS' if status_success else 'FAILED'}")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Check admin panel: http://127.0.0.1:8000/admin")
        print(f"2. View campaign: Campaign ID {campaign_id}")
        print(f"3. Start Celery worker to process calls:")
        print(f"   celery -A ai_call_system worker --loglevel=info")
        print(f"4. Monitor call queue: /api/v1/calls/api/call-queue/")
        
        print(f"\n🤖 Your AI agents now have:")
        print(f"   • 10 new contacts from CSV")
        print(f"   • 10 knowledge base topics")
        print(f"   • Queued outbound calls")
        print(f"   • Agent preference: Ali Khan")
    
    else:
        print("❌ CSV upload failed, skipping other tests")

if __name__ == '__main__':
    main()
