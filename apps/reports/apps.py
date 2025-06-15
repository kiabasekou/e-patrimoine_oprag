# apps/reports/apps.py
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Configuration de l'application Reports."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'
    verbose_name = 'Rapports OPRAG'
    
    def ready(self):
        """Initialisation des générateurs de rapports."""
        self._register_report_generators()
    
    def _register_report_generators(self):
        """Enregistre les générateurs de rapports par défaut."""
        from .registry import ReportRegistry
        from .generators import (
            PatrimoineOverviewGenerator,
            MaintenanceReportGenerator,
            AmortissementReportGenerator,
            InventaireReportGenerator
        )
        
        registry = ReportRegistry()
        registry.register('patrimoine_overview', PatrimoineOverviewGenerator)
        registry.register('maintenance_report', MaintenanceReportGenerator)
        registry.register('amortissement_report', AmortissementReportGenerator)
        registry.register('inventaire_report', InventaireReportGenerator)
