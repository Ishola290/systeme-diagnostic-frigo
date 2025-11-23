# 📝 SETUP CHATBOTIQUE - Étapes de Démarrage

## ✅ Ce qui a été créé

### 1. **Application Web Flask** (`chat/app_web.py`)
- ✅ Backend Flask complet avec authentification
- ✅ Models SQLAlchemy: User, Alert, Message, Diagnostic
- ✅ Routes API pour alertes, diagnostics, messages
- ✅ WebSocket pour communication en temps réel
- ✅ Support de la base de données SQLite (production-ready avec PostgreSQL)

### 2. **Frontend Moderne** 
- ✅ `chat/templates/` - Pages HTML
  - `login.html` - Page de connexion
  - `register.html` - Page d'enregistrement
  - `dashboard.html` - Dashboard principal
- ✅ `chat/static/` - Ressources statiques
  - `style.css` - Styles responsifs
  - `dashboard.js` - Logique JavaScript + WebSocket

### 3. **Intégration avec app.py**
- ✅ `chat_integration.py` - Module pour communiquer
- ✅ 4 méthodes principales:
  - `send_alert()` - Envoyer une alerte
  - `send_diagnostic()` - Envoyer un diagnostic
  - `send_message()` - Envoyer un message
  - `health_check()` - Vérifier la connexion

### 4. **Infrastructure**
- ✅ `requirements.txt` - Dépendances
- ✅ `config.py` - Configuration
- ✅ `init_db.py` - Script d'initialisation BD
- ✅ `Dockerfile` + `docker-compose.yml` - Déploiement
- ✅ `.gitignore` - Fichiers à ignorer
- ✅ Documentation complète

## 🚀 Démarrage Rapide (Local)

### 1. Installer les dépendances

```powershell
cd chat
pip install -r requirements.txt
```

### 2. Initialiser la base de données

```powershell
python init_db.py
```

Cela crée un utilisateur admin:
- Username: `admin`
- Password: `admin123`

### 3. Démarrer le serveur

```powershell
python app_web.py
```

La web app sera accessible à: **http://localhost:5001**

### 4. Vérifier que app.py fonctionne

```powershell
# Dans un autre terminal
python app.py
```

app.py doit être sur: **http://localhost:5000**

## 🔌 Tester la Communication

### Tester directement

```python
# Dans une session Python
import requests

# Envoyer une alerte
response = requests.post('http://localhost:5001/api/receive-alert', json={
    'title': 'Test Alerte',
    'message': 'Ceci est un test',
    'severity': 'high'
})
print(response.status_code)  # Doit être 201
```

### Intégrer dans app.py

```python
# app.py
from chat_integration import init_chat_integration

chat_web = init_chat_integration('http://localhost:5001')

# Dans votre code de diagnostic
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    # ... votre code ...
    
    # Envoyer une alerte si problème
    chat_web.send_alert(
        title='Erreur Frigo',
        message='Température anormale',
        severity='critical'
    )
```

## 🌐 Déploiement sur Render

### Étape 1: Pousser le code sur GitHub

```powershell
git add .
git commit -m "Add web chat application"
git push origin main
```

### Étape 2: Créer un service Render

1. Aller sur https://render.com
2. Cliquer "New Web Service"
3. Connecter votre repo GitHub
4. Configurer:
   - **Name**: frigo-chat-web
   - **Branch**: main
   - **Build Command**: `pip install -r chat/requirements.txt`
   - **Start Command**: `cd chat && python app_web.py`

### Étape 3: Ajouter les variables d'environnement

Dans Render Dashboard → Environment:

```
FLASK_ENV=production
SECRET_KEY=<générer avec: python -c "import secrets; print(secrets.token_hex(32))">
MAIN_APP_URL=<URL de votre app.py en production>
SQLALCHEMY_DATABASE_URI=<PostgreSQL URL de Render>
```

### Étape 4: Déployer

Render va automatiquement déployer à chaque push sur main!

## 📊 Fonctionnalités

### Dashboard
- 💬 **Chat** - Communication avec le système
- 🚨 **Alertes** - Voir et gérer les alertes
- 📋 **Diagnostics** - Historique des diagnostics
- 📊 **Stats** - Vue d'ensemble

### Sécurité
- ✅ Authentification username/email/password
- ✅ Hachage des mots de passe (werkzeug.security)
- ✅ Sessions sécurisées
- ✅ CSRF protection possible

### Real-time
- ✅ WebSocket pour messages instantanés
- ✅ Notifications de nouvelles alertes
- ✅ Synchronisation automatique

## 📁 Structure Complète

```
chat/
├── app_web.py              # Application principale
├── config.py               # Configuration
├── init_db.py              # Initialisation BD
├── test_app.py             # Tests unitaires
├── requirements.txt        # Dépendances
├── .env.example            # Variables exemple
├── .gitignore              # Fichiers à ignorer
├── Dockerfile              # Image Docker
├── README.md               # Documentation
├── INTEGRATION_GUIDE.md    # Guide d'intégration
├── deploy_render.sh        # Script Render
├── templates/
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
└── static/
    ├── style.css
    └── dashboard.js

Racine:
├── chat_integration.py     # Module intégration
├── docker-compose.yml      # Composition Docker
└── Dockerfile              # Image app.py
```

## 🔄 Workflows Típiques

### Workflow 1: Alerte en temps réel

```
1. Diagnostic détecte une erreur
2. app.py appelle chat_web.send_alert()
3. chat_web envoie via POST à /api/receive-alert
4. WebSocket émet 'new_alert' à tous les utilisateurs
5. Dashboard reçoit et affiche l'alerte
6. Utilisateur voit la notification
```

### Workflow 2: Chat avec le système

```
1. Utilisateur tape un message dans le chat web
2. Dashboard émet 'send_message' via WebSocket
3. Message sauvegardé en base de données
4. JavaScript envoie le message à app.py via HTTP
5. app.py traite la requête via l'IA
6. Réponse renvoyée au chat web
7. Dashboard reçoit et affiche la réponse
```

## ⚙️ Configuration Avancée

### Utiliser PostgreSQL (Production)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/frigo_chat
```

### CORS pour domaine spécifique

```python
# config.py
SOCKETIO_CORS_ALLOWED_ORIGINS = ["https://example.com"]
```

### Rate Limiting

```python
# app_web.py
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/receive-alert', methods=['POST'])
@limiter.limit("100 per hour")
def receive_alert():
    ...
```

## 🆘 Dépannage

### Erreur: "Cannot reach app.py"
```powershell
# Vérifier que app.py fonctionne
python -m requests http://localhost:5000
```

### Erreur: "Database is locked"
```powershell
# Supprimer la base et réinitialiser
del chat_app.db
python init_db.py
```

### WebSocket ne se connecte pas
- Vérifier le firewall
- Vérifier les logs du navigateur (F12)
- Vérifier que socketio est bien importé

## 📞 Prochaines Étapes

1. ✅ **Tester localement**
   ```bash
   python chat/app_web.py
   python app.py
   ```

2. ✅ **Intégrer dans app.py**
   - Ajouter `from chat_integration import init_chat_integration`
   - Initialiser `chat_web`
   - Appeler `chat_web.send_alert()` où nécessaire

3. ✅ **Déployer sur Render**
   - Créer un nouveau service
   - Configurer les variables d'environnement
   - Tester en production

4. ✅ **Configurer le domaine**
   - Ajouter un domaine personnalisé
   - Configurer HTTPS/SSL

5. ✅ **Mettre en place les backups**
   - Sauvegardes automatiques de la BD
   - Logs persistants

## 📚 Documentation

- [README Chat Web](./chat/README.md)
- [Guide d'Intégration](./chat/INTEGRATION_GUIDE.md)
- [Configuration](./chat/config.py)
- [Code d'Intégration](./chat_integration.py)

## 🎉 Succès!

Votre système de diagnostic frigo est maintenant équipé d'une interface web moderne et sécurisée pour:
- ✅ Recevoir les alertes
- ✅ Consulter l'historique
- ✅ Discuter avec le système
- ✅ Suivre les diagnostics

À vous de jouer! 🍺
