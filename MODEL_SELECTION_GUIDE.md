# Guide d'utilisation des modèles IA dans le chat

## 🎯 Comment choisir un modèle spécifique

Tu peux maintenant demander un modèle spécifique directement dans le chat web !

### **Mots-clés pour GPT-4.1-mini :**
- "gpt-4"
- "gpt4" 
- "gpt 4"
- "gpt-4.1-mini"
- "chatgpt"
- "openai"

### **Mots-clés pour Gemini :**
- "gemini"
- "google gemini"
- "gemini-flash"
- "gemini-pro"

### **Exemples d'utilisation :**

```
Utilisateur: Quelle est la cause d'une surchauffe compresseur ? gpt-4
Réponse: 🧠 **Réponse GPT-4.1-mini**
         [Analyse détaillée avec GPT-4.1-mini]

Utilisateur: Explique-moi les pannes de thermostat avec gemini
Réponse: 🤖 **Réponse Gemini**
         [Analyse détaillée avec Gemini]

Utilisateur: Diagnostic d'une fuite de fluide
Réponse: [Utilise le modèle par défaut selon la stratégie configurée]
```

### **Comportement par défaut :**

Si aucun modèle n'est spécifié, le système utilise :
- **Stratégie `primary_fallback`** : Gemini principal, GPT-4 fallback
- **Modèle principal** : Gemini (configurable)

### **Configuration actuelle :**

```bash
PRIMARY_MODEL=gemini          # Modèle principal
ANALYSIS_STRATEGY=primary_fallback  # Stratégie par défaut
GPT4_MODEL=gpt-4.1-mini     # Modèle GPT-4 exact
```

### **Test rapide :**

1. Va sur **http://localhost:5001/dashboard**
2. Envoie : "Test avec gpt-4"
3. Envoie : "Test avec gemini"
4. Compare les réponses !

Le système détecte automatiquement le modèle demandé et l'utilise ! 🚀
