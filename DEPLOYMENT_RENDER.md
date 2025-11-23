# Guide de Déploiement sur Render — 3 Services Microservices

## Architecture Déployée

```
Service 1: app (Main) - Port 5000
├── app.py
├── services/
└── Dockerfile (racine)
    
Service 2: chat (Web UI) - Port 5001
├── chat/app_web.py
├── chat/Dockerfile
└── Connecté à: app + gpt

Service 3: gpt (IA Service) - Port 5002
├── gpt/app_ia.py
├── gpt/Dockerfile
└── Modèle: models/phi-2/ (local, pré-téléchargé)
```

Les trois services communiquent via **URLs internes Render** (noms DNS du service).

---

## Pré-requis

✅ Dépôt GitHub avec Git LFS configuré (modèles phi-2 inclus)  
✅ Compte Render (https://render.com)  
✅ Trois services configurés (suivre les étapes ci-dessous)

---

## Étapes de Déploiement

### Étape 1 : Créer Service 1 (Main App - app.py)

1. Connecte-toi à **render.com**
2. Clique **New +** → **Web Service**
3. Sélectionne ton dépôt GitHub `systeme-diagnostic-frigo`
4. Configure comme suit :

   - **Name** : `systeme-diagnostic-main`
   - **Environment** : `Docker`
   - **Dockerfile Path** : `Dockerfile` (racine)
   - **Port** : `5000`
   - **Environment Variables** :
     ```
     FLASK_ENV=production
     PYTHONUNBUFFERED=1
     HF_LOCAL_MODEL_PATH=/app/models/phi-2
     CHAT_API_URL=http://systeme-diagnostic-chat:5001
     IA_SERVICE_URL=http://systeme-diagnostic-gpt:5002
     TELEGRAM_BOT_TOKEN=<ton_token_telegram>
     TELEGRAM_CHAT_ID=<ton_chat_id>
     ```

5. Clique **Create Web Service**

**Attends que le déploiement se termine** (~5-10 min).  
L'URL sera quelque chose comme : `https://systeme-diagnostic-main.onrender.com`

---

### Étape 2 : Créer Service 2 (Chat Web - chat/app_web.py)

1. Clique **New +** → **Web Service**
2. Sélectionne le même dépôt
3. Configure comme suit :

   - **Name** : `systeme-diagnostic-chat`
   - **Environment** : `Docker`
   - **Dockerfile Path** : `chat/Dockerfile`
   - **Port** : `5001`
   - **Environment Variables** :
     ```
     FLASK_ENV=production
     PYTHONUNBUFFERED=1
     MAIN_APP_URL=http://systeme-diagnostic-main:5000
     IA_SERVICE_URL=http://systeme-diagnostic-gpt:5002
     DATABASE_URL=sqlite:////tmp/chat_app.db
     SECRET_KEY=<une_clé_secrète_longue_aléatoire>
     ```

4. Clique **Create Web Service**

**Attends la fin du déploiement.**  
L'URL sera : `https://systeme-diagnostic-chat.onrender.com`

---

### Étape 3 : Créer Service 3 (IA Service - gpt/app_ia.py)

1. Clique **New +** → **Web Service**
2. Sélectionne le même dépôt
3. Configure comme suit :

   - **Name** : `systeme-diagnostic-gpt`
   - **Environment** : `Docker`
   - **Dockerfile Path** : `gpt/Dockerfile`
   - **Port** : `5002`
   - **Environment Variables** :
     ```
     FLASK_ENV=production
     PYTHONUNBUFFERED=1
     HF_LOCAL_MODEL_PATH=/app/../models/phi-2
     IA_MODEL=phi
     IA_USE_GPU=false
     MAIN_APP_URL=http://systeme-diagnostic-main:5000
     CHAT_API_URL=http://systeme-diagnostic-chat:5001
     ```

4. Clique **Create Web Service**

**Attends la fin du déploiement.**  
L'URL sera : `https://systeme-diagnostic-gpt.onrender.com`

---

## Communications Entre Services

| Service | Accède à | Via URL |
|---------|----------|---------|
| **main** | chat | `http://systeme-diagnostic-chat:5001` |
| **main** | gpt | `http://systeme-diagnostic-gpt:5002` |
| **chat** | main | `http://systeme-diagnostic-main:5000` |
| **chat** | gpt | `http://systeme-diagnostic-gpt:5002` |
| **gpt** | main | `http://systeme-diagnostic-main:5000` |
| **gpt** | chat | `http://systeme-diagnostic-chat:5001` |

Les noms DNS (ex: `systeme-diagnostic-main`) sont des alias internes Render — pas besoin d'IP publiques.

---

## Vérification du Déploiement

### 1. Vérifier les Logs

Pour chaque service, clique sur le service → **Logs** (en bas à droite) :

✅ **App (5000)** :
```
✅ Service IA initialisé
🚀 Démarrage Flask app
```

✅ **Chat (5001)** :
```
✅ Base de données initialisée
🚀 Démarrage du serveur web Flask
```

✅ **GPT (5002)** :
```
📁 Chargement modèle depuis chemin par défaut: .../models/phi-2
✅ Modèle phi chargé avec succès sur CPU
✅ Service IA initialisé
```

### 2. Tester les Health Checks

Depuis un terminal ou navigateur :

```bash
# Service Main
curl https://systeme-diagnostic-main.onrender.com/health

# Service Chat
curl https://systeme-diagnostic-chat.onrender.com/

# Service GPT
curl https://systeme-diagnostic-gpt.onrender.com/health
```

### 3. Tester la Communication Inter-Services

Envoie un message via le Chat Web :
- La requête traverse : Chat (5001) → GPT (5002) → Main (5000)
- Si tout fonctionne, tu reçois une réponse du modèle IA

---

## Problèmes Courants

### ❌ Le service GPT ne trouve pas le modèle

**Cause** : Les fichiers `models/phi-2/*.safetensors` n'ont pas été pushés avec Git LFS.

**Solution** :
```bash
git lfs install
git lfs track "models/**/*.safetensors"
git add models/
git commit -m "Add models with LFS"
git push
```

Redéploie sur Render.

### ❌ Les services ne communiquent pas

**Cause** : Mauvaises URLs d'environnement.

**Solution** : Vérifie que les noms des services dans les URLs correspondent exactement aux **Name** configurés sur Render. Par ex:
- Si le service chat s'appelle `my-chat-app`, l'URL doit être `http://my-chat-app:5001`

### ❌ Chat Web ne démarre pas (erreur DB)

**Cause** : `init_db.py` échoue.

**Solution** : 
1. Vérifie que `chat/init_db.py` existe et crée la DB correctement.
2. En Render, les fichiers persistent dans `/tmp/` ou montages volumes (à configurer si besoin).

### ❌ GPU non disponible (normal sur Render Free)

**Cause** : Render Free n'a pas de GPU.

**Solution** : Le service GPT roule en mode CPU (c'est configuré par `IA_USE_GPU=false`).  
Performance réduite mais acceptable pour Phi-2 (2.7B paramètres).

---

## Mise à Jour du Code

Quand tu pusses du nouveau code vers `main` :

1. **Render détecte le push** automatiquement.
2. **Chaque service redéploie indépendamment** (basé sur le Dockerfile qui a changé).
3. **Les services restent accessibles** pendant la construction (~ 5-15 min).

Pour forcer un redéploiement sans changement :
- Render → Service → **Deployment** → **Manual Deploy** → **Deploy latest commit**

---

## Scale / Upgrade

Si tu veux optimiser les performances :

- **Chat (5001)** : Monter les ressources (plus de RAM pour les sessions utilisateur).
- **GPT (5002)** : Upgrade à Render's **Paid Plan** pour GPU (Tesla K80 ou mieux) → Performance ×5-10 pour l'IA.
- **Main (5000)** : Scale les workers si beaucoup d'utilisateurs.

---

## Résumé des URLs Publiques

| Service | URL |
|---------|-----|
| **Main App** | `https://systeme-diagnostic-main.onrender.com` |
| **Chat Web UI** | `https://systeme-diagnostic-chat.onrender.com` |
| **IA Service API** | `https://systeme-diagnostic-gpt.onrender.com` |

Les services se trouvent **mutuellement** via URLs internes (ex: `http://systeme-diagnostic-gpt:5002`).

---

## Questions / Support

Si tu as des soucis :
1. Vérifie les **Logs** pour chaque service.
2. Teste les **URLs internes** depuis le terminal du service.
3. Confirme que Git LFS a bien poussé les modèles (lfs pointer files vs binary).

Bon déploiement ! 🚀
