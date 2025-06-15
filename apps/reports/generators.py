# apps/reports/generators.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """Classe de base pour tous les générateurs de rapports."""
    
    def __init__(self, template: ReportTemplate):
        self.template = template
    
    @abstractmethod
    def generate(self, parametres: Dict[str, Any]) -> bytes:
        """Génère le rapport selon les paramètres fournis."""
        pass
    
    @abstractmethod
    def validate_parameters(self, parametres: Dict[str, Any]) -> bool:
        """Valide les paramètres du rapport."""
        pass


class PatrimoineOverviewGenerator(BaseReportGenerator):
    """Générateur de rapport de vue d'ensemble du patrimoine."""
    
    def generate(self, parametres: Dict[str, Any]) -> bytes:
        """Génère un rapport Excel du patrimoine."""
        
        # Requête SQL optimisée pour les données
        query = """
        SELECT 
            b.code_bien,
            b.libelle,
            c.nom as categorie,
            sc.nom as sous_categorie,
            e.nom as entite,
            b.valeur_initiale,
            b.valeur_actuelle,
            b.date_acquisition,
            b.statut_juridique,
            CASE 
                WHEN b.date_mise_service IS NOT NULL 
                THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, b.date_mise_service))
                ELSE 0 
            END as age_annees
        FROM patrimoine_bien b
        LEFT JOIN patrimoine_souscategorie sc ON b.sous_categorie_id = sc.id
        LEFT JOIN patrimoine_categorie c ON sc.categorie_id = c.id
        LEFT JOIN patrimoine_entite e ON b.entite_id = e.id
        WHERE 1=1
        """
        
        # Application des filtres
        if parametres.get('entite_id'):
            query += f" AND b.entite_id = '{parametres['entite_id']}'"
        
        if parametres.get('date_debut'):
            query += f" AND b.date_acquisition >= '{parametres['date_debut']}'"
        
        if parametres.get('date_fin'):
            query += f" AND b.date_acquisition <= '{parametres['date_fin']}'"
        
        query += " ORDER BY b.code_bien"
        
        # Exécution et génération Excel
        df = pd.read_sql_query(query, connection)
        
        # Création du fichier Excel avec multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Patrimoine', index=False)
            
            # Sheet statistiques
            stats_df = self._generate_statistics(df)
            stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
        
        return output.getvalue()
    
    def validate_parameters(self, parametres: Dict[str, Any]) -> bool:
        """Valide les paramètres du rapport patrimoine."""
        # Validation des dates
        if parametres.get('date_debut') and parametres.get('date_fin'):
            from datetime import datetime
            try:
                debut = datetime.strptime(parametres['date_debut'], '%Y-%m-%d')
                fin = datetime.strptime(parametres['date_fin'], '%Y-%m-%d')
                if debut > fin:
                    return False
            except ValueError:
                return False
        
        return True
    
    def _generate_statistics(self, df):
        """Génère les statistiques du patrimoine."""
        stats = []
        
        if not df.empty:
            stats.append(['Nombre total de biens', len(df)])
            stats.append(['Valeur totale initiale', df['valeur_initiale'].sum()])
            stats.append(['Valeur totale actuelle', df['valeur_actuelle'].sum()])
            stats.append(['Age moyen (années)', df['age_annees'].mean()])
            
            # Répartition par catégorie
            cat_stats = df.groupby('categorie').size().reset_index(name='count')
            for _, row in cat_stats.iterrows():
                stats.append([f"Biens - {row['categorie']}", row['count']])
        
        return pd.DataFrame(stats, columns=['Indicateur', 'Valeur'])


class MaintenanceReportGenerator(BaseReportGenerator):
    """Générateur de rapport de maintenance."""
    
    def generate(self, parametres: Dict[str, Any]) -> bytes:
        """Génère un rapport de maintenance."""
        # Implémentation similaire pour les maintenances
        pass
    
    def validate_parameters(self, parametres: Dict[str, Any]) -> bool:
        return True


class AmortissementReportGenerator(BaseReportGenerator):
    """Générateur de rapport d'amortissement."""
    
    def generate(self, parametres: Dict[str, Any]) -> bytes:
        """Génère un rapport d'amortissement."""
        # Implémentation pour l'amortissement
        pass
    
    def validate_parameters(self, parametres: Dict[str, Any]) -> bool:
        return True


class InventaireReportGenerator(BaseReportGenerator):
    """Générateur de rapport d'inventaire."""
    
    def generate(self, parametres: Dict[str, Any]) -> bytes:
        """Génère un rapport d'inventaire."""
        # Implémentation pour l'inventaire
        pass
    
    def validate_parameters(self, parametres: Dict[str, Any]) -> bool:
        return True