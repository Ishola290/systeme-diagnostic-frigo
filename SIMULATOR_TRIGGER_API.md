# 🎯 API Déclenchement Simulateur Production

## 📍 Vue d'ensemble

Vous pouvez maintenant **déclencher le simulateur à la demande** via un simple appel HTTP à votre service APP!

```
Endpoint: POST /api/simulator/start
Description: Lance le simulateur avec diagnostics en arrière-plan
Réponse: Immédiate (202 Accepted)
Exécution: Asynchrone (ne bloque pas l'app)
```

---

## 🚀 Utilisation

### 1️⃣ Endpoint Info (Découvrez les options)

```bash
curl http://localhost:5000/api/simulator/info

# Réponse:
{
  "available": true,
  "description": "Simulateur de capteurs frigorifiques production-ready",
  "endpoints": {...},
  "examples": {...}
}
```

### 2️⃣ Démarrer Simulateur (Simple)

```bash
curl -X POST http://localhost:5000/api/simulator/start \
  -H "Content-Type: application/json" \
  -d '{}'

# Réponse: 202 Accepted
{
  "status": "started",
  "message": "Simulateur lancé avec 100 cycles",
  "config": {
    "cycles": 100,
    "interval": 30,
    "prob_panne": 0.1,
    "app_url": "http://localhost:5000"
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 3️⃣ Démarrer Simulateur (Personnalisé)

```bash
# Test rapide (5 diagnostics en 5 secondes)
curl -X POST http://localhost:5000/api/simulator/start \
  -H "Content-Type: application/json" \
  -d '{
    "cycles": 5,
    "interval": 5,
    "prob_panne": 0.5
  }'

# Production (100 diagnostics, 1 par minute)
curl -X POST http://localhost:5000/api/simulator/start \
  -H "Content-Type: application/json" \
  -d '{
    "cycles": 100,
    "interval": 60,
    "prob_panne": 0.15
  }'

# Stress test (1000 diagnostics rapides)
curl -X POST http://localhost:5000/api/simulator/start \
  -H "Content-Type: application/json" \
  -d '{
    "cycles": 1000,
    "interval": 1,
    "prob_panne": 0.8
  }'
```

---

## 📋 Paramètres

| Paramètre | Type | Défaut | Plage | Description |
|-----------|------|--------|-------|-------------|
| `cycles` | int | 100 | 1-10000 | Nombre de diagnostics à envoyer |
| `interval` | int | 30 | 1-3600 | Secondes entre envois |
| `prob_panne` | float | 0.1 | 0.0-1.0 | Probabilité panne (0.1 = 10%) |

---

## 💻 Exemples de Code

### Python

```python
import requests

# Info sur le simulateur
response = requests.get('http://localhost:5000/api/simulator/info')
print(response.json())

# Lancer le simulateur
response = requests.post(
    'http://localhost:5000/api/simulator/start',
    json={
        'cycles': 50,
        'interval': 30,
        'prob_panne': 0.2
    }
)
print(response.status_code)  # 202
print(response.json())
```

### JavaScript/Fetch

```javascript
// Info
fetch('http://localhost:5000/api/simulator/info')
  .then(r => r.json())
  .then(data => console.log(data))

// Lancer simulateur
fetch('http://localhost:5000/api/simulator/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    cycles: 50,
    interval: 30,
    prob_panne: 0.2
  })
})
.then(r => r.json())
.then(data => console.log(data))
```

### PowerShell

```powershell
# Info
Invoke-WebRequest -Uri "http://localhost:5000/api/simulator/info" | 
  Select-Object -ExpandProperty Content | 
  ConvertFrom-Json

# Lancer simulateur
$body = @{
    cycles = 50
    interval = 30
    prob_panne = 0.2
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/simulator/start" `
  -Method POST `
  -Headers @{'Content-Type' = 'application/json'} `
  -Body $body
```

---

## 🌐 Production (Render)

Une fois déployé sur Render, vous pouvez déclencher le simulateur depuis n'importe où:

```bash
# Depuis votre machine
curl -X POST https://frigo-app.onrender.com/api/simulator/start \
  -H "Content-Type: application/json" \
  -d '{
    "cycles": 200,
    "interval": 60,
    "prob_panne": 0.15
  }'

# Réponse: 202 Accepted
# Le simulateur lance en arrière-plan sur le serveur Render!
```

---

## 📊 Cas d'Usage

### 1. Test Rapide Avant Production

```bash
# Valider que tout fonctionne
curl -X POST http://localhost:5000/api/simulator/start \
  -d '{"cycles": 5, "interval": 5}'

# Attendez 25 secondes
# Vérifiez les données arrivent en base de données
# Vérifiez le dashboard Chat se met à jour
```

### 2. Charger la Base de Données

```bash
# Générer 500 diagnostics pour avoir du contenu
curl -X POST http://localhost:5000/api/simulator/start \
  -d '{"cycles": 500, "interval": 1, "prob_panne": 0.2}'

# Cela prend ~8 minutes
# À la fin, vous avez 500 diagnostics avec historique
```

### 3. Test Pannes

```bash
# Tester le système d'alertes
curl -X POST http://localhost:5000/api/simulator/start \
  -d '{
    "cycles": 100,
    "interval": 5,
    "prob_panne": 0.7
  }'

# Beaucoup de pannes → beaucoup d'alertes
# Vérifiez que le système réagit correctement
```

### 4. Simulation Production 24/7

```bash
# En production: une requête unique suffit!
curl -X POST https://frigo-app.onrender.com/api/simulator/start \
  -d '{
    "cycles": 10000,
    "interval": 120,
    "prob_panne": 0.15
  }'

# Cela lance ~139 heures de simulation
# Les diagnostics arrivent en continu pendant ~6 jours
```

---

## ✅ Avantages

### Vs. 4e Service Render (ancien modèle)

```
❌ Créer et maintenir un 4e service
❌ Coûts supplémentaires (même si Free plan)
❌ Complexité infrastructure

✅ Déclencher via simple appel HTTP
✅ Zéro coût supplémentaire
✅ Flexible: démarrer/arrêter à volonté
✅ Parfait pour production à la demande
```

### Vs. Simulateur Local (ancien modèle)

```
❌ Oublier de lancer le simulateur
❌ Simulateur arrête si fermer PC
❌ Difficile de varier les paramètres

✅ Déclencher depuis n'importe où
✅ Fonctionne 24/7 sur Render
✅ Contrôler cycles, interval, pannes
✅ Une ligne de code pour 6 jours de data!
```

---

## 🔒 Sécurité (Optionnel)

Pour limiter l'accès à cet endpoint en production, vous pouvez ajouter un API key:

```python
# app.py - À ajouter si nécessaire
API_KEY = os.environ.get('SIMULATOR_API_KEY')

@app.route('/api/simulator/start', methods=['POST'])
def start_simulator():
    # Vérifier la clé
    key = request.headers.get('X-API-Key')
    if key != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # ... reste du code
```

**Utilisation:**
```bash
curl -X POST https://frigo-app.onrender.com/api/simulator/start \
  -H "X-API-Key: your-secret-key" \
  -d '{...}'
```

---

## 🎯 Workflow Recommandé

### 1. Local Development

```bash
# Terminal 1: Services
docker-compose up

# Terminal 2: Trigger simulateur
curl -X POST http://localhost:5000/api/simulator/start \
  -d '{"cycles": 10, "interval": 5}'

# Observer les données arrivent
```

### 2. Before Production

```bash
# Test communication
python test_service_communication.py

# Test simulateur endpoint
curl -X POST http://localhost:5000/api/simulator/start \
  -d '{"cycles": 5, "interval": 5}'

# Vérifier tout fonctionne ✅
```

### 3. Production Render

```bash
# Une fois les 3 services déployés:
curl -X POST https://frigo-app.onrender.com/api/simulator/start \
  -d '{
    "cycles": 10000,
    "interval": 120,
    "prob_panne": 0.15
  }'

# Et voilà! 6 jours de données continues ✅
```

---

## 📞 Erreurs Courantes

### Erreur 400: Invalid parameters

```
{"error": "cycles doit être entre 1 et 10000"}
```

**Solution:** Vérifier les paramètres
```bash
curl -X POST http://localhost:5000/api/simulator/start \
  -d '{"cycles": 100, "interval": 30, "prob_panne": 0.1}'
```

### Erreur 500: Simulator not found

```
{"error": "No module named 'simulateur_production'"}
```

**Solution:** Vérifier que `simulateur_production.py` existe
```bash
ls simulateur_production.py  # Doit être au root
```

### Erreur 202 mais rien ne se passe

**Solution:** Vérifier les logs
```bash
# En local
tail -f diagnostic_frigo.log

# Sur Render
Render Dashboard → Service APP → Logs
```

---

## 🎉 Résumé

Vous avez maintenant un **endpoint magique** pour déclencher le simulateur:

```bash
# N'importe où, n'importe quand:
curl -X POST https://frigo-app.onrender.com/api/simulator/start \
  -d '{"cycles": 100, "interval": 60, "prob_panne": 0.15}'

# Et 100 diagnostics arrivent en production! 🚀
```

**Plus besoin de:**
- ❌ 4e service Render
- ❌ Lancer manuellement le simulateur
- ❌ Oublier la simulation

**Juste:**
- ✅ Un appel API
- ✅ Les données arrivent
- ✅ Production ready! 🎉
