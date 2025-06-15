#!/bin/bash
# install_dependencies.sh - Installation des dépendances Python

echo "🐍 Installation des dépendances E-Patrimoine OPRAG"
echo "================================================="

# Détection de l'environnement
if [ -z "$ENVIRONMENT" ]; then
    echo "Quel environnement souhaitez-vous configurer?"
    echo "1) Développement (avec outils de debug)"
    echo "2) Production (optimisé)"
    echo "3) Test/CI (dépendances de base)"
    read -p "Votre choix (1-3): " choice
    
    case $choice in
        1) ENVIRONMENT="development" ;;
        2) ENVIRONMENT="production" ;;
        3) ENVIRONMENT="test" ;;
        *) echo "Choix invalide"; exit 1 ;;
    esac
fi

# Créer et activer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

# Mettre à jour pip
echo "📈 Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

# Installer les dépendances selon l'environnement
case $ENVIRONMENT in
    "development")
        echo "🛠️  Installation des dépendances de DÉVELOPPEMENT..."
        pip install -r requirements-dev.txt
        echo "✅ Outils de développement installés!"
        ;;
    "production")
        echo "🚀 Installation des dépendances de PRODUCTION..."
        pip install -r requirements-prod.txt
        echo "✅ Environnement de production configuré!"
        ;;
    "test")
        echo "🧪 Installation des dépendances de TEST..."
        pip install -r requirements.txt
        echo "✅ Environnement de test configuré!"
        ;;
esac

# Vérifier l'installation
echo ""
echo "📊 Vérification de l'installation..."
python -c "import django; print(f'✓ Django {django.__version__} installé')"
python -c "import rest_framework; print('✓ Django REST Framework installé')"
python -c "import redis; print('✓ Redis client installé')"
python -c "import celery; print('✓ Celery installé')"

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Prochaines étapes:"
echo "1. Configurer le fichier .env"
echo "2. Appliquer les migrations: python manage.py migrate"
echo "3. Créer un superutilisateur: python manage.py createsuperuser"
echo "4. Lancer le serveur: python manage.py runserver"