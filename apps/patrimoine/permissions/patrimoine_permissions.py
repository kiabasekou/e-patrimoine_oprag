# permissions/patrimoine_permissions.py
from django.core.exceptions import PermissionDenied

class BienPermissions:
    @staticmethod
    def peut_voir_bien(user, bien):
        """Vérifie si l'utilisateur peut voir les détails d'un bien"""
        # Administrateurs peuvent tout voir
        if user.is_staff or user.is_superuser:
            return True
            
        # Responsables peuvent voir leurs biens
        if bien.responsabilites.filter(
            responsable__user=user, 
            type_affectation='permanent'
        ).exists():
            return True
            
        # Autres règles personnalisées
        # ...
        
        return False
    
    @staticmethod
    def peut_modifier_bien(user, bien):
        """Vérifie si l'utilisateur peut modifier un bien"""
        # Seuls les administrateurs peuvent modifier
        if user.is_staff or user.is_superuser:
            return True
        
        return False

# Décorateur pour vérifier les permissions
def bien_permission_required(permission_check):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            bien_id = kwargs.get('pk')
            if bien_id:
                from patrimoine.models import Bien
                try:
                    bien = Bien.objects.get(pk=bien_id)
                    if not permission_check(request.user, bien):
                        raise PermissionDenied("Vous n'avez pas les permissions nécessaires.")
                except Bien.DoesNotExist:
                    raise Http404("Ce bien n'existe pas.")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator