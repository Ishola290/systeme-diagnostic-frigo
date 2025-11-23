FROM python:3.11-slim

LABEL maintainer="Diagnostic Frigo Team"
LABEL description="Application Web Chat - Système Diagnostic Frigorifique"

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY chat/requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt gunicorn gevent gevent-websocket

# Copier l'application
COPY chat/ .

# Copier les modèles (optionnel pour ce service, mais utile pour cohabitation)
COPY models/ ../models/

# Créer les répertoires pour la persistance
RUN mkdir -p /app/instance /app/logs && \
    chmod 755 /app/instance /app/logs

# Variables d'environnement pour accès aux autres services
ENV MAIN_APP_URL=http://app:5000
ENV IA_SERVICE_URL=http://gpt:5002

# Exposer le port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/', timeout=5)" || exit 1

# Script de démarrage avec initialisation DB
CMD ["sh", "-c", "python init_db.py && python create_admin.py && gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:5001 --timeout 120 app_web:app"]
