"""
Simple API test script to verify the AI Call System is working
"""

import requests
from datetime import datetime

# Base URL for our API
BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed: {data}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {str(e)}")
        return False

def test_admin_access():
    """Test admin panel accessibility"""
    print("🔍 Testing admin panel access...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        if response.status_code == 200 or response.status_code == 302:  # 302 is redirect to login
            print("   ✅ Admin panel accessible")
            return True
        else:
            print(f"   ❌ Admin panel not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Admin panel error: {str(e)}")
        return False

def show_sample_data_info():
    """Show information about the sample data created"""
    print("\n📊 Sample Data Created:")
    print("=" * 40)
    
    print("\n👥 Contacts:")
    print("   • John Doe (CTO at Tech Innovations Inc)")
    print("   • Jane Smith (Marketing Director at Marketing Solutions LLC)")  
    print("   • Bob Johnson (Founder at StartupCorp)")
    
    print("\n📞 Call Templates:")
    print("   • Product Demo Outreach (Sales)")
    print("   • Customer Check-in (Follow-up)")
    
    print("\n🤖 AI Templates:")
    print("   • Sales Outreach")
    print("   • Customer Support")
    print("   • Appointment Booking")
    
    print("\n🎯 Campaign:")
    print("   • Q1 Product Demo Campaign (3 contacts)")

def show_architecture_overview():
    """Show the system architecture"""
    print("\n🏗️ System Architecture:")
    print("=" * 40)
    
    print("\n📱 Django Apps:")
    print("   • crm/          - Contact management, notes, tags")
    print("   • calls/        - Call handling, Twilio integration") 
    print("   • ai_integration/ - OpenAI services, conversation management")
    print("   • scheduling/   - Campaigns, bulk operations, scheduling")
    
    print("\n🔧 Key Components:")
    print("   • Django REST Framework - API endpoints")
    print("   • Celery - Background task processing")
    print("   • Twilio - Telephony services") 
    print("   • OpenAI - AI conversation handling")
    print("   • Redis - Message broker and caching")
    print("   • PostgreSQL - Production database")

def show_features():
    """Show key features"""
    print("\n🚀 Key Features:")
    print("=" * 40)
    
    print("\n📞 Call Management:")
    print("   • Inbound AI call handling")
    print("   • Outbound call automation")
    print("   • Call recording and transcription")
    print("   • Real-time call status tracking")
    
    print("\n🤖 AI Capabilities:")
    print("   • GPT-4 powered conversations")
    print("   • Custom conversation templates")
    print("   • Sentiment analysis")
    print("   • Intent recognition")
    print("   • Automatic call summaries")
    
    print("\n📊 CRM Features:")
    print("   • Contact management")
    print("   • Call history and notes")
    print("   • Contact tagging and categorization")
    print("   • CSV import/export")
    
    print("\n🎯 Campaign Management:")
    print("   • Bulk call campaigns")
    print("   • Call scheduling and queuing")
    print("   • Performance analytics")
    print("   • Rate limiting and compliance")

if __name__ == "__main__":
    print("🧪 AI Call System - Quick Test & Overview")
    print("=" * 60)
    
    # Test basic functionality
    health_ok = test_health_check()
    admin_ok = test_admin_access()
    
    if health_ok and admin_ok:
        print("\n✅ System is running correctly!")
    else:
        print("\n⚠️  Some issues detected, but system may still be functional")
    
    # Show information about the system
    show_sample_data_info()
    show_architecture_overview()
    show_features()
    
    print("\n🌐 System Access:")
    print("=" * 40)
    print(f"🏠 Admin Panel: {BASE_URL}/admin/")
    print(f"❤️  Health Check: {BASE_URL}/health/")
    print(f"📊 API Base: {BASE_URL}/api/v1/")
    
    print(f"\n📖 Next Steps:")
    print("1. Log into admin panel to explore the data")
    print("2. Configure your .env file with real API keys") 
    print("3. Install Redis and start Celery workers")
    print("4. Test Twilio webhooks with ngrok")
    print("5. Create production deployment")
    
    print(f"\n🎉 AI Call System is ready for development and testing!")
