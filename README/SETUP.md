# 🚀 Guide de Setup Complet - Système de Diagnostic Frigorifique

## ✅ Statut d'Implémentation

Tous les fichiers critiques ont été créés ! Voici le statut complet :

### 📁 Structure du Projet - ✅ COMPLÈTE

```
systeme-diagnostic-frigo/
├── 🔧 CONFIGURATION
│   ├── app.py                          ✅ Application Flask principale
│   ├── config.py                       ✅ Configuration centralisée
│   ├── requirements.txt                ✅ Dépendances Python
│   ├── .env.example                    ✅ Template de configuration
│   └── .env                            ⚠️  À configurer (créé mais vide)
│
├── 🤖 SERVICES (services/)
│   ├── agent_ia.py                     ✅ Communication avec Agent IA
│   ├── gemini_service.py               ✅ Intégration Google Gemini
│   ├── telegram_service.py             ✅ Notifications Telegram
│   ├── apprentissage_service.py        ✅ Apprentissage continu & archivage
│   └── __init__.py                     ✅ Package init
│
├── 🛠️  UTILITIES (utils/)
│   ├── validation.py                   ✅ Validation des données
│   ├── helpers.py                      ✅ Fonctions utilitaires
│   └── __init__.py                     ✅ Package init
│
├── 🎮 OUTILS
│   ├── simulateur.py                   ✅ Simulateur de capteurs (TEST/DÉMO)
│   ├── init_data.py                    ✅ Script d'initialisation
│   └── quick_start.md                  ✅ Guide démarrage rapide
│
├── 📊 DATA (data/)
│   ├── compteur_apprentissage.json     (créé à l'init)
│   ├── dataset_apprentissage.csv       (créé à l'init)
│   └── dernier_diagnostic.json         (créé à l'init)
│
├── 📝 LOGS (logs/)
│   └── diagnostic_frigo.log            (généré au runtime)
│
├── 🎯 TESTS (tests/)
│   ├── test_simple.py                  ✅ Tests unitaires
│   └── __init__.py                     ✅ Package init
│
└── 📚 DOCUMENTATION
    ├── README.md                       ✅ Documentation complète
    └── SETUP.md                        📍 (ce fichier)
```

---

## 🔧 ÉTAPE 1 : Installation des Dépendances

### Vérifier Python 3.11+
```powershell
python --version
```

### Créer l'environnement virtuel
```powershell
# Windows
python -m venv venv
venv\Scripts\Activate.ps1

# Si error de policy: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Installer les dépendances
```powershell
pip install -r requirements.txt
```

---

## 🔐 ÉTAPE 2 : Configuration des Credentials

### 1️⃣ Obtenir les Clés API

#### Google Gemini (GRATUIT)
1. Aller sur https://makersuite.google.com/app/apikey
2. Créer une clé API gratuite
3. Copier la clé

#### Telegram (GRATUIT)
1. Ouvrir Telegram et chercher **@BotFather**
2. Envoyer `/start` puis `/newbot`
3. Remplir les infos pour créer le bot
4. Copier le **token d'accès**
5. Pour avoir ton **Chat ID**:
   - Envoyer un message à ton bot
   - Accéder à: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copier le `chat.id`

#### Agent IA (EXISTANT)
```
URL fournie: https://agent-ia-frigo-tdmm.onrender.com
```

### 2️⃣ Configurer le fichier `.env`

Copier `.env.example` vers `.env` :
```powershell
Copy-Item .env.example .env
```

Éditer `.env` avec vos credentials :
```bash
# Windows: notepad .env
# Linux: nano .env
# VSCode: code .env
```

**Champs à remplir obligatoirement :**
```env
GEMINI_API_KEY=AIzaSy...VotreClé
TELEGRAM_BOT_TOKEN=8278706239:AAFnCW...VotreToken
TELEGRAM_CHAT_ID=6607560503
```

---

## 📊 ÉTAPE 3 : Initialisation des Données

Créer la structure des données :
```powershell
python init_data.py
```

**Ce qu'il crée :**
- ✅ Dossiers `/data`, `/logs`, `/models`
- ✅ Fichiers JSON et CSV pour apprentissage
- ✅ Fichier `.env.example` complet
- ✅ Fichier `.env` basique

---

## 🚀 ÉTAPE 4 : Démarrage de l'Application

### Terminal 1 - Lancer l'API Flask
```powershell
python app.py
```

**Vous devez voir :**
```
✅ Gemini configuré - Modèle: gemini-1.5-flash
✅ Telegram configuré - Chat ID: 6607560503
🤖 Agent IA configuré: https://agent-ia-frigo-tdmm.onrender.com
🧠 Service apprentissage initialisé
 * Running on http://localhost:5000
```

### Terminal 2 - Lancer le Simulateur
```powershell
python simulateur.py
```

**Options disponibles :**
```powershell
# Mode normal (30% pannes, 30s intervalle)
python simulateur.py

# Mode haute fréquence
python simulateur.py --interval 10 --prob 0.5

# URL API personnalisée
python simulateur.py --api http://localhost:8000

# Durée panne personnalisée
python simulateur.py --duree-panne 600
```

---

## 📡 ÉTAPE 5 : Tester l'API

### Health Check
```powershell
curl http://localhost:5000/health
```

### Envoyer un Diagnostic
```powershell
$diagnostic = @{
    Température = -18.5
    Pression_BP = 2.4
    Pression_HP = 12.1
    Intensité_Compresseur = 14.8
    Intensité_Ventilateur = 5.2
    Humidité_Evaporateur = 65
    Vibrations = 1.1
    source = "capteur_test"
    localisation = "Chambre 1"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/webhook/diagnostic-frigo" `
    -Method POST `
    -Body $diagnostic `
    -ContentType "application/json"
```

---

## 🧠 Architecture du Système

### Flux de Données Complet

```
1️⃣  CAPTEURS / SIMULATEUR
    ↓
2️⃣  VALIDATION
    └─→ utils/validation.py (vérifie les seuils)
    ↓
3️⃣  AGENT IA - PRÉDICTION
    └─→ services/agent_ia.py (appelle l'API externe)
    ↓
4️⃣  DÉTECTION DE PANNE
    └─→ Si panne détectée → GEMINI
    ↓
5️⃣  ANALYSE GEMINI
    └─→ services/gemini_service.py (génère rapport détaillé)
    ↓
6️⃣  ALERTES TELEGRAM
    └─→ services/telegram_service.py (notifie utilisateur)
    ↓
7️⃣  APPRENTISSAGE CONTINU
    └─→ services/apprentissage_service.py (met à jour modèle)
    ↓
8️⃣  ARCHIVAGE
    └─→ Sauvegarde dans data/dataset_apprentissage.csv
    ↓
9️⃣  RÉENTRAÎNEMENT (si seuil atteint)
    └─→ Agent IA /retrain endpoint
```

### Services Clés

| Service | Responsabilité | Fichier |
|---------|-------------|---------|
| **Agent IA** | Prédiction de pannes | `services/agent_ia.py` |
| **Gemini** | Analyse intelligente | `services/gemini_service.py` |
| **Telegram** | Notifications | `services/telegram_service.py` |
| **Apprentissage** | ML adaptatif + archivage | `services/apprentissage_service.py` |
| **Validation** | Vérification data | `utils/validation.py` |
| **Helpers** | Utilitaires | `utils/helpers.py` |

---

## 📊 Endpoints Disponibles

### Health Check
```
GET /health
Response: {"status": "online", "version": "2.0.0"}
```

### Diagnostic Webhook (Principal)
```
POST /webhook/diagnostic-frigo
Body: {
    Température: float,
    Pression_BP: float,
    Pression_HP: float,
    Intensité_Compresseur: float,
    Intensité_Ventilateur: float,
    Humidité_Evaporateur: float,
    Vibrations: float,
    source: string,
    localisation: string
}
Response: Diagnostic complet avec détails
```

### Stats Apprentissage (BONUS)
```
GET /stats
Response: Statistiques d'apprentissage
```

---

## 🎮 Simulateur de Capteurs

Le fichier `simulateur.py` génère des données réalistes de capteurs avec pannes.

### Types de Pannes Simulées
- 🔴 Fuite de réfrigérant
- 🔴 Compresseur fatigué
- 🔴 Ventilateur encrassé
- 🔴 Détendeur bloqué
- 🔴 Évaporateur givré
- 🔴 Capteur défaillant
- 🔴 Surcharge électrique
- 🔴 Perte de connexion

### Comment ça marche
1. Génère des capteurs normaux
2. Chaque cycle: 30% chance de panne
3. Si panne: applique signature de panne
4. Durée: 300s par défaut
5. Envoie à l'API pour diagnostic

---

## 🔍 Fichiers de Données

### `data/compteur_apprentissage.json`
Suivi du ML continu
```json
{
    "total": 156,
    "pannes_par_type": {
        "Fuite_refrigerant": 23,
        "Compresseur_fatigue": 18,
        ...
    },
    "derniers_retraining": [
        {"timestamp": "...", "diagnostics_traites": 1000}
    ]
}
```

### `data/dataset_apprentissage.csv`
Base d'apprentissage
```
timestamp,diagnostic_id,source,localisation,panne_detectee,type_panne,score_confiance,Température,...
```

### `data/dernier_diagnostic.json`
Dernier diagnostic traité
```json
{
    "diagnostic_id": "DIAG_1234567890_ABC123",
    "timestamp": "2025-01-15T10:30:45Z",
    "panne_detectee": true,
    "type_panne": "Fuite_refrigerant",
    "donnees_capteurs": {...}
}
```

---

## 📈 Logs & Monitoring

### Fichier Log Principal
```
logs/diagnostic_frigo.log
```

### Commandes Utiles
```powershell
# Voir les 50 dernières lignes
Get-Content logs/diagnostic_frigo.log -Tail 50

# Voir les logs en temps réel
Get-Content logs/diagnostic_frigo.log -Wait

# Chercher les erreurs
Select-String "ERROR" logs/diagnostic_frigo.log
```

---

## ✅ Checklist de Vérification

- [ ] Python 3.11+ installé
- [ ] `pip install -r requirements.txt` exécuté
- [ ] `.env` configuré avec credentials
- [ ] `python init_data.py` exécuté
- [ ] `python app.py` lance sans erreur
- [ ] API accessible sur http://localhost:5000/health
- [ ] `python simulateur.py` envoie diagnostics
- [ ] Logs apparaissent dans `logs/diagnostic_frigo.log`
- [ ] Notifications Telegram reçues (si panne)
- [ ] Dataset commence à se remplir

---

## 🐛 Troubleshooting

### Erreur: "GEMINI_API_KEY non configurée"
```
✅ Solution: Éditer .env avec vraie clé API
```

### Erreur: "Impossible de se connecter à l'API"
```
✅ Solution: Vérifier que python app.py tourne dans autre terminal
```

### Erreur: "Telegram non configuré"
```
✅ Solution: Vérifier TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID dans .env
```

### Les données ne s'enregistrent pas
```
✅ Solution: Vérifier que data/ et logs/ existent et sont writable
```

---

## 📞 Support & Ressources

- **Documentation Gemini** : https://ai.google.dev/
- **Telegram Bot API** : https://core.telegram.org/bots
- **Flask Documentation** : https://flask.palletsprojects.com/
- **Pandas** : https://pandas.pydata.org/

---

## 🎯 Prochaines Étapes

1. ✅ **Phase 1 Complétée** : Structure et services implémentés
2. 🔄 **Phase 2** : Configuration des credentials
3. 🚀 **Phase 3** : Tester l'API avec le simulateur
4. 📊 **Phase 4** : Analyser les logs et données
5. 🔧 **Phase 5** : Ajuster les seuils selon vos besoins

---

**Dernière mise à jour :** 18 Novembre 2025
**Statut :** ✅ PRÊT POUR DÉPLOIEMENT
