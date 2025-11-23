# 🐘 PostgreSQL - Quick Start

**⏱️ Durée totale: ~5-10 minutes**

## Étape 1: Lancer PostgreSQL en Docker

```powershell
# Depuis C:\Users\hp\Desktop\systeme-diagnostic-frigo
.\setup-postgres.ps1 -Action setup
```

✅ **Résultat attendu:**
- Conteneur `frigo-postgres` créé et lancé
- Volume `frigo-postgres-data` créé pour la persistance
- PostgreSQL accessible sur `localhost:5432`

## Étape 2: Effectuer la migration

```powershell
.\setup-postgres.ps1 -Action migrate
```

✅ **Résultat attendu:**
- Tables créées dans PostgreSQL
- Utilisateur admin créé (login: `admin`, mot de passe: `admin123`)
- Base de données initialisée

## Étape 3: Vérifier la connexion

```powershell
.\setup-postgres.ps1 -Action check
```

✅ **Résultat attendu:**
```
✅ Connexion à PostgreSQL réussie!
 ?column?
----------
        1
(1 row)
```

## Étape 4: Lancer les services

Ouvrir 3 terminaux PowerShell:

### Terminal 1 - Application principale
```powershell
$env:DATABASE_URL = "postgresql://frigo_user:frigo_secure_pass_change_me@localhost:5432/chat_app"
$env:FLASK_ENV = "development"
python app.py
```

### Terminal 2 - Chat Web UI
```powershell
$env:DATABASE_URL = "postgresql://frigo_user:frigo_secure_pass_change_me@localhost:5432/chat_app"
cd chat
python app_web.py
```

### Terminal 3 - IA Service
```powershell
$env:IA_MODEL = "gpt2"
$env:HF_LOCAL_MODEL_PATH = "./models/gpt2"
cd gpt
python app_ia.py
```

## Étape 5: Tester l'application

Ouvrir un navigateur:
- **Chat Web**: http://localhost:5001
- **API App**: http://localhost:5000
- **IA API**: http://localhost:5002/health

## 🔧 Commandes utiles

```powershell
# Démarrer PostgreSQL
.\setup-postgres.ps1 -Action start

# Arrêter PostgreSQL
.\setup-postgres.ps1 -Action stop

# Redémarrer PostgreSQL
.\setup-postgres.ps1 -Action restart

# Voir les logs
docker logs -f frigo-postgres

# Se connecter à la base directement
docker exec -it frigo-postgres psql -U frigo_user -d chat_app
```

## 📊 Vérifier les tables

```powershell
docker exec -it frigo-postgres psql -U frigo_user -d chat_app -c "\dt"
```

## ⚙️ Configuration pour Docker Compose

Si vous voulez utiliser Docker Compose (tout en un):

```powershell
# Créer le fichier .env
@'
FLASK_ENV=development
DB_USER=frigo_user
DB_PASSWORD=frigo_secure_pass_change_me
DB_NAME=chat_app
DATABASE_URL=postgresql://frigo_user:frigo_secure_pass_change_me@postgres:5432/chat_app
IA_MODEL=gpt2
'@ | Out-File .env -Encoding utf8

# Lancer tous les services
docker-compose -f docker-compose-postgres.yml up -d

# Vérifier l'état
docker-compose -f docker-compose-postgres.yml ps

# Logs
docker-compose -f docker-compose-postgres.yml logs -f chat
```

## 🚀 Configuration Render (Production)

Une fois testé localement:

1. **Ajouter PostgreSQL sur Render:**
   - Aller sur https://dashboard.render.com
   - Créer une nouvelle "PostgreSQL Database"
   - Copier la connection string (DATABASE_URL)

2. **Configurer les services Render:**
   - Service App: `python app.py`
   - Service Chat: `cd chat && python app_web.py`
   - Service IA: `cd gpt && python app_ia.py`
   - Tous avec `DATABASE_URL` pointant vers le PostgreSQL Render

3. **Variables d'environnement Render:**
   ```
   DATABASE_URL=postgresql://...@<host>/<db>
   FLASK_ENV=production
   IA_MODEL=phi
   HF_LOCAL_MODEL_PATH=/app/models/phi-2
   ```

## 📝 Fichiers créés/modifiés

✅ `chat/requirements.txt` - Ajout `psycopg2-binary`, `Flask-Migrate`
✅ `chat/app_web.py` - Support PostgreSQL avec fallback SQLite
✅ `chat/migrate_to_postgres.py` - Script de migration
✅ `chat/init_postgres.sql` - SQL d'initialisation
✅ `docker-compose-postgres.yml` - Docker Compose complet
✅ `.env.example` - Exemple de configuration
✅ `POSTGRES_SETUP.md` - Documentation détaillée
✅ `setup-postgres.ps1` - Script PowerShell pour setup
✅ Cette page `POSTGRES_QUICKSTART.md`

---

**💡 Conseil:** Testez localement avec PostgreSQL avant de pousser en production sur Render!
