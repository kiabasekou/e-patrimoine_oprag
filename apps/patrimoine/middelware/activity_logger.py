# middleware/activity_logger.py
import json
import logging
from django.utils import timezone

logger = logging.getLogger('user_activity')

class ActivityLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code exécuté avant la vue
        if request.user.is_authenticated:
            request.activity_start_time = timezone.now()
        
        response = self.get_response(request)
        
        # Code exécuté après la vue
        if hasattr(request, 'activity_start_time') and request.user.is_authenticated:
            duration = timezone.now() - request.activity_start_time
            
            # Enregistrer l'activité
            log_data = {
                'timestamp': timezone.now().isoformat(),
                'user': request.user.username,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration.total_seconds() * 1000,
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            
            logger.info(json.dumps(log_data))
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip