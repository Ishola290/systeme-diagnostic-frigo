# 📋 PRODUCTION DEPLOYMENT CHECKLIST

## ✅ Phase 1: Préparation Locale

### Vérifications
- [ ] Git repository à jour
- [ ] Tous les services testent localement
- [ ] Simulateur envoie des données
- [ ] Dashboard Chat affiche les données
- [ ] Communication inter-services vérifiée

### Commandes
```powershell
# Test complet
.\launch-all-services.ps1 -Docker
python test_service_communication.py  # ✅ Tous les tests doivent passer

# Simulateur test
python simulateur_production.py --cycles 10 --interval 5
```

---

## ✅ Phase 2: GitHub Préparation

### Fichiers à commiter
```bash
# Nouveaux fichiers
simulateur_production.py              # ✅ Simulateur prod
test_service_communication.py         # ✅ Tests communication
SERVICE_URLS_CONFIG.md                # ✅ Guide URLs
SIMULATOR_GUIDE.md                    # ✅ Guide simulateur
AUTO_SYNC_URLS.md                     # ✅ Explication sync
start-simulator.ps1                   # ✅ Launcher Windows
launch-all-services.ps1               # ✅ Launcher complet
.env.production.example               # ✅ Template env vars
.gitattributes                        # ✅ Git LFS models
```

### Git LFS (pour les modèles)
```bash
# Vérifier que les modèles sont trackés
git lfs track "models/**/*.safetensors"
git lfs track "models/**/*.bin"
git lfs track "models/**/*.json"

# Push les fichiers volumineux
git add .gitattributes
git commit -m "Setup Git LFS for models"
git push
```

### Commit Message
```
[DEPLOYMENT] Production-ready simulator and service synchronization

- Add simulateur_production.py with auto-URL detection
- Add service communication tests
- Add Render deployment configuration
- Auto-sync URLs via environment variables
- Support local (Python/Docker) and production (Render)
```

---

## ✅ Phase 3: Render Dashboard

### Service 1: APP (frigo-app)

**Settings → General**
```
Service Name: frigo-app
Build Command: pip install -r requirements.txt
Start Command: python app.py
Environment: Python 3.11
```

**Settings → Environment**
```bash
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False
CHAT_API_URL=https://frigo-chat.onrender.com
IA_SERVICE_URL=https://frigo-gpt.onrender.com
```

**Health Check**
```
Health Check Path: /health
```

---

### Service 2: CHAT (frigo-chat)

**Settings → General**
```
Service Name: frigo-chat
Build Command: pip install -r chat/requirements.txt
Start Command: cd chat && python app_web.py
Environment: Python 3.11
```

**Settings → Environment**
```bash
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False
MAIN_APP_URL=https://frigo-app.onrender.com
IA_SERVICE_URL=https://frigo-gpt.onrender.com
DATABASE_URL=sqlite:////data/app.db
# Or PostgreSQL if needed:
# DATABASE_URL=postgresql://user:pass@host:5432/db
```

**Health Check**
```
Health Check Path: /health
```

---

### Service 3: IA (frigo-gpt)

**Settings → General**
```
Service Name: frigo-gpt
Build Command: pip install -r gpt/requirements.txt
Start Command: cd gpt && python app_ia.py
Environment: Python 3.11
Plan: At least Starter ($7/month) for model loading
```

**Settings → Environment**
```bash
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False
MAIN_APP_URL=https://frigo-app.onrender.com
CHAT_API_URL=https://frigo-chat.onrender.com
IA_MODEL=phi
HF_LOCAL_MODEL_PATH=/app/models
```

**Health Check**
```
Health Check Path: /health
```

---

### Service 4: SIMULATOR (Optional)

**Settings → General**
```
Service Name: frigo-simulator
Build Command: pip install -r requirements.txt
Start Command: python simulateur_production.py --interval 120 --prob-panne 0.15
Environment: Python 3.11
Plan: Free
```

**Settings → Environment**
```bash
MAIN_APP_URL=https://frigo-app.onrender.com
SIMULATOR_INTERVAL=120
SIMULATOR_PANNE_PROB=0.15
```

---

## ✅ Phase 4: Déploiement

### Ordre d'Activation

1. **Déployer APP d'abord**
   ```
   Service: frigo-app
   Status: Deploying...
   ✅ Quand: Live (online)
   ```

2. **Puis CHAT**
   ```
   Service: frigo-chat
   Status: Deploying...
   ✅ Quand: Live (online)
   ```

3. **Puis IA**
   ```
   Service: frigo-gpt
   Status: Deploying...
   ✅ Quand: Live (online)
   ```

4. **Finalement SIMULATOR** (optionnel)
   ```
   Service: frigo-simulator
   Status: Deploying...
   ✅ Quand: Live (online)
   ```

### Vérification Déploiement

```bash
# Après 2-5 minutes par service

# Test Service APP
curl https://frigo-app.onrender.com/health
# → {"status": "healthy"} ✅

# Test Service CHAT
curl https://frigo-chat.onrender.com/health
# → {"status": "healthy"} ✅

# Test Service IA
curl https://frigo-gpt.onrender.com/health
# → {"status": "healthy"} ✅

# Test Dashboard CHAT
# Ouvrir: https://frigo-chat.onrender.com/dashboard
# ✅ Interface visible
```

---

## ✅ Phase 5: Test Production

### 1. Test Communication Inter-Services

```bash
# Depuis votre machine locale
python test_service_communication.py \
    --app-url https://frigo-app.onrender.com \
    --chat-url https://frigo-chat.onrender.com \
    --ia-url https://frigo-gpt.onrender.com

# Attendu: Tous les tests ✅
```

### 2. Test Simulateur → Production

```powershell
$env:MAIN_APP_URL = "https://frigo-app.onrender.com"

python simulateur_production.py \
    --interval 60 \
    --prob-panne 0.2 \
    --cycles 20

# Attendu: 
# ✅ Diagnostic #1 envoyé
# ✅ Diagnostic #2 envoyé
# ... (20 cycles)
```

### 3. Vérifier Dashboard

```
https://frigo-chat.onrender.com/dashboard
```

**Attendu:**
- [ ] Graphiques en temps réel
- [ ] Derniers diagnostics affichés
- [ ] Alertes pannes visibles
- [ ] Données se mettent à jour

### 4. Vérifier Logs

**Render Dashboard → Service → Logs**

- [ ] APP logs: Diagnostics reçus
- [ ] CHAT logs: Messages envoyés à IA
- [ ] IA logs: Réponses générées

---

## ✅ Phase 6: Monitoring Production

### Métriques à Surveiller

```
Render Dashboard → Service → Metrics

APP:
├─ CPU: Doit être < 50%
├─ Memory: Doit être < 500MB
├─ Network: Doit être < 1MB/s
└─ Uptime: Doit être > 99%

CHAT:
├─ CPU: Doit être < 30%
├─ Memory: Doit être < 300MB
└─ Uptime: Doit être > 99%

IA:
├─ CPU: Peut être 50-80% (LLM utilise ressources)
├─ Memory: Doit être < 2GB
└─ Uptime: Doit être > 95%
```

### Alertes à Configurer

1. **Service Down Alert**
   - Render Dashboard → Alerts
   - Create Alert: "Service offline"

2. **High Memory Alert**
   - Threshold: > 80% de limite
   - Action: Email notification

3. **Deployment Failure**
   - Render notifie automatiquement

---

## ✅ Phase 7: Maintenance Continue

### Daily Tasks
- [ ] Vérifier statut services (Render Dashboard)
- [ ] Consulter logs pour erreurs
- [ ] Vérifier métriques CPU/Memory

### Weekly Tasks
- [ ] Tester communication inter-services
- [ ] Analyser données collectées
- [ ] Vérifier espace disque

### Monthly Tasks
- [ ] Backup base de données
- [ ] Analyser performances
- [ ] Envisager optimisations

---

## 🆘 Troubleshooting Production

### Problème: Service ne démarre pas

```
❌ Status: Failed
Error: Module not found
```

**Solution:**
1. Vérifier requirements.txt complet
2. Vérifier Python version
3. Vérifier Start Command correct
4. Voir Logs pour détails

### Problème: Timeout Communication

```
⏱️  Timeout - App non réactive
```

**Solution:**
1. Vérifier URLs env vars corrects
2. Vérifier tous services sont Online
3. Augmenter timeout dans code
4. Vérifier network latency

### Problème: Données n'arrivent pas

```
❌ Simulateur: Connection refused
```

**Solution:**
1. Vérifier MAIN_APP_URL dans env
2. Vérifier /webhook/diagnostic-frigo existe
3. Vérifier APP service est Online
4. Tester: `curl https://frigo-app.onrender.com/health`

### Problème: IA Service très lent

```
⏱️  IA Response: 45 secondes
```

**Solution:**
1. Vérifier modèle correct (gpt2 au lieu de phi)
2. Réduire tokens générés
3. Vérifier CPU pas à 100%
4. Envisager upgrade à Pro plan (GPU)

---

## 📊 Rollback Procedure

Si quelque chose casse en production:

### Étape 1: Identifier le problème
```
Render Dashboard → Logs → Chercher l'erreur
```

### Étape 2: Arrêter le service
```
Service → Suspend
```

### Étape 3: Fix le code
```bash
# Fixer le bug localement
git fix...
git commit -m "Fix production issue"
git push
```

### Étape 4: Redéployer
```
Service → Resume
ou
Service → Deploy with latest commit
```

### Étape 5: Vérifier
```bash
curl https://frigo-app.onrender.com/health
# Doit revenir à ✅
```

---

## 📋 Post-Deployment Checklist

- [ ] Tous les services Online
- [ ] Communication inter-services OK
- [ ] Dashboard accessible
- [ ] Simulateur envoie données
- [ ] Logs sans erreurs
- [ ] Métriques normales
- [ ] URL URLs stabilisées (synchronisées)
- [ ] Backup stratégie en place
- [ ] Monitoring activé
- [ ] Team informée du lancement

---

## 🎉 Résumé Final

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ✅ Production Ready!                               │
│                                                      │
│  ├─ 3 Services déployés sur Render                  │
│  ├─ URLs auto-synchronisées via env vars            │
│  ├─ Simulateur envoie données temps réel            │
│  ├─ Dashboard affiche analytics                     │
│  ├─ IA traite diagnostics                           │
│  ├─ Communication inter-services établie            │
│  ├─ Monitoring et alertes en place                  │
│  └─ Prêt pour production! 🚀                        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 📞 Questions?

Voir les guides:
- `SERVICE_URLS_CONFIG.md` — Configuration URLs
- `SIMULATOR_GUIDE.md` — Utilisation simulateur
- `AUTO_SYNC_URLS.md` — Synchronisation automatique
- `IA_ARCHITECTURE.md` — Architecture IA
- `DEPLOYMENT_GUIDE.md` — Déploiement détaillé
