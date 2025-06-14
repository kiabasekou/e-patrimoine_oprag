from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Categorie, SousCategorie, Entite, Bien
from .views import FORM_MAPPING

class ModelTests(TestCase):
    def setUp(self):
        # Création d'objets de base
        self.cat = Categorie.objects.create(nom='CatTest', type='mobilier')
        self.sc = SousCategorie.objects.create(categorie=self.cat, nom='TestSC', code='mobilier_bureau')
        self.entite = Entite.objects.create(nom='Ent1', responsable='Resp1', commune=None)

    def test_str_models(self):
        self.assertEqual(str(self.cat), 'CatTest (Bien Mobilier)')
        self.assertEqual(str(self.sc), 'TestSC – CatTest')
        self.assertEqual(str(self.entite), 'Ent1')

    def test_bien_creation(self):
        b = Bien.objects.create(
            nom='Bien1', categorie=self.cat, sous_categorie=self.sc,
            entite=self.entite, valeur_initiale=100, date_acquisition=timezone.now().date()
        )
        self.assertEqual(str(b), 'Bien1')

class FormMappingTests(TestCase):
    def test_mapping_contains_all_codes(self):
        # on crée quelques sous-catégories pour vérifier le mapping
        codes = ['batiments_administratifs','infra_sanitaires','terrains',
                 'installations_techniques','equipement_medical','informatique',
                 'mobilier_bureau','vehicules_service','consommables_stocks']
        for code in codes:
            self.assertIn(code, FORM_MAPPING)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Categorie.objects.create(nom='Cat', type='mobilier')
        self.sc = SousCategorie.objects.create(categorie=self.cat, nom='Mobilier', code='mobilier_bureau')
        self.entite = Entite.objects.create(nom='Ent', responsable='R', commune=None)
        self.bien = Bien.objects.create(
            nom='Bien1', categorie=self.cat, sous_categorie=self.sc,
            entite=self.entite, valeur_initiale=500,
            date_acquisition=timezone.now().date()
        )

    def test_list_view(self):
        url = reverse('biens:bien_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Bien1')

    def test_search(self):
        url = reverse('biens:bien_list') + '?q=Bien1'
        resp = self.client.get(url)
        self.assertContains(resp, 'Bien1')

    def test_detail_view(self):
        url = reverse('biens:bien_detail', args=[self.bien.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '🔎 Bien1')

    def test_create_view_get(self):
        url = reverse('biens:bien_create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<form')

    def test_add_ajax(self):
        url = reverse('biens:ajouter_bien_complet')
        data = {
            'nom': 'Bien2', 'categorie': self.cat.id, 'sous_categorie': self.sc.id,
            'entite': self.entite.id, 'valeur_initiale': '1000',
            'date_acquisition': timezone.now().date().isoformat()
        }
        resp = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {'success': True})

# Pour exécuter ces tests:
# python manage.py test patrimoine
