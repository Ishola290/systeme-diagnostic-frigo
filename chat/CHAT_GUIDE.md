# 💬 Guide des Messages - Chat Diagnostic Frigo

## 🎯 Types de Messages Supportés

Le chat accepte plusieurs types de requêtes. Voici comment les utiliser:

---

## 1️⃣ **Messages Simples (Aide & Questions)**

### 📋 Format:
```
Qu'est-ce qu'une panne électrique?
Comment diagnostiquer une fuite?
Que faire si le compresseur ne démarre pas?
```

**Réponse attendue:** Information générale sur le sujet

### 📝 Exemples:
- "C'est quoi un diagnostic frigo?"
- "Explique-moi les alertes rouges"
- "Comment utiliser le système?"

---

## 2️⃣ **Demandes de Diagnostic**

### 📋 Format:
```
Diagnostic: [symptôme] [symptôme] [symptôme]
ou
Diagnostiquer: température élevée, bruit anormal, pas de froid
ou
Je veux diagnostiquer ma frigo qui fait du bruit
```

**Réponse attendue:** Diagnostic basé sur les symptômes

### 📝 Exemples:
```
Diagnostic: température élevée, condensation excessive, bruit de compresseur
```

```
Diagnostiquer mes symptômes: 
- La frigo fait du bruit étrange
- Le froid ne monte pas
- Les glaçons ne se forment pas
```

---

## 3️⃣ **Signaler une Panne**

### 📋 Format:
```
Panne: [description de la panne]
ou
Report: code erreur E02
ou
Problème: [détails]
```

**Réponse attendue:** Diagnostic et solutions proposées

### 📝 Exemples:
```
Panne: Erreur E02 - Température du congélateur ne descend pas
```

```
Report: Bruit anormal au démarrage, perte de froid progressive
```

---

## 4️⃣ **Demander une Solution**

### 📋 Format:
```
Solution: [problème détecté]
ou
Comment réparer: [la panne]
ou
Fix: [le problème]
```

**Réponse attendue:** Étapes pour résoudre le problème

### 📝 Exemples:
```
Solution: Thermostat défectueux
```

```
Comment réparer une fuite de gaz réfrigérant?
```

---

## 5️⃣ **Signaler un Apprentissage**

### 📋 Format:
```
Apprendre: [problème] -> [solution trouvée]
ou
Learn: [cas] = [résultat]
ou
Enregistrer: [diagnostic] avec résultat [solution]
```

**Réponse attendue:** Confirmation d'apprentissage

### 📝 Exemples:
```
Apprendre: bruit compresseur + température basse = ventilateur défaillant
```

```
Learn: erreur E05 = fuite sur système de froid
```

---

## 6️⃣ **Requêtes Système (Avancées)**

### 📋 Format:
```
Système: [commande système]
ou
/status
/diagnostics récents
/alerts
/stats
```

**Réponse attendue:** Données du système

### 📝 Exemples:
```
/status
```

```
Affiche les 5 derniers diagnostics
```

---

## 📊 Exemples Complets de Conversations

### Conversation 1: Simple Diagnostic
```
User: Diagnostic: température élevée, bruit anormal
System: Analyse en cours...
System: ⚠️ Possible panne du compresseur
         Solution: Vérifier le thermostat ou faire réviser le compresseur

User: Comment réparer?
System: 🔧 Étapes:
        1. Débranchez l'appareil
        2. Vérifiez les contacts du thermostat
        3. Si pas de changement, appelez un technicien
```

### Conversation 2: Panne Complexe
```
User: Panne: erreur E02, froid ne monte pas depuis 2 jours
System: ⚠️ Diagnostic: Possible défaut du thermostat ou capteur
        Sévérité: HAUTE
        
User: Qu'est-ce qu'un thermostat?
System: 💡 Un thermostat est...

User: Solution: thermostat défectueux
System: ✅ Solutions:
        1. Remplacement thermostat: ~50€
        2. Vérification capteur: ~20€
```

### Conversation 3: Apprentissage
```
User: Apprendre: température très basse + pas de bruit = compresseur arrêté
System: ✅ Apprentissage enregistré!
        Ce diagnostic sera utilisé pour les diagnostics futurs
        
User: Diagnostic: pas de froid, pas de bruit
System: 🔍 Basé sur apprentissage: Probable compresseur arrêté
        Vérifier l'alimentation électrique
```

---

## 🔑 Mots-Clés Spéciaux

| Mot-clé | Fonction | Exemple |
|---------|----------|---------|
| `Diagnostic:` | Lancer un diagnostic | `Diagnostic: bruit, froid faible` |
| `Panne:` | Signaler une panne | `Panne: E02` |
| `Solution:` | Demander solution | `Solution: thermostat` |
| `Apprendre:` | Enregistrer un cas | `Apprendre: bruit -> ventilateur` |
| `Système:` | Commande système | `Système: /status` |
| `/stats` | Voir statistiques | `/stats` |
| `/alerts` | Voir alertes | `/alerts` |
| `/clear` | Effacer historique | `/clear` |

---

## 📋 Symptômes Reconnus

Le système reconnaît automatiquement:

### 🌡️ **Température**
- Température élevée / trop chaude
- Température basse / trop froid
- Température instable
- Froid qui ne monte pas

### 🔊 **Bruit**
- Bruit anormal / étrange
- Bruit de compresseur
- Vibrations
- Silence complet (pas de bruit)

### 💧 **Humidité**
- Condensation excessive
- Humidité excessive
- Fuite d'eau
- Accumulation de givre

### 🔋 **Électricité**
- Pas d'alimentation
- Erreur code E...
- Disjoncteur saute
- Voyant éteint

### ❄️ **Froid**
- Pas de froid
- Froid insuffisant
- Glaçons ne se forment pas
- Congélation lente

---

## ✅ Bonne Pratique

### ✅ BON:
```
Diagnostic: température 35°C, bruit compresseur, condensation
```

### ❌ MAUVAIS:
```
frigo cassé
c pas ouf
c pas normal
```

### ✅ BON:
```
Panne: E02 - compresseur s'arrête après 5 min
```

### ❌ MAUVAIS:
```
ca marche po
```

---

## 🚀 Pour Obtenir Meilleures Réponses

1. **Soyez spécifique** - Donnez des détails
2. **Utilisez les mots-clés** - `Diagnostic:`, `Panne:`, etc.
3. **Décrivez les symptômes** - Température, bruit, comportement
4. **Donnez le contexte** - Depuis quand? Fréquence?
5. **Posez une question claire** - "Comment réparer?" vs "quoi faire"

---

## 💡 Cas Pratiques

### Cas 1: Panne Simple
```
Utilisateur: Diagnostic: pas de froid, ventilateur silencieux
Chat: Probable compresseur arrêté
      Vérifications: Alimentation? Thermostat? Câblage?
```

### Cas 2: Panne Complexe
```
Utilisateur: Panne: temp 25°C, bruit, condensation, erreur E03
Chat: Possible problème multi-facette
      1. Thermostat défaillant
      2. Fuite réfrigérant
      3. Filtre obstrué
      
      Recommandation: Appeler technicien - Sévérité HAUTE
```

### Cas 3: Apprentissage
```
Utilisateur: Apprendre: temp basse + silence = compresseur OFF
Chat: ✅ Apprentissage enregistré
      Utilité: Moins de faux positifs sur ce diagnostic
```

---

## 🆘 Problèmes Courants

### Problem: "Pas de réponse du système"
**Solution:** Vérifiez que l'app principale (port 5000) fonctionne
```powershell
curl http://localhost:5000/health
```

### Problem: "Réponse générique"
**Solution:** Soyez plus précis avec les symptômes
```
❌ "La frigo c'est cassé"
✅ "Diagnostic: température 40°C, pas de froid, bruit compresseur"
```

### Problem: "Erreur de connexion"
**Solution:** Vérifiez `.env` et `MAIN_APP_URL`
```
MAIN_APP_URL=http://localhost:5000
```

---

## 📞 Support Avancé

Pour des cas complexes, utilisez:
```
Diagnostic détaillé: 
- Modèle frigo: [modèle]
- Année: [année]
- Température actuelle: [°C]
- Bruit: [description]
- Depuis: [X jours]
```

Cela donnera un diagnostic beaucoup plus précis!
