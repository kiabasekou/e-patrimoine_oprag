# apps/patrimoine/services/bien_service.py
"""
Services métier pour la gestion des biens avec logique business complexe.
Implémente les patterns DDD (Domain Driven Design).
"""
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db import transaction
from django.db.models import Q, F, Sum, Count, Avg
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import logging

from apps.patrimoine.models import (
    Bien, HistoriqueValeur, BienResponsabilite,
    ResponsableBien, Entite, SousCategorie,
    MouvementBien, Maintenance, Inventaire
)
from apps.notifications.services import NotificationService
from apps.audit.services import AuditService
from .validators import BienValidator
from .calculators import AmortissementCalculator, ValeurCalculator

logger = logging.getLogger(__name__)


class BienService:
    """
    Service principal pour la gestion des biens.
    Encapsule la logique métier complexe.
    """
    
    def __init__(self):
        self.validator = BienValidator()
        self.amortissement_calc = AmortissementCalculator()
        self.valeur_calc = ValeurCalculator()
        self.notification_service = NotificationService()
        self.audit_service = AuditService()
    
    @transaction.atomic
    def creer_bien(
        self,
        data: Dict,
        user,
        documents: Optional[List] = None
    ) -> Bien:
        """
        Crée un nouveau bien avec validation complète et workflow.
        """
        # Validation des données
        self.validator.valider_creation_bien(data)
        
        # Générer le code patrimoine
        if 'code_patrimoine' not in data:
            data['code_patrimoine'] = self._generer_code_patrimoine(
                data['sous_categorie']
            )
        
        # Calculer les valeurs par défaut
        if 'duree_amortissement' not in data:
            data['duree_amortissement'] = data['sous_categorie'].duree_amortissement_defaut
        
        # Créer le bien
        bien = Bien.objects.create(
            **data,
            created_by=user,
            modified_by=user
        )
        
        # Créer l'historique initial
        HistoriqueValeur.objects.create(
            bien=bien,
            date=bien.date_acquisition,
            valeur=bien.valeur_acquisition,
            type_evaluation='ACQUISITION',
            motif='Valeur d\'acquisition initiale',
            created_by=user
        )
        
        # Gérer les documents
        if documents:
            self._attacher_documents(bien, documents)
        
        # Créer le profil technique selon la sous-catégorie
        self._creer_profil_technique(bien, data.get('profil_data', {}))
        
        # Workflow d'approbation si nécessaire
        if settings.OPRAG_CONFIG.get('REQUIRE_APPROVAL_WORKFLOW'):
            self._initier_workflow_approbation(bien, user)
        
        # Audit et notifications
        self.audit_service.log_creation_bien(bien, user)
        self.notification_service.notifier_nouveau_bien(bien)
        
        logger.info(f"Bien créé: {bien.code_patrimoine} par {user}")
        
        return bien
    
    @transaction.atomic
    def modifier_bien(
        self,
        bien: Bien,
        data: Dict,
        user,
        motif: str = ""
    ) -> Bien:
        """
        Modifie un bien avec traçabilité complète.
        """
        # Validation
        self.validator.valider_modification_bien(bien, data)
        
        # Sauvegarder l'état précédent pour l'audit
        etat_precedent = {
            field: getattr(bien, field)
            for field in data.keys()
        }
        
        # Appliquer les modifications
        for field, value in data.items():
            setattr(bien, field, value)
        
        bien.modified_by = user
        bien.save()
        
        # Si changement de valeur, créer un historique
        if 'valeur_acquisition' in data:
            self._creer_historique_valeur(
                bien,
                data['valeur_acquisition'],
                'REEVALUATION',
                motif or 'Modification de la valeur',
                user
            )
        
        # Audit
        self.audit_service.log_modification_bien(
            bien, user, etat_precedent, data, motif
        )
        
        # Notifications si changements critiques
        if self._est_changement_critique(etat_precedent, data):
            self.notification_service.notifier_changement_critique(bien, data)
        
        return bien
    
    @transaction.atomic
    def transferer_bien(
        self,
        bien: Bien,
        nouvelle_entite: Entite,
        user,
        motif: str,
        date_effet: Optional[date] = None
    ) -> MouvementBien:
        """
        Transfère un bien vers une nouvelle entité.
        """
        # Validation
        if not user.has_perm('patrimoine.can_transfer_bien'):
            raise ValidationError("Permission insuffisante pour transférer un bien")
        
        if bien.entite == nouvelle_entite:
            raise ValidationError("L'entité de destination est identique à l'origine")
        
        date_effet = date_effet or timezone.now().date()
        
        # Créer le mouvement
        mouvement = MouvementBien.objects.create(
            bien=bien,
            entite_origine=bien.entite,
            entite_destination=nouvelle_entite,
            type_mouvement='TRANSFERT',
            date_mouvement=date_effet,
            motif=motif,
            statut='APPROUVE' if user.is_superuser else 'EN_ATTENTE',
            created_by=user
        )
        
        # Si approuvé directement, effectuer le transfert
        if mouvement.statut == 'APPROUVE':
            self._executer_transfert(bien, nouvelle_entite, user)
        
        # Notifications
        self.notification_service.notifier_transfert_bien(
            bien, mouvement, [bien.entite.responsable, nouvelle_entite.responsable]
        )
        
        return mouvement
    
    @transaction.atomic
    def affecter_responsable(
        self,
        bien: Bien,
        responsable: ResponsableBien,
        user,
        type_affectation: str = 'PERMANENT',
        date_debut: Optional[date] = None,
        date_fin: Optional[date] = None,
        motif: str = ""
    ) -> BienResponsabilite:
        """
        Affecte un responsable à un bien.
        """
        # Validation
        self.validator.valider_affectation_responsable(
            bien, responsable, date_debut, date_fin
        )
        
        date_debut = date_debut or timezone.now().date()
        
        # Clôturer l'affectation actuelle si elle existe
        affectation_actuelle = bien.responsabilites.filter(
            actif=True,
            date_fin__isnull=True
        ).first()
        
        if affectation_actuelle:
            affectation_actuelle.date_fin = date_debut - timedelta(days=1)
            affectation_actuelle.actif = False
            affectation_actuelle.save()
        
        # Créer la nouvelle affectation
        nouvelle_affectation = BienResponsabilite.objects.create(
            bien=bien,
            responsable=responsable,
            date_debut=date_debut,
            date_fin=date_fin,
            type_affectation=type_affectation,
            motif=motif,
            actif=True,
            created_by=user
        )
        
        # Notifications
        self.notification_service.notifier_affectation_responsable(
            bien, responsable, affectation_actuelle
        )
        
        # Audit
        self.audit_service.log_affectation_responsable(
            bien, responsable, user, motif
        )
        
        return nouvelle_affectation
    
    @transaction.atomic
    def reformer_bien(
        self,
        bien: Bien,
        user,
        motif: str,
        date_reforme: Optional[date] = None,
        valeur_residuelle: Optional[Decimal] = None
    ) -> Bien:
        """
        Réforme un bien (mise hors service définitive).
        """
        # Validation
        if not user.has_perm('patrimoine.can_reform_bien'):
            raise ValidationError("Permission insuffisante pour réformer un bien")
        
        if bien.statut == 'REFORME':
            raise ValidationError("Ce bien est déjà réformé")
        
        date_reforme = date_reforme or timezone.now().date()
        
        # Mettre à jour le bien
        bien.statut = 'REFORME'
        bien.valeur_residuelle = valeur_residuelle or 0
        bien.modified_by = user
        bien.save()
        
        # Créer l'historique de valeur
        HistoriqueValeur.objects.create(
            bien=bien,
            date=date_reforme,
            valeur=bien.valeur_residuelle,
            type_evaluation='DEPRECIATION',
            motif=f"Réforme: {motif}",
            created_by=user
        )
        
        # Clôturer toutes les responsabilités actives
        bien.responsabilites.filter(
            actif=True,
            date_fin__isnull=True
        ).update(
            date_fin=date_reforme,
            actif=False
        )
        
        # Audit et notifications
        self.audit_service.log_reforme_bien(bien, user, motif)
        self.notification_service.notifier_reforme_bien(bien)
        
        return bien
    
    def calculer_amortissement(
        self,
        bien: Bien,
        date_calcul: Optional[date] = None
    ) -> Dict:
        """
        Calcule l'amortissement d'un bien à une date donnée.
        """
        date_calcul = date_calcul or timezone.now().date()
        
        return self.amortissement_calc.calculer(
            valeur_acquisition=bien.valeur_acquisition,
            date_acquisition=bien.date_acquisition,
            duree_amortissement=bien.duree_amortissement,
            valeur_residuelle=bien.valeur_residuelle,
            date_calcul=date_calcul,
            methode=settings.OPRAG_CONFIG.get('DEPRECIATION_METHOD', 'LINEAR')
        )
    
    def evaluer_bien(
        self,
        bien: Bien,
        nouvelle_valeur: Decimal,
        user,
        type_evaluation: str,
        motif: str,
        evaluateur: Optional[str] = None,
        document: Optional = None
    ) -> HistoriqueValeur:
        """
        Crée une nouvelle évaluation pour un bien.
        """
        # Validation
        if nouvelle_valeur < 0:
            raise ValidationError("La valeur ne peut pas être négative")
        
        # Créer l'historique
        historique = HistoriqueValeur.objects.create(
            bien=bien,
            date=timezone.now().date(),
            valeur=nouvelle_valeur,
            type_evaluation=type_evaluation,
            motif=motif,
            evaluateur=evaluateur or user.get_full_name(),
            document_justificatif=document,
            created_by=user
        )
        
        # Mettre à jour la valeur actuelle cachée
        bien.valeur_actuelle_cache = nouvelle_valeur
        bien.save(update_fields=['valeur_actuelle_cache'])
        
        # Notifications si écart important
        ecart = abs(float(nouvelle_valeur - bien.valeur_acquisition))
        pourcentage_ecart = (ecart / float(bien.valeur_acquisition)) * 100
        
        if pourcentage_ecart > 20:
            self.notification_service.notifier_evaluation_importante(
                bien, historique, pourcentage_ecart
            )
        
        return historique
    
    def generer_rapport_bien(
        self,
        bien: Bien,
        inclure_historique: bool = True,
        inclure_documents: bool = True
    ) -> Dict:
        """
        Génère un rapport complet sur un bien.
        """
        rapport = {
            'informations_generales': {
                'code_patrimoine': bien.code_patrimoine,
                'nom': bien.nom,
                'description': bien.description,
                'categorie': bien.categorie.nom,
                'sous_categorie': bien.sous_categorie.nom,
                'entite': bien.entite.nom,
                'localisation': {
                    'commune': bien.commune.nom if bien.commune else None,
                    'departement': bien.commune.departement.nom if bien.commune else None,
                    'province': bien.commune.departement.province.nom if bien.commune else None,
                    'localisation_precise': bien.localisation_precise,
                    'coordonnees': bien.coordonnees_gps
                }
            },
            'valeurs': {
                'valeur_acquisition': float(bien.valeur_acquisition),
                'valeur_actuelle': float(bien.valeur_actuelle),
                'date_acquisition': bien.date_acquisition.isoformat(),
                'age_mois': bien.age_en_mois,
                'taux_amortissement': bien.taux_amortissement,
                'amortissement': self.calculer_amortissement(bien)
            },
            'statut': {
                'statut': bien.get_statut_display(),
                'etat_physique': bien.get_etat_physique_display(),
                'date_mise_service': bien.date_mise_service.isoformat() if bien.date_mise_service else None,
                'garantie': {
                    'sous_garantie': bien.date_fin_garantie and bien.date_fin_garantie > timezone.now().date(),
                    'date_fin': bien.date_fin_garantie.isoformat() if bien.date_fin_garantie else None
                }
            },
            'responsable': None,
            'statistiques': {
                'nombre_mouvements': bien.mouvements.count(),
                'nombre_maintenances': bien.maintenances.count(),
                'nombre_evaluations': bien.historique_valeurs.count(),
                'derniere_maintenance': None,
                'prochaine_maintenance': bien.prochaine_maintenance.isoformat() if bien.prochaine_maintenance else None
            }
        }
        
        # Responsable actuel
        responsable = bien.responsable_actuel
        if responsable:
            rapport['responsable'] = {
                'nom': responsable.responsable.user.get_full_name(),
                'fonction': responsable.responsable.fonction,
                'depuis': responsable.date_debut.isoformat(),
                'type': responsable.get_type_affectation_display()
            }
        
        # Dernière maintenance
        derniere_maintenance = bien.maintenances.order_by('-date_realisation').first()
        if derniere_maintenance:
            rapport['statistiques']['derniere_maintenance'] = {
                'date': derniere_maintenance.date_realisation.isoformat(),
                'type': derniere_maintenance.type_maintenance,
                'cout': float(derniere_maintenance.cout) if derniere_maintenance.cout else None
            }
        
        # Historique si demandé
        if inclure_historique:
            rapport['historique'] = {
                'valeurs': [
                    {
                        'date': h.date.isoformat(),
                        'valeur': float(h.valeur),
                        'type': h.get_type_evaluation_display(),
                        'motif': h.motif
                    }
                    for h in bien.historique_valeurs.order_by('-date')[:10]
                ],
                'responsables': [
                    {
                        'responsable': r.responsable.user.get_full_name(),
                        'periode': f"{r.date_debut.isoformat()} - {r.date_fin.isoformat() if r.date_fin else 'En cours'}",
                        'type': r.get_type_affectation_display()
                    }
                    for r in bien.responsabilites.order_by('-date_debut')[:5]
                ]
            }
        
        # Documents si demandé
        if inclure_documents:
            rapport['documents'] = {
                'facture': bool(bien.facture),
                'photo': bool(bien.photo_principale),
                'autres': len(bien.documents) if bien.documents else 0
            }
        
        return rapport
    
    def rechercher_biens_critiques(
        self,
        entite: Optional[Entite] = None
    ) -> Dict[str, List[Bien]]:
        """
        Identifie les biens nécessitant une attention particulière.
        """
        queryset = Bien.objects.filter(is_removed=False)
        if entite:
            queryset = queryset.filter(entite=entite)
        
        return {
            'sans_responsable': list(
                queryset.filter(
                    responsabilites__isnull=True
                ).select_related('categorie', 'entite')[:20]
            ),
            'maintenance_en_retard': list(
                queryset.filter(
                    prochaine_maintenance__lt=timezone.now().date()
                ).select_related('categorie', 'entite')
                .order_by('prochaine_maintenance')[:20]
            ),
            'garantie_expiree_recemment': list(
                queryset.filter(
                    date_fin_garantie__lt=timezone.now().date(),
                    date_fin_garantie__gte=timezone.now().date() - timedelta(days=90)
                ).select_related('categorie', 'entite')
                .order_by('-date_fin_garantie')[:20]
            ),
            'etat_critique': list(
                queryset.filter(
                    etat_physique__in=['MAUVAIS', 'HORS_USAGE']
                ).exclude(statut='REFORME')
                .select_related('categorie', 'entite')[:20]
            ),
            'valeur_elevee_sans_securite': list(
                queryset.filter(
                    valeur_acquisition__gte=10000000  # 10 millions XAF
                ).exclude(
                    tags__contains=['SECURISE']
                ).select_related('categorie', 'entite')
                .order_by('-valeur_acquisition')[:10]
            )
        }
    
    def _generer_code_patrimoine(self, sous_categorie: SousCategorie) -> str:
        """Génère un code patrimoine unique."""
        prefix = settings.OPRAG_CONFIG.get('ASSET_CODE_PREFIX', 'OPRAG')
        year = timezone.now().year
        category_code = sous_categorie.code[:4].upper()
        
        # Dernier numéro utilisé
        last_bien = Bien.objects.filter(
            code_patrimoine__startswith=f"{prefix}-{year}-{category_code}"
        ).order_by('-code_patrimoine').first()
        
        if last_bien:
            try:
                last_number = int(last_bien.code_patrimoine.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}-{year}-{category_code}-{next_number:05d}"
    
    def _creer_profil_technique(self, bien: Bien, profil_data: Dict):
        """Crée le profil technique selon le type de bien."""
        profil_model_name = bien.sous_categorie.profil_technique
        if not profil_model_name:
            return
        
        try:
            from django.apps import apps
            ProfilModel = apps.get_model('patrimoine', profil_model_name)
            ProfilModel.objects.create(bien=bien, **profil_data)
        except Exception as e:
            logger.error(f"Erreur création profil technique: {e}")
    
    def _est_changement_critique(self, avant: Dict, apres: Dict) -> bool:
        """Détermine si un changement est critique."""
        champs_critiques = ['entite', 'statut', 'valeur_acquisition']
        return any(
            field in apres and avant.get(field) != apres[field]
            for field in champs_critiques
        )
    
    def _executer_transfert(self, bien: Bien, nouvelle_entite: Entite, user):
        """Exécute le transfert effectif d'un bien."""
        bien.entite = nouvelle_entite
        bien.modified_by = user
        bien.save()
        
        # Clôturer les responsabilités de l'ancienne entité
        bien.responsabilites.filter(
            actif=True,
            responsable__entite_principale=bien.entite
        ).update(
            date_fin=timezone.now().date(),
            actif=False
        )


# apps/patrimoine/services/inventaire_service.py
class InventaireService:
    """
    Service de gestion des inventaires physiques.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.audit_service = AuditService()
    
    @transaction.atomic
    def creer_campagne_inventaire(
        self,
        nom: str,
        date_debut: date,
        date_fin: date,
        entites: List[Entite],
        user,
        responsables: Optional[List[ResponsableBien]] = None
    ) -> 'CampagneInventaire':
        """
        Crée une nouvelle campagne d'inventaire.
        """
        from apps.patrimoine.models import CampagneInventaire, InventaireBien
        
        # Validation
        if date_debut >= date_fin:
            raise ValidationError("La date de fin doit être après la date de début")
        
        if date_debut < timezone.now().date():
            raise ValidationError("La date de début ne peut pas être dans le passé")
        
        # Créer la campagne
        campagne = CampagneInventaire.objects.create(
            nom=nom,
            date_debut=date_debut,
            date_fin=date_fin,
            statut='PLANIFIE',
            created_by=user
        )
        
        campagne.entites.set(entites)
        if responsables:
            campagne.responsables.set(responsables)
        
        # Préparer les biens à inventorier
        biens = Bien.objects.filter(
            entite__in=entites,
            statut__in=['ACTIF', 'INACTIF', 'MAINTENANCE']
        )
        
        # Créer les entrées d'inventaire
        inventaires = []
        for bien in biens:
            inventaires.append(
                InventaireBien(
                    campagne=campagne,
                    bien=bien,
                    statut='A_VERIFIER',
                    valeur_comptable=bien.valeur_actuelle
                )
            )
        
        InventaireBien.objects.bulk_create(inventaires)
        
        # Notifications
        self.notification_service.notifier_nouvelle_campagne_inventaire(
            campagne, responsables or []
        )
        
        # Planifier les rappels
        self._planifier_rappels_inventaire(campagne)
        
        logger.info(f"Campagne d'inventaire créée: {nom} ({biens.count()} biens)")
        
        return campagne
    
    @transaction.atomic
    def saisir_inventaire_bien(
        self,
        inventaire_bien: 'InventaireBien',
        user,
        present: bool,
        etat_constate: Optional[str] = None,
        localisation_constatee: Optional[str] = None,
        observations: Optional[str] = None,
        photos: Optional[List] = None
    ) -> 'InventaireBien':
        """
        Saisit le résultat d'inventaire pour un bien.
        """
        # Validation
        if inventaire_bien.statut not in ['A_VERIFIER', 'EN_COURS']:
            raise ValidationError("Ce bien a déjà été inventorié")
        
        # Mettre à jour l'inventaire
        inventaire_bien.date_verification = timezone.now()
        inventaire_bien.verifie_par = user
        inventaire_bien.present = present
        
        if present:
            inventaire_bien.statut = 'VERIFIE'
            inventaire_bien.etat_constate = etat_constate or inventaire_bien.bien.etat_physique
            inventaire_bien.localisation_constatee = localisation_constatee
        else:
            inventaire_bien.statut = 'ANOMALIE'
            inventaire_bien.type_anomalie = 'NON_TROUVE'
        
        inventaire_bien.observations = observations
        inventaire_bien.save()
        
        # Gérer les photos
        if photos:
            self._attacher_photos_inventaire(inventaire_bien, photos)
        
        # Mettre à jour le bien
        bien = inventaire_bien.bien
        bien.dernier_inventaire = timezone.now()
        
        if present and etat_constate:
            bien.etat_physique = etat_constate
        
        bien.save()
        
        # Détecter les anomalies
        anomalies = self._detecter_anomalies_inventaire(inventaire_bien)
        if anomalies:
            self._traiter_anomalies_inventaire(inventaire_bien, anomalies)
        
        return inventaire_bien
    
    def generer_rapport_inventaire(
        self,
        campagne: 'CampagneInventaire'
    ) -> Dict:
        """
        Génère un rapport complet d'inventaire.
        """
        inventaires = campagne.inventaires.select_related(
            'bien__categorie',
            'bien__entite'
        )
        
        total = inventaires.count()
        verifies = inventaires.filter(statut='VERIFIE').count()
        anomalies = inventaires.filter(statut='ANOMALIE')
        
        rapport = {
            'campagne': {
                'nom': campagne.nom,
                'periode': f"{campagne.date_debut} - {campagne.date_fin}",
                'statut': campagne.get_statut_display(),
                'progression': (verifies / total * 100) if total > 0 else 0
            },
            'statistiques': {
                'total_biens': total,
                'biens_verifies': verifies,
                'biens_non_verifies': inventaires.filter(statut='A_VERIFIER').count(),
                'anomalies_detectees': anomalies.count(),
                'taux_presence': (
                    inventaires.filter(present=True).count() / total * 100
                ) if total > 0 else 0
            },
            'anomalies_par_type': dict(
                anomalies.values_list('type_anomalie').annotate(Count('id'))
            ),
            'valeur_totale': {
                'comptable': inventaires.aggregate(
                    Sum('valeur_comptable')
                )['valeur_comptable__sum'] or 0,
                'constatee': inventaires.filter(
                    valeur_constatee__isnull=False
                ).aggregate(
                    Sum('valeur_constatee')
                )['valeur_constatee__sum'] or 0
            },
            'biens_non_trouves': [
                {
                    'code': inv.bien.code_patrimoine,
                    'nom': inv.bien.nom,
                    'valeur': float(inv.bien.valeur_actuelle),
                    'derniere_localisation': inv.bien.localisation_precise
                }
                for inv in anomalies.filter(type_anomalie='NON_TROUVE')[:20]
            ],
            'ecarts_valeur_importants': self._identifier_ecarts_valeur(campagne),
            'recommandations': self._generer_recommandations(campagne)
        }
        
        return rapport
    
    def _detecter_anomalies_inventaire(
        self,
        inventaire: 'InventaireBien'
    ) -> List[str]:
        """Détecte les anomalies lors de l'inventaire."""
        anomalies = []
        
        if not inventaire.present:
            anomalies.append('NON_TROUVE')
            return anomalies
        
        bien = inventaire.bien
        
        # Changement de localisation
        if (inventaire.localisation_constatee and 
            inventaire.localisation_constatee != bien.localisation_precise):
            anomalies.append('DEPLACEMENT_NON_AUTORISE')
        
        # Dégradation importante
        if inventaire.etat_constate in ['MAUVAIS', 'HORS_USAGE']:
            if bien.etat_physique not in ['MAUVAIS', 'HORS_USAGE']:
                anomalies.append('DEGRADATION_IMPORTANTE')
        
        # Écart de valeur
        if inventaire.valeur_constatee:
            ecart = abs(float(inventaire.valeur_constatee - inventaire.valeur_comptable))
            pourcentage = (ecart / float(inventaire.valeur_comptable)) * 100
            if pourcentage > 20:
                anomalies.append('ECART_VALEUR_IMPORTANT')
        
        return anomalies
    
    def _planifier_rappels_inventaire(self, campagne):
        """Planifie les rappels automatiques pour l'inventaire."""
        from apps.patrimoine.tasks import (
            rappel_debut_inventaire,
            rappel_fin_proche_inventaire
        )
        
        # Rappel au début
        rappel_debut_inventaire.apply_async(
            args=[str(campagne.id)],
            eta=campagne.date_debut
        )
        
        # Rappel 3 jours avant la fin
        rappel_fin_proche_inventaire.apply_async(
            args=[str(campagne.id)],
            eta=campagne.date_fin - timedelta(days=3)
        )


# apps/patrimoine/services/maintenance_service.py
class MaintenanceService:
    """
    Service de gestion de la maintenance des biens.
    """
    
    @transaction.atomic
    def planifier_maintenance(
        self,
        bien: Bien,
        type_maintenance: str,
        date_prevue: date,
        user,
        description: str = "",
        prestataire: Optional[str] = None,
        cout_estime: Optional[Decimal] = None,
        recurrence: Optional[str] = None
    ) -> 'Maintenance':
        """
        Planifie une maintenance pour un bien.
        """
        from apps.patrimoine.models import Maintenance, PlanMaintenance
        
        # Validation
        if date_prevue < timezone.now().date():
            raise ValidationError("La date de maintenance ne peut pas être dans le passé")
        
        if bien.statut == 'REFORME':
            raise ValidationError("Impossible de planifier une maintenance sur un bien réformé")
        
        # Créer la maintenance
        maintenance = Maintenance.objects.create(
            bien=bien,
            type_maintenance=type_maintenance,
            date_prevue=date_prevue,
            description=description,
            prestataire=prestataire,
            cout_estime=cout_estime,
            statut='PLANIFIEE',
            created_by=user
        )
        
        # Mettre à jour la prochaine maintenance du bien
        if not bien.prochaine_maintenance or date_prevue < bien.prochaine_maintenance:
            bien.prochaine_maintenance = date_prevue
            bien.save()
        
        # Créer un plan de maintenance récurrent si demandé
        if recurrence:
            self._creer_plan_maintenance_recurrent(
                bien, type_maintenance, date_prevue, recurrence, user
            )
        
        # Planifier les rappels
        from apps.patrimoine.tasks import rappel_maintenance
        rappel_maintenance.apply_async(
            args=[str(maintenance.id)],
            eta=date_prevue - timedelta(days=7)
        )
        
        # Notification
        self.notification_service.notifier_maintenance_planifiee(maintenance)
        
        return maintenance
    
    @transaction.atomic
    def executer_maintenance(
        self,
        maintenance: 'Maintenance',
        user,
        date_realisation: Optional[date] = None,
        cout_reel: Optional[Decimal] = None,
        rapport: Optional[str] = None,
        pieces_changees: Optional[List[str]] = None,
        prochaine_maintenance: Optional[date] = None
    ) -> 'Maintenance':
        """
        Enregistre l'exécution d'une maintenance.
        """
        # Validation
        if maintenance.statut == 'REALISEE':
            raise ValidationError("Cette maintenance a déjà été réalisée")
        
        date_realisation = date_realisation or timezone.now().date()
        
        # Mettre à jour la maintenance
        maintenance.date_realisation = date_realisation
        maintenance.cout_reel = cout_reel or maintenance.cout_estime
        maintenance.rapport = rapport
        maintenance.statut = 'REALISEE'
        maintenance.realise_par = user
        maintenance.save()
        
        # Enregistrer les pièces changées
        if pieces_changees:
            maintenance.pieces_changees = pieces_changees
            maintenance.save()
        
        # Mettre à jour le bien
        bien = maintenance.bien
        bien.date_derniere_maintenance = date_realisation
        
        if prochaine_maintenance:
            bien.prochaine_maintenance = prochaine_maintenance
        elif maintenance.plan_maintenance:
            # Calculer la prochaine date selon le plan
            prochaine = self._calculer_prochaine_maintenance(
                maintenance.plan_maintenance,
                date_realisation
            )
            bien.prochaine_maintenance = prochaine
        
        bien.save()
        
        # Créer automatiquement la prochaine maintenance si plan récurrent
        if maintenance.plan_maintenance and bien.prochaine_maintenance:
            self.planifier_maintenance(
                bien=bien,
                type_maintenance=maintenance.type_maintenance,
                date_prevue=bien.prochaine_maintenance,
                user=user,
                description=f"Maintenance récurrente - {maintenance.plan_maintenance.nom}",
                prestataire=maintenance.prestataire
            )
        
        # Audit et notifications
        self.audit_service.log_maintenance_realisee(maintenance, user)
        self.notification_service.notifier_maintenance_realisee(maintenance)
        
        return maintenance
    
    def generer_planning_maintenance(
        self,
        entite: Optional[Entite] = None,
        periode_debut: Optional[date] = None,
        periode_fin: Optional[date] = None
    ) -> Dict[str, List]:
        """
        Génère un planning de maintenance.
        """
        from apps.patrimoine.models import Maintenance
        
        periode_debut = periode_debut or timezone.now().date()
        periode_fin = periode_fin or periode_debut + timedelta(days=90)
        
        queryset = Maintenance.objects.filter(
            statut='PLANIFIEE',
            date_prevue__range=[periode_debut, periode_fin]
        ).select_related('bien__categorie', 'bien__entite')
        
        if entite:
            queryset = queryset.filter(bien__entite=entite)
        
        # Grouper par semaine
        planning = {}
        for maintenance in queryset:
            semaine = maintenance.date_prevue.isocalendar()[1]
            annee = maintenance.date_prevue.year
            cle = f"{annee}-S{semaine:02d}"
            
            if cle not in planning:
                planning[cle] = []
            
            planning[cle].append({
                'id': str(maintenance.id),
                'bien': {
                    'code': maintenance.bien.code_patrimoine,
                    'nom': maintenance.bien.nom,
                    'categorie': maintenance.bien.categorie.nom
                },
                'type': maintenance.get_type_maintenance_display(),
                'date': maintenance.date_prevue.isoformat(),
                'prestataire': maintenance.prestataire,
                'cout_estime': float(maintenance.cout_estime) if maintenance.cout_estime else None,
                'priorite': self._calculer_priorite_maintenance(maintenance)
            })
        
        return planning
    
    def analyser_historique_maintenance(
        self,
        bien: Optional[Bien] = None,
        categorie: Optional['Categorie'] = None,
        periode: int = 365  # jours
    ) -> Dict:
        """
        Analyse l'historique de maintenance.
        """
        from apps.patrimoine.models import Maintenance
        
        date_debut = timezone.now().date() - timedelta(days=periode)
        
        queryset = Maintenance.objects.filter(
            statut='REALISEE',
            date_realisation__gte=date_debut
        )
        
        if bien:
            queryset = queryset.filter(bien=bien)
        elif categorie:
            queryset = queryset.filter(bien__categorie=categorie)
        
        maintenances = queryset.select_related('bien')
        
        # Calculs statistiques
        stats = {
            'nombre_total': maintenances.count(),
            'cout_total': maintenances.aggregate(
                Sum('cout_reel')
            )['cout_reel__sum'] or 0,
            'duree_moyenne_entre_pannes': self._calculer_mtbf(maintenances),
            'taux_maintenance_preventive': self._calculer_taux_preventif(maintenances),
            'top_pannes': self._identifier_pannes_frequentes(maintenances),
            'evolution_couts': self._analyser_evolution_couts(maintenances),
            'fiabilite_prestataires': self._analyser_prestataires(maintenances)
        }
        
        if bien:
            stats['recommandations'] = self._generer_recommandations_maintenance(bien, maintenances)
        
        return stats
    
    def _calculer_priorite_maintenance(self, maintenance: 'Maintenance') -> str:
        """Calcule la priorité d'une maintenance."""
        bien = maintenance.bien
        
        # Critères de priorité
        score = 0
        
        # Valeur du bien
        if bien.valeur_actuelle > 10000000:  # 10M XAF
            score += 3
        elif bien.valeur_actuelle > 1000000:  # 1M XAF
            score += 2
        else:
            score += 1
        
        # État du bien
        if bien.etat_physique in ['MAUVAIS', 'MOYEN']:
            score += 2
        
        # Criticité (équipements médicaux, serveurs, etc.)
        if bien.sous_categorie.code in ['equipement_medical', 'serveur', 'ambulance']:
            score += 3
        
        # Retard éventuel
        if maintenance.date_prevue < timezone.now().date():
            score += 2
        
        # Déterminer la priorité
        if score >= 7:
            return 'CRITIQUE'
        elif score >= 4:
            return 'HAUTE'
        elif score >= 2:
            return 'NORMALE'
        else:
            return 'BASSE'
    
    def _calculer_mtbf(self, maintenances) -> Optional[float]:
        """Calcule le Mean Time Between Failures."""
        if maintenances.count() < 2:
            return None
        
        # Grouper par bien
        from collections import defaultdict
        from datetime import timedelta
        
        mtbf_par_bien = defaultdict(list)
        
        for maintenance in maintenances.filter(
            type_maintenance='CORRECTIVE'
        ).order_by('bien', 'date_realisation'):
            mtbf_par_bien[maintenance.bien_id].append(maintenance.date_realisation)
        
        # Calculer les intervalles
        intervalles = []
        for bien_id, dates in mtbf_par_bien.items():
            if len(dates) > 1:
                for i in range(1, len(dates)):
                    interval = (dates[i] - dates[i-1]).days
                    if interval > 0:
                        intervalles.append(interval)
        
        if intervalles:
            return sum(intervalles) / len(intervalles)
        return None


# apps/patrimoine/services/validators.py
class BienValidator:
    """
    Validateur pour les opérations sur les biens.
    """
    
    def valider_creation_bien(self, data: Dict) -> None:
        """Valide les données de création d'un bien."""
        errors = {}
        
        # Vérifications obligatoires
        champs_obligatoires = [
            'nom', 'categorie', 'sous_categorie', 'entite',
            'valeur_acquisition', 'date_acquisition'
        ]
        
        for champ in champs_obligatoires:
            if not data.get(champ):
                errors[champ] = f"Le champ {champ} est obligatoire"
        
        # Validation de la valeur
        if 'valeur_acquisition' in data:
            if data['valeur_acquisition'] <= 0:
                errors['valeur_acquisition'] = "La valeur doit être positive"
        
        # Validation de la date
        if 'date_acquisition' in data:
            if data['date_acquisition'] > timezone.now().date():
                errors['date_acquisition'] = "La date d'acquisition ne peut pas être dans le futur"
        
        # Validation du code patrimoine s'il est fourni
        if 'code_patrimoine' in data:
            if Bien.objects.filter(code_patrimoine=data['code_patrimoine']).exists():
                errors['code_patrimoine'] = "Ce code patrimoine existe déjà"
        
        # Validation de la sous-catégorie par rapport à la catégorie
        if 'categorie' in data and 'sous_categorie' in data:
            if data['sous_categorie'].categorie != data['categorie']:
                errors['sous_categorie'] = "La sous-catégorie ne correspond pas à la catégorie"
        
        if errors:
            raise ValidationError(errors)
    
    def valider_modification_bien(self, bien: Bien, data: Dict) -> None:
        """Valide les modifications d'un bien."""
        errors = {}
        
        # Vérifier si le bien peut être modifié
        if bien.statut == 'REFORME':
            errors['statut'] = "Un bien réformé ne peut pas être modifié"
        
        # Validation spécifique par champ modifié
        if 'valeur_acquisition' in data:
            if data['valeur_acquisition'] <= 0:
                errors['valeur_acquisition'] = "La valeur doit être positive"
            
            # Vérifier l'écart avec la valeur actuelle
            ecart = abs(float(data['valeur_acquisition'] - bien.valeur_acquisition))
            pourcentage = (ecart / float(bien.valeur_acquisition)) * 100
            
            if pourcentage > 50:
                errors['valeur_acquisition'] = (
                    "L'écart de valeur est trop important (>50%). "
                    "Utilisez plutôt une réévaluation."
                )
        
        if errors:
            raise ValidationError(errors)
    
    def valider_affectation_responsable(
        self,
        bien: Bien,
        responsable: ResponsableBien,
        date_debut: Optional[date],
        date_fin: Optional[date]
    ) -> None:
        """Valide l'affectation d'un responsable."""
        errors = {}
        
        # Vérifier que le responsable est actif
        if not responsable.actif:
            errors['responsable'] = "Ce responsable n'est plus actif"
        
        # Vérifier les dates
        if date_fin and date_debut and date_fin <= date_debut:
            errors['date_fin'] = "La date de fin doit être après la date de début"
        
        # Vérifier les chevauchements
        affectations_existantes = bien.responsabilites.filter(
            actif=True,
            date_fin__isnull=True
        )
        
        if date_debut:
            affectations_existantes = affectations_existantes.filter(
                Q(date_fin__gte=date_debut) | Q(date_fin__isnull=True)
            )
        
        if affectations_existantes.exists() and not date_fin:
            errors['date_debut'] = (
                "Il existe déjà une affectation active sans date de fin. "
                "Veuillez d'abord clôturer l'affectation existante."
            )
        
        if errors:
            raise ValidationError(errors)


# apps/patrimoine/services/calculators.py
class AmortissementCalculator:
    """
    Calculateur d'amortissement pour les biens.
    """
    
    def calculer(
        self,
        valeur_acquisition: Decimal,
        date_acquisition: date,
        duree_amortissement: int,  # en mois
        valeur_residuelle: Optional[Decimal] = None,
        date_calcul: Optional[date] = None,
        methode: str = 'LINEAR'
    ) -> Dict:
        """
        Calcule l'amortissement d'un bien.
        """
        date_calcul = date_calcul or timezone.now().date()
        valeur_residuelle = valeur_residuelle or Decimal('0')
        
        # Calculer l'âge en mois
        mois_ecoules = (date_calcul - date_acquisition).days / 30.44
        
        if methode == 'LINEAR':
            return self._amortissement_lineaire(
                valeur_acquisition,
                valeur_residuelle,
                duree_amortissement,
                mois_ecoules
            )
        elif methode == 'DEGRESSIF':
            return self._amortissement_degressif(
                valeur_acquisition,
                valeur_residuelle,
                duree_amortissement,
                mois_ecoules
            )
        else:
            raise ValueError(f"Méthode d'amortissement non supportée: {methode}")
    
    def _amortissement_lineaire(
        self,
        valeur_acquisition: Decimal,
        valeur_residuelle: Decimal,
        duree_amortissement: int,
        mois_ecoules: float
    ) -> Dict:
        """Calcul d'amortissement linéaire."""
        if duree_amortissement <= 0:
            return {
                'methode': 'LINEAR',
                'valeur_nette': valeur_acquisition,
                'amortissement_cumule': Decimal('0'),
                'taux_amortissement': 0,
                'dotation_mensuelle': Decimal('0')
            }
        
        # Base amortissable
        base_amortissable = valeur_acquisition - valeur_residuelle
        
        # Dotation mensuelle
        dotation_mensuelle = base_amortissable / duree_amortissement
        
        # Amortissement cumulé
        amortissement_cumule = min(
            dotation_mensuelle * Decimal(str(mois_ecoules)),
            base_amortissable
        )
        
        # Valeur nette comptable
        valeur_nette = valeur_acquisition - amortissement_cumule
        
        # Taux d'amortissement
        taux = min((mois_ecoules / duree_amortissement) * 100, 100)
        
        return {
            'methode': 'LINEAR',
            'valeur_nette': valeur_nette,
            'amortissement_cumule': amortissement_cumule,
            'taux_amortissement': taux,
            'dotation_mensuelle': dotation_mensuelle,
            'base_amortissable': base_amortissable,
            'mois_restants': max(duree_amortissement - int(mois_ecoules), 0)
        }
    
    def _amortissement_degressif(
        self,
        valeur_acquisition: Decimal,
        valeur_residuelle: Decimal,
        duree_amortissement: int,
        mois_ecoules: float
    ) -> Dict:
        """Calcul d'amortissement dégressif."""
        # Coefficient dégressif selon la durée
        if duree_amortissement <= 36:  # 3 ans
            coefficient = Decimal('1.25')
        elif duree_amortissement <= 60:  # 5 ans
            coefficient = Decimal('1.75')
        else:
            coefficient = Decimal('2.25')
        
        # Taux dégressif annuel
        taux_lineaire = Decimal('12') / Decimal(str(duree_amortissement))
        taux_degressif = taux_lineaire * coefficient
        
        # Calcul année par année
        valeur_nette = valeur_acquisition
        amortissement_cumule = Decimal('0')
        annees_ecoulees = int(mois_ecoules / 12)
        
        for annee in range(annees_ecoulees):
            # Amortissement de l'année
            amortissement_annee = valeur_nette * taux_degressif
            
            # Vérifier si on doit passer au linéaire
            annees_restantes = (duree_amortissement / 12) - annee
            if annees_restantes > 0:
                taux_lineaire_restant = Decimal('1') / Decimal(str(annees_restantes))
                if taux_lineaire_restant > taux_degressif:
                    amortissement_annee = valeur_nette * taux_lineaire_restant
            
            amortissement_cumule += amortissement_annee
            valeur_nette -= amortissement_annee
            
            # Ne pas descendre sous la valeur résiduelle
            if valeur_nette < valeur_residuelle:
                valeur_nette = valeur_residuelle
                break
        
        return {
            'methode': 'DEGRESSIF',
            'valeur_nette': valeur_nette,
            'amortissement_cumule': amortissement_cumule,
            'taux_amortissement': (float(amortissement_cumule) / float(valeur_acquisition)) * 100,
            'coefficient': coefficient,
            'taux_degressif': float(taux_degressif) * 100
        }