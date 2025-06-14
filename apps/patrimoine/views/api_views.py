# api_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Bien, Categorie, SousCategorie, Entite
from .serializers import BienSerializer, CategorieSerializer, SousCategorieSerializer, EntiteSerializer

class BienViewSet(viewsets.ModelViewSet):
    queryset = Bien.objects.all()
    serializer_class = BienSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres
        categorie = self.request.query_params.get('categorie')
        entite = self.request.query_params.get('entite')
        recherche = self.request.query_params.get('recherche')
        
        if categorie:
            queryset = queryset.filter(categorie__id=categorie)
        if entite:
            queryset = queryset.filter(entite__id=entite)
        if recherche:
            queryset = queryset.filter(nom__icontains=recherche)
            
        return queryset