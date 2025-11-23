# 🍺 Chat Web Application - Diagnostic Frigo

Application web Flask pour remplacer Telegram dans la réception des alertes et la communication avec le système de diagnostic.

## 🚀 Caractéristiques

- ✅ **Authentification utilisateur** - Login/Register sécurisé
- ✅ **Chat en temps réel** - WebSocket pour communication instantanée
- ✅ **Dashboard d'alertes** - Affichage et gestion des alertes
- ✅ **Historique diagnostics** - Suivi des diagnostics effectués
- ✅ **Notifications** - Alertes critiques en temps réel
- ✅ **Statistiques** - Vue d'ensemble du système
- ✅ **Interface minimaliste** - Design épuré et efficace

## 📋 Prérequis

- Python 3.8+
- pip
- Connexion à l'app principale (app.py) via HTTP

## 🔧 Installation

### 1. Installer les dépendances

```powershell
cd chat
pip install -r requirements.txt
```

### 2. Configurer l'environnement

```powershell
Copy-Item .env.example .env
# Éditer .env avec vos paramètres
```

### 3. Initialiser la base de données

```powershell
python init_db.py
```

Cela va créer un utilisateur admin:
- **Username**: admin
- **Password**: admin123

### 4. Démarrer le serveur

```powershell
python app_web.py
```

L'application sera accessible à: **http://localhost:5001**

## 🌐 Configuration

### Variables d'environnement (.env)

```env
# Environment
FLASK_ENV=development

# Clé secrète (générer une clé forte en production)
SECRET_KEY=votre-clé-secrète

# URL de l'application principale
MAIN_APP_URL=http://localhost:5000

# Base de données (optionnel)
DATABASE_URL=sqlite:///chat_app.db

# Pour production avec PostgreSQL:
# DATABASE_URL=postgresql://user:password@host/dbname
```

## 🔌 Communication avec app.py

L'application web communique avec `app.py` via HTTP pour:

1. **Recevoir les messages du chat** → POST `/api/chat`
2. **Recevoir les alertes** → POST `/api/receive-alert`
3. **Recevoir les diagnostics** → POST `/api/receive-diagnostic`

### Exemple d'intégration dans app.py

```python
import requests

# Envoyer une alerte
requests.post('http://localhost:5001/api/receive-alert', json={
    'type': 'error',
    'title': 'Erreur température',
    'message': 'Température trop élevée!',
    'severity': 'critical',
    'diagnostic_id': 'DIAG-123'
})

# Envoyer un diagnostic
requests.post('http://localhost:5001/api/receive-diagnostic', json={
    'diagnostic_id': 'DIAG-123',
    'description': 'Diagnostic du compresseur',
    'result': {'status': 'OK'},
    'status': 'completed'
})
```

## 📱 Utilisation

### 1. S'enregistrer

- Cliquer sur "S'enregistrer" sur la page de login
- Remplir le formulaire (username, email, password)
- Confirmer

### 2. Se connecter

- Entrer vos identifiants
- Cliquer "Se connecter"

### 3. Utiliser le Dashboard

#### 💬 Chat
- Poser des questions au système
- Recevoir des réponses en temps réel
- Historique des messages conservé

#### 🚨 Alertes
- Voir toutes les alertes du système
- Marquer comme lues
- Filtrer par sévérité

#### 📋 Diagnostics
- Historique de tous les diagnostics
- Voir les détails des résultats
- Suivre le statut (pending, completed, error)

#### 📊 Stats
- Vue d'ensemble du système
- Nombre d'alertes, messages, diagnostics
- Alertes critiques non lues

## 🚀 Déploiement

### Sur Render

1. **Pousser le code sur GitHub**

```powershell
git add .
git commit -m "Add web chat application"
git push
```

2. **Créer un nouveau service sur Render**
   - Aller sur https://render.com
   - Créer un "Web Service"
   - Connecter votre repo GitHub
   - Configurer:
     - **Build Command**: `pip install -r chat/requirements.txt`
     - **Start Command**: `cd chat && python app_web.py`
     - **Environment**: ajouter les variables du `.env`

3. **Configurer la base de données**
   - Utiliser PostgreSQL de Render (recommandé)
   - Ajouter `DATABASE_URL` à partir des variables Render

### Avec Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app/chat

COPY chat/requirements.txt .
RUN pip install -r requirements.txt

COPY chat/ .

CMD ["python", "app_web.py"]
```

```bash
docker build -t frigo-chat .
docker run -p 5001:5001 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secret \
  -e MAIN_APP_URL=http://api.example.com \
  frigo-chat
```

## 🔐 Sécurité

### En production

1. **Générer une SECRET_KEY forte**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

2. **Utiliser HTTPS**
   ```env
   SESSION_COOKIE_SECURE=True
   ```

3. **Utiliser une base de données robuste**
   ```env
   DATABASE_URL=postgresql://user:pass@host/db
   ```

4. **Ajouter un firewall**
   - Restreindre l'accès aux endpoints système
   - Valider les requêtes de l'app principale

5. **Rate limiting**
   - Implémenter rate limiting sur `/api/receive-alert`
   - Implémenter rate limiting sur `/api/chat`

## 📊 Architecture

```
chat/
├── app_web.py           # Application Flask principale
├── config.py            # Configuration
├── init_db.py           # Initialisation BD
├── requirements.txt     # Dépendances
├── .env.example         # Variables exemple
├── templates/
│   ├── login.html       # Page de connexion
│   ├── register.html    # Page d'enregistrement
│   └── dashboard.html   # Dashboard principal
└── static/
    ├── style.css        # Styles CSS
    └── dashboard.js     # Logique JavaScript
```

## 🐛 Dépannage

### Erreur: "Cannot connect to main app"
- Vérifier que app.py est en cours d'exécution
- Vérifier l'URL dans `MAIN_APP_URL`

### Erreur: "Database is locked"
- Fermer les autres sessions Flask
- Supprimer `chat_app.db` et réinitialiser

### WebSocket ne se connecte pas
- Vérifier que SocketIO est bien configuré
- Vérifier CORS_ORIGINS

## 📞 Support

Pour plus d'aide, consultez:
- [Documentation Flask](https://flask.palletsprojects.com)
- [Documentation Flask-SocketIO](https://flask-socketio.readthedocs.io)
- [Documentation SQLAlchemy](https://docs.sqlalchemy.org)

## 📄 Licence

Même licence que le projet principal
