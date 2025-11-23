FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/data /app/models

# Variables d'environnement
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV HF_LOCAL_MODEL_PATH=/app/models/phi-2
ENV CHAT_API_URL=http://chat:5001
ENV IA_SERVICE_URL=http://gpt:5002

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "app.py"]
