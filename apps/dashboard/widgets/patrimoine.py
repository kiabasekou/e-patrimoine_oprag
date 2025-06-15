# apps/dashboard/widgets/patrimoine.py
from .base import BaseWidget
from django.db import connection
from datetime import datetime, timedelta


class PatrimoineStatsWidget(BaseWidget):
    """Widget des statistiques générales du patrimoine."""
    
    def get_data(self, user, filters=None):
        """Récupère les statistiques du patrimoine."""
        
        query = """
        SELECT 
            COUNT(*) as total_biens,
            SUM(valeur_initiale) as valeur_totale_initiale,
            SUM(valeur_actuelle) as valeur_totale_actuelle,
            AVG(CASE 
                WHEN date_mise_service IS NOT NULL 
                THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_mise_service))
                ELSE 0 
            END) as age_moyen
        FROM patrimoine_bien 
        WHERE est_actif = true
        """
        
        # Application des filtres utilisateur
        if filters and filters.get('entite_id'):
            query += f" AND entite_id = '{filters['entite_id']}'"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row:
                return {
                    'total_biens': int(row[0]) if row[0] else 0,
                    'valeur_totale_initiale': float(row[1]) if row[1] else 0,
                    'valeur_totale_actuelle': float(row[2]) if row[2] else 0,
                    'age_moyen': round(float(row[3]), 1) if row[3] else 0,
                    'taux_depreciation': round(
                        ((float(row[1]) - float(row[2])) / float(row[1]) * 100) 
                        if row[1] and row[1] > 0 else 0, 2
                    )
                }
        
        return {
            'total_biens': 0,
            'valeur_totale_initiale': 0,
            'valeur_totale_actuelle': 0,
            'age_moyen': 0,
            'taux_depreciation': 0
        }
    
    def get_chart_config(self):
        """Configuration pour un graphique en donut des valeurs."""
        return {
            'type': 'doughnut',
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {'position': 'bottom'},
                    'title': {'display': True, 'text': 'Répartition des valeurs'}
                }
            }
        }


class MaintenanceAlertsWidget(BaseWidget):
    """Widget des alertes de maintenance."""
    
    def get_data(self, user, filters=None):
        """Récupère les alertes de maintenance."""
        
        # Maintenances en retard
        query_retard = """
        SELECT COUNT(*) FROM patrimoine_maintenance 
        WHERE statut = 'planifiee' 
        AND date_prevue < CURRENT_DATE
        """
        
        # Maintenances à venir (7 prochains jours)
        query_a_venir = """
        SELECT COUNT(*) FROM patrimoine_maintenance 
        WHERE statut = 'planifiee' 
        AND date_prevue BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
        """
        
        # Garanties expirant (30 prochains jours)
        query_garanties = """
        SELECT COUNT(*) FROM patrimoine_bien 
        WHERE date_fin_garantie IS NOT NULL
        AND date_fin_garantie BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query_retard)
            retard = cursor.fetchone()[0] or 0
            
            cursor.execute(query_a_venir)
            a_venir = cursor.fetchone()[0] or 0
            
            cursor.execute(query_garanties)
            garanties = cursor.fetchone()[0] or 0
        
        return {
            'maintenances_retard': retard,
            'maintenances_a_venir': a_venir,
            'garanties_expirant': garanties,
            'total_alertes': retard + a_venir + garanties
        }
    
    def get_chart_config(self):
        """Configuration pour un graphique en barres des alertes."""
        return {
            'type': 'bar',
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': 'Alertes de maintenance'}
                },
                'scales': {
                    'y': {'beginAtZero': True}
                }
            }
        }


class ValeurEvolutionWidget(BaseWidget):
    """Widget de l'évolution des valeurs dans le temps."""
    
    def get_data(self, user, filters=None):
        """Récupère l'évolution des valeurs sur 12 mois."""
        
        query = """
        SELECT 
            DATE_TRUNC('month', hv.date_evaluation) as mois,
            SUM(hv.valeur) as valeur_totale
        FROM patrimoine_historiquevaleur hv
        JOIN patrimoine_bien b ON hv.bien_id = b.id
        WHERE hv.date_evaluation >= CURRENT_DATE - INTERVAL '12 months'
        AND b.est_actif = true
        GROUP BY DATE_TRUNC('month', hv.date_evaluation)
        ORDER BY mois
        """
        
        data = []
        labels = []
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                if row[0] and row[1]:
                    labels.append(row[0].strftime('%Y-%m'))
                    data.append(float(row[1]))
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Valeur totale (XAF)',
                'data': data,
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'tension': 0.1
            }]
        }
    
    def get_chart_config(self):
        """Configuration pour un graphique en ligne."""
        return {
            'type': 'line',
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {'display': True, 'text': 'Évolution des valeurs (12 mois)'}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'ticks': {
                            'callback': 'function(value) { return value.toLocaleString() + " XAF"; }'
                        }
                    }
                }
            }
        }


class TopCategoriesWidget(BaseWidget):
    """Widget du top des catégories par valeur."""
    
    def get_data(self, user, filters=None):
        """Récupère le top 10 des catégories par valeur."""
        
        query = """
        SELECT 
            c.nom as categorie,
            COUNT(b.id) as nombre_biens,
            SUM(b.valeur_actuelle) as valeur_totale
        FROM patrimoine_categorie c
        JOIN patrimoine_souscategorie sc ON c.id = sc.categorie_id
        JOIN patrimoine_bien b ON sc.id = b.sous_categorie_id
        WHERE b.est_actif = true
        GROUP BY c.id, c.nom
        ORDER BY valeur_totale DESC
        LIMIT 10
        """
        
        labels = []
        data = []
        background_colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#36A2EB'
        ]
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows):
                if row[0] and row[2]:
                    labels.append(row[0])
                    data.append(float(row[2]))
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': background_colors[:len(data)],
                'borderWidth': 1
            }]
        }
    
    def get_chart_config(self):
        """Configuration pour un graphique en secteurs."""
        return {
            'type': 'pie',
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {'position': 'right'},
                    'title': {'display': True, 'text': 'Top catégories par valeur'}
                }
            }
        }
