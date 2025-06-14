# tests/test_services.py
from django.test import TestCase
from django.utils import timezone
from ..models import Categorie, SousCategorie, Entite, Bien, HistoriqueValeur
from ..services.bien_service import BienService

class BienServiceTests(TestCase):
    def setUp(self):
        # Créer des données de test
        self.cat = Categorie.objects.create(nom='Test Catégorie', type='mobilier')
        self.sc = SousCategorie.objects.create(categorie=self.cat, nom='Test SC', code='mobilier_bureau')
        self.entite = Entite.objects.create(nom='Test Entité', responsable='Resp1', commune=None)
        
        # Créer quelques biens
        self.bien1 = Bien.objects.create(
            nom='Bien Test 1', 
            categorie=self.cat, 
            sous_categorie=self.sc,
            entite=self.entite, 
            valeur_initiale=1000, 
            date_acquisition=timezone.now().date()
        )
        
        self.bien2 = Bien.objects.create(
            nom='Bien Test 2', 
            categorie=self.cat, 
            sous_categorie=self.sc,
            entite=self.entite, 
            valeur_initiale=2000, 
            date_acquisition=timezone.now().date()
        )

    def test_filtrer_biens(self):
        # Test de filtrage par catégorie
        biens = BienService.filtrer_biens(categorie_id=self.cat.id)
        self.assertEqual(biens.count(), 2)
        
        # Test de filtrage par recherche
        biens = BienService.filtrer_biens(search_query='Test 1')
        self.assertEqual(biens.count(), 1)
        self.assertEqual(biens.first().nom, 'Bien Test 1')
    
    def test_obtenir_statistiques(self):
        # Test des statistiques
        biens = Bien.objects.all()
        stats = BienService.obtenir_statistiques(biens)
        
        self.assertEqual(stats['valeur_totale'], 3000)
        self.assertEqual(stats['par_categorie'][0]['nb_biens'], 2)
    
    def test_ajouter_valeur_historique(self):
        # Test d'ajout d'historique
        date = timezone.now().date()
        historique = BienService.ajouter_valeur_historique(self.bien1, date, 1500)
        
        self.assertEqual(historique.bien, self.bien1)
        self.assertEqual(historique.valeur, 1500)
        self.assertEqual(historique.date, date)