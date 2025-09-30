# 🚀 AI Call System - Complete Setup & Deployment Guide

## 📋 System Overview

The AI Call System is a fully autonomous Django-based calling platform that integrates:

- **🤖 Autonomous AI Calls** - Fully automated agent calls with no human intervention
- **📞 Twilio Integration** - Professional telephony services
- **🧠 OpenAI Integration** - Advanced conversational AI
- **👥 CRM System** - Complete contact management
- **📅 Campaign Management** - Bulk calling and scheduling
- **🔐 JWT & OAuth Authentication** - Secure API access
- **⚡ Celery Background Tasks** - Scalable async processing

## ✅ Prerequisites

- Python 3.8+
- Django 5.0+
- Redis Server (for background tasks)
- PostgreSQL (for production) or SQLite (for development)
- Twilio Account with phone number
- OpenAI API Key

## 🔧 Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/ai-call-system.git
cd ai-call-system
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file:

```env
# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start Development Servers

#### Terminal 1 - Django Server
```bash
python manage.py runserver --settings=ai_call_system.settings
```

#### Terminal 2 - Redis Server
```bash
redis-server
```

#### Terminal 3 - Celery Worker
```bash
celery -A ai_call_system worker --loglevel=info
```

#### Terminal 4 - Celery Beat (Optional - for scheduled tasks)
```bash
celery -A ai_call_system beat --loglevel=info
```

## 🧪 Testing the System

### Quick API Test (No Redis Required)
```bash
python test_api_flow.py
```

### Full Autonomous Calling Test (Redis Required)
```bash
python test_complete_flow.py
```

## 🌐 Production Deployment

### 1. Server Requirements

- **CPU:** 2+ cores
- **RAM:** 4GB+ 
- **Storage:** 20GB+ SSD
- **OS:** Ubuntu 20.04+ or CentOS 8+

### 2. Production Environment Setup

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql redis-server

# Create application user
sudo useradd -m -s /bin/bash aiapp
sudo su - aiapp

# Clone and setup application
git clone https://github.com/yourusername/ai-call-system.git
cd ai-call-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Production Environment Variables

Create `/home/aiapp/ai-call-system/.env`:

```env
# Django Production Settings
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database - PostgreSQL
DATABASE_URL=postgresql://aiapp:password@localhost:5432/aiapp_db

# Twilio Production
TWILIO_ACCOUNT_SID=your_production_sid
TWILIO_AUTH_TOKEN=your_production_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI Production
OPENAI_API_KEY=your_production_openai_key

# Redis Production
REDIS_URL=redis://localhost:6379/0

# Email (for notifications)
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notifications@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
```

### 4. Database Setup (PostgreSQL)

```bash
sudo -u postgres psql
CREATE DATABASE aiapp_db;
CREATE USER aiapp WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE aiapp_db TO aiapp;
\q

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 5. Systemd Services

Create `/etc/systemd/system/aiapp-django.service`:

```ini
[Unit]
Description=AI Call System Django App
After=network.target

[Service]
Type=notify
User=aiapp
Group=aiapp
RuntimeDirectory=aiapp
WorkingDirectory=/home/aiapp/ai-call-system
Environment=DJANGO_SETTINGS_MODULE=ai_call_system.settings
EnvironmentFile=/home/aiapp/ai-call-system/.env
ExecStart=/home/aiapp/ai-call-system/venv/bin/gunicorn ai_call_system.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/aiapp-celery.service`:

```ini
[Unit]
Description=AI Call System Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=aiapp
Group=aiapp
EnvironmentFile=/home/aiapp/ai-call-system/.env
WorkingDirectory=/home/aiapp/ai-call-system
ExecStart=/home/aiapp/ai-call-system/venv/bin/celery -A ai_call_system worker --detach --loglevel=info
ExecStop=/home/aiapp/ai-call-system/venv/bin/celery -A ai_call_system control shutdown
ExecReload=/home/aiapp/ai-call-system/venv/bin/celery -A ai_call_system control reload

[Install]
WantedBy=multi-user.target
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/aiapp`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/aiapp/ai-call-system;
    }
    
    location /media/ {
        root /home/aiapp/ai-call-system;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/aiapp/aiapp.sock;
    }
}
```

### 7. SSL/TLS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 8. Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable aiapp-django aiapp-celery nginx redis-server postgresql
sudo systemctl start aiapp-django aiapp-celery nginx redis-server postgresql
sudo systemctl status aiapp-django aiapp-celery
```

## 📊 Monitoring & Maintenance

### Log Files
- Django: `/var/log/aiapp/django.log`
- Celery: `/var/log/aiapp/celery.log`  
- Nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

### Health Checks
```bash
# Check application status
curl https://yourdomain.com/health/

# Check services
sudo systemctl status aiapp-django aiapp-celery nginx redis-server postgresql
```

### Database Backup
```bash
# Daily backup script
#!/bin/bash
pg_dump aiapp_db > /backups/aiapp_db_$(date +%Y%m%d).sql
find /backups -name "*.sql" -mtime +7 -delete
```

## 🔒 Security Checklist

- [ ] Strong SECRET_KEY in production
- [ ] DEBUG=False in production
- [ ] HTTPS/SSL certificate installed
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Database passwords secure
- [ ] API keys stored securely
- [ ] Twilio webhook signatures validated
- [ ] Rate limiting enabled
- [ ] Regular security updates

## 🚀 Scaling Considerations

### High Availability
- Load balancer (nginx/HAProxy)
- Multiple Django instances
- Redis Cluster
- PostgreSQL replication
- Celery worker scaling

### Performance Optimization
- Database indexing
- Redis caching
- CDN for static files
- Connection pooling
- Celery task optimization

## 📞 Twilio Webhook Configuration

In your Twilio Console, configure:

**Phone Number Webhooks:**
- Voice URL: `https://yourdomain.com/webhooks/twilio/voice/`
- Voice Method: `POST`
- Status Callback: `https://yourdomain.com/webhooks/twilio/call-status/`

## 🎯 Usage Examples

### Creating an Autonomous Campaign

```python
import requests

# Authenticate
response = requests.post('https://yourdomain.com/auth/jwt/login/', {
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['access']

# Create campaign
campaign_data = {
    'name': 'Sales Outreach Q4',
    'campaign_type': 'bulk_calls',
    'start_date': '2025-10-01T09:00:00Z',
    'max_calls_per_hour': 50,
    'created_by': 1
}

response = requests.post(
    'https://yourdomain.com/api/v1/scheduling/campaigns/',
    json=campaign_data,
    headers={'Authorization': f'Bearer {token}'}
)
```

## 🆘 Troubleshooting

### Common Issues

**Database Connection Error:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
# Check connection settings in .env
```

**Celery Tasks Not Running:**
```bash
# Check Redis connection
redis-cli ping
# Check Celery worker status
sudo systemctl status aiapp-celery
```

**API Authentication Issues:**
```bash
# Verify JWT settings in Django admin
# Check token expiration settings
```

**Twilio Webhook Failures:**
```bash
# Check webhook URL accessibility
curl -X POST https://yourdomain.com/webhooks/twilio/voice/
# Verify webhook signature validation
```

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Celery Production Best Practices](https://docs.celeryproject.org/en/stable/userguide/deploying.html)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

**🎉 Congratulations! Your AI Call System is now fully deployed and ready for autonomous calling operations!**
