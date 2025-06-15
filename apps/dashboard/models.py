# apps/dashboard/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Dashboard(models.Model):
    """Configuration de tableau de bord personnalisé."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Propriétaire et partage
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')
    est_partage = models.BooleanField(default=False)
    utilisateurs_autorises = models.ManyToManyField(User, blank=True, related_name='dashboards_autorises')
    
    # Configuration
    layout = models.JSONField(default=dict, help_text="Configuration des widgets et leur positionnement")
    est_par_defaut = models.BooleanField(default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_dashboard'
        ordering = ['nom']


class DashboardWidget(models.Model):
    """Widget individuel dans un tableau de bord."""
    
    WIDGET_TYPES = [
        ('chart', 'Graphique'),
        ('table', 'Tableau'),
        ('metric', 'Métrique'),
        ('map', 'Carte'),
        ('alert', 'Alerte'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    
    # Configuration du widget
    nom = models.CharField(max_length=100)
    type_widget = models.CharField(max_length=20, choices=WIDGET_TYPES)
    widget_class = models.CharField(max_length=100, help_text="Nom de la classe du widget")
    
    # Position et taille
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    largeur = models.PositiveIntegerField(default=6)
    hauteur = models.PositiveIntegerField(default=4)
    
    # Configuration spécifique
    configuration = models.JSONField(default=dict)
    est_actif = models.BooleanField(default=True)
    
    # Ordre d'affichage
    ordre = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_widget'
        ordering = ['ordre', 'nom']