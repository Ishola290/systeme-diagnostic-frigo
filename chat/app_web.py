"""
Application Flask Web - Interface Web pour Système Diagnostic Frigo
Chat en temps réel + Dashboard Alertes + Historique Diagnostics
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import logging
import requests
from functools import wraps
import sys
from sqlalchemy import text

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # PostgreSQL avec fallback SQLite en développement
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    if FLASK_ENV == 'production':
        # Production: utiliser PostgreSQL (Render fourni DATABASE_URL)
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/chat_app'
    else:
        # Développement: SQLite local
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chat_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIN_APP_URL = os.environ.get('MAIN_APP_URL') or 'http://localhost:5000'
    IA_SERVICE_URL = os.environ.get('IA_SERVICE_URL') or 'http://localhost:5002'
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# Initialisation Flask
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    """Modèle Utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    messages = db.relationship('Message', backref='user', lazy=True, cascade='all, delete-orphan')
    alerts_viewed = db.relationship('Alert', backref='viewer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Alert(db.Model):
    """Modèle Alerte avec validation intelligente"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'error', 'warning', 'info'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    diagnostic_id = db.Column(db.String(100))
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    read_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Nouveaux champs pour validation
    occurrences = db.Column(db.Integer, default=1)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='new')  # new, investigating, confirmed, false_positive
    confidence = db.Column(db.Float, default=0.0)  # 0-100%
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'diagnostic_id': self.diagnostic_id,
            'severity': self.severity,
            'is_read': self.is_read,
            'occurrences': self.occurrences,
            'status': self.status,
            'confidence': round(self.confidence, 1),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_confidence(self):
        """Calcule le score de confiance de l'alerte"""
        base_score = 20.0
        
        # 1️⃣ Augmenter avec occurrences (max +60)
        occurrences_score = min(self.occurrences * 15, 60)
        
        # 2️⃣ Boost de sévérité
        severity_boost = {
            'critical': 25,
            'high': 15,
            'medium': 5,
            'low': 0
        }
        severity_score = severity_boost.get(self.severity, 0)
        
        # 3️⃣ Pattern detection: Même type d'alerte dans les 60 dernières minutes?
        from sqlalchemy import func, and_
        similar_recent = db.session.query(func.count(Alert.id)).filter(
            Alert.title == self.title,
            Alert.created_at > datetime.utcnow() - timedelta(minutes=60),
            Alert.status != 'false_positive'
        ).scalar() or 0
        
        # Si même alerte > 5 fois en 1h = faux positif (cycle normal)
        if similar_recent > 5:
            pattern_score = -30
            logger.info(f"🔄 Pattern cyclique détecté: {self.title} ({similar_recent}x en 1h)")
        else:
            pattern_score = 0
        
        # 4️⃣ Heure du jour (certaines heures = anomalies moins graves)
        hour = self.created_at.hour
        if 0 <= hour < 6:  # Nuit = froid/inactivité normal
            time_score = -15
        elif 12 <= hour < 14:  # Midi = pics normaux
            time_score = -10
        else:
            time_score = 0
        
        # 5️⃣ Calcul final
        total_score = base_score + occurrences_score + severity_score + pattern_score + time_score
        self.confidence = max(0.0, min(total_score, 100.0))
        
        logger.info(f"📊 Confidence calc: {self.title}")
        logger.info(f"   Base: {base_score} + Occurrences: {occurrences_score} + Severity: {severity_score}")
        logger.info(f"   Pattern: {pattern_score} + Time: {time_score} = {self.confidence}%")
        
        return self.confidence

class Message(db.Model):
    """Modèle Message Chat"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_from_system = db.Column(db.Boolean, default=False)  # True si du système
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'content': self.content,
            'is_from_system': self.is_from_system,
            'created_at': self.created_at.isoformat()
        }

class Diagnostic(db.Model):
    """Modèle Historique Diagnostic"""
    __tablename__ = 'diagnostics'
    
    id = db.Column(db.Integer, primary_key=True)
    diagnostic_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    result = db.Column(db.JSON)  # Résultat du diagnostic
    status = db.Column(db.String(50), default='pending')  # pending, completed, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'diagnostic_id': self.diagnostic_id,
            'description': self.description,
            'result': self.result,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# ==================== LOGIN MANAGER ====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== ROUTES AUTHENTIFICATION ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Enregistrement utilisateur"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Utilisateur déjà existant'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email déjà utilisé'}), 400
        
        # Création user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"✅ Nouvel utilisateur enregistré: {username}")
        return jsonify({'success': True, 'message': 'Utilisateur créé avec succès'}), 201
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion utilisateur"""
    if request.method == 'POST':
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Chercher par username OU par email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ Connexion: {user.username} ({user.email})")
            return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200
        
        logger.warning(f"❌ Tentative de connexion échouée: {username_or_email}")
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logger.info(f"🔓 Déconnexion: {current_user.username}")
    logout_user()
    return redirect(url_for('login'))

# ==================== ROUTES PRINCIPALES ====================

@app.route('/')
def index():
    """Page d'accueil"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html', username=current_user.username)

# ==================== ROUTES API ====================

@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Récupérer les alertes"""
    limit = request.args.get('limit', 50, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    query = Alert.query.order_by(Alert.created_at.desc())
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    alerts = query.limit(limit).all()
    return jsonify([alert.to_dict() for alert in alerts]), 200

@app.route('/api/alerts/<int:alert_id>/read', methods=['PUT'])
@login_required
def mark_alert_read(alert_id):
    """Marquer une alerte comme lue"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alerte non trouvée'}), 404
    
    alert.is_read = True
    alert.read_by_user_id = current_user.id
    db.session.commit()
    
    socketio.emit('alert_read', {'alert_id': alert_id}, broadcast=True)
    return jsonify({'success': True}), 200

@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    """Récupérer l'historique des messages"""
    limit = request.args.get('limit', 100, type=int)
    messages = Message.query.order_by(Message.created_at.desc()).limit(limit).all()
    return jsonify([msg.to_dict() for msg in reversed(messages)]), 200

@app.route('/api/messages', methods=['POST'])
@login_required
def create_message():
    """
    Créer un message utilisateur et obtenir réponse du service IA
    Communication fluide: Chat ↔ GPT
    """
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message vide'}), 400
    
    # 1️⃣ Sauvegarder le message de l'utilisateur
    msg = Message(user_id=current_user.id, content=content, is_from_system=False)
    db.session.add(msg)
    db.session.commit()
    
    logger.info(f"💬 Message utilisateur: {current_user.username} - {content[:50]}...")
    
    # 2️⃣ Émettre le message utilisateur via WebSocket (temps réel)
    socketio.emit('new_message', msg.to_dict(), broadcast=True)
    
    # 3️⃣ Appeler le service IA pour réponse
    ai_response_text = None
    error_msg = None
    
    try:
        logger.info(f"📤 Envoi message au service IA ({Config.IA_SERVICE_URL})")
        
        ia_response = requests.post(
            f"{Config.IA_SERVICE_URL}/api/chat/message",
            json={
                'message': content,
                'user_id': str(current_user.id),
                'user_name': current_user.username
            },
            timeout=30  # Augmenté pour Phi-2 CPU
        )
        
        logger.info(f"📥 Réponse service IA: {ia_response.status_code}")
        
        if ia_response.status_code == 200:
            result = ia_response.json()
            if result.get('success'):
                ai_response_text = result.get('response', 'Réponse vide')
                logger.info(f"✅ Réponse IA reçue: {ai_response_text[:50]}...")
            else:
                error_msg = result.get('error', 'Erreur inconnue')
                logger.warning(f"⚠️ Service IA retourné erreur: {error_msg}")
        else:
            error_msg = f"Statut {ia_response.status_code}"
            logger.error(f"❌ Service IA erreur: {error_msg}")
            
    except requests.exceptions.Timeout:
        error_msg = "Timeout (service IA trop lent)"
        logger.error(f"⏱️ Timeout communication avec service IA (30s dépassé)")
    except requests.exceptions.ConnectionError:
        error_msg = "Service IA indisponible"
        logger.error(f"🔌 Impossible de se connecter au service IA ({Config.IA_SERVICE_URL})")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Erreur communication IA: {e}", exc_info=True)
    
    # 4️⃣ Sauvegarder et émettre la réponse
    if ai_response_text:
        sys_msg = Message(
            user_id=1,  # ID du système
            content=ai_response_text,
            is_from_system=True
        )
        db.session.add(sys_msg)
        db.session.commit()
        
        socketio.emit('new_message', sys_msg.to_dict(), broadcast=True)
        logger.info(f"✅ Réponse IA émise via WebSocket")
    elif error_msg:
        # Envoyer message d'erreur
        error_response = f"⚠️ Erreur service IA: {error_msg}\n\nVerifiez que le service GPT est lancé sur {Config.IA_SERVICE_URL}"
        sys_msg = Message(
            user_id=1,
            content=error_response,
            is_from_system=True
        )
        db.session.add(sys_msg)
        db.session.commit()
        
        socketio.emit('new_message', sys_msg.to_dict(), broadcast=True)
        socketio.emit('error', {'message': error_msg}, broadcast=True)
    
    return jsonify(msg.to_dict()), 201

@app.route('/api/diagnostics', methods=['GET'])
@login_required
def get_diagnostics():
    """Récupérer l'historique des diagnostics"""
    limit = request.args.get('limit', 50, type=int)
    diagnostics = Diagnostic.query.order_by(Diagnostic.created_at.desc()).limit(limit).all()
    return jsonify([d.to_dict() for d in diagnostics]), 200

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Statistiques dashboard"""
    total_alerts = Alert.query.count()
    unread_alerts = Alert.query.filter_by(is_read=False).count()
    total_messages = Message.query.count()
    total_diagnostics = Diagnostic.query.count()
    
    return jsonify({
        'total_alerts': total_alerts,
        'unread_alerts': unread_alerts,
        'total_messages': total_messages,
        'total_diagnostics': total_diagnostics,
        'critical_alerts': Alert.query.filter_by(severity='critical', is_read=False).count()
    }), 200

# ==================== ROUTES SYSTÈME (FROM MAIN APP) ====================

@app.route('/api/receive-alert', methods=['POST'])
def receive_alert():
    """
    Recevoir une alerte du service IA
    VALIDATION: Vérifier confiance avant d'envoyer à Telegram
    """
    try:
        data = request.get_json()
        
        # 1️⃣ Chercher si alerte similaire récente existe
        existing_alert = Alert.query.filter(
            Alert.title == data.get('title'),
            Alert.status != 'false_positive',
            Alert.created_at > datetime.utcnow() - timedelta(minutes=5)
        ).first()
        
        if existing_alert:
            # Alerte similaire existe → Incrémenter occurrences
            existing_alert.occurrences += 1
            existing_alert.last_seen = datetime.utcnow()
            existing_alert.updated_at = datetime.utcnow()
            alert = existing_alert
            logger.info(f"🔄 Alerte récurrente: {alert.title} (occurrence #{alert.occurrences})")
        else:
            # Nouvelle alerte
            alert = Alert(
                type=data.get('type', 'info'),
                title=data.get('title', 'Alerte'),
                message=data.get('message', ''),
                diagnostic_id=data.get('diagnostic_id'),
                severity=data.get('severity', 'medium'),
                occurrences=1,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            logger.info(f"🆕 Nouvelle alerte: {alert.title}")
        
        # 2️⃣ Calculer le score de confiance
        confidence = alert.calculate_confidence()
        
        # 3️⃣ DÉCIDER: Envoyer à Telegram ou juste surveiller?
        telegram_sent = False
        
        if confidence >= 70:
            # ✅ Alerte validée → Envoyer à Telegram
            alert.status = 'confirmed'
            
            try:
                telegram_message = f"""
🚨 ALERTE CONFIRMÉE ({confidence:.0f}% confiance)

🔴 {alert.title}
━━━━━━━━━━━━━━━━━━━━━━━
📋 {alert.message}
━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Sévérité: {alert.severity.upper()}
🔢 Occurrences: {alert.occurrences}
🆔 Diagnostic: {alert.diagnostic_id or 'N/A'}
⏰ Première détection: {alert.first_seen.strftime('%H:%M:%S')}

Action requise: Vérifier immédiatement
                """
                
                requests.post(
                    f"{Config.MAIN_APP_URL}/api/telegram/notify",
                    json={'message': telegram_message},
                    timeout=5
                )
                telegram_sent = True
                logger.info(f"✅ Telegram notifié de l'alerte confirmée")
            except Exception as e:
                logger.error(f"❌ Erreur envoi Telegram: {e}")
        
        elif confidence >= 40:
            # ⚠️ Alerte suspecte → Surveiller sans notifier Telegram
            alert.status = 'investigating'
            logger.warning(f"⏳ Alerte en investigation ({confidence:.0f}% confiance): {alert.title}")
        
        else:
            # ❌ Probablement faux positif → Ignorer
            alert.status = 'false_positive'
            logger.warning(f"🔕 Faux positif détecté ({confidence:.0f}%): {alert.title}")
        
        db.session.add(alert)
        db.session.commit()
        
        # 4️⃣ Émettre via WebSocket (tous les alertes, y compris investigations)
        socketio.emit('new_alert', alert.to_dict(), broadcast=True)
        
        return jsonify({
            'success': True,
            'alert_id': alert.id,
            'confidence': confidence,
            'status': alert.status,
            'telegram_sent': telegram_sent,
            'occurrences': alert.occurrences
        }), 201
    
    except Exception as e:
        logger.error(f"❌ Erreur receive_alert: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/receive-diagnostic', methods=['POST'])
def receive_diagnostic():
    """Recevoir un diagnostic de l'app principale"""
    data = request.get_json()
    
    diagnostic = Diagnostic(
        diagnostic_id=data.get('diagnostic_id'),
        description=data.get('description'),
        result=data.get('result'),
        status=data.get('status', 'completed'),
        completed_at=datetime.utcnow() if data.get('status') == 'completed' else None
    )
    db.session.add(diagnostic)
    db.session.commit()
    
    logger.info(f"📋 Diagnostic reçu: {diagnostic.diagnostic_id}")
    
    # Émettre via WebSocket
    socketio.emit('new_diagnostic', diagnostic.to_dict(), broadcast=True)
    
    return jsonify({'success': True, 'diagnostic_id': diagnostic.id}), 201

# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Connexion WebSocket"""
    if current_user.is_authenticated:
        logger.info(f"🔌 WebSocket connecté: {current_user.username}")
        emit('connect_response', {'data': 'Connecté au serveur'})
    else:
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Déconnexion WebSocket"""
    logger.info(f"🔌 WebSocket déconnecté")

@socketio.on('send_message')
def handle_send_message(data):
    """
    WebSocket: Recevoir message et envoyer réponse IA en temps réel
    Communication ultra-fluide avec retry automatique
    """
    if not current_user.is_authenticated:
        return False
    
    content = data.get('content', '').strip()
    if not content:
        return False
    
    logger.info(f"🔴 WebSocket message de {current_user.username}: {content[:50]}...")
    
    # 1️⃣ Sauvegarder et broadcaster le message utilisateur
    msg = Message(user_id=current_user.id, content=content, is_from_system=False)
    db.session.add(msg)
    db.session.commit()
    
    emit('new_message', msg.to_dict(), broadcast=True)
    emit('message_sent')  # Confirmation à l'expéditeur
    
    # 2️⃣ Appeler service IA et attendre réponse (avec retry)
    max_retries = 2
    ai_response_text = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 [Tentative {attempt+1}/{max_retries}] Envoi à service IA...")
            
            ia_response = requests.post(
                f"{Config.IA_SERVICE_URL}/api/chat/message",
                json={
                    'message': content,
                    'user_id': str(current_user.id),
                    'user_name': current_user.username,
                    'source': 'websocket'
                },
                timeout=30  # Généreux: gpt2 ultra-rapide ~3-5s, avec marge
            )
            
            if ia_response.status_code == 200:
                result = ia_response.json()
                if result.get('success'):
                    ai_response_text = result.get('response')
                    logger.info(f"✅ Réponse IA (tentative {attempt+1}): {ai_response_text[:60]}...")
                    break
                else:
                    logger.warning(f"⚠️ Service IA erreur: {result.get('error')}")
            else:
                logger.warning(f"⚠️ Service IA statut {ia_response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout tentative {attempt+1} (>30s)")
            if attempt < max_retries - 1:
                emit('typing', {'user': 'Système', 'status': 'retry'})
                
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Impossible connexion service IA (tentative {attempt+1})")
            
        except Exception as e:
            logger.error(f"❌ Erreur IA tentative {attempt+1}: {e}")
    
    # 3️⃣ Broadcaster la réponse IA
    if ai_response_text:
        sys_msg = Message(
            user_id=1,
            content=ai_response_text,
            is_from_system=True
        )
        db.session.add(sys_msg)
        db.session.commit()
        
        emit('new_message', sys_msg.to_dict(), broadcast=True)
        emit('typing', {'user': 'Système', 'status': 'done'})
        logger.info(f"✅ Réponse émise via WebSocket")
    else:
        # Message d'erreur gracieux
        error_msg = f"⚠️ Service IA indisponible. Vérifiez que le service est lancé sur {Config.IA_SERVICE_URL}"
        sys_msg = Message(
            user_id=1,
            content=error_msg,
            is_from_system=True
        )
        db.session.add(sys_msg)
        db.session.commit()
        
        emit('new_message', sys_msg.to_dict(), broadcast=True)
        emit('error', {'message': 'Service IA indisponible'}, broadcast=True)
        logger.error(f"❌ Échec récupération réponse IA après {max_retries} tentatives")

@socketio.on('request_system_response')
def handle_system_request(data):
    """Demander une réponse du service IA"""
    if not current_user.is_authenticated:
        return False
    
    query = data.get('query', '').strip()
    if not query:
        return False
    
    try:
        # Appeler le service IA directement
        ia_response = requests.post(
            f"{Config.IA_SERVICE_URL}/api/chat/message",
            json={
                'message': query,
                'user_id': current_user.id,
                'user_name': current_user.username
            },
            timeout=10
        )
        
        if ia_response.status_code == 200:
            result = ia_response.json()
            system_response = result.get('response', 'Pas de réponse')
            
            # Sauvegarder la réponse du service IA
            sys_msg = Message(
                user_id=1,  # ID du système
                content=system_response,
                is_from_system=True
            )
            db.session.add(sys_msg)
            db.session.commit()
            
            emit('system_response', sys_msg.to_dict(), broadcast=True)
            logger.info(f"✅ Réponse système IA pour: {query[:50]}")
    except Exception as e:
        logger.error(f"❌ Erreur system response IA: {e}")
        emit('system_error', {'error': str(e)})

# ==================== DÉMARRAGE ====================

def init_db():
    """Initialiser la base de données"""
    with app.app_context():
        # Crée les tables si elles n'existent pas
        db.create_all()

        # Pour les bases SQLite déjà existantes, s'assurer que les nouvelles
        # colonnes (introduites après une évolution du modèle) existent.
        try:
            conn = db.engine.connect()
            res = conn.execute(text("PRAGMA table_info('alerts')")).fetchall()
            existing_cols = [r[1] for r in res]

            added = False
            if 'occurrences' not in existing_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN occurrences INTEGER DEFAULT 1"))
                added = True
            if 'first_seen' not in existing_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN first_seen DATETIME"))
                added = True
            if 'last_seen' not in existing_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN last_seen DATETIME"))
                added = True
            if 'status' not in existing_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN status VARCHAR(50) DEFAULT 'new'"))
                added = True
            if 'confidence' not in existing_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN confidence FLOAT DEFAULT 0.0"))
                added = True

            if added:
                logger.info("✅ Colonnes manquantes ajoutées à la table alerts")

        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification/migration DB: {e}", exc_info=True)

        logger.info("✅ Base de données initialisée")

if __name__ == '__main__':
    init_db()
    logger.info("🚀 Démarrage du serveur web Flask")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
