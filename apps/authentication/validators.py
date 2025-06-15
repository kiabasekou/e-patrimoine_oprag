# apps/authentication/validators.py
from django.contrib.auth.password_validation import BasePasswordValidator
from django.utils.translation import gettext as _
import re


class CustomPasswordValidator(BasePasswordValidator):
    """Validateur de mot de passe personnalisé pour l'OPRAG."""
    
    def __init__(self, require_uppercase=True, require_lowercase=True, 
                 require_special=True, require_numeric=True):
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_special = require_special
        self.require_numeric = require_numeric
    
    def validate(self, password, user=None):
        errors = []
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(_('Le mot de passe doit contenir au moins une majuscule.'))
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(_('Le mot de passe doit contenir au moins une minuscule.'))
        
        if self.require_numeric and not re.search(r'\d', password):
            errors.append(_('Le mot de passe doit contenir au moins un chiffre.'))
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(_('Le mot de passe doit contenir au moins un caractère spécial.'))
        
        if errors:
            from django.core.exceptions import ValidationError
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            'Votre mot de passe doit contenir au moins une majuscule, '
            'une minuscule, un chiffre et un caractère spécial.'
        )
