# apps/core/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


def rate_limit(requests_per_minute: int = 60):
    """Décorateur de limitation de taux pour les vues."""
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            
            # Identifier l'utilisateur (IP + user si authentifié)
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            user_id = request.user.id if request.user.is_authenticated else 'anonymous'
            key = f"rate_limit:{ip}:{user_id}"
            
            # Vérifier le cache
            current_requests = cache.get(key, 0)
            
            if current_requests >= requests_per_minute:
                return JsonResponse({
                    'error': 'Trop de requêtes. Veuillez patienter.',
                    'retry_after': 60
                }, status=429)
            
            # Incrémenter le compteur
            cache.set(key, current_requests + 1, 60)  # TTL de 1 minute
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def cache_result(ttl: int = 300, cache_type: str = 'api_response'):
    """Décorateur de mise en cache des résultats de vue."""
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            
            # Générer une clé de cache unique
            cache_key = CacheManager.generate_cache_key(
                f"view:{view_func.__name__}",
                method=request.method,
                path=request.path,
                user_id=request.user.id if request.user.is_authenticated else None,
                args=args,
                kwargs=kwargs
            )
            
            # Utiliser le gestionnaire de cache
            def execute_view():
                return view_func(request, *args, **kwargs)
            
            return CacheManager.get_or_set(cache_key, execute_view, ttl, cache_type)
        
        return wrapper
    return decorator


def audit_action(action_type: str = None):
    """Décorateur d'audit pour les actions sensibles."""
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            
            start_time = time.time()
            action = action_type or request.method
            
            try:
                # Exécuter la vue
                response = view_func(request, *args, **kwargs)
                success = True
                status_code = getattr(response, 'status_code', 200)
                
            except Exception as e:
                logger.error(f"Erreur dans {view_func.__name__}: {e}")
                success = False
                status_code = 500
                raise
            
            finally:
                # Enregistrer l'audit (en mode asynchrone si possible)
                try:
                    from apps.core.tasks import log_audit_entry
                    
                    audit_data = {
                        'action': action,
                        'view_name': view_func.__name__,
                        'method': request.method,
                        'path': request.path,
                        'user_id': request.user.id if request.user.is_authenticated else None,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'duration_ms': round((time.time() - start_time) * 1000, 2),
                        'success': success,
                        'status_code': status_code,
                    }
                    
                    # Envoyer en tâche asynchrone si Celery est disponible
                    if hasattr(log_audit_entry, 'delay'):
                        log_audit_entry.delay(audit_data)
                    else:
                        log_audit_entry(audit_data)
                        
                except Exception as audit_error:
                    logger.error(f"Erreur lors de l'audit: {audit_error}")
            
            return response
        
        return wrapper
    return decorator

