# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from openpyxl import Workbook
from io import BytesIO
from .models import Bien, HistoriqueValeur, UtilisateurPatrimoine

@shared_task
def exporter_inventaire_complet(filters, email_utilisateur):
    """Exporte l'inventaire complet en Excel et envoie par email"""
    # Filtrer les biens selon les critères
    queryset = Bien.objects.all()
    if 'categorie' in filters:
        queryset = queryset.filter(categorie_id=filters['categorie'])
    if 'entite' in filters:
        queryset = queryset.filter(entite_id=filters['entite'])
    # Autres filtres...
    
    # Créer le fichier Excel
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inventaire Complet"
    
    # En-têtes
    headers = [
        'ID', 'Nom', 'Catégorie', 'Sous-catégorie', 'Entité', 
        'Valeur initiale (FCFA)', 'Date acquisition', 'Responsable actuel'
    ]
    worksheet.append(headers)
    
    # Données
    for bien in queryset:
        responsable = bien.responsable_actuel
        responsable_nom = f"{responsable.responsable.prenom} {responsable.responsable.nom}" if responsable else "N/A"
        
        row = [
            bien.id,
            bien.nom,
            bien.categorie.nom if bien.categorie else '',
            bien.sous_categorie.nom if bien.sous_categorie else '',
            bien.entite.nom if bien.entite else '',
            bien.valeur_initiale,
            bien.date_acquisition.strftime('%d/%m/%Y') if bien.date_acquisition else '',
            responsable_nom
        ]
        worksheet.append(row)
    
    # Sauvegarder dans un buffer
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    
    # Récupérer l'utilisateur
    try:
        user = UtilisateurPatrimoine.objects.get(email=email_utilisateur)
        
        # Envoyer l'email avec le fichier en pièce jointe
        send_mail(
            subject='Votre export d\'inventaire est prêt',
            message=f'Bonjour {user.get_full_name()},\n\nVeuillez trouver ci-joint l\'export de l\'inventaire demandé.\n\nCordialement,\nL\'équipe e-patrimoine',
            from_email='noreply@e-patrimoine.org',
            recipient_list=[email_utilisateur],
            fail_silently=False,
            attachments=[
                ('inventaire_complet.xlsx', buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            ]
        )
        
        # Ajouter une notification dans l'application
        from .services.notification_service import NotificationService
        NotificationService.creer_notification(
            utilisateur=user,
            titre="Export d'inventaire terminé",
            message="Votre export d'inventaire a été généré avec succès et envoyé par email.",
            type_notif='success'
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'envoi de l'export: {str(e)}")
        return False
    
    return True

@shared_task
def verifier_maintenances_planifiees():
    """Vérifie les maintenances planifiées et envoie des rappels"""
    # Date actuelle
    aujourd_hui = timezone.now().date()
    
    # Vérifier les véhicules
    from .models import ProfilVehicule
    vehicules = ProfilVehicule.objects.filter(
        prochaine_maintenance__lte=aujourd_hui + timezone.timedelta(days=7)
    ).select_related('bien', 'bien__entite')
    
    for vehicule in vehicules:
        # Obtenir les responsables
        responsables = [
            r.responsable for r in vehicule.bien.responsabilites.filter(type_affectation='permanent')
        ]
        
        # Créer une notification pour chaque responsable
        for responsable in responsables:
            if hasattr(responsable, 'user') and responsable.user:
                from .services.notification_service import NotificationService
                
                jours_restants = (vehicule.prochaine_maintenance - aujourd_hui).days
                
                if jours_restants <= 0:
                    message = f"La maintenance du véhicule {vehicule.bien.nom} ({vehicule.marque} {vehicule.modele}) est en retard! Elle était prévue le {vehicule.prochaine_maintenance.strftime('%d/%m/%Y')}."
                    type_notif = 'danger'
                else:
                    message = f"La maintenance du véhicule {vehicule.bien.nom} ({vehicule.marque} {vehicule.modele}) est prévue dans {jours_restants} jours, le {vehicule.prochaine_maintenance.strftime('%d/%m/%Y')}."
                    type_notif = 'warning'
                
                NotificationService.creer_notification(
                    utilisateur=responsable.user,
                    titre=f"Maintenance à prévoir - {vehicule.bien.nom}",
                    message=message,
                    type_notif=type_notif,
                    lien=f"/biens/{vehicule.bien.id}/"
                )
    
    # Même logique pour autres types d'équipements
    # ...
    
    return True