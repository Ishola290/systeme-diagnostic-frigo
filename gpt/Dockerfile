# Multi-stage Dockerfile: Télécharge automatiquement les modèles IA
FROM python:3.11-slim as model-downloader

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et script de téléchargement depuis racine
COPY requirements.txt /tmp/requirements.txt
COPY download_models.py /tmp/download_models.py

# Installer les dépendances Python
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Télécharger les modèles IA (phi par défaut = 5GB, ~10 min)
RUN mkdir -p /app/models && \
    cd /tmp && \
    python download_models.py --model phi 2>&1 && \
    echo "✅ Modèle phi téléchargé avec succès" && \
    mv /tmp/models/phi /app/models/ || echo "Modèle déjà en place"

# ============================================================
# Stage 2: Image finale avec modèles pré-inclus
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les modèles du stage précédent
COPY --from=model-downloader /app/models /app/models

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application gpt/
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/cache

# Variables d'environnement
ENV FLASK_APP=app_ia.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV IA_MODEL=phi
ENV IA_USE_GPU=false
ENV HF_LOCAL_MODEL_PATH=/app/models/phi
ENV MAIN_APP_URL=http://app:5000
ENV CHAT_API_URL=http://chat:5001

# Port d'exposition
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Commande de démarrage
CMD ["python", "-m", "gunicorn", "-w", "1", "-b", "0.0.0.0:5002", "--timeout", "120", "app_ia:app"]
