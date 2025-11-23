# 🚀 Guide de Démarrage Rapide - 5 Minutes

## Étape 1 : Installation (2 min)

```bash
# Cloner le projet
git clone https://github.com/VOTRE_USERNAME/systeme-diagnostic-frigo.git
cd systeme-diagnostic-frigo

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Étape 2 : Configuration (2 min)

```bash
# Copier le template de configuration
cp .env.example .env

# Éditer .env avec tes credentials
# Windows: notepad .env
# Linux/Mac: nano .env
```

**Configurations minimales requises :**

```env
GEMINI_API_KEY=AIzaSy...VotreCléIci  # https://makersuite.google.com/app/apikey
TELEGRAM_BOT_TOKEN=123:ABC...         # @BotFather sur Telegram
TELEGRAM_CHAT_ID=123456789            # Ton Chat ID
```

## Étape 3 : Initialisation (30 sec)

```bash
python init_data.py
```

## Étape 4 : Démarrage (30 sec)

**Terminal 1 - Lancer l'application :**
```bash
python app.py
```

**Terminal 2 - Lancer le simulateur :**
```bash
python simulateur.py --mode stress --iterations 10
```

## ✅ C'est Tout !

Tu devrais voir :
- 📊 L'API qui démarre sur `http://localhost:5000`
- 🎮 Le simulateur qui envoie des diagnostics
- 📱 Des notifications sur Telegram

---

## 🧪 Test Rapide Manuel

```bash
curl -X POST http://localhost:5000/webhook/diagnostic-frigo \
  -H "Content-Type: application/json" \
  -d '{
    "Température": 55,
    "Pression_BP": 2.5,
    "Pression_HP": 12,
    "Courant": 14,
    "Tension": 220,
    "Humidité": 55,
    "Débit_air": 150,
    "Vibration": 10
  }'
```

Tu dois recevoir une **alerte Telegram** ! 🚨

---

## 🆘 Problèmes Courants

### "Module not found"
```bash
pip install -r requirements.txt
```

### "GEMINI_API_KEY not set"
Vérifie que `.env` existe et contient ta clé

### "Telegram not responding"
- Vérifie le token
- Démarre une conversation avec le bot sur Telegram

---

## 📚 Pour Aller Plus Loin

Consulte le [README.md](README.md) complet pour :
- Toutes les options du simulateur
- Configuration avancée
- Déploiement sur Render
- Tests unitaires

---

**🎉 Félicitations ! Ton système est opérationnel !**