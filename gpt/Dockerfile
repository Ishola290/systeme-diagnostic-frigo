FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers nécessaires depuis la racine
COPY services/ ./services/
COPY gpt/ .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/models /app/cache

ENV FLASK_APP=app_ia.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV IA_MODEL=api
ENV IA_USE_GPU=false

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

CMD ["python", "-m", "gunicorn", "-w", "1", "-b", "0.0.0.0:5002", "--timeout", "120", "app_ia:app"]
