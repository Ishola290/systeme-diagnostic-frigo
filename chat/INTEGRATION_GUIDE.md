# 🔌 Guide d'Intégration du Chat Web

Ce guide explique comment intégrer l'application web chat avec `app.py`.

## 📝 Aperçu

L'application web chat fonctionne en parallèle avec `app.py` et communique via HTTP. Cela permet:

1. ✅ Envoyer des **alertes** du système de diagnostic
2. ✅ Envoyer les **diagnostics** et leurs résultats
3. ✅ Recevoir les **messages** des utilisateurs pour traitement
4. ✅ Communication **en temps réel** via WebSocket

## 🔧 Configuration

### 1. Ajouter le module d'intégration à app.py

```python
# app.py
from chat_integration import init_chat_integration, get_chat_integration

# Initialiser lors du démarrage
chat_web = init_chat_integration(Config.CHAT_WEB_URL)

# Vérifier la connexion
if chat_web.health_check():
    print("✅ Chat web connecté")
else:
    print("⚠️  Chat web indisponible - mode dégradé")
```

### 2. Configurer les variables

```python
# config.py
class Config:
    # ... autres configs ...
    
    # URL de l'application web chat
    CHAT_WEB_URL = os.environ.get('CHAT_WEB_URL', 'http://localhost:5001')
```

### 3. Dans .env

```env
# Application web chat
CHAT_WEB_URL=http://localhost:5001

# En production:
# CHAT_WEB_URL=https://your-chat-app.render.com
```

## 📤 Envoyer des Alertes

### Exemple basique

```python
from chat_integration import get_chat_integration

chat_web = get_chat_integration()

# Envoyer une alerte
chat_web.send_alert(
    title="Erreur Température",
    message="La température du frigo est anormale: 28°C",
    severity="high",
    alert_type="error",
    diagnostic_id="DIAG-12345"
)
```

### Intégrer dans le code existant

```python
# Dans services/agent_ia.py ou agent_ia_service.py
@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    # ... code de diagnostic ...
    
    # Si erreur détectée
    if error_detected:
        chat_web = get_chat_integration()
        chat_web.send_alert(
            title="Panne Détectée",
            message=f"Type: {error_type}, Cause: {error_cause}",
            severity="critical",
            diagnostic_id=diagnostic_id
        )
    
    return jsonify({'result': result})
```

### Sévérités disponibles

- `low` - Information
- `medium` - Avertissement
- `high` - Erreur importante
- `critical` - Erreur critique

## 📋 Envoyer des Diagnostics

```python
from chat_integration import get_chat_integration

chat_web = get_chat_integration()

# Après un diagnostic complété
chat_web.send_diagnostic(
    diagnostic_id="DIAG-12345",
    description="Diagnostic du compresseur frigorifique",
    result={
        'status': 'OK',
        'temperature': 5.2,
        'pressure': 120,
        'compressor': 'fonctionnelle'
    },
    status='completed'
)
```

### Statuts disponibles

- `pending` - En cours
- `completed` - Terminé
- `error` - Erreur

## 💬 Recevoir des Messages du Chat

L'application web chat envoie les messages de l'utilisateur via:

```python
# Route dans app.py pour recevoir les messages chat
@app.route('/api/chat', methods=['POST'])
def handle_chat_message():
    data = request.get_json()
    message = data.get('message')
    user = data.get('user')
    
    # Traiter le message
    response = agent_ia.ask(message)  # Ou votre système de traitement
    
    # Envoyer la réponse au chat web
    chat_web = get_chat_integration()
    chat_web.send_message(
        content=response,
        user="System",
        is_from_system=True
    )
    
    return jsonify({
        'response': response,
        'user': user,
        'timestamp': datetime.utcnow().isoformat()
    })
```

## 📊 Cas d'Usage Complets

### Exemple 1: Diagnostic avec Alertes

```python
from chat_integration import get_chat_integration

def run_diagnostic():
    chat_web = get_chat_integration()
    
    diagnostic_id = generate_diagnostic_id()
    
    # Envoyer un diagnostic en cours
    chat_web.send_diagnostic(
        diagnostic_id=diagnostic_id,
        description="Diagnostic en cours...",
        result={},
        status='pending'
    )
    
    try:
        # Effectuer le diagnostic
        result = diagnose_fridge()
        
        # Si problèmes détectés
        if result.get('errors'):
            for error in result['errors']:
                chat_web.send_alert(
                    title=error['type'],
                    message=error['description'],
                    severity=error['severity'],
                    diagnostic_id=diagnostic_id
                )
        
        # Envoyer le résultat final
        chat_web.send_diagnostic(
            diagnostic_id=diagnostic_id,
            description="Diagnostic complet",
            result=result,
            status='completed'
        )
        
    except Exception as e:
        # En cas d'erreur
        chat_web.send_diagnostic(
            diagnostic_id=diagnostic_id,
            description=f"Erreur: {str(e)}",
            result={'error': str(e)},
            status='error'
        )
        
        chat_web.send_alert(
            title="Erreur Diagnostic",
            message=str(e),
            severity="high",
            diagnostic_id=diagnostic_id
        )
```

### Exemple 2: Intégration du Chat IA

```python
@app.route('/api/chat', methods=['POST'])
@check_api_key
def chat_endpoint():
    data = request.get_json()
    user_message = data.get('message')
    user = data.get('user', 'Anonymous')
    
    chat_web = get_chat_integration()
    
    try:
        # Obtenir la réponse de l'IA
        response = gemini.generate_response(user_message)
        
        # Envoyer la réponse au chat web
        chat_web.send_message(
            content=response,
            user="Système IA",
            is_from_system=True
        )
        
        return jsonify({
            'response': response,
            'user': user,
            'success': True
        })
        
    except Exception as e:
        chat_web.send_alert(
            title="Erreur Chat IA",
            message=f"Erreur lors du traitement: {str(e)}",
            severity="high"
        )
        
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
```

## 🔄 Flux de Communication

```
┌─────────────────────┐
│  Chat Web (5001)    │
│  ┌───────────────┐  │
│  │  Dashboard    │  │
│  │  Chat Real    │  │
│  │  Alertes      │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │ HTTP + WebSocket
           ↓
┌──────────────────────────────────┐
│  App.py (5000)                   │
│  ┌──────────────────────────────┐│
│  │ Agent IA / Gemini Service    ││
│  │ Diagnostic Logic             ││
│  │ Telegram (optionnel)         ││
│  └──────────────────────────────┘│
└──────────────────────────────────┘
```

## ⚠️ Gestion des Erreurs

L'intégration désactive automatiquement si l'app web n'est pas accessible:

```python
chat_web = get_chat_integration()

# En cas d'erreur, chat_web.enabled devient False
# Les envois retourneront False sans bloquer l'app principale

if not chat_web.send_alert(...):
    # Fallback: envoyer via Telegram ou logger
    telegram.send_alert(title, message)
    logger.warning(f"Chat web indisponible, alerte envoyée via Telegram")
```

## 🚀 Déploiement

### Local

```bash
# Terminal 1: App principale
python app.py

# Terminal 2: Chat web
cd chat
python app_web.py
```

### Docker Compose

```bash
docker-compose up
```

### Production

Voir les fichiers de déploiement:
- `chat/Dockerfile` - Image Docker
- `chat/deploy_render.sh` - Déploiement Render
- `docker-compose.yml` - Configuration complète

## 📞 Dépannage

### "Cannot connect to chat web"

```python
# Vérifier la connexion
chat_web = get_chat_integration()
if chat_web.health_check():
    print("✅ Connecté")
else:
    print("❌ Déconnecté")
```

### Les alertes ne s'affichent pas

1. Vérifier que le chat web est en cours d'exécution
2. Vérifier `CHAT_WEB_URL` dans la config
3. Vérifier les logs: `tail -f chat_app.log`

### WebSocket ne se connecte pas

1. Vérifier le firewall
2. Vérifier CORS dans config
3. Vérifier la console du navigateur pour les erreurs

## 📚 Ressources

- [Code d'intégration](./chat_integration.py)
- [Application web](./chat/README.md)
- [Configuration](./config.py)

## ✨ Prochaines Étapes

1. Déployer le chat web sur Render
2. Configurer MAIN_APP_URL dans l'environment de production
3. Tester les alertes et diagnostics en production
4. Mettre en place des backups de la base de données
5. Configurer les notifications push (optionnel)
