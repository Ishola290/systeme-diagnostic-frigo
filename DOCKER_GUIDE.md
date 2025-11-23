# 🐳 Guide Docker - Système Diagnostic Frigo

## 📋 Vue d'ensemble

Ce guide explique comment déployer l'application avec **Docker Compose** avec des **volumes persistants SQLite**.

---

## 🎯 Architecture Docker

```
┌─────────────────────────────────────────┐
│         Docker Compose                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┐ ┌──────────────┐ │
│  │  Chat Web        │ │  Main App    │ │
│  │  Port 5001       │ │  Port 5000   │ │
│  │  (Flask-SocketIO)│ │  (Flask)     │ │
│  └──────────────────┘ └──────────────┘ │
│         ↓                    ↓          │
│  ┌──────────────────┐ ┌──────────────┐ │
│  │  Chat Data Vol   │ │  Main Data   │ │
│  │  SQLite persist. │ │  Volume      │ │
│  └──────────────────┘ └──────────────┘ │
│                                         │
│  ┌──────────────────┐                  │
│  │  PostgreSQL      │ (optionnel)      │
│  │  Port 5432       │                  │
│  │  (Production)    │                  │
│  └──────────────────┘                  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 Démarrage Rapide

### Option 1: Batch (Windows)
```powershell
.\docker-start.bat
```

### Option 2: PowerShell (Windows - Recommandé)
```powershell
.\docker-run.ps1
```

### Option 3: Ligne de commande
```bash
docker-compose --env-file .env.docker up -d
```

---

## 📝 Configuration

### 1. Créer le fichier `.env.docker`

```bash
cp .env.docker.example .env.docker
```

Édite `.env.docker` et ajoute tes clés:

```env
SECRET_KEY=ta-cle-secrete-tres-longue
GEMINI_API_KEY=ton-api-key-gemini
TELEGRAM_BOT_TOKEN=ton-bot-token
TELEGRAM_CHAT_ID=ton-chat-id
```

### 2. Vérifier la configuration

```bash
docker-compose config
```

---

## 🎮 Commandes Principales

### Démarrer les services
```bash
docker-compose --env-file .env.docker up -d
```

### Voir les logs
```bash
# Chat Web
docker-compose logs -f chat-web

# App Principale
docker-compose logs -f main-app

# Tous les services
docker-compose logs -f
```

### Redémarrer les services
```bash
docker-compose restart
```

### Arrêter les services
```bash
docker-compose down
```

### Arrêter et supprimer les données
```bash
docker-compose down -v
```

### Reconstruire les images
```bash
docker-compose build --no-cache
```

---

## 📊 Volumes Persistants

Les données sont stockées dans des **volumes Docker nommés**:

| Volume | Contenu | Persistance |
|--------|---------|-------------|
| `chat-data` | Base SQLite chat | ✅ Persistant |
| `chat-logs` | Logs du chat | ✅ Persistant |
| `main-data` | Données app principale | ✅ Persistant |
| `main-logs` | Logs app principale | ✅ Persistant |
| `postgres-data` | Base PostgreSQL | ✅ Persistant (si utilisé) |

### Voir les volumes
```bash
docker volume ls
```

### Inspecter un volume
```bash
docker volume inspect frigo-diagnostic_chat-data
```

### Sauvegarder les données
```bash
# Sauvegarder la base SQLite
docker run --rm -v frigo-diagnostic_chat-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/chat-data-backup.tar.gz -C /data .

# Restaurer
docker run --rm -v frigo-diagnostic_chat-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/chat-data-backup.tar.gz -C /data
```

---

## 🌐 Accès à l'Application

Une fois les conteneurs en cours d'exécution:

### Chat Web
- **URL**: http://localhost:5001
- **Login**: admin@example.com / admin123

### App Principale
- **URL**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

---

## 🐛 Dépannage

### Conteneur ne démarre pas
```bash
# Voir les logs
docker-compose logs chat-web

# Rebuild
docker-compose build --no-cache chat-web
```

### Port déjà utilisé
```bash
# Trouver le processus
netstat -ano | findstr :5001

# Ou utiliser un autre port dans docker-compose.yml
```

### Problème de base de données
```bash
# Supprimer le volume et recommencer
docker volume rm frigo-diagnostic_chat-data

# Redémarrer
docker-compose restart chat-web
```

### Réinitialiser l'admin
```bash
# Exécuter le script dans le conteneur
docker-compose exec chat-web python create_admin.py
```

---

## 📦 Ajouter PostgreSQL (Production)

Pour utiliser PostgreSQL au lieu de SQLite:

### 1. Démarrer PostgreSQL
```bash
docker-compose --env-file .env.docker --profile postgres up -d postgres
```

### 2. Configurer `.env.docker`
```env
DATABASE_URL=postgresql://frigo:secure-password@postgres:5432/frigo_chat
POSTGRES_USER=frigo
POSTGRES_PASSWORD=secure-password
```

### 3. Modifier `chat/config.py`
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chat_app.db'
```

### 4. Redémarrer
```bash
docker-compose down
docker-compose --profile postgres up -d
```

---

## 🔄 Mise à jour de l'application

### Après modification du code
```bash
# Rebuild et redémarrer
docker-compose build chat-web
docker-compose up -d chat-web
```

### Mettre à jour les dépendances
```bash
# Modifier requirements.txt
pip freeze > requirements.txt

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 Monitoring

### Voir l'utilisation des ressources
```bash
docker stats
```

### Inspecter un conteneur
```bash
docker inspect frigo-chat-web
```

### Vérifier la santé
```bash
docker-compose ps
```

---

## 🔐 Sécurité Production

### Avant le déploiement:

1. **Changer SECRET_KEY**
   ```env
   SECRET_KEY=your-strong-random-key-here
   ```

2. **Changer les mots de passe**
   ```env
   POSTGRES_PASSWORD=strong-password
   ```

3. **Configurer HTTPS** (Nginx reverse proxy)

4. **Activer les logs de sécurité**
   ```bash
   docker-compose logs | grep ERROR
   ```

---

## 🚢 Déploiement Render (Future)

Quand tu seras prêt pour Render:

```bash
# Créer deux services Render:
# 1. Service 1: App Principale
#    Build Command: python -m pip install -r requirements.txt && python app.py
#    Start Command: python app.py
#    
# 2. Service 2: Chat Web
#    Build Command: python -m pip install -r chat/requirements.txt
#    Start Command: python chat/create_admin.py && gunicorn -w 2 -b 0.0.0.0:5001 chat.app_web:app
#    
# PostgreSQL sur Render sera alors utilisé
```

---

## 📞 Support

### Logs détaillés
```bash
docker-compose logs -f --tail=100
```

### Exécuter une commande dans le conteneur
```bash
docker-compose exec chat-web python
docker-compose exec main-app bash
```

### Accéder au shell du conteneur
```bash
docker-compose exec chat-web /bin/bash
```

---

## ✅ Checklist Déploiement

- [ ] Docker installé
- [ ] docker-compose installé
- [ ] `.env.docker` configuré avec clés API
- [ ] Ports 5000, 5001 disponibles
- [ ] Fichiers Dockerfile présents
- [ ] `docker-compose.yml` valide
- [ ] Volumes créés
- [ ] Services en cours d'exécution
- [ ] Admin créé
- [ ] Accessible via navigateur

---

## 🎉 C'est tout!

Tu as maintenant une application **entièrement dockerisée** avec des données **persistantes** et **prête pour la production**! 🚀
