# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code
COPY . .

# Créer un utilisateur non-root et lui donner les permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "patrimoine_project.wsgi:application", "--bind", "0.0.0.0:8000"]