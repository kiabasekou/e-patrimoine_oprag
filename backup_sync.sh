#!/bin/bash
# backup_sync.sh - Script de sauvegarde et synchronisation pour e-patrimoine OPRAG
# Auteur: Système e-patrimoine
# Description: Sauvegarde locale et synchronisation avec GitHub

# Configuration
PROJECT_NAME="e-patrimoine_oprag"
PROJECT_DIR="$(pwd)"
BACKUP_DIR="$HOME/backups/$PROJECT_NAME"
GITHUB_REPO="https://github.com/kiabasekou/e-patrimoine_oprag.git"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${PROJECT_NAME}_backup_${TIMESTAMP}"
LOG_FILE="$PROJECT_DIR/logs/backup_sync.log"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fonction pour afficher les messages colorés
print_status() {
    case $1 in
        "success")
            echo -e "${GREEN}✓ $2${NC}"
            log "SUCCESS: $2"
            ;;
        "error")
            echo -e "${RED}✗ $2${NC}"
            log "ERROR: $2"
            ;;
        "warning")
            echo -e "${YELLOW}⚠ $2${NC}"
            log "WARNING: $2"
            ;;
        "info")
            echo -e "${BLUE}ℹ $2${NC}"
            log "INFO: $2"
            ;;
    esac
}

# Fonction pour vérifier les prérequis
check_requirements() {
    print_status "info" "Vérification des prérequis..."
    
    # Vérifier Git
    if ! command -v git &> /dev/null; then
        print_status "error" "Git n'est pas installé"
        exit 1
    fi
    
    # Vérifier PostgreSQL dump tools
    if ! command -v pg_dump &> /dev/null; then
        print_status "warning" "pg_dump non trouvé - La sauvegarde de la base de données sera ignorée"
    fi
    
    # Créer les répertoires nécessaires
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$PROJECT_DIR/logs"
    
    print_status "success" "Prérequis vérifiés"
}

# Fonction pour sauvegarder la base de données
backup_database() {
    print_status "info" "Sauvegarde de la base de données..."
    
    if command -v pg_dump &> /dev/null; then
        # Lire les variables d'environnement
        if [ -f "$PROJECT_DIR/.env" ]; then
            source "$PROJECT_DIR/.env"
            
            if [ ! -z "$DB_NAME" ] && [ ! -z "$DB_USER" ]; then
                DB_BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}_database.sql"
                
                PGPASSWORD=$DB_PASSWORD pg_dump \
                    -h ${DB_HOST:-localhost} \
                    -p ${DB_PORT:-5432} \
                    -U $DB_USER \
                    -d $DB_NAME \
                    -f "$DB_BACKUP_FILE" \
                    --no-owner \
                    --no-privileges
                
                if [ $? -eq 0 ]; then
                    # Compresser le dump
                    gzip "$DB_BACKUP_FILE"
                    print_status "success" "Base de données sauvegardée et compressée"
                else
                    print_status "error" "Échec de la sauvegarde de la base de données"
                fi
            else
                print_status "warning" "Variables de base de données non configurées dans .env"
            fi
        else
            print_status "warning" "Fichier .env non trouvé"
        fi
    fi
}

# Fonction pour sauvegarder les fichiers media
backup_media() {
    print_status "info" "Sauvegarde des fichiers media..."
    
    if [ -d "$PROJECT_DIR/media" ]; then
        MEDIA_BACKUP="$BACKUP_DIR/${BACKUP_NAME}_media.tar.gz"
        tar -czf "$MEDIA_BACKUP" -C "$PROJECT_DIR" media/
        
        if [ $? -eq 0 ]; then
            print_status "success" "Fichiers media sauvegardés"
        else
            print_status "error" "Échec de la sauvegarde des fichiers media"
        fi
    else
        print_status "info" "Aucun répertoire media à sauvegarder"
    fi
}

# Fonction pour créer une sauvegarde locale complète
create_local_backup() {
    print_status "info" "Création de la sauvegarde locale..."
    
    # Liste des fichiers/dossiers à exclure
    EXCLUDE_LIST=(
        ".git"
        "__pycache__"
        "*.pyc"
        ".env"
        "venv"
        "env"
        "node_modules"
        "staticfiles"
        "media"
        "*.log"
        ".DS_Store"
        "*.sqlite3"
        "*.db"
        ".coverage"
        "htmlcov"
        ".pytest_cache"
        "dist"
        "build"
        "*.egg-info"
    )
    
    # Construire les options d'exclusion pour tar
    EXCLUDE_OPTIONS=""
    for item in "${EXCLUDE_LIST[@]}"; do
        EXCLUDE_OPTIONS="$EXCLUDE_OPTIONS --exclude=$item"
    done
    
    # Créer l'archive
    LOCAL_BACKUP="$BACKUP_DIR/${BACKUP_NAME}_code.tar.gz"
    tar -czf "$LOCAL_BACKUP" $EXCLUDE_OPTIONS -C "$PROJECT_DIR" .
    
    if [ $? -eq 0 ]; then
        print_status "success" "Sauvegarde locale créée: $LOCAL_BACKUP"
    else
        print_status "error" "Échec de la création de la sauvegarde locale"
        exit 1
    fi
}

# Fonction pour nettoyer les anciennes sauvegardes
cleanup_old_backups() {
    print_status "info" "Nettoyage des anciennes sauvegardes..."
    
    # Garder seulement les 7 dernières sauvegardes
    KEEP_BACKUPS=7
    
    # Compter les sauvegardes
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | grep "${PROJECT_NAME}_backup_" | wc -l)
    
    if [ $BACKUP_COUNT -gt $KEEP_BACKUPS ]; then
        # Obtenir la liste des sauvegardes à supprimer
        TO_DELETE=$(ls -1t "$BACKUP_DIR" | grep "${PROJECT_NAME}_backup_" | tail -n +$((KEEP_BACKUPS + 1)))
        
        for backup in $TO_DELETE; do
            rm -rf "$BACKUP_DIR/$backup"
            print_status "info" "Supprimé: $backup"
        done
        
        print_status "success" "Anciennes sauvegardes nettoyées"
    else
        print_status "info" "Aucune ancienne sauvegarde à nettoyer"
    fi
}

# Fonction pour synchroniser avec GitHub
sync_with_github() {
    print_status "info" "Synchronisation avec GitHub..."
    
    # Vérifier si c'est un dépôt Git
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        print_status "warning" "Ce n'est pas un dépôt Git. Initialisation..."
        git init
        git remote add origin "$GITHUB_REPO"
    fi
    
    # Vérifier la remote
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
    if [ "$CURRENT_REMOTE" != "$GITHUB_REPO" ]; then
        print_status "info" "Mise à jour de l'URL du dépôt distant"
        git remote set-url origin "$GITHUB_REPO"
    fi
    
    # Créer ou mettre à jour .gitignore
    create_gitignore
    
    # Statut Git
    print_status "info" "Statut du dépôt Git:"
    git status --short
    
    # Ajouter tous les changements
    git add -A
    
    # Vérifier s'il y a des changements à committer
    if git diff --cached --quiet; then
        print_status "info" "Aucun changement à committer"
    else
        # Créer le commit
        COMMIT_MSG="🔄 Mise à jour automatique - $(date +'%Y-%m-%d %H:%M:%S')

Sauvegarde automatique effectuée par le script backup_sync.sh
- Sauvegarde locale créée: $BACKUP_NAME
- Timestamp: $TIMESTAMP"
        
        git commit -m "$COMMIT_MSG"
        print_status "success" "Commit créé"
    fi
    
    # Récupérer les dernières modifications
    print_status "info" "Récupération des dernières modifications..."
    git fetch origin
    
    # Essayer de pull avec rebase
    if git pull --rebase origin main 2>/dev/null || git pull --rebase origin master 2>/dev/null; then
        print_status "success" "Modifications récupérées avec succès"
    else
        print_status "warning" "Aucune branche principale trouvée ou conflits détectés"
        
        # En cas de conflit, annuler le rebase
        git rebase --abort 2>/dev/null
        
        # Créer la branche main si elle n'existe pas
        if ! git show-ref --verify --quiet refs/heads/main; then
            git checkout -b main
            print_status "info" "Branche 'main' créée"
        fi
    fi
    
    # Pousser les modifications
    print_status "info" "Envoi des modifications vers GitHub..."
    
    # Déterminer la branche actuelle
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    if git push -u origin "$CURRENT_BRANCH"; then
        print_status "success" "Synchronisation avec GitHub réussie"
    else
        print_status "error" "Échec de la synchronisation avec GitHub"
        print_status "info" "Tentative de push forcé..."
        
        read -p "Voulez-vous forcer le push? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push -u origin "$CURRENT_BRANCH" --force
            print_status "warning" "Push forcé effectué"
        fi
    fi
}

# Fonction pour créer/mettre à jour .gitignore
create_gitignore() {
    cat > "$PROJECT_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.tox/
*.egg-info/
.eggs/
*.egg

# Django
*.log
*.pot
*.pyc
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environnement
.env
.env.*
!.env.example

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Backups
backups/
*.backup
*.bak

# Temporary files
*.tmp
*.temp
.~*

# OS files
Thumbs.db
.DS_Store
.AppleDouble
.LSOverride

# Logs
logs/
*.log

# Celery
celerybeat-schedule
celerybeat.pid

# Docker
.dockerignore
docker-compose.override.yml
EOF
    
    print_status "success" ".gitignore créé/mis à jour"
}

# Fonction pour créer un rapport de sauvegarde
create_backup_report() {
    REPORT_FILE="$BACKUP_DIR/${BACKUP_NAME}_report.txt"
    
    cat > "$REPORT_FILE" << EOF
========================================
RAPPORT DE SAUVEGARDE E-PATRIMOINE OPRAG
========================================

Date: $(date +'%Y-%m-%d %H:%M:%S')
Nom de la sauvegarde: $BACKUP_NAME

RÉSUMÉ:
-------
- Projet: $PROJECT_NAME
- Répertoire: $PROJECT_DIR
- Dépôt GitHub: $GITHUB_REPO

FICHIERS CRÉÉS:
--------------
EOF
    
    # Lister les fichiers de sauvegarde créés
    ls -lh "$BACKUP_DIR/${BACKUP_NAME}"* >> "$REPORT_FILE" 2>/dev/null
    
    # Ajouter les statistiques Git
    echo -e "\nSTATISTIQUES GIT:\n-----------------" >> "$REPORT_FILE"
    git log --oneline -5 >> "$REPORT_FILE" 2>/dev/null
    
    echo -e "\nESPACE DISQUE:\n--------------" >> "$REPORT_FILE"
    df -h "$BACKUP_DIR" >> "$REPORT_FILE"
    
    print_status "success" "Rapport de sauvegarde créé: $REPORT_FILE"
}

# Fonction principale
main() {
    echo "================================================"
    echo " SAUVEGARDE ET SYNCHRONISATION E-PATRIMOINE"
    echo "================================================"
    echo ""
    
    # Vérifier les prérequis
    check_requirements
    
    # Menu d'options
    echo "Que souhaitez-vous faire?"
    echo "1) Sauvegarde complète (locale + GitHub)"
    echo "2) Sauvegarde locale uniquement"
    echo "3) Synchronisation GitHub uniquement"
    echo "4) Sauvegarde base de données uniquement"
    echo "5) Restaurer une sauvegarde"
    
    read -p "Votre choix (1-5): " choice
    
    case $choice in
        1)
            create_local_backup
            backup_database
            backup_media
            sync_with_github
            cleanup_old_backups
            create_backup_report
            print_status "success" "Sauvegarde complète terminée!"
            ;;
        2)
            create_local_backup
            backup_database
            backup_media
            cleanup_old_backups
            create_backup_report
            print_status "success" "Sauvegarde locale terminée!"
            ;;
        3)
            sync_with_github
            print_status "success" "Synchronisation GitHub terminée!"
            ;;
        4)
            backup_database
            print_status "success" "Sauvegarde base de données terminée!"
            ;;
        5)
            restore_backup
            ;;
        *)
            print_status "error" "Choix invalide"
            exit 1
            ;;
    esac
    
    echo ""
    echo "================================================"
    print_status "info" "Logs disponibles dans: $LOG_FILE"
}

# Fonction de restauration
restore_backup() {
    print_status "info" "Sauvegardes disponibles:"
    
    # Lister les sauvegardes
    BACKUPS=($(ls -1t "$BACKUP_DIR" | grep "${PROJECT_NAME}_backup_" | grep "_code.tar.gz" | sed 's/_code.tar.gz//'))
    
    if [ ${#BACKUPS[@]} -eq 0 ]; then
        print_status "error" "Aucune sauvegarde trouvée"
        return
    fi
    
    # Afficher les sauvegardes
    for i in "${!BACKUPS[@]}"; do
        echo "$((i+1))) ${BACKUPS[$i]}"
    done
    
    read -p "Choisir une sauvegarde (1-${#BACKUPS[@]}): " choice
    
    if [[ "$choice" -ge 1 && "$choice" -le ${#BACKUPS[@]} ]]; then
        SELECTED_BACKUP="${BACKUPS[$((choice-1))]}"
        
        print_status "warning" "⚠️  ATTENTION: Cette action va écraser les fichiers actuels!"
        read -p "Confirmer la restauration de $SELECTED_BACKUP? (y/N) " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Créer une sauvegarde de sécurité avant la restauration
            print_status "info" "Création d'une sauvegarde de sécurité..."
            SAFETY_BACKUP="$BACKUP_DIR/safety_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
            tar -czf "$SAFETY_BACKUP" -C "$PROJECT_DIR" . --exclude=.git
            
            # Restaurer
            print_status "info" "Restauration en cours..."
            tar -xzf "$BACKUP_DIR/${SELECTED_BACKUP}_code.tar.gz" -C "$PROJECT_DIR"
            
            if [ $? -eq 0 ]; then
                print_status "success" "Restauration réussie"
                
                # Proposer de restaurer la base de données
                if [ -f "$BACKUP_DIR/${SELECTED_BACKUP}_database.sql.gz" ]; then
                    read -p "Restaurer aussi la base de données? (y/N) " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        restore_database "${SELECTED_BACKUP}_database.sql.gz"
                    fi
                fi
                
                # Proposer de restaurer les media
                if [ -f "$BACKUP_DIR/${SELECTED_BACKUP}_media.tar.gz" ]; then
                    read -p "Restaurer aussi les fichiers media? (y/N) " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        tar -xzf "$BACKUP_DIR/${SELECTED_BACKUP}_media.tar.gz" -C "$PROJECT_DIR"
                        print_status "success" "Fichiers media restaurés"
                    fi
                fi
            else
                print_status "error" "Échec de la restauration"
                print_status "info" "Sauvegarde de sécurité disponible: $SAFETY_BACKUP"
            fi
        fi
    else
        print_status "error" "Choix invalide"
    fi
}

# Fonction pour restaurer la base de données
restore_database() {
    local DB_BACKUP_FILE="$BACKUP_DIR/$1"
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        
        print_status "info" "Restauration de la base de données..."
        
        # Décompresser
        gunzip -c "$DB_BACKUP_FILE" | PGPASSWORD=$DB_PASSWORD psql \
            -h ${DB_HOST:-localhost} \
            -p ${DB_PORT:-5432} \
            -U $DB_USER \
            -d $DB_NAME
        
        if [ $? -eq 0 ]; then
            print_status "success" "Base de données restaurée"
        else
            print_status "error" "Échec de la restauration de la base de données"
        fi
    fi
}

# Lancer le script principal
main