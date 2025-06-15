# apps/authentication/apps.py
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration de l'application Authentication."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentification OPRAG'
    
    def ready(self):
        """Initialisation lors du démarrage de l'application."""
        try:
            import apps.authentication.signals  # noqa
        except ImportError:
            pass
        
        # Configuration des permissions par défaut
        self._setup_default_permissions()
    
    def _setup_default_permissions(self):
        """Configure les permissions par défaut pour l'OPRAG."""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Création des groupes métier OPRAG
        groups_data = {
            'Direction Générale': ['add', 'change', 'delete', 'view'],
            'Gestionnaires Patrimoine': ['add', 'change', 'view'],
            'Responsables Techniques': ['change', 'view'],
            'Consultants Externes': ['view'],
        }
        
        for group_name, permissions in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                # Assignation des permissions (sera complétée lors des migrations)
                pass
