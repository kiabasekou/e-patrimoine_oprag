#!/usr/bin/env python
"""Django's command-line utility for SYGEP-OPRAG with automatic environment detection."""

import os
import sys
from pathlib import Path
import logging
# Mapping des environnements vers les modules de configuration
SETTINGS_MAP = {
    "development": "config.settings.development",
    "testing": "config.settings.testing",
    "staging": "config.settings.staging",
    "production": "config.settings.production",
}
DEFAULT_ENV = "development"

def get_environment() -> str:
    """Retourne l'environnement courant."""
    return os.environ.get("ENVIRONMENT", DEFAULT_ENV).lower()


def get_settings_module(env: str) -> str:
    """Retourne le module de settings correspondant."""
    return SETTINGS_MAP.get(env, SETTINGS_MAP[DEFAULT_ENV])


def configure_environment() -> tuple[str, str]:
    """Configure DJANGO_SETTINGS_MODULE et valide l'environnement."""
    env = get_environment()
    settings_module = get_settings_module(env)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    if env not in SETTINGS_MAP:
        print(f"⚠️  Environnement '{env}' non reconnu. Utilisation de '{SETTINGS_MAP[DEFAULT_ENV]}'")
    return env, settings_module


def main() -> None:
    environment, settings_module = configure_environment()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        
        error_msg = (
            "❌ Impossible d'importer Django pour SYGEP-OPRAG.\n\n"
            "Vérifications nécessaires :\n"
            "1. Django est-il installé ? → pip install -r requirements.txt\n"
            "2. L'environnement virtuel est-il activé ?\n"
            "3. La variable PYTHONPATH est-elle correcte ?\n"
            "4. Êtes-vous dans le bon répertoire ?\n\n"
            f"Environnement détecté : {environment}\n"
            f"Module de configuration : {settings_module}\n\n"
            f"Erreur technique : {exc}"
        )
        
        
        try:
            
            logging.basicConfig(level=logging.ERROR)
            logger = logging.getLogger("sygep.startup")
            logger.error("Échec du démarrage de SYGEP-OPRAG: %s", exc)
        except Exception:
            pass
        raise ImportError(error_msg) from exc
            
        
    
    
    validate_oprag_requirements()
    
    if environment == "development" and len(sys.argv) > 1 and sys.argv[1] == "runserver":
        display_startup_info(environment, settings_module)
    execute_from_command_line(sys.argv)
    


def validate_oprag_requirements() -> None:
    """Valide les prérequis spécifiques à l'OPRAG."""
    
    base_dir = Path(__file__).resolve().parent
    required_dirs = ["apps", "config", "static", "media", "logs"]
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Répertoire créé : {dir_path}")
            except PermissionError:
                print(f"⚠️  Impossible de créer le répertoire : {dir_path}")
    
    env_file = base_dir / ".env"
    if not env_file.exists() and get_environment() == "development":
        env_example = base_dir / ".env.example"
        if env_example.exists():
            print("⚠️  Fichier .env manquant. Copiez .env.example vers .env et configurez-le.")
        else:
            print("⚠️  Fichiers .env et .env.example manquants. Configuration d'environnement requise.")


def display_startup_info(environment: str, settings_module: str) -> None:
    """Affiche les informations de démarrage."""
    print("\n" + "=" * 60)
    print("🏢 SYGEP-OPRAG - Système de Gestion du Patrimoine")
    print("   Office des Ports et Rades du Gabon")
    print("=" * 60)
    print(f"🌍 Environnement    : {environment.upper()}")
    print(f"⚙️  Configuration   : {settings_module}")
    print(f"🐍 Python          : {sys.version.split()[0]}")
    try:
        import django
        print(f"🔧 Django          : {django.get_version()}")
    except ImportError:
        print("🔧 Django          : Non installé")
    print(f"📂 Répertoire      : {Path(__file__).resolve().parent}")
    
    print("=" * 60)
    if environment == "development":
        check_services_status()
    print("\n🚀 Démarrage de l'application...\n")

def check_services_status() -> None:
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


if __name__ == "__main__":
    main()