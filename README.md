# E-PATRIMOINE OPRAG

<p align="center">
  <img src="docs/images/logo-oprag.png" alt="Logo OPRAG" width="200"/>
</p>

<p align="center">
  <strong>Système de Gestion du Patrimoine pour l'Office des Ports et Rades du Gabon</strong>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/django-5.0-green.svg" alt="Django"></a>
  <a href="#"><img src="https://img.shields.io/badge/vue.js-3.0-brightgreen.svg" alt="Vue.js"></a>
  <a href="#"><img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License"></a>
</p>

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [API Documentation](#-api-documentation)
- [Sauvegarde et Restauration](#-sauvegarde-et-restauration)
- [Développement](#-développement)
- [Tests](#-tests)
- [Déploiement](#-déploiement)
- [Maintenance](#-maintenance)
- [Contribution](#-contribution)
- [Support](#-support)
- [Licence](#-licence)

## 🌟 Vue d'ensemble

**E-Patrimoine OPRAG** est une solution complète de gestion patrimoniale développée spécifiquement pour l'Office des Ports et Rades du Gabon. Cette application web moderne permet de gérer, suivre et optimiser l'ensemble des actifs de l'organisation avec des fonctionnalités avancées de traçabilité, d'analyse et de reporting.

### Objectifs principaux

- 📊 **Inventaire complet** : Catalogage détaillé de tous les biens avec catégorisation flexible
- 🗺️ **Géolocalisation** : Visualisation cartographique de la répartition des actifs
- 📈 **Suivi financier** : Gestion des amortissements et de l'évolution des valeurs
- 👥 **Gestion des responsabilités** : Affectation et suivi des responsables par bien
- 🔧 **Maintenance préventive** : Planification et suivi des maintenances
- 📱 **Mobilité** : Interface responsive accessible sur tous les appareils

## ✨ Fonctionnalités

### Gestion des biens
- ✅ Création et modification de fiches détaillées par type de bien
- ✅ Catégorisation hiérarchique (catégories et sous-catégories)
- ✅ Profils techniques spécialisés (véhicules, bâtiments, équipements, etc.)
- ✅ Gestion des documents associés (factures, photos, contrats)
- ✅ Génération de QR codes pour l'identification rapide
- ✅ Import/Export en masse (Excel, CSV)

### Suivi et traçabilité
- ✅ Historique complet des mouvements et transferts
- ✅ Traçabilité des responsables successifs
- ✅ Historique des valeurs et réévaluations
- ✅ Journal d'audit complet des modifications

### Maintenance et alertes
- ✅ Planification des maintenances préventives et correctives
- ✅ Alertes automatiques (garanties, maintenances, etc.)
- ✅ Tableau de bord des biens critiques
- ✅ Statistiques MTBF (Mean Time Between Failures)

### Analyses et rapports
- ✅ Tableaux de bord interactifs avec graphiques
- ✅ Rapports personnalisables par entité/catégorie
- ✅ Analyses d'amortissement et de dépréciation
- ✅ Export des rapports en PDF/Excel

### Fonctionnalités avancées
- ✅ API REST complète pour intégrations
- ✅ Authentification à deux facteurs (2FA)
- ✅ Gestion multi-entités avec hiérarchie
- ✅ Workflow d'approbation configurable
- ✅ Recherche full-text avec ElasticSearch
- ✅ Sauvegarde automatisée et récupération

## 🏗️ Architecture

### Stack technologique

#### Backend
- **Framework** : Django 5.0 (Python 3.8+)
- **Base de données** : PostgreSQL 15 avec PostGIS
- **Cache** : Redis
- **Tâches asynchrones** : Celery + Redis
- **API** : Django REST Framework
- **Authentification** : JWT (JSON Web Tokens)
- **Recherche** : ElasticSearch 8.x

#### Frontend
- **Framework** : Vue.js 3 avec Composition API
- **Language** : TypeScript
- **UI Framework** : Bootstrap 5 + custom components
- **State Management** : Pinia
- **HTTP Client** : Axios
- **Graphiques** : Chart.js + D3.js
- **Cartes** : Leaflet.js

#### Infrastructure
- **Containerisation** : Docker & Docker Compose
- **Reverse Proxy** : Nginx
- **Monitoring** : Sentry + Prometheus
- **CI/CD** : GitHub Actions
- **Stockage** : Compatible S3 (AWS/MinIO)

### Structure du projet

```
e-patrimoine_oprag/
├── apps/                      # Applications Django modulaires
│   ├── patrimoine/           # App principale de gestion des biens
│   ├── api/                  # API REST
│   ├── authentication/       # Authentification et permissions
│   ├── notifications/        # Système de notifications
│   └── reports/             # Génération de rapports
├── config/                   # Configuration du projet
│   ├── settings/            # Settings par environnement
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # WSGI configuration
├── frontend/                # Application Vue.js
│   ├── src/
│   │   ├── components/     # Composants réutilisables
│   │   ├── views/          # Pages/vues
│   │   ├── stores/         # State management (Pinia)
│   │   ├── api/            # Services API
│   │   └── assets/         # Images, styles
│   └── dist/               # Build de production
├── docker/                  # Configuration Docker
│   ├── nginx/              # Config Nginx
│   ├── postgres/           # Scripts d'init PostgreSQL
│   └── redis/              # Config Redis
├── docs/                    # Documentation
├── locale/                  # Traductions (i18n)
├── logs/                    # Fichiers de logs
├── media/                   # Fichiers uploadés
├── scripts/                 # Scripts utilitaires
├── static/                  # Fichiers statiques
├── templates/              # Templates Django
├── tests/                   # Tests unitaires et d'intégration
├── .env.example            # Variables d'environnement exemple
├── .gitignore              # Fichiers ignorés par Git
├── backup_sync.sh          # Script de sauvegarde
├── docker-compose.yml      # Configuration Docker Compose
├── manage.py               # Script de gestion Django
├── package.json            # Dépendances Node.js
├── pytest.ini              # Configuration des tests
├── README.md               # Ce fichier
└── requirements.txt        # Dépendances Python
```

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- PostgreSQL 15 avec PostGIS
- Redis 7.x
- Node.js 18+ et npm
- Git
- Docker et Docker Compose (optionnel mais recommandé)

### Installation avec Docker (Recommandé)

1. **Cloner le repository**
```bash
git clone https://github.com/kiabasekou/e-patrimoine_oprag.git
cd e-patrimoine_oprag
```

2. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

3. **Lancer avec Docker Compose**
```bash
docker-compose up -d
```

4. **Initialiser la base de données**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

5. **Charger les données initiales**
```bash
docker-compose exec web python manage.py loaddata fixtures/initial_data.json
```

L'application sera accessible à :
- Frontend : http://localhost
- API : http://localhost/api
- Admin Django : http://localhost/admin

### Installation manuelle

1. **Cloner le repository**
```bash
git clone https://github.com/kiabasekou/e-patrimoine_oprag.git
cd e-patrimoine_oprag
```

2. **Créer un environnement virtuel Python**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances Python**
```bash
pip install -r requirements.txt
```

4. **Installer les dépendances Node.js**
```bash
npm install
```

5. **Configurer PostgreSQL**
```sql
CREATE DATABASE epatrimoine_oprag;
CREATE USER oprag_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE epatrimoine_oprag TO oprag_user;
CREATE EXTENSION postgis;
```

6. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres de base de données et autres configurations
```

7. **Appliquer les migrations**
```bash
python manage.py migrate
```

8. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

9. **Collecter les fichiers statiques**
```bash
python manage.py collectstatic
```

10. **Compiler le frontend**
```bash
npm run build
```

11. **Lancer le serveur de développement**
```bash
# Terminal 1 - Backend
python manage.py runserver

# Terminal 2 - Frontend (développement)
npm run dev

# Terminal 3 - Celery Worker
celery -A config worker -l info

# Terminal 4 - Celery Beat (tâches périodiques)
celery -A config beat -l info
```

## ⚙️ Configuration

### Variables d'environnement principales

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DB_NAME=epatrimoine_oprag
DB_USER=oprag_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=E-Patrimoine OPRAG <noreply@oprag.ga>

# OPRAG Specific
OPRAG_ORGANISATION_NAME=Office des Ports et Rades du Gabon
OPRAG_ASSET_CODE_PREFIX=OPRAG
OPRAG_DEFAULT_CURRENCY=XAF
OPRAG_ENABLE_2FA=True
OPRAG_REQUIRE_APPROVAL_WORKFLOW=True

# Storage (S3 compatible)
USE_S3=False
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=epatrimoine-oprag
AWS_S3_REGION_NAME=eu-west-1

# Sentry (Monitoring)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# ElasticSearch
ELASTICSEARCH_HOST=localhost:9200
```

### Configuration Nginx (Production)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 100M;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }
}
```

## 💻 Utilisation

### Accès à l'application

1. **Page de connexion** : http://localhost/login
   - Utiliser les identifiants créés avec `createsuperuser`
   - Activer l'authentification à deux facteurs (2FA) recommandé

2. **Dashboard principal** : http://localhost/dashboard
   - Vue d'ensemble des statistiques
   - Alertes et notifications
   - Accès rapide aux fonctionnalités

3. **Gestion des biens** : http://localhost/biens
   - Lister, filtrer et rechercher les biens
   - Créer de nouveaux biens
   - Exporter les données

### Workflow de base

1. **Créer les données de référence**
   - Catégories et sous-catégories
   - Entités organisationnelles
   - Responsables

2. **Ajouter un nouveau bien**
   - Sélectionner la catégorie appropriée
   - Remplir les informations obligatoires
   - Ajouter les documents (factures, photos)
   - Assigner un responsable

3. **Gérer le cycle de vie**
   - Planifier les maintenances
   - Suivre les transferts entre entités
   - Mettre à jour les évaluations
   - Réformer si nécessaire

## 📚 API Documentation

L'API REST est documentée avec OpenAPI/Swagger.

### Accès à la documentation
- Swagger UI : http://localhost/api/swagger/
- ReDoc : http://localhost/api/redoc/
- Schema JSON : http://localhost/api/schema/

### Authentification API

```bash
# Obtenir un token JWT
curl -X POST http://localhost/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'

# Utiliser le token
curl -X GET http://localhost/api/v1/biens/ \
  -H "Authorization: Bearer your-jwt-token"
```

### Endpoints principaux

- `GET /api/v1/biens/` - Liste des biens
- `POST /api/v1/biens/` - Créer un bien
- `GET /api/v1/biens/{id}/` - Détails d'un bien
- `PUT /api/v1/biens/{id}/` - Modifier un bien
- `DELETE /api/v1/biens/{id}/` - Supprimer un bien
- `POST /api/v1/biens/{id}/transferer/` - Transférer un bien
- `GET /api/v1/biens/export/` - Exporter en Excel/CSV
- `POST /api/v1/biens/import_bulk/` - Import en masse

## 💾 Sauvegarde et Restauration

### Script de sauvegarde automatique

Le projet inclut un script `backup_sync.sh` pour automatiser les sauvegardes.

```bash
# Rendre le script exécutable
chmod +x backup_sync.sh

# Lancer une sauvegarde complète
./backup_sync.sh
```

Options disponibles :
1. Sauvegarde complète (locale + GitHub)
2. Sauvegarde locale uniquement
3. Synchronisation GitHub uniquement
4. Sauvegarde base de données uniquement
5. Restaurer une sauvegarde

### Sauvegarde manuelle

```bash
# Sauvegarder la base de données
pg_dump -U oprag_user -h localhost epatrimoine_oprag > backup_$(date +%Y%m%d).sql

# Sauvegarder les fichiers media
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Sauvegarder le code (sans .git, venv, etc.)
tar --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    -czf code_backup_$(date +%Y%m%d).tar.gz .
```

### Restauration

```bash
# Restaurer la base de données
psql -U oprag_user -h localhost epatrimoine_oprag < backup_20240315.sql

# Restaurer les fichiers media
tar -xzf media_backup_20240315.tar.gz

# Restaurer le code
tar -xzf code_backup_20240315.tar.gz
```

### Automatisation avec Cron

```bash
# Éditer le crontab
crontab -e

# Ajouter une sauvegarde quotidienne à 2h du matin
0 2 * * * /path/to/e-patrimoine_oprag/backup_sync.sh 1 >> /var/log/backup.log 2>&1
```

## 🛠️ Développement

### Structure de développement

```bash
# Installer les outils de développement
pip install -r requirements-dev.txt

# Lancer les tests
pytest

# Vérifier la couverture de code
pytest --cov=apps --cov-report=html

# Linter Python
flake8 apps/
black apps/ --check

# Linter JavaScript/Vue
npm run lint

# Formater le code
black apps/
npm run format
```

### Conventions de code

- **Python** : PEP 8 avec Black formatter
- **JavaScript/TypeScript** : ESLint + Prettier
- **Vue** : Vue 3 Composition API avec TypeScript
- **Git** : Conventional Commits

### Workflow Git

```bash
# Créer une nouvelle fonctionnalité
git checkout -b feature/nom-fonctionnalite

# Commit avec message conventionnel
git commit -m "feat: ajouter la gestion des alertes email"

# Pousser et créer une Pull Request
git push origin feature/nom-fonctionnalite
```

Types de commits :
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `style:` Formatage, style
- `refactor:` Refactoring
- `test:` Ajout de tests
- `chore:` Maintenance

## 🧪 Tests

### Tests unitaires

```bash
# Lancer tous les tests
pytest

# Tests d'une app spécifique
pytest apps/patrimoine/tests/

# Tests avec verbosité
pytest -v

# Tests en parallèle
pytest -n 4
```

### Tests d'intégration

```bash
# Tests API
pytest apps/api/tests/test_integration.py

# Tests Selenium (interface)
pytest tests/e2e/ --driver Chrome
```

### Tests de performance

```bash
# Locust pour les tests de charge
locust -f tests/performance/locustfile.py
```

## 🚢 Déploiement

### Déploiement avec Docker

1. **Build des images**
```bash
docker-compose -f docker-compose.prod.yml build
```

2. **Lancer en production**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Mise à jour**
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps web
```

### Déploiement manuel

1. **Préparer le serveur**
```bash
# Installer les dépendances système
sudo apt update
sudo apt install python3.8 postgresql nginx redis supervisor

# Cloner le projet
git clone https://github.com/kiabasekou/e-patrimoine_oprag.git
cd e-patrimoine_oprag
```

2. **Configuration de production**
```bash
# Installer les dépendances
pip install -r requirements.txt
npm install --production

# Variables d'environnement
cp .env.example .env.production
# Éditer avec les valeurs de production

# Build du frontend
npm run build

# Collecter les static
python manage.py collectstatic --noinput

# Migrations
python manage.py migrate
```

3. **Configuration Supervisor**
```ini
[program:epatrimoine]
command=/path/to/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000
directory=/path/to/e-patrimoine_oprag
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/epatrimoine.log

[program:celery]
command=/path/to/venv/bin/celery -A config worker -l info
directory=/path/to/e-patrimoine_oprag
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery.log
```

## 🔧 Maintenance

### Tâches de maintenance régulières

1. **Quotidien**
   - Vérifier les logs d'erreur
   - Monitorer l'espace disque
   - Vérifier les sauvegardes

2. **Hebdomadaire**
   - Nettoyer les fichiers temporaires
   - Analyser les performances
   - Mettre à jour les dépendances de sécurité

3. **Mensuel**
   - Optimiser la base de données
   - Réviser les accès utilisateurs
   - Mettre à jour la documentation

### Commands de maintenance

```bash
# Nettoyer les sessions expirées
python manage.py clearsessions

# Optimiser la base de données
python manage.py dbshell
VACUUM ANALYZE;

# Vérifier les mises à jour de sécurité
pip list --outdated
npm audit

# Nettoyer les fichiers media orphelins
python manage.py cleanup_media
```

## 🤝 Contribution

### Guide de contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'feat: Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Standards de code

- Suivre PEP 8 pour Python
- Utiliser ESLint pour JavaScript
- Écrire des tests pour toute nouvelle fonctionnalité
- Documenter les fonctions et classes
- Mettre à jour le README si nécessaire

## 📞 Support

Pour toute question ou assistance :

- **Email** : support@oprag.ga
- **Documentation** : https://docs.e-patrimoine-oprag.ga
- **Issues GitHub** : https://github.com/kiabasekou/e-patrimoine_oprag/issues

### FAQ

**Q: Comment réinitialiser un mot de passe administrateur ?**
```bash
python manage.py changepassword username
```

**Q: Comment ajouter une nouvelle catégorie de bien ?**
R: Via l'interface d'administration Django ou l'API REST.

**Q: Comment configurer les alertes email ?**
R: Configurer les paramètres SMTP dans le fichier .env et activer les notifications dans l'interface utilisateur.

## 📄 Licence

Ce logiciel est la propriété exclusive de l'Office des Ports et Rades du Gabon (OPRAG).
Tous droits réservés. © 2024 OPRAG

**Développé par** : Ahmed SOUARE
**Contact** : souare.ahmed@gmail.com | +241 77 96 38 47

---

<p align="center">
  <strong>E-Patrimoine OPRAG</strong> - Système de Gestion du Patrimoine<br>
  Une solution moderne pour une gestion efficace des actifs
</p>