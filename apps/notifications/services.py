# apps/notifications/services.py
from typing import List, Dict, Any
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service de gestion des notifications multi-canal."""
    
    def __init__(self):
        self.providers = {
            'email': self._send_email,
            'sms': self._send_sms,
            'push': self._send_push,
            'in_app': self._send_in_app,
        }
    
    def send_notification(
        self,
        template_name: str,
        destinataires: List[User],
        context: Dict[str, Any],
        canal: str = 'email'
    ) -> bool:
        """Envoie une notification selon le template spécifié."""
        
        try:
            template = NotificationTemplate.objects.get(
                nom=template_name,
                canal=canal,
                est_actif=True
            )
            
            success_count = 0
            for destinataire in destinataires:
                if self._send_individual_notification(template, destinataire, context):
                    success_count += 1
            
            return success_count > 0
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template de notification '{template_name}' introuvable")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
            return False
    
    def _send_individual_notification(self, template, destinataire, context):
        """Envoie une notification individuelle."""
        
        # Rendu du contenu avec le contexte
        sujet_template = Template(template.sujet)
        contenu_template = Template(template.contenu_text)
        
        context_obj = Context({**context, 'user': destinataire})
        sujet = sujet_template.render(context_obj)
        contenu = contenu_template.render(context_obj)
        
        # Création de l'enregistrement notification
        notification = Notification.objects.create(
            destinataire=destinataire,
            template=template,
            sujet=sujet,
            contenu=contenu,
            canal_utilise=template.canal,
            objet_id=context.get('objet_id', ''),
            objet_type=context.get('objet_type', ''),
            donnees_supplementaires=context
        )
        
        # Envoi selon le canal
        provider = self.providers.get(template.canal)
        if provider:
            return provider(notification)
        
        return False
    
    def _send_email(self, notification):
        """Envoie un email."""
        try:
            send_mail(
                subject=notification.sujet,
                message=notification.contenu,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.destinataire.email],
                fail_silently=False
            )
            
            notification.statut = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            notification.statut = 'failed'
            notification.save()
            return False
    
    def _send_sms(self, notification):
        """Envoie un SMS (à implémenter avec un provider SMS)."""
        # TODO: Intégration avec un service SMS (Twilio, etc.)
        notification.statut = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        return True
    
    def _send_push(self, notification):
        """Envoie une push notification (à implémenter)."""
        # TODO: Intégration avec FCM ou similaire
        notification.statut = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        return True
    
    def _send_in_app(self, notification):
        """Notification interne (déjà sauvée en base)."""
        notification.statut = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        return True
