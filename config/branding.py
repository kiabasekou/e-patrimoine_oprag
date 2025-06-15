# config/branding.py
"""
Configuration du branding pour SYGEP-OPRAG
Système de Gestion du Patrimoine - OPRAG
"""

BRANDING = {
    # Identité de l'application
    'APP_NAME': 'SYGEP-OPRAG',
    'APP_FULL_NAME': 'Système de Gestion du Patrimoine - OPRAG',
    'APP_SHORT_NAME': 'SYGEP',
    'APP_DESCRIPTION': 'Solution complète de gestion patrimoniale pour l\'Office des Ports et Rades du Gabon',
    'APP_VERSION': '2.0.0',
    
    # Organisation
    'ORG_NAME': 'Office des Ports et Rades du Gabon',
    'ORG_SHORT_NAME': 'OPRAG',
    'ORG_WEBSITE': 'https://www.oprag.ga',
    'ORG_EMAIL': 'contact@oprag.ga',
    'ORG_PHONE': '+241 01 70 00 00',
    'ORG_ADDRESS': 'Port-Gentil, Gabon',
    
    # URLs et domaines
    'APP_DOMAIN': 'sygep.oprag.ga',
    'APP_URL': 'https://sygep.oprag.ga',
    'API_URL': 'https://api.sygep.oprag.ga',
    'DOCS_URL': 'https://docs.sygep.oprag.ga',
    
    # Branding visuel
    'LOGO_URL': '/static/img/logo-sygep.png',
    'FAVICON_URL': '/static/img/favicon.ico',
    'PRIMARY_COLOR': '#003366',  # Bleu marine (maritime)
    'SECONDARY_COLOR': '#0066CC',  # Bleu OPRAG
    'ACCENT_COLOR': '#FF6B35',  # Orange (contraste)
    'SUCCESS_COLOR': '#28A745',
    'WARNING_COLOR': '#FFC107',
    'DANGER_COLOR': '#DC3545',
    'INFO_COLOR': '#17A2B8',
    
    # Métadonnées
    'META_TITLE': 'SYGEP-OPRAG | Gestion du Patrimoine',
    'META_DESCRIPTION': 'Système de gestion du patrimoine de l\'OPRAG - Inventaire, maintenance et suivi des actifs',
    'META_KEYWORDS': 'OPRAG, patrimoine, gestion, actifs, Gabon, ports, maintenance',
    'META_AUTHOR': 'OPRAG - Office des Ports et Rades du Gabon',
    
    # Textes d'interface
    'WELCOME_MESSAGE': 'Bienvenue sur SYGEP-OPRAG',
    'LOGIN_TITLE': 'Connexion à SYGEP',
    'LOGIN_SUBTITLE': 'Système de Gestion du Patrimoine',
    'FOOTER_TEXT': '© 2024 OPRAG - Tous droits réservés | SYGEP v2.0',
    
    # Emails
    'EMAIL_SUBJECT_PREFIX': '[SYGEP-OPRAG]',
    'EMAIL_SIGNATURE': '''
Cordialement,

L'équipe SYGEP-OPRAG
Système de Gestion du Patrimoine
Office des Ports et Rades du Gabon

Ce message est généré automatiquement, merci de ne pas y répondre.
Pour toute assistance : support.sygep@oprag.ga
''',
    
    # Formats et préfixes
    'ASSET_CODE_PREFIX': 'SYGEP',
    'DOCUMENT_PREFIX': 'DOC-SYGEP',
    'REPORT_PREFIX': 'RPT-SYGEP',
    
    # Messages système
    'MAINTENANCE_MESSAGE': 'SYGEP est actuellement en maintenance. Veuillez réessayer dans quelques instants.',
    'ERROR_MESSAGE': 'Une erreur est survenue. L\'équipe SYGEP a été notifiée.',
    'SUCCESS_MESSAGE': 'Opération effectuée avec succès dans SYGEP.',
}

# Templates d'emails avec branding
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Bienvenue sur SYGEP-OPRAG',
        'template': 'emails/welcome_sygep.html'
    },
    'password_reset': {
        'subject': 'Réinitialisation de votre mot de passe SYGEP',
        'template': 'emails/password_reset_sygep.html'
    },
    'notification': {
        'subject': 'Notification SYGEP - {title}',
        'template': 'emails/notification_sygep.html'
    },
    'maintenance_reminder': {
        'subject': 'SYGEP - Rappel de maintenance',
        'template': 'emails/maintenance_reminder_sygep.html'
    },
    'monthly_report': {
        'subject': 'SYGEP - Rapport mensuel du patrimoine',
        'template': 'emails/monthly_report_sygep.html'
    }
}

# Configuration des rapports
REPORT_CONFIG = {
    'header': {
        'title': 'SYGEP-OPRAG',
        'subtitle': 'Système de Gestion du Patrimoine',
        'logo': 'static/img/logo-sygep-report.png'
    },
    'footer': {
        'text': 'Document généré par SYGEP-OPRAG - © 2024 OPRAG',
        'show_page_numbers': True,
        'show_date': True
    },
    'watermark': {
        'enabled': True,
        'text': 'SYGEP-OPRAG',
        'opacity': 0.1
    }
}

# Intégration dans les settings Django
def configure_branding(settings):
    """Configure le branding dans les settings Django"""
    
    # Nom de l'application
    settings.SITE_NAME = BRANDING['APP_NAME']
    settings.SITE_HEADER = BRANDING['APP_FULL_NAME']
    settings.SITE_TITLE = BRANDING['META_TITLE']
    
    # Admin interface
    settings.ADMIN_SITE_HEADER = f"{BRANDING['APP_NAME']} Administration"
    settings.ADMIN_SITE_TITLE = f"{BRANDING['APP_NAME']} Admin"
    settings.ADMIN_INDEX_TITLE = f"Gestion {BRANDING['APP_SHORT_NAME']}"
    
    # Email configuration
    settings.DEFAULT_FROM_EMAIL = f"{BRANDING['APP_NAME']} <noreply@{BRANDING['APP_DOMAIN']}>"
    settings.SERVER_EMAIL = f"server@{BRANDING['APP_DOMAIN']}"
    settings.EMAIL_SUBJECT_PREFIX = BRANDING['EMAIL_SUBJECT_PREFIX']
    
    # Context processors
    settings.TEMPLATES[0]['OPTIONS']['context_processors'].append(
        'config.context_processors.branding_context'
    )
    
    return settings
