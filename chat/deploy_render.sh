#!/bin/bash
# Script de déploiement pour Render

# Variables
RENDER_SERVICE_NAME=${RENDER_SERVICE_NAME:-"frigo-chat"}
RENDER_REGION=${RENDER_REGION:-"frankfurt"}

echo "🚀 Préparation du déploiement sur Render..."
echo "Service: $RENDER_SERVICE_NAME"
echo "Région: $RENDER_REGION"

# Créer le fichier render.yaml
cat > render.yaml << 'EOF'
services:
  - type: web
    name: frigo-chat
    runtime: python
    pythonVersion: 3.11
    plan: free
    buildCommand: pip install -r chat/requirements.txt
    startCommand: cd chat && gunicorn -w 2 -b 0.0.0.0:$PORT --worker-class eventlet -e PYTHONUNBUFFERED=1 'app_web:app'
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PYTHONUNBUFFERED
        value: 1
    healthCheckPath: /
    autoDeployOnPush: true
EOF

echo "✅ render.yaml créé"
echo ""
echo "📋 Configuration recommandée Render:"
echo "1. Build Command: pip install -r chat/requirements.txt"
echo "2. Start Command: cd chat && python app_web.py"
echo "3. Environment Variables:"
echo "   - FLASK_ENV: production"
echo "   - SECRET_KEY: (générer avec secrets.token_hex(32))"
echo "   - MAIN_APP_URL: (URL de l'app principale)"
echo "   - DATABASE_URL: (si PostgreSQL)"
echo ""
echo "✨ Pour pusher: git push origin main"
