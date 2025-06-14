from django.db import models
from django.utils import timezone

# ----------- LOCALISATION -----------
class Province(models.Model):
    nom = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nom

class Departement(models.Model):
    nom = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nom} ({self.province.nom})"

class Commune(models.Model):
    nom = models.CharField(max_length=100)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.nom

class District(models.Model):
    nom = models.CharField(max_length=100)
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nom} ({self.commune.nom})"

# ----------- CATEGORISATION -----------
class Categorie(models.Model):
    TYPE_CHOICES = [
        ('immobilier', 'Bien Immobilier'),
        ('mobilier', 'Bien Mobilier'),
    ]
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"

class SousCategorie(models.Model):
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='sous_categories')
    nom = models.CharField(max_length=100)
    code = models.SlugField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Code système unique (ex: 'ambulance', 'serveur')"
    )

    def __str__(self):
        return f"{self.nom} – {self.categorie.nom}"

# ----------- ENTITÉ -----------
class Entite(models.Model):
    nom = models.CharField(max_length=100)
    responsable = models.CharField(max_length=100)
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nom

    @property
    def departement(self):
        return self.commune.departement if self.commune else None

    @property
    def province(self):
        return self.commune.departement.province if self.commune else None

# ----------- BIEN -----------
class Bien(models.Model):
    nom = models.CharField(max_length=100)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    sous_categorie = models.ForeignKey(SousCategorie, on_delete=models.PROTECT, null=True, blank=True)
    entite = models.ForeignKey(Entite, on_delete=models.CASCADE)
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    valeur_initiale = models.DecimalField(max_digits=12, decimal_places=2)
    date_acquisition = models.DateField()
    description = models.TextField(blank=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    duree_amortissement = models.IntegerField(blank=True, null=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    annee_construction = models.PositiveIntegerField(null=True, blank=True)
    statut_juridique = models.CharField(max_length=100, blank=True)
    justificatif = models.FileField(upload_to='justificatifs/', null=True, blank=True)

    def __str__(self):
        return self.nom

    @property
    def responsable_actuel(self):
        return self.responsabilites.filter(type_affectation='permanent').first()

# ----------- RESPONSABLES -----------
class ResponsableBien(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    matricule = models.CharField(max_length=50, unique=True)
    fonction = models.CharField(max_length=100)
    categorie = models.CharField(max_length=50)
    corps = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} – {self.fonction}"

class BienResponsabilite(models.Model):
    AFFECTATION_CHOICES = [
        ('permanent', 'Permanent'),
        ('temporaire', 'Temporaire'),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='responsabilites')
    responsable = models.ForeignKey(ResponsableBien, on_delete=models.CASCADE)
    date_affectation = models.DateField()
    type_affectation = models.CharField(max_length=20, choices=AFFECTATION_CHOICES)
    motif = models.TextField(blank=True)

    # Champs spécifiques selon le type de bien
    numero_permis = models.CharField(max_length=50, blank=True, null=True)
    date_permis = models.DateField(blank=True, null=True)
    categorie_permis = models.CharField(max_length=10, blank=True, null=True)
    composition_foyer = models.TextField(blank=True, null=True)
    conditions_occupation = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    formations = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_affectation']
        verbose_name = "Responsabilité d'un bien"
        verbose_name_plural = "Responsabilités des biens"

    def __str__(self):
        return f"{self.responsable} – {self.bien} ({self.date_affectation})"

# ----------- HISTORIQUE -----------
class HistoriqueValeur(models.Model):
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='historiques')
    date = models.DateField()
    valeur = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.bien.nom} - {self.valeur} au {self.date}"

# Profils techniques pour chaque type de Bien
class ProfilVehicule(models.Model):
    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_vehicule')
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    matricule = models.CharField(max_length=50, null=True, blank=True)
    numero_chassis = models.CharField(max_length=100, null=True, blank=True)
    date_fabrication = models.DateField(null=True, blank=True)
    date_acquisition = models.DateField(null=True, blank=True)
    date_derniere_maintenance = models.DateField(null=True, blank=True)
    prochaine_maintenance = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.marque} {self.modele} ({self.matricule})"

class ProfilImmeuble(models.Model):
    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_immeuble')
    surface = models.DecimalField(max_digits=8, decimal_places=2)
    nb_etages = models.PositiveIntegerField()
    annee_construction = models.PositiveIntegerField()
    securite = models.CharField(max_length=255)

    def __str__(self):
        return f"Immeuble {self.bien.nom} - {self.surface} m²"

class ProfilInformatique(models.Model):
    STATUT_CHOICES = [
        ('en_service', 'En service'),
        ('en_maintenance', 'En maintenance'),
        ('hors_service', 'Hors service'),
        ('en_attente', 'En attente de déploiement'),
    ]
    TYPE_CHOICES = [
        ('ordinateur_fixe', 'Ordinateur fixe'),
        ('ordinateur_portable', 'Ordinateur portable'),
        ('serveur', 'Serveur'),
        ('imprimante', 'Imprimante'),
        ('scanner', 'Scanner'),
        ('photocopieur', 'Photocopieur'),
        ('reseau', 'Équipement réseau'),
        ('stockage', 'Solution de stockage'),
        ('autre', 'Autre'),
    ]

    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_informatique')
    type_equipement = models.CharField(max_length=50, choices=TYPE_CHOICES)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100)
    date_fabrication = models.DateField(null=True, blank=True)
    processeur = models.CharField(max_length=100, blank=True)
    memoire_ram = models.CharField(max_length=50, blank=True)
    capacite_stockage = models.CharField(max_length=50, blank=True)
    carte_graphique = models.CharField(max_length=100, blank=True)
    spec_tech = models.TextField(blank=True)
    os = models.CharField(max_length=100, blank=True)
    version_os = models.CharField(max_length=50, blank=True)
    logiciels = models.TextField(blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    adresse_mac = models.CharField(max_length=17, blank=True)
    nom_reseau = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_service')
    date_derniere_maj = models.DateField(auto_now=True)
    date_derniere_maintenance = models.DateField(null=True, blank=True)
    prochaine_maintenance = models.DateField(null=True, blank=True)
    date_acquisition = models.DateField(null=True, blank=True)
    date_mise_service = models.DateField(null=True, blank=True)
    fin_garantie = models.DateField(null=True, blank=True)
    contrat_maintenance = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_type_equipement_display()} - {self.marque} {self.modele}"

class ProfilEquipementMedical(models.Model):
    CLASSE_RISQUE_CHOICES = [
        ('i', 'Classe I - Risque faible'),
        ('iia', 'Classe IIa - Risque modéré'),
        ('iib', 'Classe IIb - Risque élevé'),
        ('iii', 'Classe III - Risque critique'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif - En service'),
        ('maintenance', 'En maintenance'),
        ('stockage', 'En stockage'),
        ('inutilisable', 'Hors service'),
        ('calibration', 'En calibration'),
    ]
    TYPE_CHOICES = [
        ('diagnostic', 'Diagnostic'),
        ('therapeutique', 'Thérapeutique'),
        ('laboratoire', 'Laboratoire'),
        ('monitoring', 'Surveillance'),
        ('imagerie', 'Imagerie'),
        ('chirurgical', 'Chirurgical'),
        ('sterilisation', 'Stérilisation'),
        ('autre', 'Autre'),
    ]

    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_equipement_medical')
    type_equipement = models.CharField(max_length=50, choices=TYPE_CHOICES)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100)
    date_fabrication = models.DateField(null=True, blank=True)
    certification = models.CharField(max_length=100, blank=True)
    classe_risque = models.CharField(max_length=3, choices=CLASSE_RISQUE_CHOICES, blank=True)
    normes_applicables = models.TextField(blank=True)
    organisme_certification = models.CharField(max_length=100, blank=True)
    parametres_techniques = models.TextField(blank=True)
    source_energie = models.CharField(max_length=100, blank=True)
    consommation = models.CharField(max_length=50, blank=True)
    duree_vie = models.PositiveIntegerField(null=True, blank=True)
    date_installation = models.DateField(null=True, blank=True)
    date_derniere_maintenance = models.DateField(null=True, blank=True)
    frequence_maintenance = models.PositiveIntegerField(default=365)
    maintenance = models.TextField(blank=True)
    pieces = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    departement_utilisation = models.CharField(max_length=100, blank=True)
    utilisateurs_formes = models.TextField(blank=True)
    date_acquisition = models.DateField(null=True, blank=True)
    fin_garantie = models.DateField(null=True, blank=True)
    contrat_maintenance = models.CharField(max_length=100, blank=True)
    fournisseur_service = models.CharField(max_length=100, blank=True)
    contact_sav = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_type_equipement_display()} - {self.marque} {self.modele}" 

class ProfilMobilier(models.Model):
    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_mobilier')
    materiau = models.CharField(max_length=100)
    couleur = models.CharField(max_length=50)
    fabricant = models.CharField(max_length=100)
    annee_fabrication = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Mobilier {self.bien.nom} - {self.materiau} ({self.couleur})"

class ProfilTerrain(models.Model):
    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_terrain')
    superficie = models.DecimalField(max_digits=12, decimal_places=2)
    statut_juridique = models.CharField(max_length=255)
    usage = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Terrain {self.bien.nom} - {self.superficie} m²"

class ProfilConsommable(models.Model):
    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name='profil_consommable')
    quantite_initiale = models.PositiveIntegerField()
    unite = models.CharField(max_length=50)
    stock_securite = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Consommable {self.bien.nom} - {self.quantite_initiale} {self.unite}"