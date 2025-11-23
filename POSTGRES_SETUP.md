# Configuration PostgreSQL pour le Système Diagnostic Frigo

## Installation locale (Windows)

### Option 1 : PostgreSQL installé sur la machine

```powershell
# 1. Télécharger et installer PostgreSQL 16
# https://www.postgresql.org/download/windows/

# 2. Après installation, créer une base de données
$env:PGPASSWORD = "votre_mot_de_passe"
psql -U postgres -c "CREATE DATABASE chat_app;"
psql -U postgres -c "CREATE USER frigo_user WITH PASSWORD 'frigo_secure_pass_change_me';"
psql -U postgres -c "ALTER ROLE frigo_user CREATEDB;"
psql -U postgres -d chat_app -c "GRANT ALL PRIVILEGES ON SCHEMA public TO frigo_user;"

# 3. Configurer DATABASE_URL
$env:DATABASE_URL = "postgresql://frigo_user:frigo_secure_pass_change_me@localhost:5432/chat_app"
$env:FLASK_ENV = "development"

# 4. Lancer la migration
cd chat
python migrate_to_postgres.py

# 5. Lancer l'app
cd ..
python -m flask --app chat.app_web run --port 5001
```

### Option 2 : PostgreSQL en Docker (Recommandé)

```powershell
# 1. Créer un conteneur PostgreSQL
docker run --name frigo-postgres `
  -e POSTGRES_USER=frigo_user `
  -e POSTGRES_PASSWORD=frigo_secure_pass_change_me `
  -e POSTGRES_DB=chat_app `
  -p 5432:5432 `
  -d postgres:16-alpine

# 2. Vérifier la connexion
docker exec frigo-postgres psql -U frigo_user -d chat_app -c "SELECT 1;"

# 3. Configurer .env
@'
DATABASE_URL=postgresql://frigo_user:frigo_secure_pass_change_me@localhost:5432/chat_app
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
'@ | Out-File -FilePath .env -Encoding utf8

# 4. Lancer la migration
cd chat
python migrate_to_postgres.py

# 5. Lancer les services
cd ..
python app.py  # Terminal 1 (port 5000)
cd chat && python app_web.py  # Terminal 2 (port 5001)
cd ../gpt && python app_ia.py  # Terminal 3 (port 5002)
```

### Option 3 : Docker Compose (Production-ready)

```powershell
# 1. Vérifier docker-compose.yml (ou docker-compose-postgres.yml)
# 2. Créer le fichier .env
@'
FLASK_ENV=development
DB_USER=frigo_user
DB_PASSWORD=frigo_secure_pass_change_me
DB_NAME=chat_app
DATABASE_URL=postgresql://frigo_user:frigo_secure_pass_change_me@postgres:5432/chat_app
IA_MODEL=gpt2
'@ | Out-File -FilePath .env -Encoding utf8

# 3. Lancer les services
docker-compose -f docker-compose-postgres.yml up -d

# 4. Vérifier la santé
docker-compose -f docker-compose-postgres.yml ps
docker logs frigo-postgres
docker logs frigo-chat

# 5. Accéder à l'application
# Chat Web: http://localhost:5001
# API App: http://localhost:5000
# IA API: http://localhost:5002
```

## Configuration .env

```ini
# Base de données
DATABASE_URL=postgresql://frigo_user:frigo_secure_pass_change_me@localhost:5432/chat_app
FLASK_ENV=development

# Flask
SECRET_KEY=dev-secret-key-change-in-production

# Services (dev local)
MAIN_APP_URL=http://localhost:5000
CHAT_API_URL=http://localhost:5001
IA_SERVICE_URL=http://localhost:5002

# Modèle IA
IA_MODEL=gpt2
HF_LOCAL_MODEL_PATH=./models/gpt2

# Telegram (optionnel)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Commandes utiles

```powershell
# Vérifier la connexion à PostgreSQL
psql -U frigo_user -d chat_app -h localhost

# Voir les tables
\dt

# Voir les colonnes d'une table
\d alerts

# Dumper la base de données
pg_dump -U frigo_user -d chat_app -F c -f backup.dump

# Restaurer la base de données
pg_restore -U frigo_user -d chat_app backup.dump

# Arrêter le conteneur Docker
docker stop frigo-postgres

# Redémarrer avec des données persistantes
docker start frigo-postgres
```

## Troubleshooting

### Erreur: "psycopg2 - No such file or directory"
```powershell
pip install psycopg2-binary
```

### Erreur: "could not translate host name postgres"
- Vous utilisez `docker-compose` ? Assurez-vous que les services sont sur le même réseau.
- Localement ? Utilisez `localhost` au lieu de `postgres`.

### Erreur: "FATAL: role does not exist"
```powershell
# Créer l'utilisateur
docker exec frigo-postgres createuser -U postgres frigo_user
docker exec frigo-postgres psql -U postgres -c "ALTER USER frigo_user WITH PASSWORD 'frigo_secure_pass_change_me';"
```

### Base de données vide après migration
```powershell
cd chat
python migrate_to_postgres.py
```

## Performance & Maintenance

### Index pour les requêtes courantes
```sql
CREATE INDEX idx_alerts_timestamp ON alerts(created_at DESC);
CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_messages_chat ON messages(user_id, created_at DESC);
```

### Backup automatique
```powershell
# Script PowerShell pour backup quotidien
$BackupPath = "C:\Backups"
$Database = "chat_app"
$User = "frigo_user"
$Date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BackupFile = "$BackupPath\chat_app_$Date.dump"

pg_dump -U $User -d $Database -F c -f $BackupFile
Write-Host "✅ Backup créé: $BackupFile"
```

## Migration depuis SQLite

```powershell
# 1. Exporter les données depuis SQLite
# (Le script migrate_to_postgres.py gère cela automatiquement)

# 2. Si migration manuelle nécessaire:
# - Exporter SQLite: sqlite3 chat_app.db ".dump" > dump.sql
# - Adapter la syntaxe SQL (SQLite → PostgreSQL)
# - Importer: psql -U frigo_user -d chat_app -f dump.sql
```

## Prochaines étapes

1. ✅ PostgreSQL local configuré avec docker-compose
2. ⏳ Tester les migrations
3. ⏳ Vérifier les performances (indexes)
4. ⏳ Configurer sur Render (Render Database addon)
5. ⏳ Backup & monitoring
