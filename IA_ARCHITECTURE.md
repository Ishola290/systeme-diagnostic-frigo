# 🤖 Architecture IA Modulaire - Guide Complet

## Vue d'ensemble

Le système IA supporte **plusieurs modèles** avec **sélection automatique** selon les ressources disponibles.

```
┌─────────────────────────────────────────┐
│      Demande Message/Alerte             │
└─────────────────┬───────────────────────┘
                  │
         ┌────────▼─────────┐
         │ Auto-Sélection   │
         │ Ressources       │
         └────────┬─────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
    ┌───▼───┐          ┌─────▼────┐
    │ Ollama│  CPU/GPU │HuggingFace
    └───┬───┘          └─────┬────┘
        │                    │
   ┌────▼─────────┐    ┌─────▼──────────┐
   │Modèles Locaux│    │Mistral/Phi2/IA │
   └────┬─────────┘    └─────┬──────────┘
        │                    │
        └────────┬───────────┘
                 │
         ┌───────▼────────┐
         │  Réponse       │
         │  (Rapide/Bon)  │
         └────────────────┘
```

## 📋 Modèles Disponibles

### Production-Ready

| Modèle | Taille | Params | VRAM | Vitesse | Qualité | Use Case |
|--------|--------|--------|------|---------|---------|----------|
| **Phi-2** | 5GB | 2.7B | 2-4GB | ⚡ Rapide | ⭐⭐⭐⭐ | CPU/GPU Prod |
| **Mistral-7B** | 13GB | 7B | 8-16GB | ⭐ Bon | ⭐⭐⭐⭐⭐ | GPU Haute Mém |
| **Neural-Chat** | 13GB | 7B | 8-16GB | ⭐ Bon | ⭐⭐⭐⭐ | Chat Optimisé |
| **Ollama** | Variable | - | Faible | ⚡⚡ TrèsRapide | ⭐⭐⭐⭐ | Local Engine |

### Fallback

| Modèle | Usage |
|--------|-------|
| **GPT-2** | Dev/test uniquement (généraliste) |
| **Réponses Intelligentes** | Mode dégradé (template-based) |

## 🚀 Sélection Automatique

Le système détecte automatiquement les ressources:

```python
# 1. Ollama disponible?
if ollama_running:
    model = 'ollama'

# 2. GPU disponible?
elif gpu_available:
    if gpu_memory > 10GB:
        model = 'mistral'  # GPU haute mémoire
    else:
        model = 'phi2'     # GPU limitée
        
# 3. CPU seulement
else:
    model = 'phi2'        # Optimisé CPU

# 4. Fallback
if model_fails:
    model = 'réponses_intelligentes'
```

## 🎯 Configuration par Environnement

### Développement (CPU local)
```bash
# Auto-sélection (détecte CPU, utilise phi2)
python app_ia.py

# Ou forcer gpt2 (test rapide)
export IA_MODEL=gpt2
python app_ia.py
```

### Production (GPU disponible)
```bash
# Auto-sélection (détecte GPU, utilise mistral/phi2)
python app_ia.py

# Ou forcer mistral
export IA_MODEL=mistral
python app_ia.py

# Ou forcer ollama
export IA_MODEL=ollama
python app_ia.py
```

### Docker/Render
```dockerfile
# Dans Dockerfile, spécifier le modèle production
ENV IA_MODEL=phi2           # Pour CPU
# ou
ENV IA_MODEL=mistral        # Pour GPU
# ou
ENV IA_MODEL=ollama         # Si ollama disponible
```

## 🔄 Modèles Locaux

Placer les modèles dans `models/{folder}`:

```
models/
├── phi-2/              # Phi-2 2.7B (5GB)
├── mistral-7b/         # Mistral-7B (13GB)
├── neural-chat-7b/     # Neural-Chat (13GB)
├── gpt2/               # GPT-2 125M (500MB)
└── ollama/             # (Utilise API ollama)
```

**Télécharger les modèles:**

```bash
# Phi-2 (recommandé pour prod CPU)
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
    model_dir = Path('models/phi-2'); \
    model_dir.mkdir(parents=True, exist_ok=True); \
    tokenizer = AutoTokenizer.from_pretrained('microsoft/phi-2'); \
    model = AutoModelForCausalLM.from_pretrained('microsoft/phi-2'); \
    tokenizer.save_pretrained(str(model_dir)); \
    model.save_pretrained(str(model_dir))"

# Mistral-7B (pour GPU haute mémoire)
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
    model_dir = Path('models/mistral-7b'); \
    model_dir.mkdir(parents=True, exist_ok=True); \
    tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.1'); \
    model = AutoModelForCausalLM.from_pretrained('mistralai/Mistral-7B-Instruct-v0.1'); \
    tokenizer.save_pretrained(str(model_dir)); \
    model.save_pretrained(str(model_dir))"
```

## 🔮 Réentraînement Futur

L'architecture est prête pour le fine-tuning avec données domaine frigo:

```python
# Pseudocode pour réentraînement futur
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir='./models/phi-2-finetuned-frigo',
    num_train_epochs=3,
    per_device_train_batch_size=4,
)

trainer = Trainer(
    model=base_model,  # phi2, mistral, etc.
    args=training_args,
    train_dataset=frigo_dataset,  # Données domaine frigo
    callbacks=[EarlyStoppingCallback()]
)

trainer.train()
```

**Données requises pour réentraînement:**
- ✅ Historique diagnostics
- ✅ Q&A domaine frigo
- ✅ Manuels techniques
- ✅ Alertes et solutions

## 📊 Logs et Monitoring

Lors du démarrage, le service affiche:

```
🔍 Détection des ressources disponibles...
✅ GPU disponible: 8.0GB
📊 GPU mémoire limitée -> Phi-2
📋 Configuration: Phi-2: Petit, rapide, bon (2.7B params)
🖥️ Device: CUDA
⏳ Chargement tokenizer...
⏳ Chargement modèle phi2...
✅ Modèle phi2 chargé avec succès
```

## 🔗 APIs de Réponse

Tous les modèles partagent la **même interface d'API**:

```json
POST /api/chat/message
{
    "message": "Qu'est-ce qu'une panne électrique?",
    "user_id": "123",
    "user_name": "admin"
}

Response:
{
    "success": true,
    "response": "⚡ Problème d'alimentation détecté...",
    "intent": "diagnostic",
    "model": "phi2",
    "device": "cuda",
    "processing_time_ms": 2340
}
```

## 🛠️ Troubleshooting

### Ollama n'est pas détecté
```bash
# Vérifier si ollama est lancé
curl http://localhost:11434/api/tags

# Lancer ollama
ollama serve
```

### GPU non détecté
```bash
# Vérifier CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Installer CUDA drivers
# https://developer.nvidia.com/cuda-downloads
```

### Modèle trop lent
- CPU: Utiliser phi2 (4-5s) au lieu de mistral (15-20s)
- GPU: Vérifier VRAM, peut être limité

### Modèle ne charge pas
- Vérifier chemin local: `ls models/phi-2/`
- Vérifier connectivité HF: `curl https://huggingface.co`
- Vérifier espace disque

## 📈 Évolution Prévue

1. ✅ Multi-modèles support
2. ✅ Auto-sélection ressources
3. ⏳ Fine-tuning données frigo
4. ⏳ Caching réponses
5. ⏳ A/B testing modèles
6. ⏳ Monitoring performances
7. ⏳ Fallback API distante (Claude/GPT-4)
