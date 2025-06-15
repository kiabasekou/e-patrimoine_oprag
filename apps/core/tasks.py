# apps/core/tasks.py
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def log_audit_entry(self, audit_data):
    """Tâche asynchrone pour enregistrer les entrées d'audit."""
    
    try:
        from apps.core.models import AuditLog
        
        AuditLog.objects.create(
            action=audit_data.get('action', 'UNKNOWN'),
            method=audit_data.get('method', 'GET'),
            path=audit_data.get('path', ''),
            user_id=audit_data.get('user_id'),
            ip_address=audit_data.get('ip_address', '0.0.0.0'),
            status_code=audit_data.get('status_code', 200),
            success=audit_data.get('success', True),
            duration_ms=audit_data.get('duration_ms'),
            request_data=audit_data.get('request_data', {}),
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement d'audit: {e}")
        
        # Retry avec backoff exponentiel
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=2 ** self.request.retries)


@shared_task
def cleanup_old_audit_logs():
    """Nettoie les anciens logs d'audit (plus de 2 ans)."""
    
    try:
        from apps.core.models import AuditLog
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=730)  # 2 ans
        deleted_count = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        logger.info(f"Nettoyage audit: {deleted_count} entrées supprimées")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des logs d'audit: {e}")
        return 0


@shared_task
def generate_performance_report():
    """Génère un rapport de performance quotidien."""
    
    try:
        from apps.core.models import PerformanceMetric
        from datetime import timedelta
        
        # Agréger les métriques des dernières 24h
        yesterday = timezone.now() - timedelta(days=1)
        
        metrics = PerformanceMetric.objects.filter(
            timestamp__gte=yesterday,
            periode='minute'
        ).aggregate(
            avg_response_time=models.Avg('avg_response_time'),
            total_requests=models.Sum('total_requests'),
            total_slow_requests=models.Sum('slow_requests_count'),
            avg_error_rate=models.Avg('error_rate')
        )
        
        # Créer un rapport quotidien
        if metrics['total_requests']:
            daily_metric = PerformanceMetric.objects.create(
                periode='day',
                total_requests=metrics['total_requests'],
                avg_response_time=metrics['avg_response_time'] or 0,
                slow_requests_count=metrics['total_slow_requests'] or 0,
                error_rate=metrics['avg_error_rate'] or 0,
            )
            
            # Envoyer une alerte si nécessaire
            if metrics['avg_error_rate'] and metrics['avg_error_rate'] > 5.0:
                send_mail(
                    subject='[OPRAG] Alerte: Taux d\'erreur élevé',
                    message=f'Taux d\'erreur moyen: {metrics["avg_error_rate"]:.2f}%',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=settings.ADMIN_EMAIL_LIST,
                    fail_silently=True
                )
            
            return f"Rapport quotidien généré: {daily_metric.id}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport de performance: {e}")
        return f"Erreur: {str(e)}"

