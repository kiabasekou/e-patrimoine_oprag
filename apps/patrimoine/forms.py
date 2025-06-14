from django import forms
from django.utils.text import slugify

from .models import (
    Bien,
    HistoriqueValeur,
    SousCategorie,
    ProfilVehicule,
    ProfilImmeuble,
    ProfilInformatique,
    ProfilEquipementMedical,
    ProfilMobilier,
    ProfilTerrain,
    ProfilConsommable,
)


class HistoriqueValeurForm(forms.ModelForm):
    class Meta:
        model = HistoriqueValeur
        fields = ['date', 'valeur']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valeur': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BienForm(forms.ModelForm):
    class Meta:
        model = Bien
        fields = [
            'nom', 'categorie', 'sous_categorie',
            'entite', 'valeur_initiale', 'date_acquisition', 'justificatif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select', 'id': 'id_categorie'}),
            'sous_categorie': forms.Select(attrs={'class': 'form-select', 'id': 'id_sous_categorie'}),
            'entite': forms.Select(attrs={'class': 'form-select'}),
            'valeur_initiale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_acquisition': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'justificatif': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Au départ, on ne propose pas de sous-catégories
        self.fields['sous_categorie'].queryset = SousCategorie.objects.none()

        if 'categorie' in self.data:
            try:
                cat_id = int(self.data.get('categorie'))
                self.fields['sous_categorie'].queryset = SousCategorie.objects.filter(
                    categorie_id=cat_id
                ).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.categorie:
            self.fields['sous_categorie'].queryset = self.instance.categorie.sous_categories.all()


#
# Profils techniques
#

class BaseProfilForm(forms.ModelForm):
    """
    Formulaire de base pour tous les profils : rend tous les champs obligatoires
    et donne un widget 'form-control' aux inputs standards.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # tous les champs requis
            field.required = True

            # uniformiser les widgets
            widget = field.widget
            css_class = widget.attrs.get('class', '')
            if isinstance(widget, (forms.TextInput, forms.NumberInput, forms.DateInput, forms.ClearableFileInput)):
                widget.attrs['class'] = (css_class + ' form-control').strip()
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = (css_class + ' form-select').strip()

            # pour les dates, limiter l’intervalle
            if isinstance(widget, forms.DateInput):
                widget.attrs.setdefault('type', 'date')
                widget.attrs.setdefault('min', '1900-01-01')
                widget.attrs.setdefault('max', '2100-12-31')


class ProfilVehiculeForm(BaseProfilForm):
    class Meta:
        model = ProfilVehicule
        exclude = ['bien']
        widgets = {
            'marque': forms.TextInput(attrs={'class': 'form-control'}),
            'modele': forms.TextInput(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),  # Renommé de 'immatriculation' à 'matricule'
            'numero_chassis': forms.TextInput(attrs={'class': 'form-control'}),
            'date_fabrication': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_acquisition': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_derniere_maintenance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'prochaine_maintenance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ProfilImmeubleForm(BaseProfilForm):
    class Meta:
        model = ProfilImmeuble
        exclude = ['bien']
        widgets = {
            'surface': forms.NumberInput(attrs={'step': '0.01'}),
            'nb_etages': forms.NumberInput(attrs={'min': 0}),
            'annee_construction': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'securite': forms.TextInput(),
        }


class ProfilInformatiqueForm(BaseProfilForm):
    class Meta:
        model = ProfilInformatique
        exclude = ['bien']
        widgets = {
            'type_equipement': forms.Select(),
            'date_fabrication': forms.DateInput(),
            'date_acquisition': forms.DateInput(),
            'date_derniere_maintenance': forms.DateInput(),
            'prochaine_maintenance': forms.DateInput(),
            'date_mise_service': forms.DateInput(),
            'date_derniere_maj': forms.DateInput(),
            'fin_garantie': forms.DateInput(),
            'date_mise_service': forms.DateInput(),
        }


class ProfilEquipementMedicalForm(BaseProfilForm):
    class Meta:
        model = ProfilEquipementMedical
        exclude = ['bien']
        widgets = {
            'date_fabrication': forms.DateInput(),
            'date_installation': forms.DateInput(),
            'date_derniere_maintenance': forms.DateInput(),
            'fin_garantie': forms.DateInput(),
        }


# Correction des formulaires pour correspondre aux modèles
class ProfilMobilierForm(BaseProfilForm):
    class Meta:
        model = ProfilMobilier
        exclude = ['bien']
        widgets = {
            'materiau': forms.TextInput(attrs={'class': 'form-control'}),
            'couleur': forms.TextInput(attrs={'class': 'form-control'}),
            'fabricant': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_fabrication': forms.NumberInput(attrs={'min': 1900, 'max': 2100, 'class': 'form-control'}),
        }

class ProfilTerrainForm(BaseProfilForm):
    class Meta:
        model = ProfilTerrain
        exclude = ['bien']
        widgets = {
            'superficie': forms.NumberInput(attrs={'step': '0.01'}),
        }


class ProfilConsommableForm(BaseProfilForm):
    class Meta:
        model = ProfilConsommable
        exclude = ['bien']
        widgets = {
            'quantite_initiale': forms.NumberInput(attrs={'min': 0}),
            'stock_securite': forms.NumberInput(attrs={'min': 0}),
        }
