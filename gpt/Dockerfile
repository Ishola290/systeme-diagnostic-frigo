# Stage 1: Base image avec Python et dépendances système
FROM python:3.11-slim as base

WORKDIR /app

# Installer les dépendances système pour PyTorch et compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Stage 2: Installation des dépendances Python
FROM base as builder

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Image finale
FROM base

# Copier les dépendances du builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application gpt/
COPY gpt/ .

# Copier les modèles vers ../models (accessible via chemin relatif)
COPY models/ ../models/

# Créer les répertoires de logs et data
RUN mkdir -p /app/logs /app/data /app/cache

# Définir les variables d'environnement
ENV FLASK_APP=app_ia.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV IA_MODEL=phi
ENV IA_USE_GPU=false
ENV HF_LOCAL_MODEL_PATH=/app/../models/phi-2
ENV MAIN_APP_URL=http://app:5000
ENV CHAT_API_URL=http://chat:5001

# Port d'exposition
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Commande de démarrage
CMD ["python", "-m", "gunicorn", "-w", "1", "-b", "0.0.0.0:5002", "--timeout", "120", "app_ia:app"]
