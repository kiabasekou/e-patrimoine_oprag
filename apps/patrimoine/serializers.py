# serializers.py
from rest_framework import serializers
from .models import Bien, Categorie, SousCategorie, Entite, HistoriqueValeur

class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'type']

class SousCategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = SousCategorie
        fields = ['id', 'nom', 'code', 'categorie']

class EntiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entite
        fields = ['id', 'nom', 'responsable', 'commune']

class HistoriqueValeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueValeur
        fields = ['id', 'date', 'valeur']

class BienSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)
    sous_categorie = SousCategorieSerializer(read_only=True)
    entite = EntiteSerializer(read_only=True)
    historiques = HistoriqueValeurSerializer(many=True, read_only=True)
    
    class Meta:
        model = Bien
        fields = [
            'id', 'nom', 'categorie', 'sous_categorie', 'entite',
            'valeur_initiale', 'date_acquisition', 'commune', 
            'historiques'
        ]