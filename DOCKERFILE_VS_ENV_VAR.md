# 🎯 Changer de Modèle: Dockerfile Local vs Env Var Render

## 🔴 La Question Centrale

**"Pour changer de modèle, je fais quoi?"**

```
Option A: Modifier local Dockerfile → Git commit → Render rebuild?
Option B: Juste changer env var dans Render interface?
Option C: Les deux?
```

**Réponse dépend du cas** - Voici les 3 scénarios réels:

---

## 📊 Tableau de Décision

| Cas | Modèle Actuel | Nouveau Modèle | Quoi Faire | Dockerfile? | Env Var? | Git Push? |
|-----|---|---|---|---|---|---|
| **Cas 1** | gpt2 | gpt2-medium | Env var uniquement | ❌ Non | ✅ Oui | ❌ Non |
| **Cas 2** | gpt2 | distilgpt2 | Env var uniquement | ❌ Non | ✅ Oui | ❌ Non |
| **Cas 3** | gpt2 | phi-2 | Dockerfile + env var | ✅ Oui | ✅ Oui | ✅ Oui |
| **Cas 4** | phi-2 | mistral-7b | Dockerfile + env var | ✅ Oui | ✅ Oui | ✅ Oui |

---

## 🎯 Cas 1: Modèle Léger → Modèle Léger (gpt2 → gpt2-medium)

### **Situation**
```
Actuellement en production:
  Dockerfile.render-lite avec IA_MODEL=gpt2 (500MB)

Tu veux:
  Passer à gpt2-medium (650MB)
  
Raison:
  gpt2-medium a meilleure qualité
  Toujours léger (fit dans Render gratuit)
```

### **Solution: JUSTE Env Var (FACILE!)**

**Tu NE fais RIEN localement!**

#### **Étape 1: Sur Render Dashboard**
```
1. Aller: render.com/dashboard
2. Cliquer: frigo-gpt
3. Settings → Environment
4. Chercher: IA_MODEL
5. Modifier:
   Avant: gpt2
   Après: gpt2-medium
6. Cliquer: Save
7. Cliquer: "Manual Deploy"
8. Attendre: ~1-2 min (redémarrage)
9. Premier appel: app télécharge gpt2-medium (~30-60 sec)
10. ✅ Modèle changé!
```

#### **C'est tout!**
```
❌ Pas besoin de modifier Dockerfile
❌ Pas besoin de git commit
❌ Pas besoin de redéployer
✅ Juste env var dans Render interface
```

### **Pourquoi ça marche?**

```
Dockerfile.render-lite configure:
  ENV IA_MODEL=${IA_MODEL}
  (Prend la valeur de la variable d'environnement)

Au démarrage, app_ia.py fait:
  model = os.environ.get('IA_MODEL')  # Lit depuis Render env
  load_model(model)  # gpt2-medium
  
Si IA_MODEL change:
  1. Render redémarre le conteneur
  2. Lit nouvelle valeur: gpt2-medium
  3. App télécharge gpt2-medium
  4. ✅ Fonctionne
```

**Modèles où ça marche:**
- gpt2 ↔ gpt2-medium
- gpt2 ↔ distilgpt2
- gpt2-medium ↔ distilgpt2
- (Modèles de même famille, taille similaire)

---

## 🎯 Cas 2: Modèle Léger → Modèle Lourd (gpt2 → phi-2)

### **Situation**
```
Actuellement:
  gpt2 (500MB, qualité: bonne)

Tu veux:
  phi-2 (5GB, qualité: excellente)
  
Raison:
  Besoin meilleure qualité pour diagnostics
```

### **Solution: Dockerfile Local + Render Deploy (COMPLEXE)**

#### **Scénario A: Utiliser Dockerfile.production**

**Étape 1: En Local - Modifier Dockerfile**

```dockerfile
# Changer le Dockerfile utilisé
Au lieu de:   docker build -f Dockerfile.render-lite .
Utiliser:     docker build -f Dockerfile.production .
```

**Étape 2: Sur Render**

```
1. Render Dashboard → frigo-gpt
2. Settings → Build & Deploy
3. Modifier Build Command:
   Avant: docker build -f Dockerfile.render-lite .
   Après: docker build -f Dockerfile.production .
4. Cliquer: Save
5. Cliquer: "Manual Deploy"
6. Attendre: 15-25 min (Render build & télécharge phi)
7. ✅ Modèle changé à phi!
```

**Pas besoin de git commit!**
- Tu ne modifies PAS le code local
- Tu ne changes que la config Render

#### **Scénario B: Modifier Dockerfile Local (Plus correct)**

**Étape 1: En Local - Modifier `gpt/Dockerfile.render-lite`**

Changer:
```dockerfile
ENV IA_MODEL=gpt2
```

En:
```dockerfile
ENV IA_MODEL=phi-2
```

OU utiliser `Dockerfile.production` à la place

**Étape 2: Git commit + push**

```powershell
git add gpt/Dockerfile.render-lite
git commit -m "Change model from gpt2 to phi-2"
git push origin main
```

**Étape 3: Sur Render - Redéployer**

```
1. Render Dashboard → frigo-gpt
2. Cliquer: "Manual Deploy"
   (Render va chercher le code pushé)
3. Build avec nouveau Dockerfile
4. Attendre: 15-25 min
5. ✅ Service redémarré avec phi-2
```

### **Pourquoi plus complexe?**

```
Dockerfile.render-lite (original):
  IA_MODEL=gpt2
  Image: 500MB
  Startup: 2 sec

Dockerfile.production:
  RUN python download_models.py --model phi
  Image: 6.5GB (pré-compile phi!)
  Build: 20 min
  Startup: 2 sec (phi pré-inclus)
  
Changement de Dockerfile = changement de COMMENT on build

Donc:
  1. Faut changer le Dockerfile
  2. Faut que Render le voit
  3. Render reconstruit l'image (15-25 min)
```

---

## 🎯 Cas 3: Reste Simple - Juste Env Var

### **Le Plus Simple: Approche Pure Env Var**

**Configuration Render:**
```
IA_MODEL = gpt2  (défaut)
HF_LOCAL_MODEL_PATH = /app/models
```

**Modèles disponibles (dynamiquement):**
- gpt2 (500MB)
- distilgpt2 (350MB)
- gpt2-medium (650MB)
- Et d'autres modèles HuggingFace

**Pour changer:**
```
1. Render → Environment
2. IA_MODEL = distilgpt2
3. Manual Deploy
4. Modèle téléchargé automatiquement
5. ✅ Fonctionne!
```

**Dockerfile reste INCHANGÉ**
```dockerfile
ENV IA_MODEL=gpt2  (défaut, si env var pas défini)
```

---

## 📋 Résumé Simple

### **Cas 1: Léger → Léger (gpt2 → gpt2-medium)**
```
Dockerfile:  ❌ NE change pas
Env Var:     ✅ Change: IA_MODEL=gpt2-medium
Git Push:    ❌ NE fait pas
Action:      Just change Render env var + Manual Deploy
Temps:       2-3 min
```

### **Cas 2: Léger → Lourd (gpt2 → phi-2)**
```
Dockerfile:  ✅ Change localement
Env Var:     ✅ Peut changer aussi
Git Push:    ✅ Commit et push le changement
Action:      Modifier Dockerfile local → Push → Render rebuild
Temps:       15-25 min (build Render)

OU

Dockerfile:  ❌ NE change pas fichier
Env Var:     ❌ Mais change le Dockerfile utilisé
Git Push:    ❌ Non
Action:      Render interface → Build Command → docker build -f Dockerfile.production
Temps:       15-25 min
```

---

## 🧠 La Logique Pour Comprendre

### **Comment Render Deploy Fonctionne**

```
┌─────────────────────────────────────────────────┐
│ Render voit: push sur main ou Manual Deploy     │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│ Render utilise la config stockée sur son infra: │
│                                                 │
│ Build Command: docker build -f [DOCKERFILE] .   │
│ Root Directory: ./gpt                           │
│ Start Command: python app_ia.py                 │
│ Environment Vars: IA_MODEL=gpt2                 │
│                  MAIN_APP_URL=...               │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│ Render execute la commande build:               │
│                                                 │
│ docker build -f Dockerfile.render-lite .        │
│ (avec env vars spécifiées)                      │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│ Si Dockerfile local changé (après git push):    │
│ ✅ Render utilise le nouveau Dockerfile         │
│ (parce qu'il clone le repo à jour)              │
│                                                 │
│ Si seulement env var changé sur Render:        │
│ ✅ Dockerfile reste le même                     │
│ ✅ Mais env var change                          │
│ ✅ App lit nouvelle env var au démarrage        │
└─────────────────────────────────────────────────┘
```

### **Donc:**

| Changement | Où? | Effet |
|-----------|-----|-------|
| **Modifier Dockerfile local** | Fichier local `gpt/Dockerfile.render-lite` | Render rebuild avec nouveau Dockerfile |
| **Git push** | GitHub | Render voit le nouveau Dockerfile, le build utilise |
| **Changer env var Render** | Interface Render | Modèle change sans rebuild l'image |

---

## ✅ Exemples Concrets

### **Exemple 1: Je veux gpt2-medium**

```powershell
# Option 1: Env var uniquement (RAPIDE)
1. Render Dashboard
2. frigo-gpt → Environment
3. IA_MODEL = gpt2-medium
4. Manual Deploy
5. ✅ Done! (2 min)

# Option 2: Modifier Dockerfile (Pas nécessaire)
❌ Tu pourrais aussi modifier le Dockerfile local
❌ Mais c'est overkill pour un modèle léger
```

### **Exemple 2: Je veux phi-2**

```powershell
# Option A: Changer Dockerfile localement (CORRECT)
1. Modifier: gpt/Dockerfile.render-lite
   ENV IA_MODEL=phi-2
2. git add gpt/Dockerfile.render-lite
3. git commit -m "Change to phi-2"
4. git push origin main
5. Render Dashboard → Manual Deploy
6. Attendre 20 min build
7. ✅ Done!

# Option B: Changer Render Build Command (AUSSI OK)
1. Render Dashboard
2. frigo-gpt → Settings
3. Build Command: docker build -f Dockerfile.production .
4. Manual Deploy
5. Attendre 20 min build
6. ✅ Done!

# Option C: Juste env var (❌ NON, va crash OOM)
❌ IA_MODEL=phi-2
❌ Pas assez de RAM (512MB vs 8GB nécessaire)
❌ Modèle commence télécharger, crash
```

---

## 🎯 Règles Simples

### **Règle 1: Modèle Léger → Modèle Léger**
```
✅ Juste env var sur Render
❌ Pas toucher Dockerfile
❌ Pas git push
Temps: 2-3 min
```

### **Règle 2: Modèle Lourd (Pré-compilé)**
```
✅ Modifier Dockerfile local
✅ Git push
✅ Render build avec nouveau Dockerfile
Temps: 15-25 min
```

### **Règle 3: Modèle Lourd (Dynamic Download)**
```
❌ DON'T: Juste env var (va crash OOM)
✅ FAUT: Pré-compiler dans Dockerfile
✅ OU: Utiliser instance Render plus grosse
```

---

## 🚀 Recommandation Pour Toi (MAINTENANT)

### **Deploy Initial:**

```
1. Déployer sur Render avec:
   Dockerfile: Dockerfile.render-lite
   IA_MODEL: gpt2
   
2. Ça fonctionne, production prête ✅

3. Plus tard, si tu veux changer:
   
   Si LEGERmodèle:
     → Juste Render env var
     → 2 min
   
   Si LOURD modèle:
     → Modifier Dockerfile local
     → Git push
     → Render build
     → 20 min
```

---

## 🎓 Résumé Final

**Ta question: "Dockerfile local vs Env Var Render?"**

**Réponse:** Les DEUX, mais c'est différent:

1. **Dockerfile Local**
   - Définit COMMENT on build l'image
   - Change le comportement de base
   - Requiert git push et rebuild Render
   - Pour changements structuraux

2. **Env Var Render**
   - Configure le comportement RUNTIME
   - App les lit au démarrage
   - Pas de rebuild image
   - Pour changements dynamiques

3. **Pour changer modèle:**
   - Modèles légers: Env var suffisant ✅
   - Modèles lourds: Dockerfile local + git push ✅

**Prochaine fois tu sais: C'est quoi le cas d'usage?**
- Léger: Env var seulement
- Lourd: Dockerfile + git push

---

## ✅ Checklist Compréhension

- [ ] Comprendre différence Dockerfile vs Env Var?
- [ ] Cas léger (gpt2 → gpt2-medium) = env var?
- [ ] Cas lourd (gpt2 → phi-2) = Dockerfile + git?
- [ ] Render rebuilt quand Dockerfile change?
- [ ] Modèles légers téléchargent dynamiquement?
- [ ] Prêt à déployer?

Tu as des questions? Demande des clarifications! 🎯
