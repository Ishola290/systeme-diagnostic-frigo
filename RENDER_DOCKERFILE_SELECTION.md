# 🐳 Comment Chaque Service Connaît Son Dockerfile - Render Deploy Guide

## Le Problème

Render voit plusieurs Dockerfiles dans le repo:
```
Dockerfile                    (original - pré-compilé phi)
Dockerfile.production         (intermédiaire)
Dockerfile.render-lite        (recommandé)
chat/Dockerfile               (service chat)
gpt/Dockerfile                (service IA - original)
gpt/Dockerfile.production     (service IA - production)
gpt/Dockerfile.render-lite    (service IA - lite)
```

**Question**: Render - lequel utiliser? 🤔

**Réponse**: Tu le dis explicitement dans la configuration Render!

---

## ✅ Solution: Configuration Render par Service

Render a 2 façons de spécifier le Dockerfile:

### **Méthode 1: Render Dashboard UI** (Plus simple)

Lors de la création de chaque Web Service sur Render:

#### **Service 1: frigo-app** (Racine)

```
Render Dashboard → New Web Service
└── Connect GitHub: systeme-diagnostic-frigo

Configuration:
┌─────────────────────────────────────┐
│ Name:              frigo-app        │
│ Region:            Frankfurt        │
│ Runtime:           Docker           │
│ Root Directory:    ./ (défaut)      │
│ Build Command:     docker build \   │
│                    -f               │
│ Dockerfile.render-lite .            │  ← CLEF!
└─────────────────────────────────────┘

Résultat:
  Render execute: docker build -f Dockerfile.render-lite -t image .
```

#### **Service 2: frigo-chat** (chat/)

```
Render Dashboard → New Web Service
└── Connect GitHub: systeme-diagnostic-frigo

Configuration:
┌─────────────────────────────────────┐
│ Name:              frigo-chat       │
│ Region:            Frankfurt        │
│ Runtime:           Docker           │
│ Root Directory:    chat/ ← IMPORTANT│
│ Build Command:     docker build \   │
│                    -f               │
│                    Dockerfile .     │  ← Chat/Dockerfile
└─────────────────────────────────────┘

Note: Root Directory = chat/
      Donc cherche: chat/Dockerfile par défaut
```

#### **Service 3: frigo-gpt** (gpt/)

```
Render Dashboard → New Web Service
└── Connect GitHub: systeme-diagnostic-frigo

Configuration:
┌─────────────────────────────────────┐
│ Name:              frigo-gpt        │
│ Region:            Frankfurt        │
│ Runtime:           Docker           │
│ Root Directory:    gpt/ ← IMPORTANT │
│ Build Command:     docker build \   │
│                    -f               │
│ Dockerfile.render-lite .            │  ← GPT/Dockerfile.render-lite
└─────────────────────────────────────┘

Note: Root Directory = gpt/
      Chemin: gpt/Dockerfile.render-lite
```

---

### **Méthode 2: render.yaml** (Infrastructure as Code)

Alternative: Créer fichier `render.yaml` à la racine pour définir tous les services:

```yaml
services:
  # Service 1: Application principale
  - type: web
    name: frigo-app
    runtime: docker
    region: frankfurt
    rootDir: ./
    dockerfilePath: ./Dockerfile.render-lite
    buildCommand: "docker build -f Dockerfile.render-lite ."
    startCommand: "python app.py"
    envVars:
      - key: CHAT_API_URL
        value: "https://frigo-chat.onrender.com"
      - key: IA_SERVICE_URL
        value: "https://frigo-gpt.onrender.com"

  # Service 2: Chat
  - type: web
    name: frigo-chat
    runtime: docker
    region: frankfurt
    rootDir: ./chat
    dockerfilePath: ./chat/Dockerfile
    buildCommand: "docker build -f Dockerfile ."
    startCommand: "python app_web.py"
    envVars:
      - key: MAIN_APP_URL
        value: "https://frigo-app.onrender.com"

  # Service 3: IA Service
  - type: web
    name: frigo-gpt
    runtime: docker
    region: frankfurt
    rootDir: ./gpt
    dockerfilePath: ./gpt/Dockerfile.render-lite
    buildCommand: "docker build -f Dockerfile.render-lite ."
    startCommand: "python app_ia.py"
    envVars:
      - key: MAIN_APP_URL
        value: "https://frigo-app.onrender.com"
      - key: CHAT_API_URL
        value: "https://frigo-chat.onrender.com"
```

> **Important**: Render.yaml est avancé - utilise Dashboard UI pour 1er déploiement

---

## 🎯 Processus Détaillé Render

### **Quand tu crées frigo-app sur Render**

```
Step 1: Tu cliques "New Web Service"
        ↓
Step 2: Tu connectes GitHub
        ↓
Step 3: Render demande:
        ┌──────────────────────────────────────┐
        │ Build Command?                       │
        │                                      │
        │ Options:                             │
        │ • docker build . (défaut)            │
        │ • docker build -f Dockerfile .       │
        │ • docker build -f Dockerfile.lite .  │ ← TU CHOISIS
        └──────────────────────────────────────┘
        
Step 4: Render sauvegarde ta configuration
        ↓
Step 5: À chaque déploiement (push ou manuel):
        
        Render execute EXACTEMENT:
        └── docker build -f Dockerfile.render-lite .
        
        Cela construit l'image en utilisant Dockerfile.render-lite
        ↓
Step 6: Image créée et déployée
```

---

## 📋 Tableau Récapitulatif

| Service | Root Dir | Dockerfile | Build Command | Status |
|---------|----------|-----------|---|---|
| **frigo-app** | `./` | `Dockerfile.render-lite` | `docker build -f Dockerfile.render-lite .` | ✅ Lite |
| **frigo-chat** | `./chat` | `Dockerfile` | `docker build -f Dockerfile .` | ✅ Standard |
| **frigo-gpt** | `./gpt` | `Dockerfile.render-lite` | `docker build -f Dockerfile.render-lite .` | ✅ Lite |

---

## 🚀 Processus de Déploiement Complet

### **Étape 1: Créer frigo-app**

```
1. Aller sur render.com/dashboard
2. Cliquer "New → Web Service"
3. Sélectionner le repo GitHub: systeme-diagnostic-frigo
4. Configuration:

   ┌─────────────────────────────────────────┐
   │ Name:              frigo-app            │
   │ Region:            Frankfurt            │
   │ Runtime:           Docker               │
   │ Root Directory:    ./ (défaut)          │
   └─────────────────────────────────────────┘

5. Descendre à "Build Command"
   
   Remplacer:  docker build .
   Par:        docker build -f Dockerfile.render-lite .
   
6. Ajouter env vars:
   
   CHAT_API_URL = https://frigo-chat.onrender.com
   IA_SERVICE_URL = https://frigo-gpt.onrender.com

7. Cliquer "Create Web Service"
   → Render commence build
   → Attendre ~3-5 min
   → ✅ frigo-app.onrender.com en ligne
```

### **Étape 2: Créer frigo-chat**

```
1. Render Dashboard → "New → Web Service"
2. Sélectionner: systeme-diagnostic-frigo
3. Configuration:

   ┌─────────────────────────────────────────┐
   │ Name:              frigo-chat           │
   │ Region:            Frankfurt            │
   │ Runtime:           Docker               │
   │ Root Directory:    chat/ ← CHANGEMENT!  │
   └─────────────────────────────────────────┘

4. Render va chercher: chat/Dockerfile par défaut
   (Pas besoin de spécifier -f, c'est déjà là)
   
   Ou si tu veux spécifier:
   Build Command: docker build -f Dockerfile .
   
5. Ajouter env vars:
   
   MAIN_APP_URL = https://frigo-app.onrender.com

6. Cliquer "Create Web Service"
   → Build ~2-3 min
   → ✅ frigo-chat.onrender.com en ligne
```

### **Étape 3: Créer frigo-gpt**

```
1. Render Dashboard → "New → Web Service"
2. Sélectionner: systeme-diagnostic-frigo
3. Configuration:

   ┌─────────────────────────────────────────┐
   │ Name:              frigo-gpt            │
   │ Region:            Frankfurt            │
   │ Runtime:           Docker               │
   │ Root Directory:    gpt/ ← CHANGEMENT!   │
   └─────────────────────────────────────────┘

4. Build Command: docker build -f Dockerfile.render-lite .
   (Important: Utilise .render-lite, pas Dockerfile standard)
   
5. Ajouter env vars:
   
   MAIN_APP_URL = https://frigo-app.onrender.com
   CHAT_API_URL = https://frigo-chat.onrender.com

6. Cliquer "Create Web Service"
   → Build ~3-5 min
   → ✅ frigo-gpt.onrender.com en ligne
```

---

## 🔍 Comment Render Sait Quel Dockerfile Utiliser

### **Mécanisme Interne**

```
┌─────────────────────────────────────────────────┐
│ Render Configuration Storagée                   │
│                                                 │
│ Service: frigo-app                              │
│ ├─ git_repo: systeme-diagnostic-frigo          │
│ ├─ root_directory: ./                          │
│ ├─ build_command: docker build -f              │
│ │                 Dockerfile.render-lite .     │
│ ├─ start_command: python app.py                │
│ └─ envs: [CHAT_API_URL, IA_SERVICE_URL]        │
│                                                 │
│ Service: frigo-chat                             │
│ ├─ git_repo: systeme-diagnostic-frigo          │
│ ├─ root_directory: chat/                       │
│ ├─ build_command: docker build -f              │
│ │                 Dockerfile .                 │
│ ├─ start_command: python app_web.py            │
│ └─ envs: [MAIN_APP_URL]                        │
│                                                 │
│ Service: frigo-gpt                              │
│ ├─ git_repo: systeme-diagnostic-frigo          │
│ ├─ root_directory: gpt/                        │
│ ├─ build_command: docker build -f              │
│ │                 Dockerfile.render-lite .     │
│ ├─ start_command: python app_ia.py             │
│ └─ envs: [MAIN_APP_URL, CHAT_API_URL]          │
└─────────────────────────────────────────────────┘

À chaque déploiement (push GitHub):
  1. Render clone le repo
  2. Va au root_directory
  3. Execute build_command exactement
  4. Construit l'image avec Dockerfile spécifié
  5. Lance le conteneur
  6. Execute start_command
```

---

## 🧠 Exemples Concrets

### **Exemple 1: Modifie frigo-app → Redéploie**

```
Toi: git push origin main

GitHub Event:
  └─ Webhook → Render

Render Process:
  1. Récupère config frigo-app
  2. Clone repo
  3. cd ./ (root_directory)
  4. Execute: docker build -f Dockerfile.render-lite .
     └─ Utilise: Dockerfile.render-lite ✅
     
  5. Lance: python app.py
  6. ✅ Mis à jour
```

### **Exemple 2: Modifie frigo-chat → Redéploie**

```
Toi: git push origin main

Render Process:
  1. Récupère config frigo-chat
  2. Clone repo
  3. cd ./chat (root_directory)
  4. Execute: docker build -f Dockerfile .
     └─ Cherche: ./chat/Dockerfile ✅
     
  5. Lance: python app_web.py
  6. ✅ Mis à jour
```

### **Exemple 3: Modifie gpt/app_ia.py → Redéploie**

```
Toi: git push origin main

Render Process:
  1. Récupère config frigo-gpt
  2. Clone repo
  3. cd ./gpt (root_directory)
  4. Execute: docker build -f Dockerfile.render-lite .
     └─ Cherche: ./gpt/Dockerfile.render-lite ✅
     
  5. Lance: python app_ia.py
  6. ✅ Mis à jour
```

---

## 🔄 Si tu Veux Changer de Dockerfile

### **Scénario: Passer de render-lite à production**

```
Situation:
  frigo-app utilise Dockerfile.render-lite
  Tu veux utiliser Dockerfile.production (plus rapide)

Solution:
  1. Aller Render Dashboard
  2. Cliquer sur frigo-app
  3. Settings → Build & Deploy
  4. Modifier "Build Command":
     Ancien: docker build -f Dockerfile.render-lite .
     Nouveau: docker build -f Dockerfile.production .
  5. Sauvegarder
  6. Cliquer "Manual Deploy"
  7. Render reconstruit avec Dockerfile.production ✅
```

---

## 📊 Architecture Finale

```
GitHub Repo (main branch)
│
├─ Dockerfile.render-lite          ← frigo-app l'utilise
├─ Dockerfile.production           ← Alt pour frigo-app
├─ Dockerfile                      ← Backup
│
├─ chat/
│  ├─ Dockerfile                   ← frigo-chat l'utilise
│  └─ app_web.py
│
└─ gpt/
   ├─ Dockerfile.render-lite       ← frigo-gpt l'utilise
   ├─ Dockerfile.production        ← Alt pour frigo-gpt
   ├─ Dockerfile                   ← Backup
   └─ app_ia.py


Render Cloud
│
├─ frigo-app.onrender.com
│  ├─ Config: build -f Dockerfile.render-lite
│  └─ Récupère depuis: racine/Dockerfile.render-lite
│
├─ frigo-chat.onrender.com
│  ├─ Config: build -f Dockerfile
│  ├─ Root: ./chat
│  └─ Récupère depuis: chat/Dockerfile
│
└─ frigo-gpt.onrender.com
   ├─ Config: build -f Dockerfile.render-lite
   ├─ Root: ./gpt
   └─ Récupère depuis: gpt/Dockerfile.render-lite
```

---

## ✅ Checklist Render Setup

- [ ] **frigo-app**
  - [ ] Créé sur Render
  - [ ] Build Command: `docker build -f Dockerfile.render-lite .`
  - [ ] Root Directory: `./`
  - [ ] Env vars: CHAT_API_URL, IA_SERVICE_URL
  - [ ] ✅ En ligne

- [ ] **frigo-chat**
  - [ ] Créé sur Render
  - [ ] Build Command: `docker build -f Dockerfile .`
  - [ ] Root Directory: `./chat`
  - [ ] Env vars: MAIN_APP_URL
  - [ ] ✅ En ligne

- [ ] **frigo-gpt**
  - [ ] Créé sur Render
  - [ ] Build Command: `docker build -f Dockerfile.render-lite .`
  - [ ] Root Directory: `./gpt`
  - [ ] Env vars: MAIN_APP_URL, CHAT_API_URL
  - [ ] ✅ En ligne

---

## 🎓 Résumé Technique

**Q: Comment Render sait quel Dockerfile utiliser?**

**A:** C'est toi qui dis lors de la création du service:
1. Tu spécifies le "Build Command" (ex: `docker build -f Dockerfile.render-lite .`)
2. Render sauvegarde cette config
3. À chaque redéploiement, Render execute EXACTEMENT cette commande
4. Donc il utilise le Dockerfile que tu as spécifié

**Les 3 clés:**
- `Root Directory`: Où Render cherche les fichiers
- `Build Command`: Comment construire l'image (quel Dockerfile)
- `Start Command`: Comment démarrer le service (quel script)

**Chaque service a sa propre config** → Chacun sait exactement quel Dockerfile utiliser ✅

---

## 🚀 Prêt à Déployer?

Voici la checklist:
1. ✅ Code pushé sur GitHub
2. ✅ Dockerfiles créés (.render-lite, etc)
3. ✅ Documentation complète (ce fichier)
4. ⏳ **Créer 3 Web Services sur Render** (suivre sections ci-dessus)
5. ⏳ Vérifier que chaque service en ligne
6. ⏳ Tester URLs auto-sync
7. ⏳ Tester APIs en production

Allons-y! 🚀
