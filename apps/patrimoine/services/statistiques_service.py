from django.core.cache import cache
from django.db.models import Sum, Count, Avg

class StatistiquesService:
    @staticmethod
    def obtenir_statistiques_globales():
        """Obtient les statistiques globales avec mise en cache"""
        cache_key = 'statistiques_globales'
        stats = cache.get(cache_key)
        
        if not stats:
            from ..models import Bien
            
            stats = {
                'total_biens': Bien.objects.count(),
                'valeur_totale': Bien.objects.aggregate(Sum('valeur_initiale'))['valeur_initiale__sum'] or 0,
                'repartition_categories': list(Bien.objects.values('categorie__nom')
                    .annotate(count=Count('id'), value=Sum('valeur_initiale'))
                    .order_by('-count')),
                'valeur_moyenne': Bien.objects.aggregate(Avg('valeur_initiale'))['valeur_initiale__avg'] or 0,
            }
            
            # Mettre en cache pour 1 heure
            cache.set(cache_key, stats, 60 * 60)
        
        return stats