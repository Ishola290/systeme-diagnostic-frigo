# 🎯 Décision Rapide: Quelle Dockerfile Utiliser?

## 📊 Les 3 Options

### **Dockerfile** (Original - Pré-compilé avec phi)
```
Utiliser si:
  ✅ Render Premium instance (4GB+ RAM)
  ✅ Budget flexible
  ✅ Qualité maximale importante
  ✅ Latence critique (50ms)

Résultat:
  ⏱️ Build: 20-30 min (phi-2 downloaded & compiled)
  💾 Image: 6.5GB
  💰 Coût: ~$10-25/mois (Premium instance)
  ⚡ Performance: Excellente
```

### **Dockerfile.render-lite** ⭐ RECOMMANDÉ RENDER
```
Utiliser si:
  ✅ Render gratuit/standard (512MB-1GB RAM)
  ✅ Budget zéro
  ✅ OK avec ~30-60sec 1er appel
  ✅ Préfères flexibilité

Résultat:
  ⏱️ Build: 2-3 min
  💾 Image: 500MB
  💰 Coût: Gratuit
  ⚡ Performance: Acceptable
  
Fonctionnement:
  1. Service démarre rapide
  2. Utilisateur fait 1er appel API
  3. Télécharge modèle de HuggingFace (~30-60s)
  4. Appels suivants: rapide
```

### **Dockerfile.production** (Intermédiaire)
```
Utiliser si:
  ✅ Instance Standard Render (2GB RAM)
  ✅ Optimisation performance/coût
  ✅ Modèles pré-téléchargés OK

Résultat:
  ⏱️ Build: 15-25 min
  💾 Image: 3-4GB
  💰 Coût: ~$5-10/mois
  ⚡ Performance: Bonne
```

---

## 🚀 Procédure Déploiement Render

### **Étape 1: Créer Service**
```
Render Dashboard:
  → New → Web Service
  → Connect GitHub
  → Select: systeme-diagnostic-frigo
```

### **Étape 2: Configuration**

```
Name: frigo-app
Region: Frankfurt
Runtime: Docker

Build Command:
  # Choisir UNE ligne selon stratégie:
  
  # Option 1 (Recommended): Render-lite
  docker build -f Dockerfile.render-lite .
  
  # Option 2: Production classique
  docker build -f Dockerfile.production .
  
  # Option 3: Original
  docker build -f Dockerfile .

Start Command: python app.py
```

### **Étape 3: Environment Variables**
```
CHAT_API_URL=https://frigo-chat.onrender.com
IA_SERVICE_URL=https://frigo-gpt.onrender.com
FLASK_ENV=production

# Si utilise Stratégie S3:
# AWS_ACCESS_KEY_ID=xxxxx
# AWS_SECRET_ACCESS_KEY=xxxxx
```

### **Étape 4: Deploy**
```
Click "Create Web Service"
→ Render commence le build
→ Monitor logs en temps réel
→ Attendre: 3min (lite) ou 20min (production)
→ ✅ Service en ligne!
```

---

## 🧪 Test Localement Avant Render

### **Tester Dockerfile.render-lite**
```powershell
# Construire image localement
docker build -f Dockerfile.render-lite -t frigo-app-lite .

# Lancer conteneur
docker run -p 5000:5000 frigo-app-lite

# Tester health
Invoke-WebRequest http://localhost:5000/health

# Premier appel API (télécharge modèle)
$response = Invoke-WebRequest -Uri "http://localhost:5000/api/diagnose" `
  -Method POST `
  -Body '{"symptoms": "temperature"}'
  
# Observe:
# - Premier appel: ~30-60 sec
# - Deuxième appel: ~500ms
```

### **Tester Dockerfile (Original)**
```powershell
docker build -f Dockerfile -t frigo-app-prod .

# ⚠️ Attendre 20-30 min (phi-2 download)
# ✅ Image finale: 6.5GB
```

---

## ⚠️ Résolution d'Erreurs Render

### **Erreur: "Out of Memory (OOM)"**
```
Log: "Killed" ou "127"

Cause: Instance n'a pas assez de RAM

Solution:
1. Utiliser Dockerfile.render-lite (au lieu de Dockerfile)
   → Redéployer
   
2. Ou: Upgrade instance
   → Render: Standard → Premium
   → Coût: ~$7/mois → $25/mois
```

### **Erreur: "Build timeout (> 45 min)"**
```
Log: "Build cancelled after 45 minutes"

Cause: Download phi-2 trop lent

Solution:
1. Utiliser Dockerfile.render-lite
   → Télécharge modèle à la demande
   → Build: 2-3 min
   
2. Ou: Réduire modèle dans Dockerfile.production
   → phi → gpt2 ou mistral-7b
```

### **Service démarre mais retourne 502 Bad Gateway**
```
Cause: Crash en mémoire pendant inférence

Solution:
1. Vérifier logs Render
2. Si "CUDA out of memory": Utiliser gpt2 (léger)
3. Si "Python OOM": Utiliser Dockerfile.render-lite
4. Redéployer
```

---

## 📋 Stratégie Recommandée (Étapes)

### **Phase 1: Test Local (Gratuit)**
```
1. Tester Dockerfile.render-lite localement
   docker build -f Dockerfile.render-lite .
   
2. Vérifier que app démarre rapidement
   → Build: 2-3 min
   → Startup: 5-10 sec
   
3. Appeler API et vérifier 1er appel
   POST /api/diagnose
   → Attendre modèle: 30-60 sec OK
   → Résultat correct
```

### **Phase 2: Déployer sur Render (Gratuit)**
```
1. Push à GitHub
   git push origin main
   
2. Créer 3 Web Services sur Render:
   - frigo-app (Dockerfile.render-lite)
   - frigo-chat (chat/Dockerfile)
   - frigo-gpt (gpt/Dockerfile.render-lite)
   
3. Build command: docker build -f Dockerfile.render-lite .

4. Monitor:
   - Build time: ~3 min (rapide ✅)
   - Deploy: ~1 min
   - Total: ~4-5 min
```

### **Phase 3: Test en Production**
```
1. Tester health:
   GET https://frigo-app.onrender.com/health
   
2. Tester 1er appel (télécharge modèle):
   POST https://frigo-app.onrender.com/api/diagnose
   → Attendre: 30-60 sec (modèle HF)
   → Résultat OK
   
3. Tester 2e appel:
   → Immédiat (~500ms)
   
4. Vérifier URL auto-sync:
   → app → chat ✅
   → app → gpt ✅
```

### **Phase 4: Optimiser (Optionnel)**
```
Si performance insatisfaisante:
  1. Upgrade Render instance (+$7/mois)
  2. Ou: Utiliser S3 pour modèles (+$0.1/mois)
  3. Ou: Utiliser API HF Inference (+$1/mois)
```

---

## 📌 Fichiers à Pousser sur GitHub

```
Required:
✅ Dockerfile.render-lite      (Recommended for Render)
✅ gpt/Dockerfile.render-lite  (Recommended for Render)
✅ Dockerfile                  (Original - backup)
✅ gpt/Dockerfile              (Original - backup)
✅ Dockerfile.production       (Alternative - premium)
✅ gpt/Dockerfile.production   (Alternative - premium)

Documentation:
✅ RENDER_MEMORY_STRATEGIES.md (ce fichier)
✅ AUTO_DEPLOY_PROCESS.md
✅ SERVICE_URLS_CONFIG.md
```

---

## 🎯 Sommaire Décision

| Question | Réponse | Action |
|----------|---------|--------|
| **Budget?** | Zéro | Utiliser `Dockerfile.render-lite` ✅ |
| **Latence** | Important | Utiliser `Dockerfile.production` ou upgrade |
| **RAM Render?** | <1GB | Render-lite obligatoire |
| **RAM Render?** | >2GB | Peut utiliser production |
| **Premier appel lent** | OK | Render-lite (30-60s OK) |
| **Premier appel** | Inacceptable | Production ou API |

---

## 📞 Support

**Si Render build échoue:**
1. Vérifier logs (Render Dashboard)
2. Changer Dockerfile (lite si OOM)
3. Redéployer
4. Attendre: Render retry auto après crash

**Si service très lent:**
1. Vérifier RAM Render (Metrics tab)
2. Upgrade si <256MB libres
3. Ou: Réduire modèle

**Si API retourne erreur:**
1. Vérifier logs Render
2. Vérifier URL auto-sync (env vars)
3. Test health: `GET /health`

---

## ✅ Checklist Finale

- [ ] Dockerfiles validés localement
- [ ] `.render-lite` testés et OK
- [ ] Git push complété
- [ ] 3 Web Services créés sur Render
- [ ] Build commands utilisent `.render-lite`
- [ ] Env vars configurés sur Render
- [ ] Health checks passent
- [ ] 1er appel API réussit
- [ ] URLs auto-sync vérifié

**Prêt?** 🚀 Créer les Web Services sur Render!
