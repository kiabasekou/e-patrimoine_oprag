# apps/dashboard/widgets/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from django.db import connection


class BaseWidget(ABC):
    """Classe de base pour tous les widgets de dashboard."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    @abstractmethod
    def get_data(self, user, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Récupère les données du widget."""
        pass
    
    @abstractmethod
    def get_chart_config(self) -> Dict[str, Any]:
        """Retourne la configuration du graphique (Chart.js)."""
        pass
    
    def validate_filters(self, filters: Dict[str, Any]) -> bool:
        """Valide les filtres appliqués au widget."""
        return True

