# Multi-stage Dockerfile: Télécharge automatiquement les modèles
FROM python:3.11-slim as model-downloader

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et script de téléchargement
COPY requirements.txt download_models.py ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Télécharger les modèles IA (phi par défaut = 5GB, ~10 min)
RUN mkdir -p /app/models && \
    python download_models.py --model phi 2>&1 && \
    echo "✅ Modèle phi téléchargé avec succès"

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

# Copier l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/data

# Variables d'environnement
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV HF_LOCAL_MODEL_PATH=/app/models/phi
ENV CHAT_API_URL=http://chat:5001
ENV IA_SERVICE_URL=http://gpt:5002

# Exposer le port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Commande de démarrage
CMD ["python", "app.py"]
