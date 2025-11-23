# 🌐 Configuration URLs Services - Production Render

## 📋 Vue d'ensemble

Le système est composé de **3 services indépendants** déployés sur Render:

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  1. SERVICE APP (app.py)                                │
│     ├─ Port: 5000                                       │
│     ├─ Endpoints: /webhook/diagnostic-frigo             │
│     ├─ Role: API principale, réception diagnostics      │
│     └─ URL Render: https://frigo-app.onrender.com       │
│                                                           │
│  2. SERVICE CHAT (chat/app_web.py)                       │
│     ├─ Port: 5001                                       │
│     ├─ Endpoints: /chat, /dashboard                     │
│     ├─ Role: Web UI, visualisation temps réel           │
│     └─ URL Render: https://frigo-chat.onrender.com      │
│                                                           │
│  3. SERVICE IA (gpt/app_ia.py)                           │
│     ├─ Port: 5002                                       │
│     ├─ Endpoints: /api/chat/message                     │
│     ├─ Role: Traitement LLM, analyse diagnostics        │
│     └─ URL Render: https://frigo-gpt.onrender.com       │
│                                                           │
│  4. SIMULATEUR (simulateur_production.py)               │
│     └─ Envoie données réalistes vers Service 1          │
│        Auto-détection URLs via env vars                 │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Synchronisation Automatique des URLs

### Méthode 1: Variables d'Environnement (Render)

En déployant sur **Render**, chaque service obtient une URL unique:
```
Service APP:  https://YOUR-APP-NAME.onrender.com
Service CHAT: https://YOUR-CHAT-NAME.onrender.com  
Service IA:   https://YOUR-IA-NAME.onrender.com
```

**Configuration dans Render Dashboard:**

Pour **chaque service**, ajouter les variables d'environnement:

#### Service APP (app.py)
```bash
CHAT_API_URL=https://YOUR-CHAT-NAME.onrender.com
IA_SERVICE_URL=https://YOUR-IA-NAME.onrender.com
ENVIRONMENT=production
```

#### Service CHAT (chat/app_web.py)
```bash
MAIN_APP_URL=https://YOUR-APP-NAME.onrender.com
IA_SERVICE_URL=https://YOUR-IA-NAME.onrender.com
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:5432/db
```

#### Service IA (gpt/app_ia.py)
```bash
MAIN_APP_URL=https://YOUR-APP-NAME.onrender.com
CHAT_API_URL=https://YOUR-CHAT-NAME.onrender.com
ENVIRONMENT=production
IA_MODEL=phi
```

### Méthode 2: Docker Compose (Local Dev)

En local avec Docker Compose, les services découvrent automatiquement leurs URLs via les **noms de service**:

```yaml
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - CHAT_API_URL=http://chat:5001
      - IA_SERVICE_URL=http://gpt:5002
  
  chat:
    build: ./chat
    ports:
      - "5001:5001"
    environment:
      - MAIN_APP_URL=http://app:5000
      - IA_SERVICE_URL=http://gpt:5002
  
  gpt:
    build: ./gpt
    ports:
      - "5002:5002"
    environment:
      - MAIN_APP_URL=http://app:5000
      - CHAT_API_URL=http://chat:5001
```

### Méthode 3: Auto-Détection (Simulateur)

Le nouveau `simulateur_production.py` **détecte automatiquement** les URLs:

```python
# 1. Vérifier les env vars
MAIN_APP_URL = os.environ.get('MAIN_APP_URL', 'http://localhost:5000')

# 2. Tenter résolution noms Docker
socket.gethostbyname('app')  # → http://app:5000

# 3. Fallback localhost
# → http://localhost:5000
```

**Flux de découverte:**
```
┌─────────────────────────┐
│  Env vars définis?      │
│  (MAIN_APP_URL=...)     │
└──────────┬──────────────┘
           │ OUI
           ↓
     ✅ Utiliser env var
           │
           │ NON
           ↓
┌─────────────────────────┐
│  En Docker?             │
│  (test DNS de 'app')    │
└──────────┬──────────────┘
           │ OUI
           ↓
  ✅ Utiliser http://app:5000
           │
           │ NON
           ↓
   ✅ Utiliser localhost:5000
```

## 🚀 Déploiement sur Render

### Étape 1: Créer 3 Web Services

Sur **https://render.com/dashboard**:

**Service 1 - App Principal**
```
Name: frigo-app
Build Command: pip install -r requirements.txt
Start Command: python app.py
Plan: Free ($0/month) ou Starter ($7/month)
Environment:
  - CHAT_API_URL=https://frigo-chat.onrender.com
  - IA_SERVICE_URL=https://frigo-gpt.onrender.com
  - ENVIRONMENT=production
```

**Service 2 - Chat UI**
```
Name: frigo-chat
Build Command: pip install -r chat/requirements.txt
Start Command: cd chat && python app_web.py
Plan: Free ($0/month) ou Starter ($7/month)
Environment:
  - MAIN_APP_URL=https://frigo-app.onrender.com
  - IA_SERVICE_URL=https://frigo-gpt.onrender.com
  - ENVIRONMENT=production
  - DATABASE_URL=postgresql://user:pass@host:5432/chat_app
```

**Service 3 - IA Service**
```
Name: frigo-gpt
Build Command: pip install -r gpt/requirements.txt
Start Command: cd gpt && python app_ia.py
Plan: Starter ($7/month, minimum) ou Pro pour GPU
Environment:
  - MAIN_APP_URL=https://frigo-app.onrender.com
  - CHAT_API_URL=https://frigo-chat.onrender.com
  - ENVIRONMENT=production
  - IA_MODEL=phi  # ou: gpt2, mistral, neural, ollama
```

### Étape 2: Configurer Simulateur

**Option A - Simulateur sur Render (4e Service)**

Créer 4e service pour le simulateur:
```
Name: frigo-simulator
Build Command: pip install -r requirements.txt
Start Command: python simulateur_production.py
Plan: Free ($0/month)
Environment:
  - MAIN_APP_URL=https://frigo-app.onrender.com
```

**Option B - Simulateur sur votre machine**

```powershell
# Configuration locale avec URLs Render
$env:MAIN_APP_URL="https://frigo-app.onrender.com"
$env:CHAT_API_URL="https://frigo-chat.onrender.com"
$env:IA_SERVICE_URL="https://frigo-gpt.onrender.com"

python simulateur_production.py --interval 30 --prob-panne 0.15
```

## 📊 Flux de Communication

### En Local (Docker Compose)
```
Simulateur → http://app:5000/webhook → App (5000)
                  ↓
            http://chat:5001 → Chat (5001)
                  ↓
            http://gpt:5002 → IA (5002)
```

### En Production (Render)
```
Simulateur → https://frigo-app.onrender.com/webhook → App
                  ↓
            https://frigo-chat.onrender.com → Chat
                  ↓
            https://frigo-gpt.onrender.com → IA
```

### Vérification Connectivité

```bash
# Vérifier endpoints
curl https://frigo-app.onrender.com/health
curl https://frigo-chat.onrender.com/health
curl https://frigo-gpt.onrender.com/health

# Vérifier communication inter-services
curl -X POST https://frigo-app.onrender.com/api/check-ia \
  -H "Content-Type: application/json" \
  -d '{"ia_url": "https://frigo-gpt.onrender.com"}'
```

## 🔍 Dépannage URL Mismatch

### Problème: URLs hardcodées en localhost

**Avant** (❌ Non-fonctionnel en production):
```python
# app.py
requests.post('http://localhost:5001/chat')  # ❌ Erreur!
```

**Après** (✅ Fonctionnel):
```python
# app.py
chat_url = os.environ.get('CHAT_API_URL', 'http://localhost:5001')
requests.post(f'{chat_url}/chat')  # ✅ Correct
```

### Problème: Services ne trouvent pas les URLs

**Vérifier:**
1. ✅ Variables d'environnement définies dans Render Dashboard
2. ✅ URLs complètes avec `https://` pour Render
3. ✅ URLs avec `http://` et noms de service pour Docker
4. ✅ Ports corrects (5000, 5001, 5002)
5. ✅ Health check de chaque service

### Problème: Simulateur timeout

```
❌ Timeout - App non réactive
```

**Solutions:**
```bash
# 1. Vérifier que l'app est en ligne
curl -I https://frigo-app.onrender.com

# 2. Vérifier logs Render
# Dashboard → Service → Logs

# 3. Augmenter timeout
python simulateur_production.py --app-url https://frigo-app.onrender.com

# 4. Réduire fréquence
python simulateur_production.py --interval 60  # 1 min entre envois
```

## ✅ Checklist Déploiement

- [ ] Créer 3 Web Services sur Render
- [ ] Copier URLs auto-générées (frigo-app.onrender.com, etc.)
- [ ] Configurer env vars dans chaque service
- [ ] Vérifier health check de chaque service
- [ ] Tester communication inter-services
- [ ] Lancer simulateur avec URLs production
- [ ] Vérifier données arrivent en temps réel dans Chat
- [ ] Vérifier IA traite les diagnostics
- [ ] Monitorer logs pour erreurs

## 📝 Variables d'Environnement Template

Fichier `.env.production`:
```bash
# === SERVICE URLS (SET AFTER RENDER DEPLOYMENT) ===
MAIN_APP_URL=https://frigo-app.onrender.com
CHAT_API_URL=https://frigo-chat.onrender.com
IA_SERVICE_URL=https://frigo-gpt.onrender.com

# === DATABASE ===
DATABASE_URL=postgresql://user:pass@host:5432/chat_app

# === APP SETTINGS ===
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False

# === IA SETTINGS ===
IA_MODEL=phi
HF_LOCAL_MODEL_PATH=/app/models

# === SIMULATION ===
SIMULATOR_INTERVAL=30
SIMULATOR_PANNE_PROB=0.15
```

## 🎯 Synchronisation Automatique: Expliqué

Quand vous déployez sur Render:

1. **Render génère automatiquement** une URL unique pour chaque service
   ```
   frigo-app → https://frigo-app.onrender.com
   frigo-chat → https://frigo-chat.onrender.com
   frigo-gpt → https://frigo-gpt.onrender.com
   ```

2. **Vous configurez les env vars** dans chaque service
   ```
   Service APP: CHAT_API_URL=https://frigo-chat.onrender.com
   Service CHAT: IA_SERVICE_URL=https://frigo-gpt.onrender.com
   ```

3. **Services découvrent les URLs** au démarrage
   ```python
   chat_url = os.environ.get('CHAT_API_URL')  # ✅ Auto-découvert
   ```

4. **Communication établie** automatiquement
   ```
   App → utilise CHAT_API_URL → Chat
   Chat → utilise IA_SERVICE_URL → IA
   IA → utilise MAIN_APP_URL → App
   ```

**Résultat**: Les URLs sont **synchronisées automatiquement** - pas de hardcoding! 🎉

## 📞 Support

En cas de problème:
1. Vérifier logs Render Dashboard
2. Tester URLs avec `curl`
3. Vérifier variables d'environnement
4. Consulter `IA_ARCHITECTURE.md` pour détails
