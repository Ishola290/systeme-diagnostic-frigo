# 🎯 Guide Simulateur Production

## Vue d'ensemble

Le **simulateur de capteurs** génère des données réalistes de diagnostic frigorifique et les envoie en temps réel à votre service APP.

```
┌─────────────────────┐
│ Simulateur Capteurs │
│  (data generator)   │
└──────────┬──────────┘
           │
      📤 POST
           │
           ↓
┌─────────────────────────────────────┐
│ App Service                         │
│ /webhook/diagnostic-frigo           │
│                                     │
│ ├─ Stockage données                 │
│ ├─ Appel Chat (analyse temps réel)  │
│ └─ Appel IA (diagnostics)           │
└─────────────────────────────────────┘
```

## 🚀 Utilisation

### Local (Docker Compose)

**Démarrer les services:**
```powershell
# Terminal 1: Services
docker-compose up

# Terminal 2: Simulateur
python simulateur_production.py
```

### Local (Python Scripts)

**Terminal 1: App**
```powershell
python app.py
```

**Terminal 2: Chat**
```powershell
cd chat
python app_web.py
```

**Terminal 3: IA Service**
```powershell
cd gpt
python app_ia.py
```

**Terminal 4: Simulateur**
```powershell
python simulateur_production.py
```

### Production (Render)

**Option A: Simulateur comme 4e Service Render**

1. Créer nouveau Web Service sur Render
   ```
   Name: frigo-simulator
   Build Command: pip install -r requirements.txt
   Start Command: python simulateur_production.py --interval 60
   Plan: Free
   ```

2. Configurer env vars:
   ```
   MAIN_APP_URL=https://frigo-app.onrender.com
   ```

3. Le simulateur lancera automatiquement les diagnostics

**Option B: Simulateur sur votre machine (recommandé pour test)**

```powershell
# Configuration avec URLs Render
$env:MAIN_APP_URL = "https://frigo-app.onrender.com"

# Lancer
python simulateur_production.py --interval 60 --prob-panne 0.15
```

## 🎛️ Paramètres

### Interface CLI

```powershell
# Aide
python simulateur_production.py --help

# Configurations
python simulateur_production.py \
    --app-url http://localhost:5000 \
    --interval 30 \
    --prob-panne 0.1 \
    --cycles 100

# Production
python simulateur_production.py \
    --app-url https://frigo-app.onrender.com \
    --interval 60 \
    --prob-panne 0.15

# Continu (par défaut)
python simulateur_production.py
```

### Paramètres détaillés

| Paramètre | Défaut | Plage | Description |
|-----------|--------|-------|-------------|
| `--app-url` | `http://localhost:5000` | - | URL du service APP |
| `--interval` | `30` | 1-3600 | Secondes entre envois |
| `--prob-panne` | `0.1` | 0.0-1.0 | Probabilité panne (0.1 = 10%) |
| `--cycles` | ∞ | 1+ | Nombre de cycles (∞ = continu) |
| `--no-auto-detect` | off | - | Désactiver découverte automatique |

### Variable d'environnement

```python
# env vars surpassent les defaults
$env:MAIN_APP_URL = "https://api.example.com"
$env:SIMULATOR_INTERVAL = "60"
$env:SIMULATOR_PANNE_PROB = "0.2"
```

## 📊 Données générées

### Capteurs normaux

```json
{
  "diagnostic_id": "SIM_000001",
  "timestamp": "2024-01-15T10:30:45.123456",
  "type": "simulation",
  "capteurs": {
    "Température": 4.8,
    "Pression_BP": 2.45,
    "Pression_HP": 12.1,
    "Courant": 14.8,
    "Tension": 382.5,
    "Vibration": 0.48,
    "Humidité": 64.2,
    "Débit_air": 98.5
  },
  "panne_active": null,
  "source": "simulateur"
}
```

### Pannes simulées (12 types)

#### 1. Surchauffe Compresseur
```
⚠️  Signature: T↑↑ + Courant↑ + Vibration↑
💡 Causes: Surcharge, filtre sale, réfrigérant manquant
```

#### 2. Fuite Fluide
```
⚠️  Signature: Pression_BP↓ + T↑ + Courant↓
💡 Causes: Joint défectueux, corrosion, vibrations
```

#### 3. Givrage Évaporateur
```
⚠️  Signature: T↓↓ + Humidité↑ + Débit_air↓
💡 Causes: Chauffage de dégivrage défaillant, thermostat
```

#### 4. Panne Électrique
```
⚠️  Signature: Tension↓↓ + Courant=0
💡 Causes: Disjoncteur déclenché, câbles, contacter
```

#### 5. Obstruction Conduit
```
⚠️  Signature: Débit_air↓↓ + Pression_BP↑
💡 Causes: Accumulation glace, débris, filtre
```

#### 6. Défaillance Ventilateur
```
⚠️  Signature: Débit_air↓ + Humidité↑
💡 Causes: Moteur fatigué, pale cassée, blocage
```

#### 7. Capteur Défectueux
```
⚠️  Signature: Valeurs invalides (ex: -999.0)
💡 Causes: Câble rompu, connecteur, capteur grillé
```

#### 8. Pression Anormale HP
```
⚠️  Signature: Pression_HP↑↑ + Courant↑
💡 Causes: Condenseur sale, ventilateur HP, blockage
```

#### 9. Pression Anormale BP
```
⚠️  Signature: Pression_BP↑ + T↑
💡 Causes: Évaporateur sale, TOR bloqueé, accumulation
```

#### 10. Défaut Dégivrage
```
⚠️  Signature: T↓↓ + Débit↓
💡 Causes: Thermostat, relais, chauffage défaillant
```

#### 11. Défaillance Thermostat
```
⚠️  Signature: T↑↑ + Courant↑
💡 Causes: Thermostat collé ouvert, électronique
```

#### 12. Défaillance Compresseur
```
⚠️  Signature: Courant=0 + Vibration↓
💡 Causes: Compresseur grillé, relais, protecteur
```

## 🔄 Auto-Détection des URLs

Le simulateur détecte automatiquement les services:

```python
# 1. Vérifier env vars (Render)
MAIN_APP_URL = os.environ.get('MAIN_APP_URL')
# → https://frigo-app.onrender.com

# 2. Essayer DNS Docker
socket.gethostbyname('app')
# → http://app:5000 ✅

# 3. Fallback localhost
# → http://localhost:5000
```

**Résultat:** Les URLs se synchronisent automatiquement! 🎉

## 📈 Exemples de Scénarios

### Scénario 1: Test Rapide (5 cycles)

```powershell
python simulateur_production.py `
    --cycles 5 `
    --interval 5 `
    --prob-panne 0.5
```

Output:
```
✅ Diagnostic #1 envoyé
✅ Diagnostic #2 envoyé
🚨 PANNE DÉTECTÉE: surchauffe_compresseur
✅ Diagnostic #3 envoyé
✅ Diagnostic #4 envoyé
✅ Panne résolue
✅ Diagnostic #5 envoyé
```

### Scénario 2: Production Stable (30 min)

```powershell
python simulateur_production.py `
    --interval 120 `
    --prob-panne 0.05 `
    --cycles 15
```

- 1 diagnostic toutes les 2 minutes
- Panne rare (5%)
- 30 minutes total

### Scénario 3: Stress Test (100 pannes)

```powershell
python simulateur_production.py `
    --interval 5 `
    --prob-panne 0.8 `
    --cycles 100
```

- Diagnostic toutes les 5 sec
- Panne fréquente (80%)
- Test robustesse système

## ✅ Vérification Fonctionnement

### 1. Logs du Simulateur

```
✅ Diagnostic #42 envoyé
🚨 PANNE DÉTECTÉE: fuite_fluide
📊 Statistiques: 42 envoyés
```

### 2. Vérifier API App

```powershell
# Tester webhook
curl -X POST http://localhost:5000/webhook/diagnostic-frigo `
  -H "Content-Type: application/json" `
  -d @- << EOF
{
  "diagnostic_id": "TEST_001",
  "timestamp": "2024-01-15T10:30:00",
  "capteurs": {"Température": 5.0}
}
EOF
```

### 3. Vérifier Base Données

```powershell
# Voir les diagnostics reçus
sqlite3 chat/instance/chat_app.db "SELECT COUNT(*) FROM diagnostic;"
# → 42
```

### 4. Vérifier Dashboard Chat

```
http://localhost:5001/dashboard
```

- Graphiques se mettent à jour en temps réel
- Alertes s'affichent pour pannes
- Historique s'accumule

## 🔧 Dépannage

### Problème: Timeout

```
⏱️  Timeout - App non réactive
```

**Solutions:**
```powershell
# 1. Vérifier que l'app est running
curl http://localhost:5000/health

# 2. Augmenter timeout
python simulateur_production.py --interval 60

# 3. Vérifier logs app
# Ouvrir app.py terminal
```

### Problème: Connection Refused

```
🔌 Connexion perdue - Vérifier app_url
```

**Solutions:**
```powershell
# 1. Vérifier URL correcte
$env:MAIN_APP_URL  # Doit être défini

# 2. Vérifier service running
netstat -ano | findstr :5000

# 3. Lancer app
python app.py
```

### Problème: Données n'arrivent pas

**Vérifier:**
1. ✅ Simulateur running (`python simulateur_production.py`)
2. ✅ App running (`python app.py`)
3. ✅ Webhook existe (`/webhook/diagnostic-frigo`)
4. ✅ URL correcte dans simulateur
5. ✅ Logs app montrent les POST

### Problème: Service Discovery échoue (Docker)

```
ℹ️  app not resolvable (not in Docker)
```

**Normal si:** Vous êtes en local (pas dans Docker)

**En Docker:** C'est une erreur, vérifier:
```bash
docker network ls  # Vérifier network frigo-network existe
docker-compose ps  # Tous les services running
```

## 📝 Fichiers Créés

| Fichier | Utilité |
|---------|---------|
| `simulateur_production.py` | Simulateur principal avec auto-détection |
| `SERVICE_URLS_CONFIG.md` | Configuration URLs inter-services |
| `test_service_communication.py` | Test communication services |
| `start-simulator.ps1` | Launcher PowerShell |
| `.env.production.example` | Template config production |

## 🎓 Cas d'Usage

### Cas 1: Développement Local

```powershell
# Terminal 1
docker-compose up

# Terminal 2
python simulateur_production.py --interval 30 --prob-panne 0.2
```

✅ Testez en local avec données réalistes

### Cas 2: Avant Déploiement

```powershell
python test_service_communication.py
# Vérifier tous les services communiquent

python simulateur_production.py --cycles 50 --interval 10
# Vérifier données envoyées correctement
```

✅ Validez avant production

### Cas 3: Production Continue

```
Service Render: frigo-simulator
Start Command: python simulateur_production.py --interval 120 --prob-panne 0.15
```

✅ Données continues, pannes realistes

## 📞 Questions Fréquentes

**Q: Puis-je lancer le simulateur depuis Render?**
A: Oui! Créez un 4e Web Service avec `python simulateur_production.py`

**Q: Comment changer la fréquence des pannes?**
A: `--prob-panne 0.3` (30%), `--prob-panne 0.05` (5%)

**Q: Est-ce que les URLs se synchro automatiquement?**
A: Oui! Le simulateur détecte env vars → Docker DNS → localhost

**Q: Puis-je voir quels types de pannes?**
A: Oui, le code a 12 pannes définies, vérifier logs

**Q: Comment arrêter le simulateur?**
A: `Ctrl+C` dans le terminal

---

✅ **Prêt à déployer?** Voir `SERVICE_URLS_CONFIG.md` pour Render setup
