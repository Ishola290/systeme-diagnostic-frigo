# 🧠 Stratégies Mémoire pour Render - Alternatives Complètes

## ⚠️ Le Problème

| Service | RAM Requise | Render Gratuit | Render Standard | Render Premium |
|---------|-------------|---|---|---|
| **phi-2 (5GB)** | 8-12 GB | ❌ Crash | ⚠️ Lent | ✅ OK |
| **gpt2 (500MB)** | 2-3 GB | ✅ OK | ✅ OK | ✅ OK |
| **mistral-7B (13GB)** | 16+ GB | ❌ Crash | ❌ Crash | ⚠️ Lent |

**Render Gratuit**: 512MB RAM (trop petit)
**Render Standard**: 1-2GB RAM (insuffisant pour phi)
**Render Premium**: 4GB+ RAM (fonctionne, coûteux)

---

## 🎯 Stratégie 1: Modèle Léger (Recommandé - Gratuit)

### **Remplacer phi-2 par gpt2**

#### Avantages
- ✅ **RAM**: 2-3GB (fonctionne sur instance gratuite)
- ✅ **Speed**: Démarrage <2 sec
- ✅ **Coût**: Gratuit
- ✅ **Stockage**: 500MB (télécharge rapidement)

#### Inconvénients
- ⚠️ **Qualité**: Moins bon que phi-2 (mais convenable pour diag frigo)
- ⚠️ **Performance**: Plus lent en inférence

#### Implémentation

**Fichier: `Dockerfile` (racine)**
```dockerfile
# ❌ Ancien (trop lourd)
RUN python download_models.py --model phi

# ✅ Nouveau (léger)
RUN python download_models.py --model gpt2
```

**Fichier: `gpt/Dockerfile`**
```dockerfile
# ❌ Ancien
RUN python download_models.py --model phi

# ✅ Nouveau
RUN python download_models.py --model gpt2
```

**Fichier: `download_models.py`**
```python
# ✅ Mettre gpt2 par défaut
DEFAULT_MODEL = 'gpt2'  # Au lieu de 'phi'
```

**Fichier: `.env.production` (Render)**
```env
IA_MODEL=gpt2           # Changer de phi
HF_LOCAL_MODEL_PATH=/app/models/gpt2
```

#### Résultat
- **Build time**: 3-5 min (ultra rapide)
- **Image size**: 1-1.5GB (fit dans instance gratuite)
- **RAM usage**: 500MB-1GB (OK)
- **Coût**: 0€/mois

---

## 🚀 Stratégie 2: Modèle Dynamique sur HuggingFace (Recommandé - Scalable)

### **Télécharger le modèle à la demande (pas pré-compilé)**

#### Concept
```
Client → API → "Model not loaded"
              → Download from HuggingFace (~1 min)
              → Cache localement
              → Répondre
```

#### Avantages
- ✅ **Image légère**: 500MB (juste app + deps)
- ✅ **Gratuit**: Aucun frais supplémentaire
- ✅ **Flexible**: Changer de modèle sans redéployer
- ✅ **Scalable**: Marche sur instance petite

#### Inconvénients
- ⚠️ **Premier appel**: 30-60 sec (télécharge modèle)
- ⚠️ **Stockage**: Epuise disque Render après plusieurs requêtes

#### Implémentation

**Fichier: `gpt/ia_service.py` (modifier la fonction d'init)**

```python
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
        return cls._instance
    
    def load_model(self, model_name='gpt2'):
        """Charge le modèle avec caching local"""
        
        # Chemin local (Render a /app et /tmp)
        local_path = f"/app/models/{model_name}"
        
        # Priorité 1: Modèle pré-compilé (s'il existe)
        if os.path.exists(local_path):
            print(f"✅ Chargement depuis cache local: {local_path}")
            self.model = AutoModelForCausalLM.from_pretrained(local_path)
            self.tokenizer = AutoTokenizer.from_pretrained(local_path)
            return
        
        # Priorité 2: Télécharger de HuggingFace
        print(f"📥 Téléchargement de {model_name} depuis HuggingFace...")
        try:
            # Télécharger avec cache dans /tmp (disque Render)
            cache_dir = "/tmp/hf_cache"
            os.makedirs(cache_dir, exist_ok=True)
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )
            print(f"✅ {model_name} chargé depuis HuggingFace")
        except Exception as e:
            print(f"❌ Erreur: {e}")
            # Fallback vers gpt2
            self.load_model('gpt2')
    
    def infer(self, prompt, max_length=100):
        """Inférence avec lazy-loading"""
        if self.model is None:
            self.load_model()
        
        inputs = self.tokenizer.encode(prompt, return_tensors='pt')
        outputs = self.model.generate(inputs, max_length=max_length)
        return self.tokenizer.decode(outputs[0])

# Usage dans app_ia.py
model_manager = ModelManager()

@app.route('/api/infer', methods=['POST'])
def infer():
    data = request.json
    prompt = data.get('prompt', '')
    result = model_manager.infer(prompt)
    return {'result': result}
```

**Dockerfile - Version Légère (Render)**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs /app/cache

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/tmp/hf_cache

EXPOSE 5002

CMD ["python", "app_ia.py"]
```

#### Résultat
- **Build time**: 2-3 min (ultra rapide)
- **Image size**: 500MB
- **Premier appel**: +30-60 sec (télécharge modèle)
- **Appels suivants**: Instantané
- **Coût**: 0€/mois

---

## 💾 Stratégie 3: AWS S3 / Google Cloud Storage (Recommandé - Pro)

### **Modèle hébergé externement, téléchargé à l'init**

#### Concept
```
┌──────────────┐
│  Render      │
│  (app)       │
└──────────────┘
        │
        └──→ S3 / GCS
             (modèle stocké)
             │
             └──→ Télécharge au démarrage
                  (cache local)
```

#### Avantages
- ✅ **Image compacte**: 200MB (sans modèle)
- ✅ **Rapide**: Télécharge au démarrage (~30 sec avec CDN)
- ✅ **Flexible**: Changer de modèle sans redéployer code
- ✅ **Versioning**: Gérer plusieurs versions

#### Inconvénients
- 💰 **Coût**: ~$0.10-1/mois (stockage S3)
- 🔧 **Setup**: Configuration AWS/GCS requise
- 🌐 **Réseau**: Dépend de connexion cloud

#### Implémentation (AWS S3)

**1. Upload modèle sur S3**
```powershell
# Local (ta machine)
aws s3 cp models/phi-2/ s3://frigo-models/phi-2/ --recursive

# Coût: ~$0.10/mois pour 5GB
```

**2. Ajouter boto3 dans requirements.txt**
```
boto3==1.28.85
```

**3. Modifier `gpt/ia_service.py`**
```python
import boto3
from botocore.exceptions import NoCredentialsError

def download_model_from_s3(model_name):
    """Télécharge modèle depuis S3 au démarrage"""
    
    s3 = boto3.client('s3')
    bucket = 'frigo-models'
    local_path = f'/app/models/{model_name}'
    
    try:
        # Télécharger tous les fichiers
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=f'{model_name}/')
        
        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                if key.endswith('/'):
                    os.makedirs(f'/app/{key}', exist_ok=True)
                else:
                    local_file = f'/app/{key}'
                    os.makedirs(os.path.dirname(local_file), exist_ok=True)
                    print(f"📥 Téléchargement: {key}...")
                    s3.download_file(bucket, key, local_file)
        
        print(f"✅ Modèle {model_name} téléchargé depuis S3")
    except NoCredentialsError:
        print("❌ AWS credentials manquantes")
        raise

# Appeler au démarrage app_ia.py
@app.before_first_request
def init_model():
    download_model_from_s3('phi-2')
    model_manager.load_model('phi-2')
```

**4. Variables d'env Render**
```env
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_DEFAULT_REGION=eu-west-1
```

#### Résultat
- **Build time**: 2 min
- **Image size**: 200MB
- **Startup time**: 30-60 sec (télécharge S3)
- **Coût**: 0€ (Render) + ~$0.10/mois (S3)

---

## 🌐 Stratégie 4: API Externe (Recommandé - Basique)

### **Utiliser une API de modèles pré-déployée**

#### Concept
```
Ton app → Appelle API → HuggingFace Inference API
                        ou Replicate
                        ou Together AI
```

#### Avantages
- ✅ **Zéro serveur**: Pas besoin d'héberger modèle
- ✅ **Image minuscule**: 100MB
- ✅ **Gratuit**: Tier gratuit disponible (limité)
- ✅ **Simple**: Juste appels HTTP

#### Inconvénients
- 💰 **Coût**: ~$0.001-0.01 par requête
- 🌐 **Dépendance**: Reliant à service externe
- ⏱️ **Latence**: 2-10 sec par appel (réseau)

#### Implémentation (HuggingFace Inference API)

**1. Obtenir API token**
```
https://huggingface.co/settings/tokens
→ New token (Read) → copier
```

**2. Modifier `gpt/app_ia.py`**
```python
import requests

HF_API_TOKEN = os.getenv('HF_API_TOKEN')
HF_MODEL_ID = 'microsoft/phi-2'
HF_API_URL = f'https://api-inference.huggingface.co/models/{HF_MODEL_ID}'

@app.route('/api/infer', methods=['POST'])
def infer():
    data = request.json
    prompt = data.get('prompt', '')
    
    headers = {'Authorization': f'Bearer {HF_API_TOKEN}'}
    response = requests.post(
        HF_API_URL,
        headers=headers,
        json={'inputs': prompt}
    )
    
    if response.status_code == 200:
        result = response.json()[0]['generated_text']
        return {'result': result}
    else:
        return {'error': response.text}, 500
```

**3. Variables d'env Render**
```env
HF_API_TOKEN=hf_xxxxxxxxxxxxx
```

#### Résultat
- **Build time**: 1-2 min (ultra rapide)
- **Image size**: 100MB
- **Inférence**: 2-10 sec (réseau)
- **Coût**: ~$0.01-1/mois (selon usage)

---

## 📊 Comparaison Complète

| Stratégie | RAM | Disque | Build | Coût | Latence | Qualité |
|-----------|-----|--------|-------|------|---------|---------|
| **1. gpt2 (Léger)** | 512MB ✅ | 500MB | 3min | 0€ | 100ms | Bonne |
| **2. HF Dynamic** | 512MB ✅ | 1GB | 2min | 0€ | 1s (1st), 100ms | Excellente |
| **3. S3 Download** | 512MB ✅ | 2GB | 2min | $0.1 | 100ms | Excellente |
| **4. HF API** | 256MB ✅ | 100MB | 1min | $0.01-1 | 2-10s | Excellente |
| **phi-2 (Pré-compilé)** | 8GB ❌ | 6GB ❌ | 20min | 0€ | 100ms | Excellent |

---

## 🎯 Recommandations par Cas

### **Budget: Zéro, Rapidité: Important**
👉 **Stratégie 2 (HF Dynamic)** 
- Télécharge modèle à la demande
- Premier appel: 30-60 sec
- Appels suivants: rapide

### **Budget: Zéro, Latence: Critique**
👉 **Stratégie 1 (gpt2 Léger)**
- Utilise gpt2 pré-compilé
- Instantané toujours
- Qualité acceptable pour diagnostics frigo

### **Budget: Petit ($10/mois)**
👉 **Stratégie 3 (S3)**
- Modèle sur AWS S3
- Télécharge à l'init (~30 sec)
- Rapide après

### **Budget: Flexible**
👉 **Stratégie 4 (API Externe)**
- Zéro infra
- Pay-as-you-go
- Latence acceptable (2-10s)

---

## 🔧 Implémentation Recommandée (Hybride)

### **Approche Intelligent Fallback**

```python
# gpt/app_ia.py
class SmartModelLoader:
    """Charge modèle avec stratégie intelligente"""
    
    @staticmethod
    def load():
        """Priorités: Local → S3 → HF Dynamic → API → gpt2"""
        
        # Priorité 1: Modèle pré-compilé local
        if os.path.exists('/app/models/phi'):
            return load_local_model('phi')
        
        # Priorité 2: S3 (si credentials disponibles)
        if os.getenv('AWS_ACCESS_KEY_ID'):
            return load_from_s3('phi-2')
        
        # Priorité 3: HuggingFace Dynamic
        if os.getenv('INTERNET_AVAILABLE'):
            return load_from_huggingface('phi-2')
        
        # Priorité 4: API Externe (HF Inference)
        if os.getenv('HF_API_TOKEN'):
            return HuggingFaceAPIClient('phi-2')
        
        # Fallback: gpt2 local (toujours dispo)
        return load_local_model('gpt2')
```

#### Deployment Flow
```
Production (Render):
1. Essaie charger /app/models/phi (stratégie 1 ou 3)
2. Si pas dispo, télécharge de HF (stratégie 2)
3. Si connexion lente, utilise API (stratégie 4)
4. Fallback: gpt2 (stratégie 1)
```

---

## 📋 Checklist Déploiement Render

### **Avant de Pousser sur Render**

- [ ] Choisir stratégie (1-4 ci-dessus)
- [ ] Modifier `Dockerfile` pour stratégie choisie
- [ ] Tester localement: `docker build .`
- [ ] Git push les changes
- [ ] Configurer variables d'env sur Render

### **Pendant le Déploiement**

- [ ] Render commence le build
- [ ] Monitor les logs de compilation
- [ ] Attendre selon timing (3min-20min)
- [ ] Vérifier que service démarre

### **Après le Déploiement**

- [ ] Test: `GET /health`
- [ ] Test: `POST /api/infer` (mesurer temps)
- [ ] Monitor: Render dashboard (RAM/CPU)
- [ ] Optimiser: Réajuster si crashes

---

## 🚨 Si le Déploiement Échoue

### **Erreur: "Out of Memory"**
```
Solution rapide:
1. Basculer à stratégie gpt2 (léger)
2. Redéployer
3. Plus tard: Upgrade instance ou S3
```

### **Erreur: "Disk space full"**
```
Solution:
1. Réduire taille modèle (gpt2 au lieu phi)
2. Utiliser S3 (téléchargement à l'init)
3. Ou: Upgrade instance Render
```

### **Service démarre mais très lent**
```
Problème: Modèle chargé en RAM, pas assez
Solutions:
1. Utiliser quantization (4-bit)
2. Utiliser ONNX format (plus rapide)
3. Réduire modèle (gpt2)
4. Upgrade instance
```

---

## 💡 Résumé Final

**Render a limites RAM** → Besoin stratégie alternative

**4 Options Valides:**
1. ✅ **Modèle léger** (gpt2) - Gratuit, rapide, qualité OK
2. ✅ **Dynamic download** - Gratuit, 1er appel lent, rapide après
3. ✅ **S3 storage** - $0.1/mois, rapide, flexible
4. ✅ **API externe** - Zéro serveur, pay-as-you-go

**Recommandation**: Stratégie 2 (Dynamic) ou 1 (gpt2)
- Zéro coût supplémentaire
- Marche sur instance gratuite Render
- Acceptable pour diagnostics frigo

**Next Step**: Tester localement avant Render! 🚀
