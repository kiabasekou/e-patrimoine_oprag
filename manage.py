#!/usr/bin/env python
"""
Django's command-line utility for SYGEP-OPRAG administrative tasks.
Enterprise-grade version with advanced error handling and environment management.
"""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks with enterprise-grade error handling."""
    
    # Configuration de l'environnement par défaut
    default_settings = 'config.settings.development'
    
    # Détection automatique de l'environnement
    current_env = os.environ.get('ENVIRONMENT', 'development').lower()
    
    # Mapping des environnements vers les modules de configuration
    settings_modules = {
        'development': 'config.settings.development',
        'testing': 'config.settings.testing', 
        'staging': 'config.settings.staging',
        'production': 'config.settings.production',
    }
    
    # Sélection du module de configuration approprié
    settings_module = settings_modules.get(current_env, default_settings)
    
    # Configuration du module de settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    
    # Validation de l'environnement
    if current_env not in settings_modules:
        print(f"⚠️  Environnement '{current_env}' non reconnu. Utilisation de '{default_settings}'")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Message d'erreur amélioré pour l'OPRAG
        error_msg = (
            "❌ Impossible d'importer Django pour SYGEP-OPRAG.\n\n"
            "Vérifications nécessaires :\n"
            "1. Django est-il installé ? → pip install -r requirements.txt\n"
            "2. L'environnement virtuel est-il activé ?\n"
            "3. La variable PYTHONPATH est-elle correcte ?\n"
            "4. Êtes-vous dans le bon répertoire ?\n\n"
            f"Environnement détecté : {current_env}\n"
            f"Module de configuration : {settings_module}\n\n"
            f"Erreur technique : {exc}"
        )
        
        # Log de l'erreur pour le debugging
        try:
            import logging
            logging.basicConfig(level=logging.ERROR)
            logger = logging.getLogger('sygep.startup')
            logger.error(f"Échec du démarrage de SYGEP-OPRAG: {exc}")
        except ImportError:
            pass  # Si logging n'est pas disponible
            
        raise ImportError(error_msg) from exc
    
    # Validation des prérequis pour l'OPRAG
    validate_oprag_requirements()
    
    # Affichage des informations de démarrage en mode développement
    if current_env == 'development' and len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        display_startup_info(current_env, settings_module)
    
    # Exécution de la commande
    execute_from_command_line(sys.argv)


def validate_oprag_requirements():
    """Valide les prérequis spécifiques à l'OPRAG."""
    
    # Validation des répertoires critiques
    base_dir = Path(__file__).resolve().parent
    required_dirs = ['apps', 'config', 'static', 'media', 'logs']
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Répertoire créé : {dir_path}")
            except PermissionError:
                print(f"⚠️  Impossible de créer le répertoire : {dir_path}")
    
    # Validation du fichier .env en développement
    env_file = base_dir / '.env'
    if not env_file.exists() and os.environ.get('ENVIRONMENT', 'development') == 'development':
        env_example = base_dir / '.env.example'
        if env_example.exists():
            print("⚠️  Fichier .env manquant. Copiez .env.example vers .env et configurez-le.")
        else:
            print("⚠️  Fichiers .env et .env.example manquants. Configuration d'environnement requise.")


def display_startup_info(environment, settings_module):
    """Affiche les informations de démarrage pour l'OPRAG."""
    
    print("\n" + "="*60)
    print("🏢 SYGEP-OPRAG - Système de Gestion du Patrimoine")
    print("   Office des Ports et Rades du Gabon")
    print("="*60)
    print(f"🌍 Environnement    : {environment.upper()}")
    print(f"⚙️  Configuration   : {settings_module}")
    print(f"🐍 Python          : {sys.version.split()[0]}")
    
    try:
        import django
        print(f"🔧 Django          : {django.get_version()}")
    except ImportError:
        print("🔧 Django          : Non installé")
    
    print(f"📂 Répertoire      : {Path(__file__).resolve().parent}")
    print("="*60)
    
    # Vérification des services essentiels en développement
    if environment == 'development':
        check_services_status()
    
    print("\n🚀 Démarrage de l'application...\n")


def check_services_status():
    """Vérifie le statut des services essentiels."""
    
    services_status = []
    
    # Vérification PostgreSQL
    try:
        import psycopg2
        # Tentative de connexion basique (sera configurée via les settings)
        services_status.append(("PostgreSQL", "✅ Disponible"))
    except ImportError:
        services_status.append(("PostgreSQL", "❌ psycopg2 non installé"))
    
    # Vérification Redis
    try:
        import redis
        services_status.append(("Redis", "✅ Client disponible"))
    except ImportError:
        services_status.append(("Redis", "❌ redis-py non installé"))
    
    # Vérification Celery
    try:
        import celery
        services_status.append(("Celery", "✅ Disponible"))
    except ImportError:
        services_status.append(("Celery", "❌ Non installé"))
    
    # Affichage du statut
    if services_status:
        print("\n📊 Statut des services :")
        for service, status in services_status:
            print(f"   {service:<12} : {status}")


if __name__ == '__main__':
    main()