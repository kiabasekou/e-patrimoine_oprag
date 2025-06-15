# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


class User(AbstractUser):
    """Utilisateur enterprise OPRAG avec fonctionnalités avancées."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informations OPRAG
    matricule = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Matricule OPRAG de l'employé"
    )
    
    entite = models.ForeignKey(
        'patrimoine.Entite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs'
    )
    
    # Profil utilisateur
    telephone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+241[0-9]{8}$', 'Format: +24177123456')],
        blank=True
    )
    
    poste = models.CharField(max_length=100, blank=True)
    departement = models.CharField(max_length=100, blank=True)
    
    # Sécurité avancée
    force_password_change = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(default=timezone.now)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user_oprag'
        verbose_name = 'Utilisateur OPRAG'
        verbose_name_plural = 'Utilisateurs OPRAG'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.matricule or self.username})"
    
    @property
    def needs_password_change(self):
        """Vérifie si l'utilisateur doit changer son mot de passe."""
        if self.force_password_change:
            return True
        
        # Changement obligatoire tous les 90 jours
        days_since_change = (timezone.now() - self.last_password_change).days
        return days_since_change > 90
    
    @property
    def is_account_locked(self):
        """Vérifie si le compte est verrouillé."""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False


class UserSession(models.Model):
    """Gestion des sessions utilisateurs avec audit."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    
    # Informations de connexion
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'auth_user_sessions'
        ordering = ['-last_activity']
