# tasks/__init__.py
from .rapports import exporter_inventaire_complet
from .maintenance import verifier_maintenances_planifiees
from .notifications import envoyer_notifications_groupees

# Pour permettre l'import direct depuis patrimoine.tasks
__all__ = [
    'exporter_inventaire_complet',
    'verifier_maintenances_planifiees',
    'envoyer_notifications_groupees',
]