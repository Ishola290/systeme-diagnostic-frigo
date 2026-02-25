"""
Application Flask Web - Interface Web pour Système Diagnostic Frigo
Chat en temps réel + Dashboard Alertes + Historique Diagnostics
AUTHENTIFICATION DESACTIVEE - Mode Invité uniquement
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os
import json
import logging
import requests
import sys
from pathlib import Path

# Import DB Postgres (fallback sur fichiers si pas dispo)
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_postgres import (
    save_alert, get_alerts, get_alerts_stats,
    save_diagnostic, get_diagnostics_stats,
    is_postgres_enabled, init_db as init_postgres_db
)

# ==================== MODE SANS AUTHENTIFICATION ====================
USE_DB = False  # AUTHENTIFICATION COMPLETEMENT DESACTIVEE
db = None

# Mock complet pour utilisateur
class MockUser:
    id = 1
    username = "Invité"
    email = "guest@local"
    is_authenticated = True
    is_active = True
    is_anonymous = False
    is_admin = False
    
    def get_id(self):
        return "1"

current_user = MockUser()

# Mock pour décorateur login_required
def login_required(func):
    return func

# ==================== CONFIGURATION ====================
class Config:
    """Configuration Flask"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-chat-2024'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # URLs des services
    MAIN_APP_URL = os.environ.get('MAIN_APP_URL') or 'http://localhost:5000'
    IA_SERVICE_URL = os.environ.get('IA_SERVICE_URL') or 'http://localhost:5002'
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    USE_DB = False

# Initialisation Flask
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# ==================== CONFIGURATION IA SERVICE ====================
IA_SERVICE_URL = os.environ.get('IA_SERVICE_URL', 'http://localhost:5002')

# Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== PERSISTENCE FICHIERS ====================
CHAT_DATA_DIR = Path(__file__).parent / "data"
CHAT_DATA_DIR.mkdir(exist_ok=True)
ALERTS_FILE = CHAT_DATA_DIR / "alerts.json"
MESSAGES_FILE = CHAT_DATA_DIR / "messages.json"

def _load_json_file(filepath):
    """Charger des données depuis un fichier JSON"""
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def _save_json_file(filepath, data):
    """Sauvegarder des données dans un fichier JSON"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde {filepath}: {e}")
        return False

# Charger les données au démarrage
_alerts_cache = _load_json_file(ALERTS_FILE)
_messages_cache = _load_json_file(MESSAGES_FILE)
logger.info(f"📂 Données chargées: {len(_alerts_cache)} alertes, {len(_messages_cache)} messages")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Page d'accueil - Redirection vers dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard principal - Sans authentification"""
    return render_template('dashboard.html', username="Invité")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login désactivé - Redirection vers dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout désactivé - Redirection vers dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register désactivé - Redirection vers dashboard"""
    return redirect(url_for('dashboard'))

# ==================== API ROUTES ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts_route():
    """Récupérer les alertes - Sans auth"""
    try:
        limit = request.args.get('limit', 10, type=int)
        severity = request.args.get('severity', None)
        
        # Récupérer depuis Postgres si disponible
        if is_postgres_enabled():
            alerts = get_alerts(limit=limit, severity=severity)
            return jsonify(alerts), 200
        
        # Sinon, utiliser le fichier local
        global _alerts_cache
        alerts = _alerts_cache[-limit:] if _alerts_cache else []
        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]
        return jsonify(alerts), 200
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération alertes: {e}")
        return jsonify([]), 200

@app.route('/api/alerts/<int:alert_id>/read', methods=['PUT'])
def mark_alert_read(alert_id):
    """Marquer une alerte comme lue - Sans auth"""
    return jsonify({'success': True}), 200

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Récupérer l'historique des messages - Sans auth"""
    global _messages_cache
    return jsonify(_messages_cache[-50:]), 200

@app.route('/api/messages', methods=['POST'])
def create_message():
    """Créer un message - Sans auth"""
    try:
        data = request.get_json(silent=True) or {}
        msg = {
            'id': len(_messages_cache) + 1,
            'content': data.get('content', ''),
            'is_from_system': data.get('is_from_system', False),
            'user_name': data.get('user_name', 'Invité'),
            'created_at': datetime.utcnow().isoformat()
        }
        _messages_cache.append(msg)
        _save_json_file(MESSAGES_FILE, _messages_cache)
        return jsonify({'success': True, 'message': msg}), 201
    except Exception as e:
        logger.error(f"❌ Erreur création message: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/diagnostics', methods=['GET'])
def get_diagnostics_route():
    """Récupérer l'historique des diagnostics - Sans auth"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if is_postgres_enabled():
            # TODO: Implémenter get_diagnostics dans db_postgres.py si besoin
            # Pour l'instant, fallback sur fichiers
            pass
        
        # Lire depuis fichier local
        diagnostic_file = Path(__file__).parent.parent / "data" / "dernier_diagnostic.json"
        diagnostics = []
        
        if diagnostic_file.exists():
            try:
                with open(diagnostic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('panne_detectee'):
                        diagnostic = {
                            'id': data.get('diagnostic_id', 'UNKNOWN'),
                            'timestamp': data.get('timestamp', ''),
                            'type_panne': data.get('apprentissage', {}).get('type_panne', 'Inconnu'),
                            'severite': data.get('apprentissage', {}).get('severite', 'medium'),
                            'confiance': data.get('apprentissage', {}).get('confiance', 0),
                            'panne_detectee': data.get('panne_detectee', False),
                            'created_at': data.get('timestamp', '')
                        }
                        diagnostics.append(diagnostic)
            except Exception as e:
                logger.warning(f"⚠️ Erreur lecture diagnostic: {e}")
        
        return jsonify(diagnostics[-limit:]), 200
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération diagnostics: {e}")
        return jsonify([]), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiques dashboard - Sans auth"""
    try:
        # Calculer le nombre de diagnostics
        diagnostic_file = Path(__file__).parent.parent / "data" / "dernier_diagnostic.json"
        total_diagnostics = 0
        if diagnostic_file.exists():
            try:
                with open(diagnostic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('panne_detectee'):
                        total_diagnostics = 1
            except:
                pass
        
        if is_postgres_enabled():
            alert_stats = get_alerts_stats()
            return jsonify({
                'total_alerts': alert_stats.get('total_alerts', 0),
                'unread_alerts': alert_stats.get('critical_alerts', 0) + alert_stats.get('high_alerts', 0),
                'total_messages': len(_messages_cache),
                'total_diagnostics': total_diagnostics,
                'critical_alerts': alert_stats.get('critical_alerts', 0)
            }), 200
        else:
            # Stats depuis fichier local
            global _alerts_cache
            total = len(_alerts_cache)
            critical = len([a for a in _alerts_cache if a.get('severity') == 'critical'])
            high = len([a for a in _alerts_cache if a.get('severity') == 'high'])
            return jsonify({
                'total_alerts': total,
                'unread_alerts': critical + high,
                'total_messages': len(_messages_cache),
                'total_diagnostics': total_diagnostics,
                'critical_alerts': critical
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Erreur stats: {e}")
        return jsonify({
            'total_alerts': 0,
            'unread_alerts': 0,
            'total_messages': 0,
            'total_diagnostics': 0,
            'critical_alerts': 0
        }), 200

@app.route('/api/receive-alert', methods=['POST'])
def receive_alert():
    """Recevoir une alerte du service IA - Sans auth"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        logger.info(f"🚨 Alerte reçue: {data.get('title', 'N/A')}")
        
        # Créer l'alerte
        alert_id = data.get('alert_id') or f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        alert_data = {
            'id': alert_id,
            'alert_id': alert_id,
            'timestamp': datetime.now().isoformat(),
            'severity': data.get('severity', 'medium'),
            'title': data.get('title', 'Alerte'),
            'message': data.get('message', ''),
            'payload': data,
            'source': 'ia_service',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Sauvegarder en Postgres si disponible
        if is_postgres_enabled():
            try:
                save_alert(alert_data)
                logger.info(f"✅ Alerte sauvegardée en Postgres: {alert_id}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur sauvegarde alerte Postgres: {e}")
        
        # Sauvegarder en fichier local (toujours, pour fallback)
        global _alerts_cache
        _alerts_cache.append(alert_data)
        _save_json_file(ALERTS_FILE, _alerts_cache)
        logger.info(f"✅ Alerte sauvegardée en fichier: {alert_id}")
        
        # Émettre via WebSocket
        socketio.emit('new_alert', alert_data)
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'confidence': 100,
            'status': 'confirmed',
            'occurrences': 1
        }), 201
    
    except Exception as e:
        logger.error(f"❌ Erreur receive_alert: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/receive-diagnostic', methods=['POST'])
def receive_diagnostic():
    """Recevoir un diagnostic - Sans auth"""
    return jsonify({'success': True}), 201

# ==================== WEBSOCKET ====================

@socketio.on('connect')
def handle_connect():
    """Connexion WebSocket"""
    logger.info("🔌 WebSocket connecté")
    emit('connect_response', {'data': 'Connecté au serveur'})

@socketio.on('disconnect')
def handle_disconnect():
    """Déconnexion WebSocket"""
    logger.info("🔌 WebSocket déconnecté")

@socketio.on('send_message')
def handle_send_message(data):
    """
    Recevoir message du technicien et envoyer à l'IA pour réponse
    Communication: Chat → IA Service → Chat (réponse)
    """
    global _messages_cache
    
    content = data.get('content', '').strip()
    model = data.get('model', 'gpt4')  # GPT-4 par défaut
    user_id = data.get('user_id', 'technician_1')
    user_name = data.get('user_name', 'Technicien')
    
    if not content:
        emit('error', {'message': 'Message vide'})
        return False
    
    logger.info(f"💬 Message de {user_name} [modèle: {model}]: {content[:50]}...")
    
    # Message utilisateur - avec ID incrémental
    user_msg = {
        'id': len(_messages_cache) + 1,
        'content': content,
        'is_from_system': False,
        'user_name': user_name,
        'model': model,
        'created_at': datetime.utcnow().isoformat()
    }
    _messages_cache.append(user_msg)
    _save_json_file(MESSAGES_FILE, _messages_cache)  # SAUVEGARDER
    
    socketio.emit('new_message', user_msg)
    emit('typing', {'user': 'IA', 'status': 'typing'})
    
    # Envoyer au service IA pour traitement avec le modèle
    try:
        ia_response = requests.post(
            f"{IA_SERVICE_URL}/api/chat/message",
            json={
                'message': content,
                'user_id': user_id,
                'user_name': user_name,
                'source': 'chat_web',
                'model': model  # Ajouter le modèle demandé
            },
            timeout=30
        )
        
        if ia_response.status_code == 200:
            ia_result = ia_response.json()
            if ia_result.get('success'):
                response_text = ia_result.get('response', 'Je ne peux pas répondre pour le moment.')
                processing_time = ia_result.get('processing_time_ms', 0)
                logger.info(f"✅ Réponse IA reçue en {processing_time}ms")
            else:
                response_text = "Désolé, une erreur s'est produite lors du traitement."
                logger.warning(f"⚠️ IA a retourné une erreur: {ia_result}")
        else:
            response_text = f"Service IA indisponible (HTTP {ia_response.status_code})"
            logger.error(f"❌ Erreur HTTP IA: {ia_response.status_code}")
            
    except requests.Timeout:
        response_text = "Le service IA met trop de temps à répondre. Veuillez réessayer."
        logger.error("❌ Timeout lors de l'appel au service IA")
    except Exception as e:
        response_text = "Erreur de communication avec le service IA."
        logger.error(f"❌ Erreur appel IA: {e}")
    
    # Réponse du système
    sys_msg = {
        'id': len(_messages_cache) + 1,
        'content': response_text,
        'is_from_system': True,
        'user_name': 'IA',
        'model': model,
        'created_at': datetime.utcnow().isoformat()
    }
    _messages_cache.append(sys_msg)
    _save_json_file(MESSAGES_FILE, _messages_cache)  # SAUVEGARDER
    
    socketio.emit('new_message', sys_msg)
    emit('typing', {'user': 'IA', 'status': 'done'})

# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info(" Démarrage du serveur web Flask (SANS AUTHENTIFICATION)")
    logger.info(" Dashboard accessible sans login sur http://localhost:5001/dashboard")
    logger.info("📱 Dashboard accessible sans login sur http://localhost:5001/dashboard")
    # Use threading mode for Windows compatibility
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)
