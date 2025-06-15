# apps/core/middleware.py
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time
import logging
import pytz

User = get_user_model()
logger = logging.getLogger(__name__)


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware de gestion intelligente des fuseaux horaires.
    Adapte automatiquement le timezone selon l'utilisateur ou la géolocalisation.
    """
    
    def process_request(self, request):
        """Active le timezone approprié pour la requête."""
        
        # Timezone par défaut pour le Gabon
        default_timezone = pytz.timezone('Africa/Libreville')
        
        # Si utilisateur authentifié, utiliser son timezone préféré
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_timezone = getattr(request.user, 'timezone', None)
            if user_timezone:
                try:
                    timezone.activate(pytz.timezone(user_timezone))
                    return
                except Exception:
                    pass
        
        # Détection par géolocalisation (headers ou IP)
        timezone_from_geo = self._detect_timezone_from_request(request)
        if timezone_from_geo:
            timezone.activate(timezone_from_geo)
        else:
            timezone.activate(default_timezone)
    
    def process_response(self, request, response):
        """Nettoie le timezone à la fin de la requête."""
        timezone.deactivate()
        return response
    
    def _detect_timezone_from_request(self, request):
        """Détecte le timezone à partir de la requête."""
        
        # Vérifier le header personnalisé
        tz_header = request.META.get('HTTP_X_TIMEZONE')
        if tz_header:
            try:
                return pytz.timezone(tz_header)
            except Exception:
                pass
        
        # Détection par IP (implémentation simplifiée)
        client_ip = self._get_client_ip(request)
        if client_ip:
            # Cache de 1 heure pour éviter les requêtes répétées
            cache_key = f'timezone_ip_{client_ip}'
            cached_tz = cache.get(cache_key)
            if cached_tz:
                return pytz.timezone(cached_tz)
            
            # Ici on pourrait intégrer un service de géolocalisation IP
            # Pour le Gabon, on utilise le timezone par défaut
            detected_tz = 'Africa/Libreville'
            cache.set(cache_key, detected_tz, 3600)  # 1 heure
            return pytz.timezone(detected_tz)
        
        return None
    
    def _get_client_ip(self, request):
        """Récupère l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware d'audit avancé pour tracer toutes les actions sensibles.
    Logs détaillés pour la conformité et la sécurité.
    """
    
    # Actions à auditer
    AUDIT_ACTIONS = {
        'POST': 'CREATE',
        'PUT': 'UPDATE', 
        'PATCH': 'UPDATE',
        'DELETE': 'DELETE'
    }
    
    # Chemins sensibles à auditer
    SENSITIVE_PATHS = [
        '/api/v1/biens/',
        '/api/v1/maintenance/',
        '/api/v1/transferts/',
        '/admin/',
        '/auth/'
    ]
    
    def process_request(self, request):
        """Capture les informations de la requête pour l'audit."""
        
        # Marquer le début du traitement
        request._audit_start_time = time.time()
        
        # Capturer les données avant modification
        if self._should_audit(request):
            request._audit_before_data = self._capture_request_data(request)
    
    def process_response(self, request, response):
        """Enregistre l'audit après traitement de la requête."""
        
        if self._should_audit(request) and hasattr(request, '_audit_before_data'):
            self._log_audit_entry(request, response)
        
        return response
    
    def _should_audit(self, request):
        """Détermine si la requête doit être auditée."""
        
        # Ignorer les requêtes anonymes sauf pour l'authentification
        if not request.user.is_authenticated and '/auth/' not in request.path:
            return False
        
        # Vérifier si c'est une action modifiante
        if request.method not in self.AUDIT_ACTIONS:
            return False
        
        # Vérifier si le chemin est sensible
        return any(sensitive in request.path for sensitive in self.SENSITIVE_PATHS)
    
    def _capture_request_data(self, request):
        """Capture les données pertinentes de la requête."""
        
        data = {
            'method': request.method,
            'path': request.path,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Capturer les paramètres de requête (sans données sensibles)
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Ne pas logger les mots de passe ou tokens
            sensitive_fields = ['password', 'token', 'secret', 'key']
            safe_data = {}
            
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if not any(field in key.lower() for field in sensitive_fields):
                        safe_data[key] = str(value)[:200]  # Limiter la taille
            
            data['request_data'] = safe_data
        
        return data
    
    def _log_audit_entry(self, request, response):
        """Enregistre l'entrée d'audit en base."""
        
        try:
            from apps.core.models import AuditLog
            
            # Calculer la durée du traitement
            duration = None
            if hasattr(request, '_audit_start_time'):
                duration = round((time.time() - request._audit_start_time) * 1000, 2)
            
            # Créer l'entrée d'audit
            audit_data = request._audit_before_data.copy()
            audit_data.update({
                'action': self.AUDIT_ACTIONS.get(request.method, 'UNKNOWN'),
                'status_code': response.status_code,
                'duration_ms': duration,
                'success': 200 <= response.status_code < 400,
            })
            
            AuditLog.objects.create(**audit_data)
            
        except Exception as e:
            # Ne jamais faire échouer la requête à cause de l'audit
            logger.error(f"Erreur lors de l'audit: {e}")
    
    def _get_client_ip(self, request):
        """Récupère l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware de monitoring des performances avec alertes automatiques.
    Suit les temps de réponse, les requêtes lentes, et l'utilisation des ressources.
    """
    
    # Seuils d'alerte (en secondes)
    SLOW_REQUEST_THRESHOLD = 2.0
    VERY_SLOW_REQUEST_THRESHOLD = 5.0
    
    def process_request(self, request):
        """Démarre le monitoring de la requête."""
        
        request._perf_start_time = time.time()
        request._perf_queries_before = len(connection.queries)
    
    def process_response(self, request, response):
        """Enregistre les métriques de performance."""
        
        if not hasattr(request, '_perf_start_time'):
            return response
        
        # Calculer les métriques
        duration = time.time() - request._perf_start_time
        queries_count = len(connection.queries) - request._perf_queries_before
        
        # Enregistrer dans les logs
        self._log_performance_metrics(request, response, duration, queries_count)
        
        # Alertes pour les requêtes lentes
        if duration > self.VERY_SLOW_REQUEST_THRESHOLD:
            self._alert_very_slow_request(request, duration, queries_count)
        elif duration > self.SLOW_REQUEST_THRESHOLD:
            self._alert_slow_request(request, duration, queries_count)
        
        # Ajouter les headers de performance en développement
        if settings.DEBUG:
            response['X-Response-Time'] = f"{duration:.3f}s"
            response['X-DB-Queries'] = str(queries_count)
        
        return response
    
    def _log_performance_metrics(self, request, response, duration, queries_count):
        """Enregistre les métriques de performance."""
        
        # Log structuré pour l'analyse
        logger.info(
            "Performance metrics",
            extra={
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'duration_seconds': round(duration, 3),
                'db_queries_count': queries_count,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'ip_address': self._get_client_ip(request),
            }
        )
        
        # Sauvegarder en cache pour le dashboard de monitoring
        cache_key = f"perf_metrics_{int(time.time() // 60)}"  # Par minute
        metrics = cache.get(cache_key, {
            'total_requests': 0,
            'total_duration': 0,
            'slow_requests': 0,
            'db_queries': 0
        })
        
        metrics['total_requests'] += 1
        metrics['total_duration'] += duration
        metrics['db_queries'] += queries_count
        
        if duration > self.SLOW_REQUEST_THRESHOLD:
            metrics['slow_requests'] += 1
        
        cache.set(cache_key, metrics, 3600)  # 1 heure
    
    def _alert_slow_request(self, request, duration, queries_count):
        """Alerte pour requête lente."""
        
        logger.warning(
            f"Requête lente détectée: {request.path} ({duration:.3f}s, {queries_count} requêtes DB)",
            extra={
                'path': request.path,
                'method': request.method,
                'duration': duration,
                'queries_count': queries_count,
                'alert_type': 'slow_request'
            }
        )
    
    def _alert_very_slow_request(self, request, duration, queries_count):
        """Alerte pour requête très lente."""
        
        logger.error(
            f"Requête TRÈS lente détectée: {request.path} ({duration:.3f}s, {queries_count} requêtes DB)",
            extra={
                'path': request.path,
                'method': request.method,
                'duration': duration,
                'queries_count': queries_count,
                'alert_type': 'very_slow_request'
            }
        )
        
        # Ici on pourrait envoyer une notification push aux administrateurs
        # ou intégrer avec un service comme Slack
    
    def _get_client_ip(self, request):
        """Récupère l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip