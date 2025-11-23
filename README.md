# 🧊 Système de Diagnostic Frigorifique IA avec Apprentissage Continu

Système intelligent de détection et prédiction de pannes pour installations frigorifiques, avec analyse par IA Gemini et notifications Telegram en temps réel.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Fonctionnalités

- ✅ **Détection de 12+ types de pannes** avec IA
- 🤖 **Analyse Gemini** pour diagnostics détaillés
- 📱 **Alertes Telegram** en temps réel
- 🧠 **Apprentissage continu** automatique
- 🆕 **Détection de nouvelles pannes** autonome
- 📊 **Archivage** et historique complet
- 🎮 **Simulateur intégré** pour tests
- 🚀 **API REST** complète

## 📋 Prérequis

- Python 3.11+
- Compte Google (pour Gemini AI - GRATUIT)
- Bot Telegram (GRATUIT)

## 🚀 Installation Rapide

### 1. Cloner le Repository

```bash
git clone https://github.com/VOTRE_USERNAME/systeme-diagnostic-frigo.git
cd systeme-diagnostic-frigo
```

### 2. Créer l'Environnement Virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration

Copier le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

Éditer `.env` avec vos credentials :

```env
# Gemini AI (Obtenir sur https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=AIzaSy...

# Telegram
TELEGRAM_BOT_TOKEN=8278706239:AAFnCW...
TELEGRAM_CHAT_ID=6607560503

# Agent IA (votre service Render)
AGENT_IA_URL=https://agent-ia-frigo.onrender.com

# Configuration
ENV=development
PORT=5000
```

### 5. Initialiser les Données

```bash
python init_data.py
```

## 🎮 Utilisation

### Démarrer l'Application

```bash
python app.py
```

L'API sera disponible sur `http://localhost:5000`

### Démarrer le Simulateur

**Mode Normal** (30% de pannes, intervalle 30s) :
```bash
python simulateur.py
```

**Mode Stress** (tests rapides, intervalle 5s) :
```bash
python simulateur.py --mode stress
```

**Mode Pannes** (80% de pannes pour tests) :
```bash
python simulateur.py --mode pannes --iterations 50
```

**Mode Personnalisé** :
```bash
python simulateur.py --interval 10 --prob-panne 0.5 --iterations 100
```

### Options du Simulateur

| Option | Description | Défaut |
|--------|-------------|--------|
| `--url` | URL de l'API | `http://localhost:5000/webhook/diagnostic-frigo` |
| `--iterations` | Nombre d'envois (infini si omis) | ∞ |
| `--interval` | Délai entre envois (secondes) | 30 |
| `--prob-panne` | Probabilité de panne (0.0-1.0) | 0.3 |
| `--mode` | Mode prédéfini : `normal`, `stress`, `pannes` | `normal` |

## 📡 Endpoints API

### POST `/webhook/diagnostic-frigo`

Envoie un diagnostic complet.

**Requête :**
```json
{
  "Température": -18,
  "Pression_BP": 2.5,
  "Pression_HP": 12,
  "Courant": 5.5,
  "Tension": 220,
  "Humidité": 55,
  "Débit_air": 150,
  "Vibration": 2,
  "source": "capteur_1",
  "localisation": "Chambre_Froide_A"
}
```

**Réponse :**
```json
{
  "success": true,
  "diagnostic_id": "DIAG_1730000000000",
  "panne_detectee": false,
  "type_panne": null,
  "score_confiance": 0,
  "apprentissage": {
    "compteur": 145,
    "retraining_requis": false,
    "nouvelle_panne": false
  }
}
```

### GET `/health`

Vérification de l'état du service.

### GET `/stats`

Obtenir les statistiques d'apprentissage.

### POST `/test-telegram`

Tester l'envoi Telegram.

```json
{
  "message": "Test du système"
}
```

## 🧠 Types de Pannes Détectées

| Panne | Variables Surveillées |
|-------|----------------------|
| Surchauffe compresseur | Température, Courant, Vibration |
| Fuite de fluide | Pression BP, Température, Courant |
| Givrage évaporateur | Température, Humidité, Débit air |
| Panne électrique | Tension, Courant |
| Obstruction conduit | Débit air, Pression BP |
| Défaillance ventilateur | Débit air, Humidité |
| Capteur défectueux | Température, Courant |
| Pression anormale HP | Pression HP, Courant |
| Pression anormale BP | Pression BP, Température |
| Défaut dégivrage | Température, Débit air |
| Défaillance thermostat | Température, Courant |
| Défaillance compresseur | Courant, Vibration |

## 📊 Exemples d'Utilisation

### 1. Test Rapide avec cURL

```bash
curl -X POST http://localhost:5000/webhook/diagnostic-frigo \
  -H "Content-Type: application/json" \
  -d '{
    "Température": 55,
    "Pression_BP": 2.5,
    "Pression_HP": 12,
    "Courant": 14,
    "Tension": 220,
    "Humidité": 55,
    "Débit_air": 150,
    "Vibration": 10
  }'
```

### 2. Test avec Python

```python
import requests

donnees = {
    "Température": -18,
    "Pression_BP": 2.5,
    "Pression_HP": 12,
    "Courant": 5.5,
    "Tension": 220,
    "Humidité": 55,
    "Débit_air": 150,
    "Vibration": 2,
    "localisation": "Test_Zone_1"
}

response = requests.post(
    'http://localhost:5000/webhook/diagnostic-frigo',
    json=donnees
)

print(response.json())
```

### 3. Simulation de 1000 Cas (pour réentraînement)

```bash
python simulateur.py --iterations 1000 --interval 1
```

## 🔧 Configuration Avancée

### Seuils Personnalisés

Modifier `config.py` :

```python
SEUILS = {
    'Température': {'min': -30, 'max': 10, 'optimal': -18},
    'Pression_BP': {'min': 1.0, 'max': 5.0, 'optimal': 2.5},
    # ...
}
```

### Fréquence de Réentraînement

```python
SEUIL_RETRAINING = 1000  # Tous les 1000 diagnostics
```

### Seuil Nouvelle Panne

```python
SEUIL_NOUVELLE_PANNE = 50  # 50 exemples minimum
```

## 📱 Notifications Telegram

Le système envoie 3 types de notifications :

1. **🚨 Alerte Panne** - Analyse Gemini détaillée avec plan d'action
2. **🔄 Réentraînement** - Confirmation après mise à jour des modèles
3. **🆕 Nouvelle Panne** - Découverte d'un nouveau type de panne

### Exemple de Message

```
🚨🚨🚨 ALERTE SYSTÈME FRIGORIFIQUE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 IDENTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 DIAG_1730000000000
📅 29/10/2025 15:30:45
📍 Chambre_Froide_A

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 PANNES DÉTECTÉES (2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. surchauffe_compresseur (92%)
2. pression_anormale_HP (85%)

📋 ANALYSE GEMINI:
Le compresseur présente une surchauffe 
critique avec surpression HP...

✅ PLAN D'ACTION:
1. Arrêter immédiatement le compresseur
2. Vérifier le système de refroidissement
3. Contrôler le circuit HP
```

## 🧪 Tests

### Tests Unitaires

```bash
pytest tests/
```

### Tests d'Intégration

```bash
pytest tests/ -m integration
```

### Coverage

```bash
pytest --cov=services --cov-report=html
```

## 📦 Déploiement sur Render

### 1. Préparer le Déploiement

Créer `render.yaml` :

```yaml
services:
  - type: web
    name: diagnostic-frigo
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
```

### 2. Déployer

1. Push sur GitHub
2. Connecter Render à votre repo
3. Ajouter les variables d'environnement
4. Deploy

## 🐛 Dépannage

### Problème : "Gemini API Key Invalid"

- Vérifier la clé sur https://makersuite.google.com/app/apikey
- S'assurer qu'elle est bien dans `.env`

### Problème : "Telegram Bot Not Responding"

- Vérifier le token
- Démarrer une conversation avec le bot
- Tester avec `/test-telegram`

### Problème : "Agent IA Timeout"

- L'agent Render est peut-être endormi
- Attendre 30-60 secondes
- Réessayer

## 📈 Roadmap

- [ ] Interface web Dashboard
- [ ] Support multi-sites
- [ ] Export rapports PDF
- [ ] Intégration MQTT
- [ ] API GraphQL
- [ ] Application mobile

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

## 👨‍💻 Auteur

**Votre Nom**
- GitHub: [@votre-username](https://github.com/votre-username)
- Telegram: @votre-telegram

## 🙏 Remerciements

- Google Gemini AI
- Telegram Bot API
- Flask Framework
- Communauté Open Source

---

⭐ **Si ce projet vous aide, n'hésitez pas à lui donner une étoile !** ⭐