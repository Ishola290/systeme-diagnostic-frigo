# 🚀 Guide de Déploiement - Architecture IA 3 Services

## ✅ Changements Réalisés

### 1. **app.py** - Service Principal
- ❌ **Supprimé:** GeminiService
- ✅ **Remplacé par:** Appels au service IA (port 5002)
- **Modifications:**
  - Routes alerte → `/api/alerts/process` (service IA)
  - Routes retraining → `/api/learn` (service IA)
  - Routes nouvelle panne → `/api/learn` (service IA)
  - Fallback HTTP avec gestion d'erreurs

### 2. **chat/app_web.py** - Service Web
- ❌ **Supprimé:** Appels app.py pour messages
- ✅ **Remplacé par:** Appels directs au service IA (port 5002)
- **Modifications:**
  - Config.IA_SERVICE_URL ajoutée
  - POST `/api/messages` → appelle `/api/chat/message` (service IA)
  - WebSocket `send_message` → appelle service IA en temps réel
  - WebSocket `request_system_response` → appelle service IA

### 3. **gpt/Dockerfile** - Containerisation IA
- Base Python 3.11
- Dépendances: torch, transformers, accelerate, etc.
- Modèle par défaut: Phi-2 (auto-téléchargé au démarrage)
- Health check intégré
- Gunicorn en production (1 worker, timeout 120s)

### 4. **docker-compose.yml** - Orchestration 3 Services
- ✅ **Service 1:** main-app (port 5000) - Diagnostic principal
- ✅ **Service 2:** chat-web (port 5001) - Interface web chat
- ✅ **Service 3:** ia-service (port 5002) - LLM Phi-2 local
- **Volumes persistants:**
  - ia-models (5-10GB) - Modèles LLM
  - ia-data - Base de connaissances
  - ia-logs - Logs du service IA

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   CLIENT (Browser)                       │
└──────────────────────┬──────────────────────────────────┘
                       │ WebSocket
                       ↓
┌─────────────────────────────────────────────────────────┐
│  CHAT WEB (port 5001)                                   │
│  - Dashboard en temps réel                              │
│  - Historique messages                                  │
│  - Alertes                                              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    IA Service     MAIN APP      Telegram
    (port 5002)   (port 5000)
        │              │
        └──────┬───────┘
               │
        ┌──────────────────┐
        │  Phi-2 LLM       │
        │  (2.7B model)    │
        │  GPU/CPU auto    │
        └──────────────────┘
```

## 📦 Déploiement Local

### Étape 1: Préparation

```powershell
# Aller au répertoire racine
cd c:\Users\hp\Desktop\systeme-diagnostic-frigo

# Vérifier Docker
docker --version
docker-compose --version

# Créer les fichiers d'environnement
echo "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN" > .env
echo "TELEGRAM_CHAT_ID=YOUR_CHAT_ID" >> .env
echo "IA_MODEL=phi" >> .env
echo "IA_USE_GPU=false" >> .env
```

### Étape 2: Build des images

```powershell
# Build complet des 3 services (peut prendre 10-15 minutes)
docker-compose build

# Ou rebuild sans cache
docker-compose build --no-cache
```

### Étape 3: Démarrage

```powershell
# Démarrer tous les services
docker-compose up -d

# Vérifier que les services sont en cours d'exécution
docker-compose ps

# Regarder les logs
docker-compose logs -f
```

### Étape 4: Tests

```powershell
# Test main-app
curl http://localhost:5000/health

# Test chat-web
curl http://localhost:5001/

# Test ia-service
curl http://localhost:5002/health
```

## 🤖 Chargement du Modèle Phi-2

**Important:** La première exécution du service IA téléchargera le modèle (~5.3GB)
- **Temps:** 5-30 minutes selon la connexion internet
- **Espace:** 15GB disque libre recommandé
- **Une seule fois:** Le modèle est mis en cache dans le volume `ia-models`

### Monitoring du téléchargement

```powershell
# Suivre les logs du téléchargement
docker logs -f frigo-ia-service

# Vérifier l'espace utilisé par le modèle
docker volume ls
docker volume inspect frigo_ia-models
```

## 🎯 Utilisation

### Via le Dashboard Web

1. **Ouvrir:** http://localhost:5001
2. **Login:** admin@example.com / admin123
3. **Chat:** Envoyer un message
4. **Réponse IA:** Obtenir une réponse intelligente du modèle Phi-2

### Via API HTTP

```powershell
# Chat message
curl -X POST http://localhost:5002/api/chat/message `
  -H "Content-Type: application/json" `
  -d '{
    "message": "Le compresseur ne démarre pas",
    "user_id": "test",
    "user_name": "Technicien"
  }'

# Alerte
curl -X POST http://localhost:5002/api/alerts/process `
  -H "Content-Type: application/json" `
  -d '{
    "title": "Anomalie température",
    "severity": "critical",
    "sensors": {"temp": 28, "humidity": 65}
  }'
```

## ⚙️ Configuration

### Variables d'Environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `IA_MODEL` | `phi` | Modèle LLM: phi, mistral, neural, llama, gpt2 |
| `IA_USE_GPU` | `false` | Utiliser GPU NVIDIA (nécessite nvidia-docker) |
| `IA_TEMPERATURE` | `0.7` | Créativité des réponses (0-1) |
| `IA_MAX_TOKENS` | `512` | Longueur max des réponses |
| `FLASK_ENV` | `production` | Mode: production ou development |

### Changer de modèle LLM

```powershell
# Utiliser Mistral-7B (meilleure qualité, plus lent)
docker-compose down
$env:IA_MODEL="mistral"
docker-compose up -d

# Utiliser GPT-2 (très léger, test rapide)
$env:IA_MODEL="gpt2"
docker-compose up -d ia-service
```

## 🐛 Résolution de Problèmes

### Service IA ne démarre pas

```powershell
# Vérifier les logs
docker logs frigo-ia-service

# Relancer avec rebuild
docker-compose up -d --build ia-service
```

### Pas assez de mémoire

```powershell
# Utiliser modèle plus léger
$env:IA_MODEL="gpt2"
docker-compose restart ia-service

# Ou désactiver GPU (si activé)
$env:IA_USE_GPU="false"
```

### Modèle très lent

C'est **normal** sur CPU:
- Phi-2 sur CPU: 3-5 sec/réponse (normal)
- Mistral sur CPU: 20+ sec/réponse
- **Solution:** Installer GPU ou utiliser GPT-2

### Erreur "CUDA out of memory"

```powershell
$env:IA_USE_GPU="false"
docker-compose restart ia-service
```

## 📊 Performance

| Modèle | Vitesse | CPU | GPU | Qualité |
|--------|---------|-----|-----|---------|
| GPT-2 | ⚡⚡⚡ | 0.5s | 0.1s | Basique |
| Phi-2 | ⚡⚡ | 3-5s | 0.5s | Bon ⭐ |
| Mistral | ⚡ | 20s+ | 1-2s | Excellent |

## 🔒 Production

### Avant de déployer en production:

1. **Changer les secrets**
   ```bash
   # Générer une clé sécurisée
   python -c "import secrets; print(secrets.token_hex(32))"
   # Ajouter à .env
   SECRET_KEY=<votre-clé-générée>
   ```

2. **Utiliser Mistral pour meilleure qualité**
   ```bash
   IA_MODEL=mistral
   ```

3. **Activer GPU si disponible**
   ```bash
   IA_USE_GPU=true
   ```

4. **Mettre à jour les credentials**
   ```bash
   TELEGRAM_BOT_TOKEN=<token>
   TELEGRAM_CHAT_ID=<chat-id>
   POSTGRES_PASSWORD=<password-sécurisé>
   ```

5. **Reverse proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name votre-domaine.com;
       
       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 📈 Monitoring

```powershell
# Logs en temps réel
docker-compose logs -f

# Stats ressources
docker stats

# Vérifier la santé des services
docker-compose ps

# Redémarrer un service
docker-compose restart ia-service
```

## 🛑 Arrêt et Nettoyage

```powershell
# Arrêter les services
docker-compose stop

# Redémarrer
docker-compose restart

# Tout arrêter et supprimer les conteneurs
docker-compose down

# Supprimer aussi les volumes (ATTENTION: perte de données)
docker-compose down -v
```

## ✨ Résumé Architecture

**Avant:**
```
app.py → Gemini API → Telegram → Chat Web
        (Lent, Coûteux, En ligne)
```

**Après:**
```
app.py ──→ IA Service (Phi-2 Local) ──→ Telegram
Chat Web ─→ IA Service (Phi-2 Local) ──→ WebSocket
           (Rapide, Gratuit, Hors ligne)
```

## 🎉 Étapes Suivantes

1. ✅ **Services connectés** - app.py, chat-web, ia-service
2. ✅ **Docker prêt** - docker-compose.yml, Dockerfile
3. 📊 **Fine-tuning** (optionnel) - Adapter modèle sur vos données
4. 📚 **RAG** (optionnel) - Ajouter ChromaDB pour knowledge base
5. 🚀 **Production** - Déployer en cloud (AWS, GCP, Azure)

**Status:** ✅ PRÊT POUR LA PRODUCTION
