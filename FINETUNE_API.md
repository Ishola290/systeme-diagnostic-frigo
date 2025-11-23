# 🔬 Fine-Tuning API - Réentraînement Production

## 📍 Vue d'ensemble

Vous pouvez maintenant **réentraîner les modèles IA à la demande** directement depuis l'API!

```
Service: gpt/app_ia.py
Port: 5002
Endpoint: POST /api/finetune/start
Description: Lance le fine-tuning asynchrone avec vos données
Réponse: Immédiate (202 Accepted)
```

---

## 🎯 Utilité

Le fine-tuning permet d'adapter les modèles IA à **votre domaine spécifique** (frigorifique):

```
Avant (Modèle Généraliste):
  Q: "Frigo fait bruit fort"
  A: "C'est normal, tous les frigos font du bruit"
  ❌ Réponse générale, pas adapté

Après (Fine-tuning Frigo):
  Q: "Frigo fait bruit fort"  
  A: "Vérifiez le compresseur, le ventilateur, 
      et l'accumulation de givre"
  ✅ Réponse spécialisée pour frigorifique!
```

---

## 🚀 Utilisation

### 1️⃣ Obtenir les Infos (Découvrez les Options)

```bash
curl http://localhost:5002/api/finetune/info

# Réponse:
{
  "available": true,
  "supported_models": ["phi", "phi2", "mistral", "neural"],
  "supported_formats": ["csv", "jsonl"],
  "endpoints": {...}
}
```

### 2️⃣ Lancer le Fine-Tuning (Simple)

```bash
curl -X POST http://localhost:5002/api/finetune/start \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi",
    "dataset_url": "data/frigo_training.csv"
  }'

# Réponse: 202 Accepted
{
  "status": "started",
  "job_id": "ft_20240115_103045_abc123",
  "message": "Fine-tuning lancé pour phi",
  "config": {
    "model": "phi",
    "dataset": "data/frigo_training.csv",
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": 2e-5
  }
}
```

### 3️⃣ Lancer Fine-Tuning (Personnalisé)

```bash
# Configuration complète
curl -X POST http://localhost:5002/api/finetune/start \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "dataset_url": "https://example.com/frigo_data.jsonl",
    "epochs": 5,
    "batch_size": 2,
    "learning_rate": 1e-5
  }'

# Réponse:
{
  "job_id": "ft_20240115_103045_xyz789",
  "status": "started",
  "message": "Fine-tuning lancé"
}
```

### 4️⃣ Vérifier le Statut

```bash
curl http://localhost:5002/api/finetune/status/ft_20240115_103045_abc123

# Réponse:
{
  "job_id": "ft_20240115_103045_abc123",
  "status": "completed",
  "progress": 1.0,
  "model_path": "models/phi-finetuned-20240115_103045/"
}
```

### 5️⃣ Lister les Modèles Fine-Tunés

```bash
curl http://localhost:5002/api/finetune/models

# Réponse:
{
  "models": [
    {
      "name": "phi-finetuned-20240115_103045",
      "base_model": "phi",
      "created": "2024-01-15T10:30:45",
      "size_mb": 2540,
      "latest": true,
      "path": "models/phi-finetuned-20240115_103045"
    },
    {
      "name": "mistral-finetuned-20240114_150000",
      "base_model": "mistral",
      "created": "2024-01-14T15:00:00",
      "size_mb": 6500,
      "path": "models/mistral-finetuned-20240114_150000"
    }
  ],
  "total": 2
}
```

---

## 📋 Paramètres

| Paramètre | Type | Défaut | Plage | Description |
|-----------|------|--------|-------|-------------|
| `model` | string | - | phi, mistral, neural, gpt2 | Modèle à réentraîner |
| `dataset_url` | string | - | - | Chemin/URL du dataset |
| `epochs` | int | 3 | 1-20 | Nombre de passes sur les données |
| `batch_size` | int | 4 | 1-16 | Taille des batches |
| `learning_rate` | float | 2e-5 | - | Taux d'apprentissage |

---

## 📊 Format des Données

### Format CSV

```csv
text
"Frigo très froid, compresseur fait bruit"
"Fuite d'eau sous le frigo"
"Thermostat défaillant, température inconstante"
...
```

**Fichier:** `data/frigo_training.csv`

```bash
# Créer et charger
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "phi",
    "dataset_url": "data/frigo_training.csv"
  }'
```

### Format JSONL

```jsonl
{"text": "Frigo très froid, compresseur fait bruit"}
{"text": "Fuite d'eau sous le frigo"}
{"text": "Thermostat défaillant, température inconstante"}
```

**Fichier:** `data/frigo_training.jsonl`

```bash
# Charger depuis JSONL
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "mistral",
    "dataset_url": "data/frigo_training.jsonl"
  }'
```

---

## 💻 Exemples de Code

### Python

```python
import requests
import json

# 1. Info
response = requests.get('http://localhost:5002/api/finetune/info')
print(response.json())

# 2. Lancer fine-tuning
response = requests.post(
    'http://localhost:5002/api/finetune/start',
    json={
        'model': 'phi',
        'dataset_url': 'data/frigo_training.csv',
        'epochs': 3,
        'batch_size': 4
    }
)
job_id = response.json()['job_id']
print(f"Fine-tuning lancé: {job_id}")

# 3. Vérifier statut
response = requests.get(f'http://localhost:5002/api/finetune/status/{job_id}')
status = response.json()
print(f"Status: {status['status']}, Progress: {status['progress']*100}%")

# 4. Lister modèles
response = requests.get('http://localhost:5002/api/finetune/models')
models = response.json()['models']
for model in models:
    print(f"- {model['name']} ({model['size_mb']}MB)")
```

### JavaScript/Fetch

```javascript
// 1. Lancer fine-tuning
fetch('http://localhost:5002/api/finetune/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'phi',
    dataset_url: 'data/frigo_training.csv',
    epochs: 3
  })
})
.then(r => r.json())
.then(data => {
  console.log('Job ID:', data.job_id);
  
  // 2. Vérifier statut
  setInterval(() => {
    fetch(`http://localhost:5002/api/finetune/status/${data.job_id}`)
      .then(r => r.json())
      .then(status => console.log('Status:', status.status))
  }, 5000)
})

// 3. Lister modèles
fetch('http://localhost:5002/api/finetune/models')
  .then(r => r.json())
  .then(data => console.log('Modèles:', data.models))
```

### PowerShell

```powershell
# 1. Lancer fine-tuning
$body = @{
    model = "phi"
    dataset_url = "data/frigo_training.csv"
    epochs = 3
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5002/api/finetune/start" `
  -Method POST `
  -Headers @{'Content-Type' = 'application/json'} `
  -Body $body

$jobId = ($response.Content | ConvertFrom-Json).job_id
Write-Host "Job ID: $jobId"

# 2. Vérifier statut
$status = Invoke-WebRequest -Uri "http://localhost:5002/api/finetune/status/$jobId"
$status.Content | ConvertFrom-Json | Select-Object status, progress
```

---

## 🌐 Production (Render)

Une fois déployé, vous pouvez réentraîner en production:

```bash
# Depuis votre machine
curl -X POST https://frigo-gpt.onrender.com/api/finetune/start \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi",
    "dataset_url": "https://example.com/frigo_data.csv",
    "epochs": 5,
    "batch_size": 2
  }'

# Job ID retourné
# Fine-tuning lance en background sur Render
# Logs disponibles: Render Dashboard → Logs
```

---

## 📈 Cas d'Usage

### 1. Test Fine-Tuning Local

```bash
# Petite donnée de test (10 exemples)
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "gpt2",
    "dataset_url": "data/test_frigo.csv",
    "epochs": 1,
    "batch_size": 1
  }'

# Durée: ~2 minutes
# Valider que le processus fonctionne
```

### 2. Fine-Tuning Complet

```bash
# Dataset complet (1000+ exemples)
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "phi",
    "dataset_url": "data/frigo_complet.csv",
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": 2e-5
  }'

# Durée: ~30-60 minutes (dépend GPU)
# Modèle hautement spécialisé après
```

### 3. Production - Réentraînement Mensuel

```bash
# En production: réentraîner avec données du mois
curl -X POST https://frigo-gpt.onrender.com/api/finetune/start \
  -d '{
    "model": "phi",
    "dataset_url": "https://s3.amazonaws.com/data/frigo_nov2024.csv",
    "epochs": 5
  }'

# S'exécute en background
# Nouveau modèle prêt après ~1 heure
# Logs en temps réel disponibles
```

### 4. Comparaison Modèles

```bash
# Fine-tuner plusieurs modèles
models = ["gpt2", "phi", "mistral"]

for model in models:
    curl -X POST http://localhost:5002/api/finetune/start \
      -d "{\"model\": \"$model\", \"dataset_url\": \"data/test.csv\"}"

# Comparer les modèles fine-tunés
# Sélectionner le meilleur pour production
```

---

## ✅ Workflow Recommandé

### Phase 1: Préparer les Données

```bash
# 1. Collecter des cas réels
#    - Diagnostics effectués
#    - Problèmes rencontrés
#    - Solutions appliquées

# 2. Formater en CSV/JSONL
cat > data/frigo_training.csv << EOF
text
"Bruit compresseur → Vérifier huile, accumulateur"
"Froid insuffisant → Vérifier thermostat, capteur"
...
EOF

# 3. Valider format
wc -l data/frigo_training.csv  # Doit avoir 100+ lignes
```

### Phase 2: Test Fine-Tuning

```bash
# Tester avec petit dataset
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "gpt2",
    "dataset_url": "data/frigo_training.csv",
    "epochs": 1,
    "batch_size": 1
  }'

# Attendre ~2 min
# Vérifier pas d'erreurs
```

### Phase 3: Production Fine-Tuning

```bash
# Fine-tuner le modèle complet
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "phi",
    "dataset_url": "data/frigo_training.csv",
    "epochs": 5,
    "batch_size": 4
  }'

# Attendre ~1 heure
# Nouveau modèle: models/phi-finetuned-20240115_103045/
```

### Phase 4: Utiliser Nouveau Modèle

```python
# Dans app_ia.py ou autre service:
import os

# Option 1: Auto-détection (modèle le plus récent)
fine_tuned_models = os.listdir('models')
latest = sorted([m for m in fine_tuned_models if 'finetuned' in m])[-1]
model_path = f'models/{latest}'

# Option 2: Spécifier explicitement
os.environ['IA_MODEL_PATH'] = 'models/phi-finetuned-20240115_103045'
```

---

## ⚡ Durée Fine-Tuning

| Modèle | Données | GPU | CPU | Epochs |
|--------|---------|-----|-----|--------|
| gpt2 | 100 | 1-2 min | 5-10 min | 1 |
| phi | 100 | 3-5 min | 15-30 min | 3 |
| mistral | 100 | 5-10 min | 30-60 min | 3 |
| phi | 1000 | 10-20 min | 60-120 min | 3 |
| phi | 10000 | 60-120 min | 300+ min | 5 |

**Note:** Durée dépend de hardware disponible

---

## 🎯 Meilleure Pratique

```
┌─────────────────────────────────────────┐
│ 1. Collecter données réelles             │
│    (Cas d'utilisation de production)     │
├─────────────────────────────────────────┤
│ 2. Formatter CSV/JSONL                   │
│    (Vérifier qualité données)            │
├─────────────────────────────────────────┤
│ 3. Fine-tuner sur model petit (gpt2)     │
│    (Test et validation)                  │
├─────────────────────────────────────────┤
│ 4. Fine-tuner sur modèle large (phi)     │
│    (Production final)                    │
├─────────────────────────────────────────┤
│ 5. Évaluer performances                  │
│    (Comparer avant/après)                │
├─────────────────────────────────────────┤
│ 6. Déployer en production                │
│    (Utiliser nouveau modèle)             │
└─────────────────────────────────────────┘
```

---

## 🎉 Résumé

Vous avez maintenant **API complète pour réentraîner à la demande**:

```bash
# Une requête pour adapter vos modèles:
curl -X POST http://localhost:5002/api/finetune/start \
  -d '{
    "model": "phi",
    "dataset_url": "data/frigo_training.csv",
    "epochs": 5
  }'

# Et le modèle s'adapte à votre domaine! 🚀
```

**Prochaines versions:**
- ✅ Monitoring du fine-tuning
- ✅ Utilisation automatique du modèle fine-tuné
- ✅ Stockage des modèles sur cloud (S3, etc.)
- ✅ Pipeline réentraînement automatique

---

Voir `SIMULATOR_TRIGGER_API.md` pour endpoint simulateur 🎯
