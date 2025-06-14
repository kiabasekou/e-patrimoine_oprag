# apps/patrimoine/models/base.py
"""
Modèles de base optimisés pour la gestion patrimoniale OPRAG.
Applique les meilleures pratiques : UUID, soft delete, audit trail, indexation.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.contrib.postgres.search import SearchVectorField
from simple_history.models import HistoricalRecords
from model_utils.models import TimeStampedModel, SoftDeletableModel
from django.db.models import Q, F, Sum, Count
from decimal import Decimal

User = get_user_model()


class BaseModel(TimeStampedModel, SoftDeletableModel):
    """
    Modèle de base avec UUID, timestamps, soft delete et audit trail.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metadata = models.JSONField(default=dict, blank=True, help_text="Métadonnées flexibles")
    
    class Meta:
        abstract = True
        ordering = ['-created']
        indexes = [
            models.Index(fields=['created']),
            models.Index(fields=['is_removed']),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AuditMixin(models.Model):
    """Mixin pour l'audit trail complet."""
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(class)s_created',
        verbose_name=_("Créé par")
    )
    modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(class)s_modified',
        verbose_name=_("Modifié par")
    )
    history = HistoricalRecords(inherit=True)
    
    class Meta:
        abstract = True


class SearchableMixin(models.Model):
    """Mixin pour la recherche full-text avec PostgreSQL."""
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        abstract = True
        indexes = [
            GinIndex(fields=['search_vector']),
        ]


# Modèles de localisation optimisés
class Province(BaseModel, AuditMixin):
    """Province avec géométrie spatiale."""
    nom = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.CharField(max_length=10, unique=True)
    geometry = models.JSONField(null=True, blank=True, help_text="Données GeoJSON")
    
    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Departement(BaseModel, AuditMixin):
    """Département avec relation optimisée."""
    nom = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=20, unique=True)
    province = models.ForeignKey(
        Province, 
        on_delete=models.PROTECT,
        related_name='departements'
    )
    
    class Meta:
        verbose_name = _("Département")
        verbose_name_plural = _("Départements")
        unique_together = ['nom', 'province']
        ordering = ['province__nom', 'nom']
        indexes = [
            models.Index(fields=['province', 'nom']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.province.nom})"


class Commune(BaseModel, AuditMixin):
    """Commune avec coordonnées GPS et indexation spatiale."""
    nom = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=30, unique=True)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        related_name='communes'
    )
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=8,
        null=True, 
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=8,
        null=True, 
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    population = models.PositiveIntegerField(null=True, blank=True)
    superficie_km2 = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True
    )
    
    class Meta:
        verbose_name = _("Commune")
        verbose_name_plural = _("Communes")
        unique_together = ['nom', 'departement']
        ordering = ['departement__province__nom', 'departement__nom', 'nom']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['departement', 'nom']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.departement.nom})"
    
    @property
    def coordinates(self):
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None


class District(BaseModel, AuditMixin):
    """District/Quartier."""
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=40, unique=True)
    commune = models.ForeignKey(
        Commune,
        on_delete=models.PROTECT,
        related_name='districts'
    )
    
    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")
        unique_together = ['nom', 'commune']
        ordering = ['commune__nom', 'nom']


# Modèles de catégorisation optimisés
class Categorie(BaseModel, AuditMixin, SearchableMixin):
    """Catégorie principale avec hiérarchie."""
    class TypeBien(models.TextChoices):
        IMMOBILIER = 'IMMOBILIER', _('Bien Immobilier')
        MOBILIER = 'MOBILIER', _('Bien Mobilier')
        INCORPOREL = 'INCORPOREL', _('Bien Incorporel')
    
    nom = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.SlugField(max_length=50, unique=True)
    type = models.CharField(
        max_length=20, 
        choices=TypeBien.choices,
        db_index=True
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='enfants'
    )
    icone = models.CharField(max_length=50, blank=True, help_text="Classe CSS de l'icône")
    couleur = models.CharField(max_length=7, blank=True, help_text="Code couleur hexadécimal")
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")
        ordering = ['type', 'ordre', 'nom']
        indexes = [
            models.Index(fields=['type', 'actif']),
            models.Index(fields=['parent', 'ordre']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
    
    def get_descendants(self):
        """Retourne tous les descendants de la catégorie."""
        descendants = []
        for child in self.enfants.filter(actif=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class SousCategorie(BaseModel, AuditMixin, SearchableMixin):
    """Sous-catégorie avec profil technique associé."""
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name='sous_categories'
    )
    nom = models.CharField(max_length=100, db_index=True)
    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    profil_technique = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nom du modèle de profil technique associé"
    )
    champs_obligatoires = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="Liste des champs obligatoires pour cette sous-catégorie"
    )
    duree_amortissement_defaut = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Durée d'amortissement par défaut en mois"
    )
    taux_depreciation_annuel = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        verbose_name = _("Sous-catégorie")
        verbose_name_plural = _("Sous-catégories")
        ordering = ['categorie__nom', 'nom']
        indexes = [
            models.Index(fields=['categorie', 'code']),
        ]
    
    def __str__(self):
        return f"{self.nom} – {self.categorie.nom}"


# Modèle Entité optimisé
class Entite(BaseModel, AuditMixin, SearchableMixin):
    """Entité organisationnelle OPRAG."""
    class TypeEntite(models.TextChoices):
        DIRECTION = 'DIRECTION', _('Direction')
        SERVICE = 'SERVICE', _('Service')
        DEPARTEMENT = 'DEPARTEMENT', _('Département')
        AGENCE = 'AGENCE', _('Agence')
        PORT = 'PORT', _('Port')
        TERMINAL = 'TERMINAL', _('Terminal')
    
    nom = models.CharField(max_length=200, unique=True, db_index=True)
    code = models.CharField(max_length=20, unique=True)
    type = models.CharField(
        max_length=20,
        choices=TypeEntite.choices,
        db_index=True
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='sous_entites'
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entites_dirigees'
    )
    responsable_adjoint = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entites_adjoint'
    )
    commune = models.ForeignKey(
        Commune,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    budget_annuel = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    effectif = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Entité")
        verbose_name_plural = _("Entités")
        ordering = ['type', 'nom']
        indexes = [
            models.Index(fields=['type', 'actif']),
            models.Index(fields=['parent', 'nom']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_hierarchy(self):
        """Retourne la hiérarchie complète de l'entité."""
        hierarchy = []
        current = self
        while current:
            hierarchy.insert(0, current)
            current = current.parent
        return hierarchy
    
    @property
    def departement(self):
        return self.commune.departement if self.commune else None
    
    @property
    def province(self):
        return self.commune.departement.province if self.commune else None


# Modèle Bien principal optimisé
class Bien(BaseModel, AuditMixin, SearchableMixin):
    """Modèle principal pour tous les biens patrimoniaux."""
    
    class StatutBien(models.TextChoices):
        ACTIF = 'ACTIF', _('Actif - En service')
        INACTIF = 'INACTIF', _('Inactif - Hors service')
        MAINTENANCE = 'MAINTENANCE', _('En maintenance')
        REFORME = 'REFORME', _('Réformé')
        CEDE = 'CEDE', _('Cédé')
        DETRUIT = 'DETRUIT', _('Détruit')
        VOLE = 'VOLE', _('Volé')
        PERDU = 'PERDU', _('Perdu')
    
    class EtatPhysique(models.TextChoices):
        NEUF = 'NEUF', _('Neuf')
        EXCELLENT = 'EXCELLENT', _('Excellent')
        BON = 'BON', _('Bon')
        MOYEN = 'MOYEN', _('Moyen')
        MAUVAIS = 'MAUVAIS', _('Mauvais')
        HORS_USAGE = 'HORS_USAGE', _('Hors d\'usage')
    
    # Identifiants
    code_patrimoine = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Code unique OPRAG"
    )
    code_comptable = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Code comptable"
    )
    
    # Informations de base
    nom = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name='biens'
    )
    sous_categorie = models.ForeignKey(
        SousCategorie,
        on_delete=models.PROTECT,
        related_name='biens'
    )
    
    # Localisation et affectation
    entite = models.ForeignKey(
        Entite,
        on_delete=models.PROTECT,
        related_name='biens'
    )
    commune = models.ForeignKey(
        Commune,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    localisation_precise = models.CharField(
        max_length=255,
        blank=True,
        help_text="Bâtiment, étage, bureau, etc."
    )
    coordonnees_gps = models.JSONField(
        null=True,
        blank=True,
        help_text="Coordonnées GPS {lat, lng}"
    )
    
    # Valeurs et dates
    valeur_acquisition = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    devise = models.CharField(
        max_length=3,
        default='XAF',
        help_text="Code devise ISO"
    )
    date_acquisition = models.DateField()
    date_mise_service = models.DateField(null=True, blank=True)
    duree_amortissement = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="En mois"
    )
    valeur_residuelle = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # État et statut
    statut = models.CharField(
        max_length=20,
        choices=StatutBien.choices,
        default=StatutBien.ACTIF,
        db_index=True
    )
    etat_physique = models.CharField(
        max_length=20,
        choices=EtatPhysique.choices,
        default=EtatPhysique.BON,
        db_index=True
    )
    
    # Informations techniques
    numero_serie = models.CharField(max_length=100, blank=True, db_index=True)
    modele = models.CharField(max_length=100, blank=True)
    marque = models.CharField(max_length=100, blank=True)
    fournisseur = models.CharField(max_length=200, blank=True)
    
    # Documents
    facture = models.FileField(
        upload_to='factures/%Y/%m/',
        null=True,
        blank=True
    )
    photo_principale = models.ImageField(
        upload_to='photos/%Y/%m/',
        null=True,
        blank=True
    )
    documents = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des documents associés"
    )
    
    # Garantie et maintenance
    date_fin_garantie = models.DateField(null=True, blank=True)
    contrat_maintenance = models.CharField(max_length=100, blank=True)
    prochaine_maintenance = models.DateField(null=True, blank=True)
    
    # Tags et classification
    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )
    code_qr = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    code_barre = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    
    # Champs calculés
    valeur_actuelle_cache = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False
    )
    dernier_inventaire = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Bien")
        verbose_name_plural = _("Biens")
        ordering = ['-date_acquisition', 'nom']
        indexes = [
            models.Index(fields=['statut', 'etat_physique']),
            models.Index(fields=['categorie', 'sous_categorie']),
            models.Index(fields=['entite', 'statut']),
            models.Index(fields=['date_acquisition']),
            models.Index(fields=['code_qr']),
            models.Index(fields=['code_barre']),
            GinIndex(fields=['tags']),
        ]
        permissions = [
            ("can_validate_bien", "Peut valider un bien"),
            ("can_reform_bien", "Peut réformer un bien"),
            ("can_transfer_bien", "Peut transférer un bien"),
            ("can_export_data", "Peut exporter les données"),
        ]
    
    def __str__(self):
        return f"{self.code_patrimoine} - {self.nom}"
    
    def save(self, *args, **kwargs):
        # Générer le code patrimoine si non défini
        if not self.code_patrimoine:
            self.code_patrimoine = self.generate_code_patrimoine()
        
        # Calculer la valeur actuelle
        self.update_valeur_actuelle()
        
        super().save(*args, **kwargs)
    
    def generate_code_patrimoine(self):
        """Génère un code patrimoine unique."""
        from django.utils import timezone
        prefix = "OPRAG"
        year = timezone.now().year
        category_code = self.sous_categorie.code[:3].upper()
        
        # Trouver le prochain numéro
        last_code = Bien.objects.filter(
            code_patrimoine__startswith=f"{prefix}-{year}-{category_code}"
        ).order_by('-code_patrimoine').first()
        
        if last_code:
            last_number = int(last_code.code_patrimoine.split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{prefix}-{year}-{category_code}-{next_number:05d}"
    
    def update_valeur_actuelle(self):
        """Calcule et met à jour la valeur actuelle du bien."""
        if self.duree_amortissement and self.date_acquisition:
            from dateutil.relativedelta import relativedelta
            from django.utils import timezone
            
            mois_ecoules = (timezone.now().date() - self.date_acquisition).days / 30
            if mois_ecoules < self.duree_amortissement:
                taux_amortissement = mois_ecoules / self.duree_amortissement
                amortissement = float(self.valeur_acquisition) * taux_amortissement
                self.valeur_actuelle_cache = Decimal(
                    max(float(self.valeur_acquisition) - amortissement, 
                        float(self.valeur_residuelle or 0))
                )
            else:
                self.valeur_actuelle_cache = self.valeur_residuelle or 0
        else:
            self.valeur_actuelle_cache = self.valeur_acquisition
    
    @property
    def valeur_actuelle(self):
        """Retourne la valeur actuelle du bien."""
        return self.valeur_actuelle_cache or self.valeur_acquisition
    
    @property
    def age_en_mois(self):
        """Retourne l'âge du bien en mois."""
        if self.date_acquisition:
            from django.utils import timezone
            return (timezone.now().date() - self.date_acquisition).days / 30
        return 0
    
    @property
    def taux_amortissement(self):
        """Retourne le taux d'amortissement actuel."""
        if self.duree_amortissement and self.age_en_mois:
            return min(self.age_en_mois / self.duree_amortissement * 100, 100)
        return 0
    
    @property
    def responsable_actuel(self):
        """Retourne le responsable actuel du bien."""
        return self.responsabilites.filter(
            date_fin__isnull=True,
            actif=True
        ).select_related('responsable').first()
    
    def get_historique_valeurs(self):
        """Retourne l'historique des valeurs du bien."""
        return self.historique_valeurs.all().order_by('-date')
    
    def get_timeline(self):
        """Retourne la timeline complète du bien."""
        from itertools import chain
        
        # Historique des valeurs
        valeurs = self.historique_valeurs.all()
        
        # Historique des responsables
        responsables = self.responsabilites.all()
        
        # Historique des maintenances
        maintenances = self.maintenances.all()
        
        # Historique des mouvements
        mouvements = self.mouvements.all()
        
        # Combiner et trier
        timeline = sorted(
            chain(valeurs, responsables, maintenances, mouvements),
            key=lambda x: x.created,
            reverse=True
        )
        
        return timeline


# Modèles d'historique et de suivi
class HistoriqueValeur(BaseModel, AuditMixin):
    """Historique des valeurs d'un bien."""
    bien = models.ForeignKey(
        Bien,
        on_delete=models.CASCADE,
        related_name='historique_valeurs'
    )
    date = models.DateField()
    valeur = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    type_evaluation = models.CharField(
        max_length=50,
        choices=[
            ('ACQUISITION', _('Acquisition')),
            ('REEVALUATION', _('Réévaluation')),
            ('EXPERTISE', _('Expertise')),
            ('DEPRECIATION', _('Dépréciation')),
            ('CESSION', _('Cession')),
        ]
    )
    motif = models.TextField(blank=True)
    evaluateur = models.CharField(max_length=200, blank=True)
    document_justificatif = models.FileField(
        upload_to='evaluations/%Y/%m/',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Historique de valeur")
        verbose_name_plural = _("Historiques de valeurs")
        ordering = ['-date']
        unique_together = ['bien', 'date', 'type_evaluation']
        indexes = [
            models.Index(fields=['bien', '-date']),
        ]


class ResponsableBien(BaseModel, AuditMixin):
    """Responsable d'un ou plusieurs biens."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='responsabilite_biens'
    )
    matricule = models.CharField(max_length=50, unique=True)
    fonction = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email_professionnel = models.EmailField()
    entite_principale = models.ForeignKey(
        Entite,
        on_delete=models.SET_NULL,
        null=True
    )
    signature = models.ImageField(
        upload_to='signatures/',
        null=True,
        blank=True
    )
    actif = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Responsable de bien")
        verbose_name_plural = _("Responsables de biens")
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['matricule']),
            models.Index(fields=['actif']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.matricule}"


class BienResponsabilite(BaseModel, AuditMixin):
    """Association entre un bien et son responsable avec historique."""
    bien = models.ForeignKey(
        Bien,
        on_delete=models.CASCADE,
        related_name='responsabilites'
    )
    responsable = models.ForeignKey(
        ResponsableBien,
        on_delete=models.PROTECT,
        related_name='biens_geres'
    )
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    type_affectation = models.CharField(
        max_length=20,
        choices=[
            ('PERMANENT', _('Permanent')),
            ('TEMPORAIRE', _('Temporaire')),
            ('DELEGATION', _('Délégation')),
        ],
        default='PERMANENT'
    )
    motif = models.TextField(blank=True)
    document_affectation = models.FileField(
        upload_to='affectations/%Y/%m/',
        null=True,
        blank=True
    )
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Responsabilité de bien")
        verbose_name_plural = _("Responsabilités de biens")
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['bien', 'actif']),
            models.Index(fields=['responsable', 'actif']),
            models.Index(fields=['date_debut', 'date_fin']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(date_fin__gte=F('date_debut')) | Q(date_fin__isnull=True),
                name='date_fin_after_date_debut'
            ),
        ]
    
    def save(self, *args, **kwargs):
        # Désactiver les autres responsabilités actives
        if self.actif and not self.date_fin:
            BienResponsabilite.objects.filter(
                bien=self.bien,
                actif=True,
                date_fin__isnull=True
            ).exclude(pk=self.pk).update(
                date_fin=self.date_debut,
                actif=False
            )
        super().save(*args, **kwargs)