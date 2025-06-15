# apps/reports/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class ReportTemplate(models.Model):
    """Template de rapport réutilisable."""
    
    TYPE_CHOICES = [
        ('patrimoine', 'Rapport patrimoine'),
        ('maintenance', 'Rapport maintenance'),
        ('financier', 'Rapport financier'),
        ('inventaire', 'Rapport inventaire'),
        ('custom', 'Rapport personnalisé'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    type_rapport = models.CharField(max_length=20, choices=TYPE_CHOICES)
    format_sortie = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    
    # Configuration du template
    template_content = models.TextField(help_text="Template Jinja2 ou SQL")
    parametres_schema = models.JSONField(default=dict, help_text="Schema des paramètres")
    
    # Métadonnées
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'reports_template'
        ordering = ['nom']


class GeneratedReport(models.Model):
    """Rapport généré et ses métadonnées."""
    
    STATUS_CHOICES = [
        ('pending', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
        ('expired', 'Expiré'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    
    # Informations de génération
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    nom_fichier = models.CharField(max_length=200)
    taille_fichier = models.BigIntegerField(null=True, blank=True)
    
    # Statut et dates
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Paramètres utilisés
    parametres = models.JSONField(default=dict)
    
    # Chemin du fichier généré
    file_path = models.CharField(max_length=500, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'reports_generated'
        ordering = ['-created_at']