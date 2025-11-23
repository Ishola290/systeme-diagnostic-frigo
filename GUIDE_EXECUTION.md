# Guide d'Exécution - Système de Diagnostic Frigo

## 🚀 Démarrage Rapide

### 1. **Prérequis**
- Python 3.8+
- pip (gestionnaire de paquets Python)
- Git

### 2. **Installation des dépendances**

#### Pour l'application principale (app.py):
```powershell
# Navigue dans le répertoire racine
cd c:\Users\hp\Desktop\systeme-diagnostic-frigo

# Installe les dépendances principales
pip install -r requirements.txt
```

#### Pour l'application web Chat (dossier chat):
```powershell
# Navigue dans le dossier chat
cd c:\Users\hp\Desktop\systeme-diagnostic-frigo\chat

# Installe les dépendances du chat
pip install -r requirements.txt
```

### 3. **Configuration des variables d'environnement**

#### Pour l'application principale:
```powershell
# Copie le fichier .env.example
copy .env.example .env

# Édite le .env avec tes clés API
# - GEMINI_API_KEY
# - TELEGRAM_BOT_TOKEN
# - TELEGRAM_CHAT_ID
```

#### Pour le chat web:
```powershell
cd chat

# Copie le fichier .env.example
copy .env.example .env

# Édite le .env avec:
# - SECRET_KEY (génère une clé aléatoire)
# - DATABASE_URL
# - MAIN_APP_URL (URL de app.py, ex: http://localhost:5000)
```

### 4. **Initialiser la base de données**

#### Application principale:
```powershell
# Depuis la racine
python init_data.py
```

#### Chat web:
```powershell
# Depuis le dossier chat
python init_db.py
```

---

## 📋 Exécution

### Option A: Exécution séparée (Développement)

#### Terminal 1 - Application principale:
```powershell
cd c:\Users\hp\Desktop\systeme-diagnostic-frigo
python app.py
```

**Sortie attendue:**
```
 * Running on http://127.0.0.1:5000
```

#### Terminal 2 - Application Chat Web:
```powershell
cd c:\Users\hp\Desktop\systeme-diagnostic-frigo\chat
python app_web.py
```

**Sortie attendue:**
```
 * Running on http://127.0.0.1:5001
```

### Option B: Docker Compose (Recommandé - Production)

#### Démarrage rapide:
```powershell
# Windows Batch
.\docker-start.bat

# Ou PowerShell (recommandé)
.\docker-run.ps1
```

**Avantages:**
- ✅ Données persistantes avec SQLite
- ✅ Volumes Docker nommés
- ✅ Prêt pour production
- ✅ Scalable avec PostgreSQL

**Accès:**
- Chat Web: http://localhost:5001
- App Principale: http://localhost:5000

**Commandes utiles:**
```powershell
# Voir les logs
.\docker-run.ps1 -Logs

# Arrêter
.\docker-run.ps1 -Down

# Nettoyer complètement
.\docker-run.ps1 -Clean

# Reconstruire
.\docker-run.ps1 -Build
```

Consulte `DOCKER_GUIDE.md` pour plus de détails.

### Option C: Exécution avec Docker Compose (Manuel)

```powershell
# Depuis la racine du projet
docker-compose up

# Ou en arrière-plan:
docker-compose up -d
```

**Accès:**
- Application principale: http://localhost:5000
- Chat Web: http://localhost:5001

### Option C: Exécution avec Gunicorn (Production)

#### Application principale:
```powershell
gunicorn --worker-class gevent --workers 4 --bind 0.0.0.0:5000 app:app
```

#### Chat Web:
```powershell
cd chat
gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:5001 app_web:app
```

---

## 🌐 Accès à l'Application

### Application Chat Web:
- **URL**: http://localhost:5001
- **Login par défaut**:
  - Email: `admin@example.com`
  - Mot de passe: `admin123`

### API principale:
- **URL**: http://localhost:5000
- **Documentation**: http://localhost:5000/api/docs (si disponible)

---

## 🧪 Tests

### Tester l'application principale:
```powershell
pytest tests/
```

### Tester le chat web:
```powershell
cd chat
pytest test_app.py
```

### Tester l'intégration:
```powershell
python chat/test_app.py --integration
```

---

## 🔌 Communication entre les apps

L'application Chat communique avec l'app principale via HTTP:

**Configuration** (dans `chat/.env`):
```
MAIN_APP_URL=http://localhost:5000
```

**Exemple d'appel:**
```python
import requests

# Récupérer un diagnostic
response = requests.get('http://localhost:5000/api/diagnostics/derniers')
data = response.json()
```

---

## 📊 Endpoints importants

### App principale (port 5000):
- `POST /api/diagnostic` - Lancer un diagnostic
- `GET /api/diagnostics/derniers` - Récupérer les derniers diagnostics
- `POST /api/chat/message` - Envoyer un message au chat IA

### Chat Web (port 5001):
- `GET /` - Interface web
- `POST /api/auth/login` - Authentification
- `GET /api/alerts` - Récupérer les alertes
- `GET /api/diagnostics` - Récupérer les diagnostics
- `WS /socket.io` - WebSocket pour le chat temps réel

---

## 🐛 Dépannage

### Port déjà utilisé:
```powershell
# Trouver quel processus utilise le port
netstat -ano | findstr :5000

# Tuer le processus (remplace PID)
taskkill /PID <PID> /F
```

### Erreur de base de données:
```powershell
# Réinitialiser la base de données
rm chat/instance/chat.db
python chat/init_db.py
```

### Erreur d'importation:
```powershell
# Réinstaller les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### WebSocket ne fonctionne pas:
```powershell
# Installe les dépendances WebSocket
pip install flask-socketio python-socketio python-engineio
pip install gevent gevent-websocket
```

---

## 📱 Déploiement

### Sur Render:

1. **Crée un account Render**
2. **Crée deux nouveaux services:**
   - Service 1: Application principale
   - Service 2: Chat Web
3. **Configure les variables d'environnement** dans Render
4. **Déploie** avec `deploy_render.sh`

```powershell
bash chat/deploy_render.sh
```

---

## 📝 Notes

- ✅ Les deux applications fonctionnent sur des ports différents
- ✅ Communication via HTTP REST + WebSocket
- ✅ Pas de surcharge système
- ✅ Authentification requise pour le chat
- ✅ Historique complet des diagnostics

---

## 🆘 Besoin d'aide?

- Vérifie les logs: `diagnostic_frigo.log` (app principale)
- Vérifie les logs: `chat/chat.log` (chat web)
- Consulte `INTEGRATION_GUIDE.md` pour l'intégration détaillée
