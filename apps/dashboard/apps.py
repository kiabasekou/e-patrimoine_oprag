# apps/dashboard/apps.py
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuration de l'application Dashboard."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Tableaux de bord OPRAG'
    
    def ready(self):
        """Initialisation des widgets par défaut."""
        self._register_default_widgets()
    
    def _register_default_widgets(self):
        """Enregistre les widgets par défaut."""
        from .widgets.registry import WidgetRegistry
        from .widgets import (
            PatrimoineStatsWidget,
            MaintenanceAlertsWidget,
            ValeurEvolutionWidget,
            TopCategoriesWidget
        )
        
        registry = WidgetRegistry()
        registry.register('patrimoine_stats', PatrimoineStatsWidget)
        registry.register('maintenance_alerts', MaintenanceAlertsWidget)
        registry.register('valeur_evolution', ValeurEvolutionWidget)
        registry.register('top_categories', TopCategoriesWidget)