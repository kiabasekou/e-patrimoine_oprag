# apps/core/exceptions.py
class OPRAGException(Exception):
    """Exception de base pour SYGEP-OPRAG."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or 'OPRAG_ERROR'
        self.details = details or {}
        super().__init__(self.message)


class BusinessLogicError(OPRAGException):
    """Erreur de logique métier."""
    pass


class ValidationError(OPRAGException):
    """Erreur de validation des données."""
    pass


class SecurityError(OPRAGException):
    """Erreur de sécurité."""
    pass


class IntegrationError(OPRAGException):
    """Erreur d'intégration avec un système externe."""
    pass
