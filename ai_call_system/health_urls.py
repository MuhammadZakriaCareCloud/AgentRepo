from django.urls import path
from django.http import JsonResponse
from django.conf import settings
import redis
from celery import current_app

def health_check(request):
    """Basic health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AI Call System',
        'version': '1.0.0'
    })

def detailed_health_check(request):
    """Detailed health check including dependencies"""
    health_status = {
        'status': 'healthy',
        'service': 'AI Call System',
        'version': '1.0.0',
        'checks': {}
    }
    
    # Check database
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        health_status['checks']['redis'] = 'healthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Celery worker
    try:
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = 'healthy'
        else:
            health_status['checks']['celery'] = 'no workers available'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['celery'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    return JsonResponse(health_status)

urlpatterns = [
    path('', health_check, name='health-check'),
    path('detailed/', detailed_health_check, name='detailed-health-check'),
]
