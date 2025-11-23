# 🚀 Guide Rapide: Créer 3 Services Render en 15 min

## 📋 Vue d'ensemble

Tu vas créer 3 Web Services Render qui utilisent chacun UN Dockerfile spécifique.

```
Service 1: frigo-app      → Utilise: Dockerfile.render-lite (racine)
Service 2: frigo-chat     → Utilise: chat/Dockerfile
Service 3: frigo-gpt      → Utilise: gpt/Dockerfile.render-lite
```

---

## ✅ Avant de Commencer

**Conditions Préalables:**
- [ ] Compte Render.com créé (gratuit)
- [ ] GitHub connecté à Render
- [ ] Code pushé sur `main` branch
- [ ] Dockerfiles créés (render-lite, etc)

---

## 🎯 Service 1: frigo-app

### **Étape 1: Aller sur Render**
```
1. Ouvre: https://render.com/dashboard
2. Cliquer: "New" → "Web Service"
```

### **Étape 2: Connecter GitHub**
```
3. Sélectionner: systeme-diagnostic-frigo
4. Cliquer: "Connect"
```

### **Étape 3: Configuration**

```
Name:                    frigo-app
Runtime:                 Docker
Region:                  Frankfurt (ou proche de toi)
Branch:                  main
Root Directory:          ./
Build Command:           docker build -f Dockerfile.render-lite .
Start Command:           python app.py
```

### **Étape 4: Variables d'Environnement**

Scroller jusqu'à "Environment"

```
CHAT_API_URL             https://frigo-chat.onrender.com
IA_SERVICE_URL           https://frigo-gpt.onrender.com
FLASK_ENV                production
PYTHONUNBUFFERED         1
```

### **Étape 5: Créer le Service**

```
Cliquer: "Create Web Service"

Attendre:
  ⏳ Building... (5-10 min)
  ✅ Service is live!

URL: https://frigo-app.onrender.com
```

---

## 🎯 Service 2: frigo-chat

### **Étape 1: Nouveau Service**
```
Render Dashboard → "New" → "Web Service"
```

### **Étape 2: Connecter GitHub**
```
Sélectionner: systeme-diagnostic-frigo
```

### **Étape 3: Configuration**

**IMPORTANT: Root Directory = chat/**

```
Name:                    frigo-chat
Runtime:                 Docker
Region:                  Frankfurt
Branch:                  main
Root Directory:          chat/           ← CRUCIAL!
Build Command:           docker build -f Dockerfile .
Start Command:           python app_web.py
```

### **Étape 4: Variables d'Environnement**

```
MAIN_APP_URL             https://frigo-app.onrender.com
FLASK_ENV                production
PYTHONUNBUFFERED         1
DATABASE_URL             (optionnel pour PostgreSQL)
```

### **Étape 5: Créer le Service**

```
Cliquer: "Create Web Service"

Attendre:
  ⏳ Building... (3-5 min)
  ✅ Service is live!

URL: https://frigo-chat.onrender.com
```

---

## 🎯 Service 3: frigo-gpt

### **Étape 1: Nouveau Service**
```
Render Dashboard → "New" → "Web Service"
```

### **Étape 2: Connecter GitHub**
```
Sélectionner: systeme-diagnostic-frigo
```

### **Étape 3: Configuration**

**IMPORTANT: Root Directory = gpt/**

```
Name:                    frigo-gpt
Runtime:                 Docker
Region:                  Frankfurt
Branch:                  main
Root Directory:          gpt/            ← CRUCIAL!
Build Command:           docker build -f Dockerfile.render-lite .
Start Command:           python app_ia.py
```

### **Étape 4: Variables d'Environnement**

```
MAIN_APP_URL             https://frigo-app.onrender.com
CHAT_API_URL             https://frigo-chat.onrender.com
FLASK_ENV                production
PYTHONUNBUFFERED         1
IA_MODEL                 gpt2
```

### **Étape 5: Créer le Service**

```
Cliquer: "Create Web Service"

Attendre:
  ⏳ Building... (5-10 min)
  ✅ Service is live!

URL: https://frigo-gpt.onrender.com
```

---

## 🧪 Tester Après le Déploiement

### **Test 1: Health Checks**

```powershell
# Test frigo-app
Invoke-WebRequest https://frigo-app.onrender.com/health

# Test frigo-chat
Invoke-WebRequest https://frigo-chat.onrender.com/health

# Test frigo-gpt
Invoke-WebRequest https://frigo-gpt.onrender.com/health

Résultat attendu: HTTP 200 OK
```

### **Test 2: URLs Auto-Sync**

```powershell
# Test que app connaît chat
Invoke-WebRequest https://frigo-app.onrender.com/api/check-services

# Résultat esperé:
# {
#   "chat": "https://frigo-chat.onrender.com",
#   "gpt": "https://frigo-gpt.onrender.com",
#   "status": "✅ All connected"
# }
```

### **Test 3: API Principal**

```powershell
$body = @{
    symptoms = "temperature"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://frigo-app.onrender.com/api/diagnose" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

### **Test 4: Premier Appel IA (Lent)**

```powershell
# Premier appel: télécharge modèle (~30-60s)
Measure-Command {
  Invoke-WebRequest `
    -Uri "https://frigo-gpt.onrender.com/api/infer" `
    -Method POST `
    -Body '{"prompt":"Test"}' `
    -ContentType "application/json"
}

# Résultat: ~30-60 secondes (normal!)
```

### **Test 5: Deuxième Appel IA (Rapide)**

```powershell
# Deuxième appel: modèle en cache (~500ms)
Measure-Command {
  Invoke-WebRequest `
    -Uri "https://frigo-gpt.onrender.com/api/infer" `
    -Method POST `
    -Body '{"prompt":"Test2"}' `
    -ContentType "application/json"
}

# Résultat: ~500ms (rapide ✅)
```

---

## 🔍 Monitoring Render

### **Voir les Logs**

```
Render Dashboard → Select Service → Logs

Regarde:
  ✅ "Server running on..."
  ⚠️ Any errors?
  📊 Memory/CPU usage
```

### **Si Crash OOM**

```
Logs show: "Killed" ou OutOfMemory

Actions:
  1. Stop service: Settings → Delete & Recreate
  2. Utiliser: Dockerfile au lieu de render-lite
  3. Ou: Upgrade instance type (Standard → Premium)
```

### **Si Build Timeout**

```
Logs show: "Build cancelled after 45 minutes"

Actions:
  1. Réduire modèle (gpt2 au lieu phi)
  2. Ou: Utiliser render-lite (plus rapide)
  3. Ou: Upgrade instance
```

---

## 📊 Timeline Attendu

```
Total Time: ~30-40 minutes

Service 1 (frigo-app):
  Build: 5-10 min
  Deploy: 1 min
  Total: 6-11 min

Service 2 (frigo-chat):
  Build: 3-5 min
  Deploy: 1 min
  Total: 4-6 min

Service 3 (frigo-gpt):
  Build: 5-10 min (premier appel télécharge modèle)
  Deploy: 1 min
  Total: 6-11 min

Total: 16-28 min ✅
```

---

## 🚨 Troubleshooting Rapide

| Problème | Cause | Solution |
|----------|-------|----------|
| **Build échoue** | Dockerfile pas trouvé | Vérifier chemin fichier (Build Command) |
| **Service crash** | OOM | Réduire modèle ou upgrade instance |
| **502 Bad Gateway** | App crash | Vérifier logs Render |
| **Health check échoue** | Port mauvais | Vérifier EXPOSE dans Dockerfile |
| **URLs pas synchro** | Env vars manquantes | Vérifier MAIN_APP_URL, CHAT_API_URL |
| **Premier appel lent** | Normal | Télécharge modèle (~30-60s) OK |

---

## ✅ Checklist Finale

Service 1: frigo-app
- [ ] Créé sur Render
- [ ] Build Command: `docker build -f Dockerfile.render-lite .`
- [ ] Env vars configurées
- [ ] ✅ Health check OK
- [ ] ✅ En ligne

Service 2: frigo-chat
- [ ] Créé sur Render
- [ ] Root Directory: `chat/`
- [ ] Build Command: `docker build -f Dockerfile .`
- [ ] Env vars configurées
- [ ] ✅ Health check OK
- [ ] ✅ En ligne

Service 3: frigo-gpt
- [ ] Créé sur Render
- [ ] Root Directory: `gpt/`
- [ ] Build Command: `docker build -f Dockerfile.render-lite .`
- [ ] Env vars configurées
- [ ] ✅ Health check OK
- [ ] ✅ En ligne

Global:
- [ ] Tous les services communiquent
- [ ] URLs auto-sync OK
- [ ] Pas de crash/error logs
- [ ] 🚀 Production prête!

---

## 🎓 Résumé Clés

**Comment Render sait quel Dockerfile?**
→ Tu le dis dans "Build Command" lors de la création

**Exemple:**
```
Build Command: docker build -f Dockerfile.render-lite .
              → Render utilise Dockerfile.render-lite
              
Build Command: docker build -f Dockerfile .
              → Render utilise chat/Dockerfile (avec Root: chat/)
```

**Chaque service indépendant:**
- frigo-app: Configuration A + Dockerfile.render-lite
- frigo-chat: Configuration B + chat/Dockerfile
- frigo-gpt: Configuration C + gpt/Dockerfile.render-lite

---

## 🚀 Allons-y!

Prêt? Crée les 3 services sur Render maintenant! 🎯

Questions? Reviens à `RENDER_DOCKERFILE_SELECTION.md` pour détails complets.
