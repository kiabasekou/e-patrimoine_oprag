# apps/core/routers.py
class PrimaryReplicaRouter:
    """
    Router de base de données pour répartir les lectures/écritures.
    Optimise les performances en utilisant des réplicas en lecture.
    """
    
    def db_for_read(self, model, **hints):
        """Suggère la base pour les opérations de lecture."""
        
        # En développement, utiliser la base par défaut
        if settings.DEBUG:
            return 'default'
        
        # Pour les rapports et analytics, utiliser le replica si disponible
        if hasattr(model._meta, 'app_label'):
            if model._meta.app_label in ['reports', 'dashboard']:
                return 'replica' if 'replica' in settings.DATABASES else 'default'
        
        # Lectures sur le replica par défaut en production
        return 'replica' if 'replica' in settings.DATABASES else 'default'
    
    def db_for_write(self, model, **hints):
        """Suggère la base pour les opérations d'écriture."""
        
        # Toutes les écritures sur la base principale
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Autorise les relations entre objets."""
        
        # Relations autorisées si les objets sont sur des bases compatibles
        db_set = {'default', 'replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Contrôle quelles migrations sont appliquées sur quelle base."""
        
        # Migrations uniquement sur la base principale
        return db == 'default'
