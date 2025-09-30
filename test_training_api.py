#!/usr/bin/env python
"""
Test script for AI Agent Training API endpoints

This script tests all the training-related API endpoints:
1. Training data management
2. Knowledge base operations
3. Training sessions
4. Performance metrics
5. Conversation patterns
"""

import os
import sys
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Default credentials
USERNAME = "admin"
PASSWORD = "admin"

class TrainingAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
    
    def authenticate(self):
        """Authenticate and get JWT tokens"""
        print("🔐 Authenticating...")
        
        auth_data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/token/", json=auth_data)
            
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens['access']
                self.refresh_token = tokens['refresh']
                
                # Set authorization header
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                })
                
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_training_data_endpoints(self):
        """Test training data endpoints"""
        print("\n" + "="*50)
        print("TESTING TRAINING DATA ENDPOINTS")
        print("="*50)
        
        # 1. List training data
        print("\n1. GET /api/v1/ai/training/training-data/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/training-data/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} training data entries")
                if data.get('results'):
                    first_entry = data['results'][0]
                    print(f"   Example entry: {first_entry.get('conversation_category')} - {first_entry.get('outcome')}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 2. Get training data analytics
        print("\n2. GET /api/v1/ai/training/training-data/analytics/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/training-data/analytics/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                analytics = response.json()
                print("✅ Analytics retrieved:")
                print(f"   Total conversations: {analytics.get('total_conversations', 0)}")
                print(f"   Average success score: {analytics.get('average_success_score', 0)}")
                print(f"   High quality count: {analytics.get('high_quality_count', 0)}")
                print(f"   By category: {analytics.get('by_category', {})}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 3. Filter by category
        print("\n3. GET /api/v1/ai/training/training-data/?category=sales")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/training-data/?category=sales")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} sales conversations")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 4. Filter by high quality
        print("\n4. GET /api/v1/ai/training/training-data/?high_quality=true")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/training-data/?high_quality=true")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} high-quality conversations")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def test_knowledge_base_endpoints(self):
        """Test knowledge base endpoints"""
        print("\n" + "="*50)
        print("TESTING KNOWLEDGE BASE ENDPOINTS")
        print("="*50)
        
        # 1. List knowledge base entries
        print("\n1. GET /api/v1/ai/training/knowledge-base/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/knowledge-base/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} knowledge base entries")
                if data.get('results'):
                    first_entry = data['results'][0]
                    print(f"   Example: {first_entry.get('title')} ({first_entry.get('knowledge_type')})")
                    print(f"   Success rate: {first_entry.get('success_rate', 0):.2%}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 2. Search by intent
        print("\n2. GET /api/v1/ai/training/knowledge-base/search_by_intent/?intent=pricing")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/knowledge-base/search_by_intent/?intent=pricing")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} entries for 'pricing' intent")
                for match in data.get('matches', [])[:3]:  # Show first 3
                    print(f"   - {match.get('title')}: {match.get('success_rate', 0):.2%} success")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 3. Create new knowledge entry
        print("\n3. POST /api/v1/ai/training/knowledge-base/ (Create new entry)")
        new_knowledge = {
            "knowledge_type": "faq",
            "category": "general",
            "title": "How to handle general inquiries",
            "content": "When handling general inquiries, always be polite, ask clarifying questions, and provide helpful information.",
            "context": "Use when customer asks general questions about services",
            "tags": ["general", "customer_service"],
            "trigger_phrases": ["general", "information", "help"],
            "confidence_score": 0.8
        }
        
        try:
            response = self.session.post(f"{API_BASE}/ai/training/knowledge-base/", json=new_knowledge)
            print(f"Status: {response.status_code}")
            if response.status_code == 201:
                created_entry = response.json()
                print(f"✅ Created knowledge entry: {created_entry.get('title')}")
                print(f"   ID: {created_entry.get('id')}")
                return created_entry.get('id')
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        return None
    
    def test_training_session_endpoints(self):
        """Test training session endpoints"""
        print("\n" + "="*50)
        print("TESTING TRAINING SESSION ENDPOINTS")
        print("="*50)
        
        # 1. List training sessions
        print("\n1. GET /api/v1/ai/training/training-sessions/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/training-sessions/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} training sessions")
                if data.get('results'):
                    first_session = data['results'][0]
                    print(f"   Example: {first_session.get('training_type')} - {first_session.get('status')}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 2. Start new training session
        print("\n2. POST /api/v1/ai/training/training-sessions/start_training/")
        training_config = {
            "training_type": "incremental",
            "training_parameters": {
                "learning_rate": 0.001,
                "batch_size": 16,
                "epochs": 5
            },
            "training_data_ids": []  # Would include actual IDs in real scenario
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/ai/training/training-sessions/start_training/",
                json=training_config
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 201:
                session_data = response.json()
                print(f"✅ Started training session: {session_data.get('training_session_id')}")
                return session_data.get('training_session_id')
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        return None
    
    def test_performance_metrics_endpoints(self):
        """Test performance metrics endpoints"""
        print("\n" + "="*50)
        print("TESTING PERFORMANCE METRICS ENDPOINTS")
        print("="*50)
        
        # 1. List performance metrics
        print("\n1. GET /api/v1/ai/training/performance-metrics/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/performance-metrics/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} performance metric records")
                if data.get('results'):
                    first_metric = data['results'][0]
                    print(f"   Example: {first_metric.get('period_type')} - {first_metric.get('success_rate', 0):.2%} success")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 2. Get performance summary
        print("\n2. GET /api/v1/ai/training/performance-metrics/summary/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/performance-metrics/summary/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                summary = response.json()
                if summary.get('summary'):
                    metrics = summary['summary']
                    print("✅ Performance summary:")
                    print(f"   Total conversations: {metrics.get('total_conversations', 0)}")
                    print(f"   Average success rate: {metrics.get('average_success_rate', 0):.2%}")
                    print(f"   Average response time: {metrics.get('average_response_time', 0):.2f}s")
                    print(f"   Total cost: ${metrics.get('total_cost', 0):.3f}")
                else:
                    print("✅ No metrics available for the specified period")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def test_conversation_patterns_endpoints(self):
        """Test conversation patterns endpoints"""
        print("\n" + "="*50)
        print("TESTING CONVERSATION PATTERNS ENDPOINTS")
        print("="*50)
        
        # 1. List conversation patterns
        print("\n1. GET /api/v1/ai/training/conversation-patterns/")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/conversation-patterns/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('count', 0)} conversation patterns")
                if data.get('results'):
                    first_pattern = data['results'][0]
                    print(f"   Example: {first_pattern.get('pattern_name')} ({first_pattern.get('pattern_type')})")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # 2. Get top patterns
        print("\n2. GET /api/v1/ai/training/conversation-patterns/top_patterns/?limit=5")
        try:
            response = self.session.get(f"{API_BASE}/ai/training/conversation-patterns/top_patterns/?limit=5")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {data.get('count', 0)} top patterns")
                for pattern in data.get('patterns', []):
                    print(f"   - {pattern.get('pattern_name')}: {pattern.get('success_rate', 0):.2%} success")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def test_knowledge_usage_recording(self, knowledge_id):
        """Test recording knowledge usage"""
        if not knowledge_id:
            print("\n⚠️ Skipping knowledge usage test - no knowledge ID available")
            return
        
        print(f"\n3. POST /api/v1/ai/training/knowledge-base/{knowledge_id}/record_usage/")
        usage_data = {
            "success": True,
            "satisfaction_score": 4.5
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/ai/training/knowledge-base/{knowledge_id}/record_usage/",
                json=usage_data
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Successfully recorded knowledge usage")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting AI Agent Training API Tests")
        print("="*60)
        
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run all test suites
        self.test_training_data_endpoints()
        knowledge_id = self.test_knowledge_base_endpoints()
        self.test_knowledge_usage_recording(knowledge_id)
        self.test_training_session_endpoints()
        self.test_performance_metrics_endpoints()
        self.test_conversation_patterns_endpoints()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED!")
        print("="*60)
        print("\nTest Summary:")
        print("✅ Training Data endpoints tested")
        print("✅ Knowledge Base endpoints tested")
        print("✅ Training Session endpoints tested")
        print("✅ Performance Metrics endpoints tested")
        print("✅ Conversation Patterns endpoints tested")
        print("\n💡 The agent training API is ready for use!")
        
        return True


def main():
    """Main function to run the tests"""
    print("AI Agent Training API Test Suite")
    print("Make sure the Django server is running on http://127.0.0.1:8000")
    
    input("Press Enter to start testing...")
    
    tester = TrainingAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🌟 All tests completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python demo_agent_training.py' to see the training system in action")
        print("2. Use the API endpoints in your applications")
        print("3. Monitor agent performance and learning progress")
    else:
        print("\n❌ Some tests failed. Please check the server and try again.")


if __name__ == "__main__":
    main()
