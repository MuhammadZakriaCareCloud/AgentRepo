import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Middleware to handle JWT authentication for API endpoints"""
    
    def process_request(self, request):
        # Skip authentication for certain paths
        skip_paths = [
            '/admin/',
            '/auth/register/',
            '/auth/jwt/login/',
            '/health/',
            '/webhooks/',
        ]
        
        # Check if path should skip authentication
        for skip_path in skip_paths:
            if request.path.startswith(skip_path):
                return None
        
        # Only process API endpoints
        if not request.path.startswith('/api/'):
            return None
            
        # Try JWT authentication
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result:
                request.user, request.auth = auth_result
                logger.debug(f"JWT authenticated user: {request.user.username}")
        except (InvalidToken, TokenError) as e:
            logger.warning(f"JWT authentication failed: {str(e)}")
            # Don't return error here, let the view handle it
            pass
        
        return None


class APILoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests and responses"""
    
    def process_request(self, request):
        if request.path.startswith('/api/'):
            logger.info(f"API Request: {request.method} {request.path} - User: {getattr(request.user, 'username', 'Anonymous')}")
        return None
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            logger.info(f"API Response: {request.method} {request.path} - Status: {response.status_code}")
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Only apply rate limiting to API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Simple rate limiting (100 requests per minute per IP)
        import time
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old entries
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if timestamp > minute_ago
            ]
        else:
            self.request_counts[client_ip] = []
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= 100:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.'
            }, status=429)
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
