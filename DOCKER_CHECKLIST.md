# 📋 Checklist Déploiement Docker

## ✅ Phase 1: Vérification Prérequis

- [ ] Docker installé (`docker --version`)
- [ ] Docker Compose installé (`docker-compose --version`)
- [ ] Python 3.8+ disponible
- [ ] Ports 5000, 5001 libres
- [ ] Au moins 2 GB RAM disponible
- [ ] Au moins 5 GB espace disque

## ✅ Phase 2: Configuration

- [ ] Fichier `.env.docker` copié depuis `.env.docker.example`
- [ ] `GEMINI_API_KEY` configurée
- [ ] `TELEGRAM_BOT_TOKEN` configuré
- [ ] `TELEGRAM_CHAT_ID` configuré
- [ ] `SECRET_KEY` générée (changée de "dev-secret-key")
- [ ] `.env.docker` non commité sur git

## ✅ Phase 3: Fichiers

- [ ] `Dockerfile` (racine) ✓
- [ ] `chat/Dockerfile` ✓
- [ ] `docker-compose.yml` ✓
- [ ] `.dockerignore` ✓
- [ ] `chat/.dockerignore` ✓
- [ ] `.env.docker` configuré
- [ ] Tous les fichiers Python présents

## ✅ Phase 4: Vérification Syntaxe

```powershell
# Exécuter le vérificateur
python verify_docker.py
```

- [ ] Résultat: "✅ Configuration Docker prête!"

## ✅ Phase 5: Premier Démarrage

```powershell
# Démarrer Docker
.\docker-run.ps1

# Ou manuel
docker-compose --env-file .env.docker up -d
```

- [ ] Pas d'erreur au démarrage
- [ ] Conteneurs créés
- [ ] Volumes créés

## ✅ Phase 6: Vérification des Services

```powershell
# Voir l'état
docker-compose ps

# Vérifier les logs
docker-compose logs chat-web
docker-compose logs main-app
```

- [ ] Chat Web: `Up` ✓
- [ ] Main App: `Up` ✓
- [ ] Pas d'erreurs critiques

## ✅ Phase 7: Accès Web

- [ ] Chat Web accessible: http://localhost:5001
- [ ] App Principale accessible: http://localhost:5000
- [ ] Login fonctionne (admin@example.com / admin123)
- [ ] Chat répond aux messages
- [ ] Pas d'erreur 500

## ✅ Phase 8: Persistance Données

```powershell
# Vérifier les volumes
docker volume ls
```

- [ ] `frigo-diagnostic_chat-data` existe
- [ ] `frigo-diagnostic_main-data` existe
- [ ] `frigo-diagnostic_chat-logs` existe

## ✅ Phase 9: Test Persistance

```powershell
# Créer un test
# 1. Envoyer un message dans le chat
# 2. Créer un utilisateur
# 3. Arrêter les conteneurs
.\docker-run.ps1 -Down

# 4. Redémarrer
.\docker-run.ps1

# 5. Vérifier que les données sont toujours là
```

- [ ] Données persistées après redémarrage
- [ ] Admin toujours présent
- [ ] Messages conservés

## ✅ Phase 10: Logs et Monitoring

```powershell
# Voir les logs en temps réel
.\docker-run.ps1 -Logs
```

- [ ] Logs accessible et lisibles
- [ ] Pas d'erreurs répétitives
- [ ] Health checks passent

## ✅ Phase 11: Nettoyage et Sécurité

- [ ] `.env.docker` n'est pas committé
- [ ] Pas de clés API en dur dans les fichiers
- [ ] `SECRET_KEY` changée pour production
- [ ] Mots de passe PostgreSQL changés

## ✅ Phase 12: Documentation

- [ ] `DOCKER_GUIDE.md` lu et compris
- [ ] `SETUP_DOCKER_COMPLETE.md` consulté
- [ ] Commandes principales mémorisées
- [ ] Procédures de dépannage connues

---

## 🚀 Déploiement Production

Une fois les phases 1-12 complétées et testées en local:

### Pour Render:

- [ ] Compte Render créé
- [ ] Service #1 créé (App Principale)
- [ ] Service #2 créé (Chat Web)
- [ ] Variables d'environnement configurées
- [ ] PostgreSQL Render configuré
- [ ] Domaines personnalisés (optionnel)
- [ ] SSL/HTTPS activé

### Pré-déploiement:

- [ ] Code committé et pushé
- [ ] Tests en local passés
- [ ] Base de données nettoyée
- [ ] Logs archivés
- [ ] Backup des données locales

---

## 📞 Points de Contrôle Importants

| Point | État | Notes |
|-------|------|-------|
| Docker installé | ✓ | Version 20+ |
| docker-compose | ✓ | Version 2+ |
| Ports libres | ✓ | 5000, 5001 |
| Config .env | ✓ | Non committé |
| Conteneurs up | ✓ | Tous running |
| Accès web | ✓ | 200 OK |
| Persistance | ✓ | Volumes OK |
| Admin login | ✓ | Marche bien |
| Logs clairs | ✓ | Pas d'erreurs |
| Production | ✓ | Quand prêt |

---

## 🎯 Résumé Quick Start

```powershell
# 1. Configuration (une fois)
cp .env.docker.example .env.docker
# Édite .env.docker

# 2. Vérification
python verify_docker.py

# 3. Démarrage
.\docker-run.ps1

# 4. Accès
# Chat: http://localhost:5001
# Login: admin@example.com / admin123

# 5. Logs
.\docker-run.ps1 -Logs

# 6. Arrêt
.\docker-run.ps1 -Down
```

---

## ✨ C'est Prêt!

Tu as maintenant une application **production-ready** avec Docker! 🎉

Besoin d'aide? Consulte `DOCKER_GUIDE.md`
