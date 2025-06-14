from django.contrib import admin
from .models import (
    Categorie, SousCategorie, Entite, Bien, HistoriqueValeur,
    Province, Departement, Commune, District,
    ResponsableBien, BienResponsabilite
)
# ... reste du fichier inchangé ...
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter

# ✅ Admins simples
admin.site.register(Categorie)
admin.site.register(Entite)
admin.site.register(HistoriqueValeur)
admin.site.register(Province)
admin.site.register(Departement)
admin.site.register(Commune)
admin.site.register(District)

# ✅ ResponsableBien avec options
@admin.register(ResponsableBien)
class ResponsableBienAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "matricule", "fonction", "corps", "categorie")
    search_fields = ("nom", "prenom", "matricule", "fonction", "corps")
    list_filter = ("categorie", "corps")

# ✅ Inline pour affectation dans Bien
class BienResponsabiliteInline(admin.TabularInline):
    model = BienResponsabilite
    extra = 1
    autocomplete_fields = ['responsable']
    fields = (
        'responsable', 'type_affectation', 'date_affectation',
        'numero_permis', 'categorie_permis', 'composition_foyer',
        'certifications'
    )
    

class ResponsableActuelFilter(SimpleListFilter):
    title = _('Responsable actuel')
    parameter_name = 'responsable_actuel'

    def lookups(self, request, model_admin):
        responsables = ResponsableBien.objects.all()
        return [(r.id, f"{r.prenom} {r.nom}") for r in responsables]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(responsabilites__responsable__id=self.value(), responsabilites__type_affectation='permanent')
        return queryset

# ✅ Bien avec inline

@admin.register(Bien)
class BienAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'categorie', 'sous_categorie',
        'valeur_initiale', 'date_acquisition',
        'get_responsable_actuel'
    )
    list_filter = ('categorie', 'sous_categorie')
    search_fields = ('nom', 'responsabilites__responsable__nom', 'responsabilites__responsable__prenom')

    inlines = [BienResponsabiliteInline]

    def get_responsable_actuel(self, obj):
        actif = obj.responsable_actuel
        if actif:
            return f"{actif.responsable.prenom} {actif.responsable.nom}"
        return "—"
    get_responsable_actuel.short_description = "Responsable actuel"
    list_filter = ('categorie', 'sous_categorie', ResponsableActuelFilter)


@admin.register(SousCategorie)
class SousCategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'code')
    search_fields = ('nom', 'code')




