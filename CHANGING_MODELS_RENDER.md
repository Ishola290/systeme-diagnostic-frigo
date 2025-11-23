# 🔄 Changer de Modèle IA sur Render - Guide Complet

## ⚠️ Attention: Distinction Importante

### **La Confusion**
```
❌ FAUX: Juste changer IA_MODEL env var → Modèle change instantanément
✅ VRAI: Dépend du modèle et de la configuration Dockerfile
```

---

## 📊 Comprendre le Fonctionnement

### **Scenario 1: Modèle dans Dockerfile (Pré-compilé)**

```
Dockerfile.production inclut:
  RUN python download_models.py --model phi

Résultat:
  ✅ Image finale: 6.5GB avec phi pré-inclus
  ✅ Démarrage: Immédiat (~2 sec)
  
Si tu changes IA_MODEL env var:
  gpt2 → phi (ou autre)
  ⚠️ NE change rien
  → Modèle reste celui du Dockerfile
```

### **Scenario 2: Modèle Téléchargé à la Demande (Dynamic)**

```
Dockerfile.render-lite:
  Pas de téléchargement dans Dockerfile
  IA_MODEL spécifie le modèle à utiliser

Résultat:
  ✅ Image légère: 500MB
  ⏳ Premier appel: ~30-60 sec (télécharge modèle)
  
Si tu changes IA_MODEL env var:
  gpt2 → gpt2-medium ou distilgpt2
  ✅ Change au redémarrage
  → App télécharge le nouveau modèle (30-60 sec)
  
Si tu changes IA_MODEL:
  gpt2 → phi2 (13GB!)
  ⚠️ Possible mais attente: 2-5 min de téléchargement
  ⚠️ RAM Render peut crash (512MB insuffisant)
```

---

## 🎯 3 Approches (Choisis UNE)

### **Approche 1: Simple - Rester sur gpt2** ⭐ RECOMMANDÉ

**Configuration Actuelle = Approche 1**

```
Dockerfile.render-lite:
  ENV IA_MODEL=gpt2

Comportement:
  ✅ Toujours utilise gpt2
  ✅ Pas de téléchargement extra
  ✅ Rapide et stable
  
Si tu veux changer plus tard:
  Render → frigo-gpt → Environment
  IA_MODEL = distilgpt2 (ou autre léger)
  Redéployer
  
Modèles compatibles (taille similaire):
  • gpt2-medium (650MB)
  • distilgpt2 (350MB)
  • gpt2-large (1.5GB) ⚠️ Possible mais lent
```

**✅ À faire MAINTENANT (rien!)** - C'est déjà configuré

---

### **Approche 2: Flexible - Plusieurs Modèles Légers**

**Permettre switch entre modèles sans redéployer le Dockerfile**

#### **Fichier à modifier: `gpt/Dockerfile.render-lite`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs /app/models /app/cache

# ============================================================
# FLEXIBLE: Supporte plusieurs modèles via env var
# ============================================================
ENV FLASK_APP=app_ia.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# ← CLEF: Pas de IA_MODEL par défaut dans Dockerfile
# La config viendra de Render Environment variables

ENV HF_HOME=/app/models
ENV IA_USE_GPU=false
ENV MAIN_APP_URL=http://app:5000
ENV CHAT_API_URL=http://chat:5001

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

CMD ["python", "app_ia.py"]
```

#### **Modifie aussi `gpt/ia_service.py`**

Ajoute fallback intelligent au début du fichier:

```python
import os

# Déterminer le modèle à utiliser
def get_model_name():
    """
    Priorités de sélection:
    1. IA_MODEL env var (si spécifié)
    2. Auto-sélection selon ressources
    """
    model = os.environ.get('IA_MODEL')
    
    if model:
        return model
    
    # Auto-sélection basée sur mémoire/GPU
    try:
        import psutil
        import torch
        
        total_mem = psutil.virtual_memory().total / (1024**3)  # GB
        has_gpu = torch.cuda.is_available()
        
        if has_gpu:
            return 'mistral-7b'
        elif total_mem >= 8:
            return 'phi-2'
        elif total_mem >= 4:
            return 'gpt2-medium'
        else:
            return 'gpt2'  # Fallback sûr
    except:
        return 'gpt2'  # Fallback ultime

IA_MODEL = get_model_name()
```

#### **Configuration Render pour Approche 2**

```
Service: frigo-gpt

Environment Variables:

IA_MODEL = gpt2                    # À créer MAINTENANT
MAIN_APP_URL = https://frigo-app.onrender.com
CHAT_API_URL = https://frigo-chat.onrender.com
```

**Plus tard, pour changer le modèle:**

```
1. Render Dashboard → frigo-gpt
2. Environment → Modifier IA_MODEL
3. Ancienne valeur: gpt2
   Nouvelle valeur: gpt2-medium (ou distilgpt2)
4. Save
5. Manual Deploy

Résultat:
  ✅ Image rebuild? NON
  ✅ Juste env var change
  ✅ Au redémarrage: télécharge nouveau modèle
```

**Modèles testés et recommandés:**

| Modèle | Size | RAM | Download | Qualité | Speed |
|--------|------|-----|----------|---------|-------|
| gpt2 | 500MB | 2GB | 20sec | Bonne | Rapide |
| distilgpt2 | 350MB | 1GB | 15sec | OK | Très Rapide |
| gpt2-medium | 650MB | 3GB | 30sec | Très bonne | Rapide |
| phi-2 | 5GB | 8GB | 120sec | Excellente | Normal |
| mistral-7b | 13GB | 16GB | 300sec | Excellente | Lent |

---

### **Approche 3: Hardcore - Pré-charger Multiple Modèles**

**Télécharger plusieurs modèles d'avance dans Dockerfile**

```dockerfile
FROM python:3.11-slim as model-downloader

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY download_models.py /tmp/download_models.py

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN mkdir -p /app/models && \
    python /tmp/download_models.py --model gpt2 && \
    python /tmp/download_models.py --model gpt2-medium && \
    echo "✅ Tous les modèles téléchargés"

# Stage 2: Final image
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY --from=model-downloader /app/models /app/models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/logs /app/cache

ENV FLASK_APP=app_ia.py
ENV FLASK_ENV=production
ENV HF_HOME=/app/models
ENV IA_MODEL=gpt2

EXPOSE 5002

CMD ["python", "app_ia.py"]
```

**Résultat:**
- ✅ Build: 10-15 min (télécharge 2 modèles)
- ✅ Image: 2GB
- ✅ Switch instant entre gpt2 et gpt2-medium
- ⚠️ Prend plus d'espace que Approche 1

---

## 📋 Recommandation Par Cas

### **Tu veux lancer en production MAINTENANT?**
👉 **Approche 1 (Simple)** - ✅ Configuré par défaut
```
Utilise gpt2
Aucune config supplémentaire
Prêt à déployer
```

### **Tu veux flexibilité pour changer plus tard?**
👉 **Approche 2 (Flexible)** - ⭐ RECOMMANDÉ
```
Ajoute IA_MODEL env var sur Render
Permet switch entre modèles légers
Build rapide, pas d'image grosse
```

### **Tu veux performance maximale, coût flexible?**
👉 **Approche 3 (Multiple)** - Pro
```
Pré-charge plusieurs modèles
Switch instant
Plus d'espace, plus de temps build
```

---

## 🔧 Configuration Maintenant (Étape par Étape)

### **Choix: Je Vais Avec Approche 1 (Simple)**

```
✅ Rien à faire - c'est déjà configuré!

Fichiers actuels:
  ✅ Dockerfile.render-lite (gpt/)  → ENV IA_MODEL=gpt2
  ✅ app_ia.py → Utilise IA_MODEL env var
  ✅ ia_service.py → Auto-select fallback

Pour déployer:
  1. Git push
  2. Créer frigo-gpt sur Render
  3. Root: gpt/
  4. Build: docker build -f Dockerfile.render-lite .
  5. Env: IA_MODEL = gpt2
```

### **Choix: Je Vais Avec Approche 2 (Flexible)**

À faire MAINTENANT:

**Étape 1: Modifier `gpt/Dockerfile.render-lite`**

Supprimer la ligne:
```dockerfile
ENV IA_MODEL=gpt2
```

(Laisser vide - viendra de Render)

**Étape 2: Ajouter code intelligent à `gpt/ia_service.py`**

Au top du fichier:
```python
import os

def get_model_name():
    model = os.environ.get('IA_MODEL', 'gpt2')  # gpt2 par défaut
    return model
```

**Étape 3: Configuration Render**

Environment variables:
```
IA_MODEL = gpt2  (défaut)
```

Puis tu peux changer plus tard:
```
IA_MODEL = gpt2-medium
IA_MODEL = distilgpt2
```

---

## 🚀 Résumé: Feuille de Route

### **MAINTENANT (avant déploiement)**

- [ ] Décider: Approche 1 (simple) ou 2 (flexible)?
- [ ] Si Approche 2: Modifier `gpt/Dockerfile.render-lite`
- [ ] Si Approche 2: Ajouter code `ia_service.py`
- [ ] Git push
- [ ] Créer services Render (frigo-app, frigo-chat, frigo-gpt)

### **SUR RENDER (configuration)**

- [ ] frigo-gpt → Environment → IA_MODEL = gpt2
- [ ] Autres env vars: MAIN_APP_URL, CHAT_API_URL
- [ ] Deploy

### **PLUS TARD (si changement needed)**

```
Aller Render Dashboard:
  frigo-gpt → Settings → Environment
  
Modifier:
  IA_MODEL = gpt2       → IA_MODEL = gpt2-medium
  
Sauvegarder → Manual Deploy

App redémarre avec nouveau modèle ✅
```

---

## ⚠️ Important: Limites Render

**Si tu changes vers modèle LOURD:**

```
Exemple:
  gpt2 (500MB) → phi-2 (5GB)
  
❌ PROBLÈME:
  Render instance RAM: 512MB
  phi-2 besoin: 8GB minimum
  
RÉSULTAT:
  ✅ Modèle commence télécharger
  ⚠️ App crash OOM pendant téléchargement
  ❌ Service down
  
SOLUTIONS:
  1. Utiliser Dockerfile.production
     (pré-compile phi dans l'image)
  2. Ou: Upgrade instance Render (payant)
  3. Ou: Utiliser S3 storage
```

---

## 💡 Exemple Pratique

### **Tu veux passer de gpt2 → gpt2-medium**

**Sur ta machine (local):**
```powershell
# Test localement d'abord
$env:IA_MODEL = "gpt2-medium"
python gpt/app_ia.py
# Vérifie que ça fonctionne
```

**Sur Render:**
```
1. Dashboard → frigo-gpt
2. Environment → Modifier IA_MODEL
   Avant: gpt2
   Après: gpt2-medium
3. Save
4. Manual Deploy
5. Attendre: 30-60 sec (télécharge modèle)
6. Vérifier logs: "✅ Model loaded"
```

---

## 📞 Troubleshooting

| Problème | Cause | Solution |
|----------|-------|----------|
| **Modèle ne change pas** | Env var pas prise en compte | Redéployer (Manual Deploy) |
| **App crash avec OOM** | Modèle trop lourd | Utiliser modèle plus léger |
| **Téléchargement très lent** | Modèle lourd, bande étroite | Normal, attendre |
| **Service reste en crash loop** | RAM insuffisant | Upgrade Render ou réduire modèle |

---

## ✅ Checklist Finale

- [ ] Décidé: Approche 1, 2 ou 3?
- [ ] Modifié Dockerfile si nécessaire
- [ ] Code intelligent pour auto-select?
- [ ] Modèles compatibles identifiés
- [ ] Prêt à configurer Render
- [ ] Documentation sauvegardée

**Prochaine étape**: Déployer sur Render! 🚀
