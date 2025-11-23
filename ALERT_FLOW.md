# 🔄 Flux Complet: Alerte → IA Service → Chat & Telegram

## ✅ Architecture Mise à Jour

```
┌─────────────────┐
│   Diagnostic    │
│   (Capteurs)    │
└────────┬────────┘
         │
         ↓
┌─────────────────────────┐
│   app.py (port 5000)    │
│ - Prédiction pannes     │
│ - Détect anomalies      │
└────────┬────────────────┘
         │
    Panne détectée?
         │
    YES ↓ NO → Fin
    ┌────────────────────────────────┐
    │ POST /api/alerts/process       │
    │ (Service IA)                   │
    └────────┬───────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │   Service IA (port 5002)       │
    │ - Enrich l'alerte              │
    │ - Analyse avec Phi-2 LLM       │
    │ - Génère solutions             │
    └──┬──────────────────────┬──────┘
       │                      │
   POST│                      │POST
       ↓                      ↓
  ┌────────────┐      ┌──────────────┐
  │ Chat Web   │      │   app.py     │
  │ (5001)     │      │ /api/telegram│
  │            │      │ /notify      │
  │ ✅ Alerte  │      └──────┬───────┘
  │    stored  │             │
  │ ✅ WebSock │         Telegram
  │    notify  │         (Bot Token)
  └────────────┘             │
                         Technicien
                         reçoit
                         notification
```

## 📋 Flux Détaillé

### 1️⃣ **app.py** → Diagnostic
```python
# Capteurs envoient données
POST /webhook/diagnostic-frigo
{
  "temperature": 28,
  "humidity": 65,
  "pressure": 1.2
}
```

### 2️⃣ **app.py** → Prédiction
```python
prediction = agent_ia.predict(donnees)
# Résultat: Panne détectée = "Compresseur bloqué"
```

### 3️⃣ **app.py** → Service IA (Enrichissement)
```python
POST http://localhost:5002/api/alerts/process
{
  "title": "Panne détectée: Compresseur bloqué",
  "severity": "critical",
  "sensors": {...},
  "prediction": {...}
}
```

### 4️⃣ **Service IA** Traite & Enrichit
```python
# ia_service.process_alert()
# - Analyse l'alerte
# - Génère solutions avec Phi-2
# - Retourne alerte enrichie
{
  "analysis": "Compresseur bloqué. Solutions: 1) Vérifier alimentation 2) Débloquer mécaniquement",
  "severity_score": 4,
  "suggested_solutions": [...]
}
```

### 5️⃣ **Service IA** → Chat Web
```python
POST http://localhost:5001/api/receive-alert
{
  "type": "error",
  "title": "Panne détectée: Compresseur bloqué",
  "message": "Analyse du service IA...",
  "severity": "critical",
  "diagnostic_id": "..."
}

Résultat:
✅ Alerte stockée en DB
✅ WebSocket 'new_alert' envoyé
✅ Dashboard actualise en temps réel
```

### 6️⃣ **Service IA** → app.py (Telegram)
```python
POST http://localhost:5000/api/telegram/notify
{
  "message": "🚨 Panne détectée: Compresseur bloqué\n\nAnalyse du service IA..."
}

↓ app.py reçoit et envoie à Telegram

telegram.envoyer_notification_sync(message)

Résultat:
✅ Technicien reçoit notification Telegram
✅ Contenu enrichi par IA
```

## 🔗 Endpoints Nouvelle Architecture

| Service | Endpoint | Méthode | Source | Destination |
|---------|----------|---------|--------|-------------|
| **app.py** | POST `/api/alerts/process` | POST | Service IA | Service IA |
| **Service IA** | POST `/api/alerts/process` | POST | app.py | ← |
| **Service IA** | POST `/api/receive-alert` | POST | ← | Chat Web |
| **Service IA** | POST `/api/telegram/notify` | POST | ← | app.py |
| **app.py** | POST `/api/telegram/notify` | POST | Service IA | Telegram |
| **Chat Web** | POST `/api/receive-alert` | POST | Service IA | ← |

## 📊 Bénéfices Nouveau Flux

| Aspect | Avant | Après |
|--------|-------|-------|
| **Enrichissement** | Aucun | ✅ Phi-2 génère solutions |
| **Chat reçoit alertes** | ❌ Non | ✅ Oui, en temps réel |
| **Telegram reçoit** | ❌ Alerte brute | ✅ Alerte enrichie par IA |
| **Logs/Audit** | ❌ Limités | ✅ Complets (IA + Chat + Telegram) |
| **Expérience tech** | ❌ Cherche solutions | ✅ Solutions proposées par IA |

## 🚀 Test du Flux Complet

```powershell
# 1. Démarrer tous les services
docker-compose up -d

# 2. Attendre que le modèle Phi-2 soit chargé (5-10 min)
docker logs -f frigo-ia-service

# 3. Envoyer un diagnostic avec panne
curl -X POST http://localhost:5000/webhook/diagnostic-frigo \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 35,
    "humidity": 80,
    "pressure": 0.8
  }'

# 4. Résultats attendus:
# ✅ app.py détecte la panne
# ✅ Service IA enrichit l'alerte
# ✅ Chat Web reçoit l'alerte
# ✅ Dashboard (http://localhost:5001) s'actualise
# ✅ Telegram envoie notification
```

## 📝 Logs du Flux

```
app.py: "🚨 Panne détectée - Compresseur bloqué"
↓
app.py: "POST /api/alerts/process au service IA"
↓
Service IA: "🚨 Alerte reçue: Compresseur bloqué"
Service IA: "💬 Traitement avec Phi-2 LLM"
Service IA: "✅ Alerte envoyée au Chat Web"
Service IA: "✅ Notification Telegram envoyée"
↓
app.py: "📱 Notification Telegram reçue du service IA"
app.py: "✅ Message envoyé à Telegram"
↓
Chat Web: "📢 Alerte reçue: Compresseur bloqué"
Chat Web: "✅ WebSocket 'new_alert' diffusé"
↓
Dashboard: "🔴 Alerte CRITIQUE affichée"
Telegram Bot: "🚨 Panne détectée: Compresseur bloqué\n\nSolutions: ..."
```

## ✨ Résumé

**Avant:**
```
app.py → Gemini (cloud) → Telegram
```

**Maintenant:**
```
app.py → Service IA (Phi-2 local)
         ├→ Enrichissement
         ├→ Chat Web (WebSocket)
         ├→ Telegram (notification enrichie)
         └→ Apprentissage continu
```

**Impact:**
- ✅ **Gratuit** - Plus d'API Gemini payante
- ✅ **Rapide** - Local, pas de réseau
- ✅ **Intelligent** - Solutions proposées automatiquement
- ✅ **Transparent** - Logs complets
- ✅ **Résilience** - Fonctionne hors ligne
