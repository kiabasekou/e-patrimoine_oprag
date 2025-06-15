# apps/core/apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration de l'application Core."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core OPRAG'
    
    def ready(self):
        """Initialisation des composants core."""
        self._setup_logging()
        self._validate_environment()
    
    def _setup_logging(self):
        """Configure le système de logging avancé."""
        import logging.config
        from django.conf import settings
        
        if hasattr(settings, 'LOGGING'):
            logging.config.dictConfig(settings.LOGGING)
    
    def _validate_environment(self):
        """Valide la configuration de l'environnement."""
        from django.conf import settings
        import warnings
        
        # Vérifications de sécurité en production
        if not settings.DEBUG:
            if settings.SECRET_KEY == 'your-secret-key-here':
                warnings.warn("SECRET_KEY par défaut détectée en production!")
            
            if not settings.ALLOWED_HOSTS:
                warnings.warn("ALLOWED_HOSTS vide en production!")