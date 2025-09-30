# 🤖 AI Call System - Autonomous Agent Calling Platform

A comprehensive Django-based AI-powered call handling system with **fully autonomous agent capabilities** that can make calls and handle entire conversations without any human intervention.

## ⚡ Key Features

### 🎯 **Autonomous AI Agent Calls (Zero Human Interaction)**
- **Fully autonomous outbound calling** - No human involvement required
- **AI handles entire conversations** - From greeting to closing
- **Real-time decision making** during calls
- **Automatic follow-up scheduling** and CRM updates
- **24/7 operation** with infinite scalability
- **Multiple call purposes**: sales, support, demos, renewals, surveys

### 📞 **Advanced Call Management**
- Inbound and outbound call handling
- Twilio integration for telephony services
- Real-time call monitoring and analytics
- Call recording and transcription
- Queue management with priority handling
- Background processing with Celery

### 👥 **Comprehensive CRM System**
- Complete contact management
- Interaction history and detailed notes
- Lead tracking and automated scoring
- Contact import/export capabilities
- Advanced search and filtering
- AI-powered contact insights

### 🧠 **AI Integration & Analytics**
- OpenAI integration for natural conversations
- Real-time sentiment analysis
- Intelligent conversation routing
- Automated call summarization
- Performance analytics and insights
- Predictive outcome modeling

### 📅 **Campaign & Scheduling Management**
- Bulk calling campaigns
- Scheduled call sequences
- Campaign performance tracking
- A/B testing capabilities
- ROI analysis and reporting
- Webhook and API triggers

### Advanced Features
- **Twilio Integration**: Production-ready telephony via Twilio
- **Campaign Management**: Organize calls into campaigns
- **Analytics Dashboard**: Comprehensive reporting and metrics
- **Webhook Support**: Real-time call status updates
- **Background Processing**: Celery-powered async task processing

## 📁 Project Structure

```
ai_call_system/
├── ai_call_system/          # Django project settings
│   ├── settings.py          # Main configuration
│   ├── urls.py             # URL routing
│   ├── celery.py           # Celery configuration
│   └── health_urls.py      # Health check endpoints
├── calls/                   # Call management app
│   ├── models.py           # Call, Queue, Template models
│   ├── views.py            # API endpoints
│   ├── tasks.py            # Background tasks
│   ├── webhook_views.py    # Twilio webhooks
│   └── services/
│       └── twilio_service.py # Twilio integration
├── crm/                    # Customer relationship management
│   ├── models.py          # Contact, Note, Tag models
│   └── management/
│       └── commands/
│           └── import_contacts.py # CSV import
├── ai_integration/         # AI service integration
│   ├── models.py          # AI providers, conversations
│   └── services/
│       └── ai_service.py  # OpenAI integration
├── scheduling/            # Campaign and scheduling
│   └── models.py         # Campaign, Schedule models
└── requirements.txt      # Python dependencies
```

## 🛠️ Installation & Setup

### 1. Environment Setup

```powershell
# Clone the project (if from repository)
git clone <repository-url>
cd ai_call_system

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env` file and configure your settings:

```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://username:password@localhost:5432/ai_call_system

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```powershell
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Start Services

#### Terminal 1 - Django Server
```powershell
python manage.py runserver
```

#### Terminal 2 - Celery Worker
```powershell
celery -A ai_call_system worker --loglevel=info
```

#### Terminal 3 - Celery Beat Scheduler
```powershell
celery -A ai_call_system beat --loglevel=info
```

## 🔧 Configuration

### Twilio Webhook URLs

Configure these URLs in your Twilio console:

```
Voice URL: https://yourdomain.com/webhooks/twilio/voice/
Status Callback: https://yourdomain.com/webhooks/twilio/call-status/
Recording Callback: https://yourdomain.com/webhooks/twilio/recording/
```

### AI Templates

Create call templates via Django admin or API:

```python
# Example call template
{
    "name": "Sales Outreach",
    "template_type": "sales",
    "initial_greeting": "Hi {contact.first_name}, I'm calling about our special offer...",
    "conversation_flow": {
        "intro": "Tell me about your current needs",
        "qualification": "What's your budget range?",
        "close": "Would you like to schedule a demo?"
    }
}
```

## 📡 API Endpoints

### Calls Management
- `GET /api/v1/calls/` - List all calls
- `POST /api/v1/calls/initiate/` - Start outbound call
- `POST /api/v1/calls/bulk-call/` - Bulk call initiation
- `GET /api/v1/calls/analytics/dashboard/` - Call analytics

### CRM Operations  
- `GET /api/v1/crm/contacts/` - List contacts
- `POST /api/v1/crm/contacts/` - Create contact
- `POST /api/v1/crm/contacts/import/` - Import from CSV
- `GET /api/v1/crm/contacts/{id}/calls/` - Contact call history

### Campaign Management
- `GET /api/v1/scheduling/campaigns/` - List campaigns
- `POST /api/v1/scheduling/campaigns/` - Create campaign
- `POST /api/v1/scheduling/campaigns/{id}/start/` - Start campaign

### AI Integration
- `POST /api/v1/ai/chat/` - AI chat endpoint
- `GET /api/v1/ai/templates/` - List AI templates
- `GET /api/v1/ai/analytics/dashboard/` - AI usage analytics

## 💼 Usage Examples

### 1. Import Contacts

```powershell
python manage.py import_contacts contacts.csv --skip-duplicates
```

CSV Format:
```csv
first_name,last_name,phone_number,email,company,contact_type
John,Doe,+1234567890,john@example.com,Acme Inc,lead
Jane,Smith,+0987654321,jane@example.com,Widget Corp,customer
```

### 2. Schedule Bulk Campaign

```python
# API call to create campaign
POST /api/v1/scheduling/campaigns/
{
    "name": "Q4 Sales Outreach",
    "campaign_type": "bulk_calls",
    "start_date": "2024-01-01T09:00:00Z",
    "call_template": "template_id",
    "target_contacts": ["contact_id_1", "contact_id_2"]
}
```

### 3. Process Call Queue

```powershell
# Manual queue processing
python manage.py process_call_queue --limit 50

# Or via API
POST /api/v1/calls/queue/process/
```

## 🚀 **How Autonomous Calling Works**

The AI agent can call users completely autonomously:

### 1. **Trigger Methods (No Human Required)**
```python
# Programmatic trigger
from calls.autonomous_agent import trigger_sales_outreach_call
task = trigger_sales_outreach_call(contact_id, context)

# API trigger
POST /calls/api/calls/trigger_autonomous_call/
{
    "contact_id": "uuid",
    "call_purpose": "sales_outreach",
    "context": {"product": "Cloud Solutions"}
}

# Webhook trigger (automatic from user actions)
# Schedule trigger (time-based automation)
```

### 2. **Autonomous Conversation Flow**
```
AI Agent: "Hi, this is Alex from TechSolutions. Am I speaking with John?"
Human: "Yes, what's this about?"
AI Agent: "I'm reaching out about cloud infrastructure solutions..."
[AI analyzes response, adapts conversation in real-time]
Human: "We are looking to upgrade our infrastructure."
[AI detects interest, shifts to discovery mode]
AI Agent: "Perfect! What challenges are you facing currently?"
[Conversation continues autonomously until objective achieved]
```

### 3. **Automatic Actions After Call**
- ✅ Schedule follow-up meetings/demos
- ✅ Update CRM records and lead status
- ✅ Create detailed call notes
- ✅ Send emails and calendar invites
- ✅ Trigger additional workflows
- ✅ Notify sales teams

## 💻 **Technology Stack**

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Message Queue**: Celery with Redis
- **Telephony**: Twilio Voice API
- **AI**: OpenAI GPT models
- **Background Processing**: Celery workers
- **API**: RESTful endpoints for integration
- **Deployment**: Docker-ready with production configs

## 🚀 **Quick Start**

### Prerequisites
- Python 3.11+
- Redis server
- Twilio account with phone number
- OpenAI API key

### Installation

1. **Clone and setup:**
```bash
git clone https://github.com/yourusername/ai-call-system.git
cd ai-call-system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment (.env):**
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key

# Database & Redis
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

3. **Initialize and run:**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# In separate terminal for background tasks
celery -A ai_call_system worker -l info
```

4. **Test autonomous calling:**
```bash
python autonomous_demo_simple.py
```

## 📖 **Usage Examples**

### **Single Autonomous Call**
```python
from calls.autonomous_agent import trigger_sales_outreach_call

# AI agent will call user autonomously
task = trigger_sales_outreach_call(
    contact_id="user-uuid",
    context={
        'product_interest': 'Cloud Solutions',
        'budget_range': '$10k-50k',
        'urgency': 'high'
    }
)
```

### **Campaign Calls via API**
```bash
curl -X POST http://yourapi.com/calls/api/calls/trigger_campaign_calls/ \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "campaign-uuid",
    "call_purpose": "product_demo",
    "stagger_minutes": 15
  }'
```

### **Bulk Autonomous Calls**
```bash
curl -X POST http://yourapi.com/calls/api/calls/bulk_autonomous_calls/ \
  -d '{
    "calls": [
        {
            "contact_id": "uuid1",
            "call_purpose": "follow_up",
            "delay_minutes": 0
        },
        {
            "contact_id": "uuid2",
            "call_purpose": "customer_support", 
            "delay_minutes": 10
        }
    ]
  }'
```

## 📚 **Documentation**

- **[🤖 Autonomous Calling Guide](AUTONOMOUS_CALLING_GUIDE.md)** - Complete guide to autonomous AI agent calls
- **[📋 Project Summary](PROJECT_SUMMARY.md)** - Detailed project overview and architecture
- **[⚙️ Copilot Instructions](.github/copilot-instructions.md)** - Development guidelines and patterns

## 🎯 **Call Types Supported**

| Call Type | Purpose | Autonomous Actions |
|-----------|---------|-------------------|
| **Sales Outreach** | Initial contact & qualification | Demo scheduling, lead scoring |
| **Follow-up Calls** | Continue conversations | Proposal scheduling, objection handling |
| **Product Demos** | Scheduled presentations | Meeting setup, material sending |
| **Customer Support** | Proactive issue resolution | Ticket creation, escalation |
| **Appointment Booking** | Meeting scheduling | Calendar integration, reminders |
| **Renewal Reminders** | Contract renewals | Negotiation scheduling, terms discussion |
| **Surveys** | Feedback collection | Data analysis, reporting |

## 🔧 **API Endpoints**

### **Autonomous Call Triggers**
- `POST /calls/api/calls/trigger_autonomous_call/` - Single autonomous call
- `POST /calls/api/calls/bulk_autonomous_calls/` - Multiple calls
- `POST /calls/api/calls/trigger_campaign_calls/` - Campaign calls
- `GET /calls/api/calls/autonomous_call_status/` - Call status monitoring

### **Webhook Integration**
- `POST /webhooks/twilio/autonomous-agent/` - Twilio webhook handler
- Auto-triggers from user actions (form submissions, CRM events, etc.)

## 🌟 **Key Advantages**

- **🚀 Zero Human Involvement** - Completely autonomous operation
- **⏰ 24/7 Operation** - Works around the clock, no breaks
- **📈 Infinite Scalability** - Handle thousands of calls simultaneously  
- **🎯 Perfect Consistency** - Same quality every call, no bad days
- **📊 Data-Driven** - Every decision based on real-time analysis
- **💰 Cost Effective** - Fraction of human agent costs
- **⚡ Instant Follow-up** - Actions taken immediately after calls
- **🌍 Multi-language** - Can handle any language needed

## 🔄 **Production Deployment**

### **Docker Deployment**
```bash
docker-compose up -d
```

### **Environment Configuration**
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgres://user:pass@localhost:5432/ai_call_system
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
OPENAI_API_KEY=your_openai_key
REDIS_URL=redis://localhost:6379/0
```

### **Production Checklist**
- ✅ Configure Twilio phone numbers and webhooks
- ✅ Set up OpenAI API keys with sufficient credits
- ✅ Deploy with Redis and Celery workers
- ✅ Configure production database (PostgreSQL)
- ✅ Set up monitoring and logging
- ✅ Test with real phone numbers

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-call-system/issues)
- **Documentation**: [Full Documentation](AUTONOMOUS_CALLING_GUIDE.md)
- **Demos**: Run `python autonomous_demo_simple.py` for live demonstration

## 🗺️ **Roadmap**

- [ ] Multi-language AI conversation support
- [ ] Advanced AI training and customization
- [ ] Video calling integration (Twilio Video)
- [ ] Advanced analytics dashboard
- [ ] Mobile app for monitoring
- [ ] Third-party CRM integrations (Salesforce, HubSpot)
- [ ] Voice cloning and custom AI voices
- [ ] Real-time conversation coaching
- [ ] Advanced lead scoring algorithms
- [ ] Integration with marketing automation platforms

---

## 🧪 Testing the System

### Core API Testing (No Redis Required)

Test authentication, API endpoints, and CRUD operations:

```bash
python test_api_flow.py
```

**Features Tested:**
- ✅ JWT Authentication & Authorization
- ✅ Protected API Endpoints (CRM, Calls, Campaigns, AI)
- ✅ CRUD Operations with Validation
- ✅ Role-based Access Control

### Full Autonomous Calling Test (Requires Redis)

For complete autonomous calling functionality:

1. **Install and start Redis server**
2. **Start Celery worker:**
   ```bash
   celery -A ai_call_system worker --loglevel=info
   ```
3. **Run complete test:**
   ```bash
   python test_complete_flow.py
   ```

**Additional Features Tested:**
- ✅ Autonomous AI Agent Calls
- ✅ Background Task Processing  
- ✅ Real-time Call Queue Management
- ✅ Full Calling Workflow Automation

## 🎉 **Ready to Start?**

Your autonomous AI calling system is ready to make calls that handle everything automatically!

```bash
# Start the development server 
python manage.py runserver --settings=ai_call_system.settings

# Admin interface
# Visit: http://127.0.0.1:8000/admin

# API endpoints
# Visit: http://127.0.0.1:8000/api/v1/
```

### Key Endpoints:

- **Authentication:** `/auth/jwt/login/`, `/auth/register/`
- **CRM:** `/api/v1/crm/contacts/`, `/api/v1/crm/notes/` 
- **Calls:** `/api/v1/calls/api/calls/`, `/api/v1/calls/api/call-queue/`
- **Campaigns:** `/api/v1/scheduling/campaigns/`
- **AI:** `/api/v1/ai/conversations/`, `/api/v1/ai/messages/`

**🚀 The future of calling is autonomous - no humans required!**
