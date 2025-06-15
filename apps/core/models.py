# apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class AuditLog(models.Model):
    """Log d'audit pour toutes les actions sensibles."""
    
    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
        ('EXPORT', 'Export'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informations de l'action
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    
    # Utilisateur et session
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Informations techniques
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Résultat
    status_code = models.PositiveIntegerField()
    success = models.BooleanField()
    duration_ms = models.FloatField(null=True, blank=True)
    
    # Données contextuelles
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    # Métadonnées
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'core_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]


class PerformanceMetric(models.Model):
    """Métriques de performance agrégées."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Période de mesure
    timestamp = models.DateTimeField(default=timezone.now)
    periode = models.CharField(max_length=20, default='minute')  # minute, hour, day
    
    # Métriques globales
    total_requests = models.PositiveIntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    slow_requests_count = models.PositiveIntegerField(default=0)
    error_rate = models.FloatField(default=0.0)
    
    # Métriques base de données
    avg_db_queries = models.FloatField(default=0.0)
    max_db_queries = models.PositiveIntegerField(default=0)
    
    # Utilisation mémoire et CPU (si disponible)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    cpu_usage_percent = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'core_performance_metric'
        ordering = ['-timestamp']
        unique_together = ['timestamp', 'periode']