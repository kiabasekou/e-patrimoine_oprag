# middleware/audit_middleware.py
from django.utils import timezone
from ..models import JournalAudit, Bien, HistoriqueValeur

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Modèles à auditer et leurs champs sensibles
        self.modeles_audites = {
            'bien': {
                'class': Bien,
                'fields': ['valeur_initiale', 'statut_juridique', 'entite_id']
            },
            'historiquevaleur': {
                'class': HistoriqueValeur,
                'fields': ['valeur']
            }
        }

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Ignorer les requêtes anonymes et les appels admin/media/static
        if not request.user.is_authenticated or \
           request.path.startswith('/admin/') or \
           request.path.startswith('/static/') or \
           request.path.startswith('/media/'):
            return None
        
        # Détecter l'action à partir de la vue
        action = self._detect_action(request, view_func)
        if not action:
            return None
        
        # Identifier le modèle concerné
        model_name = self._get_model_name(view_func)
        if not model_name or model_name not in self.modeles_audites:
            return None
        
        # Récupérer l'ID de l'objet
        obj_id = view_kwargs.get('pk')
        if not obj_id and request.method == 'POST':
            obj_id = request.POST.get('id')
        
        if obj_id:
            # Créer l'entrée d'audit
            audit = JournalAudit(
                utilisateur=request.user,
                action=action,
                modele=model_name,
                objet_id=obj_id,
                adresse_ip=self._get_client_ip(request)
            )
            
            # Pour les mises à jour, capturer l'état avant modification
            if action == 'update':
                model_class = self.modeles_audites[model_name]['class']
                try:
                    obj = model_class.objects.get(pk=obj_id)
                    audit.details['before'] = {
                        f: getattr(obj, f) for f in self.modeles_audites[model_name]['fields']
                    }
                except model_class.DoesNotExist:
                    pass
            
            audit.save()
            
            # Stocker l'audit dans la requête pour post_save
            request.current_audit = audit
        
        return None
    
    def process_template_response(self, request, response):
        # Compléter l'audit après le traitement pour les actions de modification
        if hasattr(request, 'current_audit') and request.current_audit.action == 'update':
            audit = request.current_audit
            model_class = self.modeles_audites[audit.modele]['class']
            
            try:
                obj = model_class.objects.get(pk=audit.objet_id)
                audit.details['after'] = {
                    f: getattr(obj, f) for f in self.modeles_audites[audit.modele]['fields']
                }
                audit.set_changes(audit.details.get('before', {}), audit.details.get('after', {}))
            except model_class.DoesNotExist:
                pass
        
        return response
    
    def _detect_action(self, request, view_func):
        """Détermine l'action en fonction de la méthode HTTP et de la vue"""
        if request.method == 'GET':
            if 'export' in view_func.__name__.lower():
                return 'export'
            return 'view'
        elif request.method == 'POST':
            if 'create' in view_func.__name__.lower():
                return 'create'
            return 'update'
        elif request.method == 'DELETE' or request.method == 'POST' and 'delete' in request.path:
            return 'delete'
        return None
    
    def _get_model_name(self, view_func):
        """Extrait le nom du modèle à partir de la vue"""
        view_name = view_func.__name__.lower()
        for model in self.modeles_audites.keys():
            if model.lower() in view_name:
                return model
        return None
    
    def _get_client_ip(self, request):
        """Récupère l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip