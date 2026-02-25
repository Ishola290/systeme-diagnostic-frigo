# Déploiement sur Render - Guide complet

## Architecture finale (compatible Render gratuit)

```
Render Services (3 instances):
├── App principale (5000 → 10000)
├── Chat Web (5001 → 10000)  
└── IA Service Gemini (5002 → 10000)

Vos modèles externes:
├── API Prédiction Panne 1 (votre serveur)
├── API Prédiction Panne 2 (votre serveur)
└── Google Gemini API (cloud)
```

## Étapes de déploiement

### 1. Créer les services sur Render

1. **App principale**
   - Repository: votre repo Git
   - Root Directory: /
   - Dockerfile Path: `Dockerfile.render`
   - Environment Variables: voir `.env.render`

2. **Chat Web**
   - Repository: votre repo Git
   - Root Directory: `chat/`
   - Dockerfile Path: `Dockerfile.render`
   - Environment Variables: mêmes que app principale

3. **IA Service**
   - Repository: votre repo Git
   - Root Directory: `gpt/`
   - Dockerfile Path: `Dockerfile.render`
   - Environment Variables: ajouter `GEMINI_API_KEY`

### 2. Variables d'environnement obligatoires

```bash
# Pour tous les services
FLASK_ENV=production
PYTHONUNBUFFERED=1

# Pour IA Service
GEMINI_API_KEY=votre_clé_gemini_ici
GEMINI_MODEL=gemini-2.5-flash

# Pour App principale
AGENT_IA_URL=https://vos-modeles.onrender.com
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id

# URLs inter-services (Render génère automatiquement)
MAIN_APP_URL=https://votre-app.onrender.com
CHAT_API_URL=https://votre-chat.onrender.com
IA_SERVICE_URL=https://votre-ia.onrender.com
```

### 3. Configuration des URLs

Après déploiement, mettez à jour les URLs dans les variables d'environnement:

```bash
# Exemple:
MAIN_APP_URL=https://frigo-diagnostic.onrender.com
CHAT_API_URL=https://frigo-chat.onrender.com
IA_SERVICE_URL=https://frigo-ia.onrender.com
```

### 4. Test de déploiement

1. **Health checks**
   ```bash
   curl https://votre-app.onrender.com/health
   curl https://votre-chat.onrender.com/
   curl https://votre-ia.onrender.com/health
   ```

2. **Test complet**
   - Accéder au chat: `https://votre-chat.onrender.com/dashboard`
   - Envoyer un message de test
   - Vérifier la réponse Gemini

## Avantages de cette architecture

✅ **Compatible Render gratuit** (512MB RAM max)
✅ **Pas de modèles locaux** (tout via API)
✅ **Scalable** (chaque service indépendant)
✅ **Robuste** (health checks, fallbacks)
✅ **Sécurisé** (API keys, isolation)

## Migration depuis local

```bash
# Local (Ollama)
export IA_MODEL=ollama
export OLLAMA_URL=http://localhost:11434

# Production (Gemini)
export GEMINI_API_KEY=votre_clé
export GEMINI_MODEL=gemini-2.5-flash
```

Le code détecte automatiquement l'environnement !
