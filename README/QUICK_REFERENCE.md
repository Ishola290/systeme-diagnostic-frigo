# 🚀 GUIDE DÉMARRAGE IMMÉDIAT

## ⚡ 5 Étapes Pour Commencer

### Étape 1️⃣ : LIRE (2 min)
```
Ouvrir et lire: 00_COMMENCER_ICI.md
ou: SETUP.md (pour guide complet)
```

### Étape 2️⃣ : CONFIGURER (3 min)
```powershell
# Windows: Ouvrir et éditer .env
notepad .env

# Remplir obligatoirement:
GEMINI_API_KEY=AIzaSy...VotreClé
TELEGRAM_BOT_TOKEN=8278706239:AAF...VotreToken  
TELEGRAM_CHAT_ID=123456789
```

### Étape 3️⃣ : INITIALISER (1 min)
```powershell
# Activer environnement
venv\Scripts\Activate.ps1

# Installer dépendances (si pas déjà fait)
pip install -r requirements.txt

# Initialiser données
python init_data.py
```

### Étape 4️⃣ : TESTER (2 min)
```powershell
# Terminal 1: API
python app.py

# Terminal 2: Simulateur (nouveau terminal)
python simulateur.py
```

### Étape 5️⃣ : VÉRIFIER (1 min)
```
Voir les logs: logs/diagnostic_frigo.log
Recevoir alerte Telegram
Vérifier data/dataset_apprentissage.csv
```

---

## 📋 CHECKLIST DÉMARRAGE

- [ ] `.env` configuré avec credentials
- [ ] `pip install -r requirements.txt` exécuté
- [ ] `python init_data.py` lancé
- [ ] `data/`, `logs/` créés
- [ ] `python app.py` tourne sans erreur
- [ ] `python simulateur.py` envoie diagnostics
- [ ] Logs apparaissent dans `logs/diagnostic_frigo.log`
- [ ] Notifications Telegram reçues

---

## 🎯 LES FICHIERS À CONNAÎTRE

### Essentiels (LIRE EN PREMIER)
1. `00_COMMENCER_ICI.md` - Point de départ ← **COMMENCEZ PAR LÀ**
2. `SETUP.md` - Guide installation détaillé

### Comprendre le Projet
3. `IMPLEMENTATION_SUMMARY.md` - Architecture
4. `COMPLETION_SUMMARY.md` - Ce qui a été fait

### Utilisation
5. `README.md` - Vue d'ensemble
6. `quick_start.md` - 5 minutes

### Configuration
7. `.env.example` - Template config
8. `config.py` - Config Python

---

## ⚠️ PROBLÈMES COURANTS

### "GEMINI_API_KEY non trouvée"
**Solution:** Éditer `.env` et ajouter votre clé

### "Cannot connect to API"
**Solution:** Vérifier que `python app.py` tourne dans autre terminal

### "Telegram non configuré"
**Solution:** Vérifier `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` dans `.env`

### "Données ne s'enregistrent pas"
**Solution:** Vérifier que `data/` et `logs/` existent et sont writable

---

## 📊 FICHIERS CRÉÉS/MODIFIÉS

### Nouveaux
✅ `services/gemini_service.py` - Service Gemini
✅ `services/apprentissage_service.py` - ML continu
✅ `simulateur.py` - Simulateur capteurs
✅ `SETUP.md` - Guide installation
✅ `IMPLEMENTATION_SUMMARY.md` - Résumé
✅ Autres docs...

### Améliorés
✅ `utils/validation.py` - Validation robuste
✅ `utils/helpers.py` - 20+ helpers
✅ `init_data.py` - Init complète
✅ `.env.example` - Config documentée

---

## 🎮 TESTER MAINTENANT

```powershell
# 1. Vérifier que tout est en place
python verify_setup.py

# 2. Initialiser les données
python init_data.py

# 3. Terminal 1 - API
python app.py

# 4. Terminal 2 - Simulateur (nouveau)
python simulateur.py

# 5. Vérifier Health
curl http://localhost:5000/health
```

---

## 💡 TIPS

1. Vérifier toujours `logs/diagnostic_frigo.log` en cas de problème
2. Le simulateur génère 8 types différents de pannes
3. La première panne peut prendre 30 secondes (intervalle par défaut)
4. Telegram: s'assurer que le bot a reçu un message avant
5. Gemini API est gratuite (incluse dans Google Cloud Free Tier)

---

## 📞 BESOIN D'AIDE ?

| Question | Où Chercher |
|----------|------------|
| Installation ? | `SETUP.md` Section 1-4 |
| Architectur ? | `IMPLEMENTATION_SUMMARY.md` |
| Configuration ? | `.env.example` + `SETUP.md` |
| Code ? | Docstrings dans les fichiers |
| Problèmes ? | `SETUP.md` Section "Troubleshooting" |

---

**🚀 C'EST PRÊT - ALLEZ Y !**

Commencez par: `00_COMMENCER_ICI.md`
