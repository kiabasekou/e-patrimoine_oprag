# apps/core/utils.py
from django.core.cache import cache
from django.conf import settings
from typing import Any, Optional
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Gestionnaire de cache intelligent avec invalidation automatique."""
    
    # TTL par défaut pour différents types de données
    DEFAULT_TTL = {
        'user_data': 300,      # 5 minutes
        'static_data': 3600,   # 1 heure
        'reports': 1800,       # 30 minutes
        'dashboard': 300,      # 5 minutes
        'api_response': 600,   # 10 minutes
    }
    
    @classmethod
    def get_or_set(cls, key: str, callback, ttl: Optional[int] = None, cache_type: str = 'api_response'):
        """Récupère une valeur du cache ou l'exécute et la met en cache."""
        
        try:
            # Vérifier le cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Exécuter le callback et mettre en cache
            value = callback()
            ttl = ttl or cls.DEFAULT_TTL.get(cache_type, 300)
            cache.set(key, value, ttl)
            
            return value
            
        except Exception as e:
            logger.error(f"Erreur cache pour la clé {key}: {e}")
            # En cas d'erreur de cache, exécuter directement
            return callback()
    
    @classmethod
    def invalidate_pattern(cls, pattern: str):
        """Invalide toutes les clés correspondant au pattern."""
        
        try:
            # Cette fonctionnalité dépend du backend de cache utilisé
            # Pour Redis, on pourrait utiliser des patterns
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(pattern)
            else:
                # Fallback : invalidation manuelle des clés connues
                logger.warning(f"Invalidation de pattern non supportée: {pattern}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du pattern {pattern}: {e}")
    
    @classmethod
    def generate_cache_key(cls, prefix: str, **kwargs) -> str:
        """Génère une clé de cache unique basée sur les paramètres."""
        
        # Trier les paramètres pour avoir une clé déterministe
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        
        # Hash des paramètres pour éviter les clés trop longues
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        return f"{prefix}:{params_hash}"


class SecurityValidator:
    """Validateur de sécurité pour les données sensibles."""
    
    # Patterns de données sensibles à masquer
    SENSITIVE_PATTERNS = [
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Cartes de crédit
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
        r'\b\+241[0-9]{8}\b',  # Téléphones Gabon
        r'\bmot[\s_-]?de[\s_-]?passe\b',  # Mots de passe
    ]
    
    @classmethod
    def sanitize_data(cls, data: Any) -> Any:
        """Sanitise les données en masquant les informations sensibles."""
        
        if isinstance(data, dict):
            return {key: cls.sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return cls._mask_sensitive_strings(data)
        else:
            return data
    
    @classmethod
    def _mask_sensitive_strings(cls, text: str) -> str:
        """Masque les chaînes sensibles dans le texte."""
        
        import re
        
        masked_text = text
        for pattern in cls.SENSITIVE_PATTERNS:
            masked_text = re.sub(pattern, '***MASKED***', masked_text, flags=re.IGNORECASE)
        
        return masked_text
    
    @classmethod
    def validate_file_upload(cls, file) -> tuple[bool, str]:
        """Valide un fichier uploadé pour la sécurité."""
        
        # Extensions autorisées
        ALLOWED_EXTENSIONS = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.txt', '.csv', '.zip'
        }
        
        # Taille maximale (50MB)
        MAX_FILE_SIZE = 50 * 1024 * 1024
        
        # Vérifier l'extension
        file_extension = file.name.split('.')[-1].lower()
        if f'.{file_extension}' not in ALLOWED_EXTENSIONS:
            return False, f"Extension '{file_extension}' non autorisée"
        
        # Vérifier la taille
        if file.size > MAX_FILE_SIZE:
            return False, f"Fichier trop volumineux ({file.size / 1024 / 1024:.1f}MB > 50MB)"
        
        # Vérifications basiques du contenu
        try:
            # Lire les premiers octets pour vérifier le type MIME
            file.seek(0)
            header = file.read(1024)
            file.seek(0)
            
            # Vérifications basiques selon l'extension
            if file_extension in ['jpg', 'jpeg'] and not header.startswith(b'\xff\xd8'):
                return False, "Fichier JPEG corrompu ou invalide"
            elif file_extension == 'png' and not header.startswith(b'\x89PNG'):
                return False, "Fichier PNG corrompu ou invalide"
            elif file_extension == 'pdf' and not header.startswith(b'%PDF'):
                return False, "Fichier PDF corrompu ou invalide"
                
        except Exception as e:
            return False, f"Erreur lors de la validation: {str(e)}"
        
        return True, "Fichier valide"

