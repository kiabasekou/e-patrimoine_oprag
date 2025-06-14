# services/notification_service.py
from ..models import Notification, UtilisateurPatrimoine, Bien, HistoriqueValeur

class NotificationService:
    @staticmethod
    def notifier_responsables_bien(bien, titre, message, type_notif='info', lien=''):
        """Notifie tous les responsables d'un bien"""
        responsables = [r.responsable.user for r in bien.responsabilites.all() 
                        if hasattr(r.responsable, 'user') and r.responsable.user]
        
        for user in responsables:
            Notification.objects.create(
                utilisateur=user,
                titre=titre,
                message=message,
                type=type_notif,
                lien=lien
            )
    
    @staticmethod
    def notifier_changement_valeur(bien, historique):
        """Notifie d'un changement de valeur"""
        difference = historique.valeur - bien.valeur_initiale
        pourcentage = (difference / bien.valeur_initiale) * 100 if bien.valeur_initiale else 0
        
        # Déterminer le type de notification selon l'ampleur du changement
        type_notif = 'info'
        if abs(pourcentage) > 25:
            type_notif = 'warning'
        if abs(pourcentage) > 50:
            type_notif = 'danger'
        
        # Message avec la variation
        message = f"La valeur du bien {bien.nom} a "
        if difference > 0:
            message += f"augmenté de {abs(difference):,.2f} FCFA (+{abs(pourcentage):.1f}%)"
        else:
            message += f"diminué de {abs(difference):,.2f} FCFA (-{abs(pourcentage):.1f}%)"
        
        # Notifier les gestionnaires
        gestionnaires = UtilisateurPatrimoine.objects.filter(role__in=['admin', 'gestionnaire'])
        for user in gestionnaires:
            Notification.objects.create(
                utilisateur=user,
                titre=f"Changement de valeur - {bien.nom}",
                message=message,
                type=type_notif,
                lien=f"/biens/{bien.id}/"
            )
        
        # Notifier les responsables
        NotificationService.notifier_responsables_bien(
            bien=bien,
            titre=f"Changement de valeur - {bien.nom}",
            message=message,
            type_notif=type_notif,
            lien=f"/biens/{bien.id}/"
        )