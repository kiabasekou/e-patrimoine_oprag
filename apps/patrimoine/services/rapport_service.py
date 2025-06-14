# services/rapport_service.py
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncMonth, TruncYear
from ..models import Bien, HistoriqueValeur, Categorie, Entite

class RapportService:
    @staticmethod
    def rapport_acquisitions_mensuelles(annee=None):
        """Génère un rapport des acquisitions par mois"""
        queryset = Bien.objects.all()
        
        if annee:
            queryset = queryset.filter(date_acquisition__year=annee)
        
        data = (
            queryset
            .annotate(mois=TruncMonth('date_acquisition'))
            .values('mois')
            .annotate(
                nombre=Count('id'),
                valeur_totale=Sum('valeur_initiale')
            )
            .order_by('mois')
        )
        
        return list(data)
    
    @staticmethod
    def rapport_evolution_valeur(bien_id=None, categorie_id=None, periode='annuel'):
        """Génère un rapport sur l'évolution des valeurs dans le temps"""
        queryset = HistoriqueValeur.objects.all()
        
        # Filtres
        if bien_id:
            queryset = queryset.filter(bien_id=bien_id)
        if categorie_id:
            queryset = queryset.filter(bien__categorie_id=categorie_id)
        
        # Groupement par période
        if periode == 'mensuel':
            queryset = queryset.annotate(periode=TruncMonth('date'))
        else:  # annuel par défaut
            queryset = queryset.annotate(periode=TruncYear('date'))
        
        data = (
            queryset
            .values('periode')
            .annotate(
                valeur_moyenne=Avg('valeur'),
                valeur_totale=Sum('valeur'),
                nombre_biens=Count('bien_id', distinct=True)
            )
            .order_by('periode')
        )
        
        return list(data)
    
    @staticmethod
    def rapport_repartition_geographique():
        """Génère un rapport de répartition géographique des biens"""
        return (
            Bien.objects.values(
                province=F('commune__departement__province__nom'),
                departement=F('commune__departement__nom'),
                commune=F('commune__nom')
            )
            .annotate(
                nombre=Count('id'),
                valeur_totale=Sum('valeur_initiale')
            )
            .order_by('province', 'departement', 'commune')
        )