# apps/notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class NotificationTemplate(models.Model):
    """Template de notification réutilisable."""
    
    TYPE_CHOICES = [
        ('maintenance_due', 'Maintenance échue'),
        ('garantie_expire', 'Garantie expirée'),
        ('bien_transfere', 'Bien transféré'),
        ('inventaire_requis', 'Inventaire requis'),
        ('valeur_mise_a_jour', 'Valeur mise à jour'),
        ('approval_required', 'Approbation requise'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push notification'),
        ('in_app', 'Notification interne'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, unique=True)
    type_notification = models.CharField(max_length=50, choices=TYPE_CHOICES)
    canal = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    
    # Contenu du template
    sujet = models.CharField(max_length=200)
    contenu_text = models.TextField()
    contenu_html = models.TextField(blank=True)
    
    # Configuration
    est_actif = models.BooleanField(default=True)
    priorite = models.IntegerField(default=1, help_text="1=Basse, 5=Très haute")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_template'
        ordering = ['nom']


class Notification(models.Model):
    """Notification individuelle envoyée à un utilisateur."""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyée'),
        ('delivered', 'Délivrée'),
        ('read', 'Lue'),
        ('failed', 'Échec'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Contenu personnalisé
    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    
    # Métadonnées
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    canal_utilise = models.CharField(max_length=20)
    
    # Dates importantes
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Données contextuelles
    objet_id = models.CharField(max_length=100, blank=True)
    objet_type = models.CharField(max_length=50, blank=True)
    donnees_supplementaires = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
