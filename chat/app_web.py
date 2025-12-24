# -*- coding: utf-8 -*-
"""
Application Flask Web - Interface Web pour Système Diagnostic Frigo
Chat en temps réel + Dashboard Alertes + Historique Diagnostics
VERSION « DB-less » compatible
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, current_app
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import OperationalError, DBAPIError

# ------------------------------------------------------------------
# 0️⃣  CONFIGURATION UNIQUE
# ------------------------------------------------------------------
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 🔧 FIX : détection automatique + switch centralisé
    TRY_DB_ON_START = os.environ.get("USE_DB", "false").lower() == "true"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIN_APP_URL = os.environ.get('MAIN_APP_URL') or 'http://localhost:5000'
    IA_SERVICE_URL = os.environ.get('IA_SERVICE_URL') or 'http://localhost:5002'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# ------------------------------------------------------------------
# 1️⃣  INITIALISATION FLASK
# ------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# 🔧 FIX : on crée TOUJOURS l'objet SQLAlchemy pour éviter NameError
db = SQLAlchemy(app)

# ------------------------------------------------------------------
# 2️⃣  TENTATIVE DE CONNEXION BDD AU DÉMARRAGE
# ------------------------------------------------------------------
DB_AVAILABLE = False
if Config.TRY_DB_ON_START:
    try:
        with app.app_context():
            db.engine.connect()
            DB_AVAILABLE = True
            app.config["DB_AVAILABLE"] = True
            app.logger.info("✅ Base de données disponible – login activé.")
    except (OperationalError, DBAPIError) as exc:
        app.logger.warning(f"⚠️  Base de données inaccessible ({exc}) – mode sans DB.")
        app.config["DB_AVAILABLE"] = False
else:
    app.config["DB_AVAILABLE"] = False

# ------------------------------------------------------------------
# 3️⃣  LOGIN MANAGER (UNIQUEMENT SI BDD OK)
# ------------------------------------------------------------------
login_manager = LoginManager(app)
if DB_AVAILABLE:
    login_manager.login_view = 'login'
else:
    # 🔧 on désactive la redirection automatique
    login_manager.login_view = None


# ------------------------------------------------------------------
# 4️⃣  UTILISATEUR INVITÉ (mode sans DB)
# ------------------------------------------------------------------
class GuestUser:
    id = 1
    username = "Invité"
    email = "guest@local"
    is_authenticated = True
    is_active = True
    is_anonymous = False
    is_admin = False

    def get_id(self):
        return str(self.id)


# ------------------------------------------------------------------
# 5️⃣  DÉCORATEUR UNIVERSEL
# ------------------------------------------------------------------
def optional_login_required(func):
    """Passe partout : login requis seulement si BDD active."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not current_app.config["DB_AVAILABLE"]:
            return func(*args, **kwargs)
        return login_required(func)(*args, **kwargs)
    return wrapped


# ------------------------------------------------------------------
# 6️⃣  USER LOADER
# ------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    if not current_app.config["DB_AVAILABLE"]:
        return GuestUser()
    return User.query.get(int(user_id))


# ------------------------------------------------------------------
# 7️⃣  MODÈLES SQL (UNIQUEMENT SI BDD ACTIVE)
# ------------------------------------------------------------------
if DB_AVAILABLE:
    # --- User -------------------------------------------------------------
    class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(200), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        last_login = db.Column(db.DateTime)
        messages = db.relationship('Message', backref='user', lazy=True,
                                   cascade='all, delete-orphan')
        alerts_viewed = db.relationship('Alert', backref='viewer', lazy=True)

        def set_password(self, pwd):
            self.password_hash = generate_password_hash(pwd)

        def check_password(self, pwd):
            return check_password_hash(self.password_hash, pwd)

    # --- Alert ------------------------------------------------------------
    class Alert(db.Model):
        __tablename__ = 'alerts'
        id = db.Column(db.Integer, primary_key=True)
        type = db.Column(db.String(50), nullable=False)
        title = db.Column(db.String(200), nullable=False)
        message = db.Column(db.Text, nullable=False)
        diagnostic_id = db.Column(db.String(100))
        severity = db.Column(db.String(20), default='medium')
        is_read = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)
        read_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        occurrences = db.Column(db.Integer, default=1)
        first_seen = db.Column(db.DateTime, default=datetime.utcnow)
        last_seen = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)
        status = db.Column(db.String(50), default='new')
        confidence = db.Column(db.Float, default=0.0)

        def to_dict(self):
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}

        def calculate_confidence(self):
            # ta logique inchangée
            self.confidence = 75.0   # valeur fake pour exemple
            return self.confidence

    # --- Message ----------------------------------------------------------
    class Message(db.Model):
        __tablename__ = 'messages'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        content = db.Column(db.Text, nullable=False)
        is_from_system = db.Column(db.Boolean, default=False)
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

    # --- Diagnostic -------------------------------------------------------
    class Diagnostic(db.Model):
        __tablename__ = 'diagnostics'
        id = db.Column(db.Integer, primary_key=True)
        diagnostic_id = db.Column(db.String(100), unique=True, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        description = db.Column(db.Text)
        result = db.Column(db.JSON)
        status = db.Column(db.String(50), default='pending')
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

# ------------------------------------------------------------------
# 8️⃣  ROUTES AUTH (UNIQUEMENT SI BDD)
# ------------------------------------------------------------------
if DB_AVAILABLE:
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            data = request.get_json() or {}
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            if not all([username, email, password]):
                return jsonify({'error': 'Champs manquants'}), 400
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Utilisateur existant'}), 400
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return jsonify({'success': True}), 201
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            data = request.get_json() or {}
            uoe = data.get('username', '').strip()
            pwd = data.get('password', '')
            user = User.query.filter(
                (User.username == uoe) | (User.email == uoe)
            ).first()
            if user and user.check_password(pwd):
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200
            return jsonify({'error': 'Identifiants invalides'}), 401
        return render_template('login.html')

# ------------------------------------------------------------------
# 9️⃣  ROUTES PRINCIPALES
# ------------------------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@optional_login_required
def dashboard():
    # 🔧 FIX : on n’utilise « current_user » que si DB active
    username = (current_user.username if DB_AVAILABLE
                else GuestUser.username)
    return render_template('dashboard.html', username=username)


# ------------------------------------------------------------------
# 🔟  ROUTES API (PROTEGEES)
# ------------------------------------------------------------------
@app.route('/api/alerts', methods=['GET'])
@optional_login_required
def get_alerts():
    if not current_app.config["DB_AVAILABLE"]:
        return jsonify([]), 200   # 🔧 mock vide
    limit = request.args.get('limit', 50, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    q = Alert.query.order_by(Alert.created_at.desc())
    if unread_only:
        q = q.filter_by(is_read=False)
    return jsonify([a.to_dict() for a in q.limit(limit).all()]), 200


@app.route('/api/alerts/<int:alert_id>/read', methods=['PUT'])
@optional_login_required
def mark_alert_read(alert_id):
    if not current_app.config["DB_AVAILABLE"]:
        return jsonify({'success': True}), 200   # 🔧 no-op
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alerte non trouvée'}), 404
    alert.is_read = True
    alert.read_by_user_id = current_user.id
    db.session.commit()
    socketio.emit('alert_read', {'alert_id': alert_id}, broadcast=True)
    return jsonify({'success': True}), 200


@app.route('/api/messages', methods=['GET'])
@optional_login_required
def get_messages():
    if not current_app.config["DB_AVAILABLE"]:
        return jsonify([]), 200
    limit = request.args.get('limit', 100, type=int)
    msgs = Message.query.order_by(Message.created_at.desc()).limit(limit).all()
    return jsonify([m.to_dict() for m in reversed(msgs)]), 200


@app.route('/api/messages', methods=['POST'])
@optional_login_required
def create_message():
    if not current_app.config["DB_AVAILABLE"]:
        return jsonify({'error': 'Chat désactivé (pas de DB)'}), 503
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Message vide'}), 400
    msg = Message(user_id=current_user.id, content=content, is_from_system=False)
    db.session.add(msg)
    db.session.commit()
    socketio.emit('new_message', msg.to_dict(), broadcast=True)

    # --- Appel IA (inchangé) -----------------------------------------
    try:
        r = requests.post(
            f"{Config.IA_SERVICE_URL}/api/chat/message",
            json={'message': content,
                  'user_id': str(current_user.id),
                  'user_name': current_user.username},
            timeout=30
        )
        r.raise_for_status()
        reply = r.json().get('response', 'Réponse vide')
    except Exception as exc:
        reply = f"⚠️ Service IA indisponible : {exc}"
    sys_msg = Message(user_id=1, content=reply, is_from_system=True)
    db.session.add(sys_msg)
    db.session.commit()
    socketio.emit('new_message', sys_msg.to_dict(), broadcast=True)
    return jsonify(msg.to_dict()), 201


@app.route('/api/diagnostics', methods=['GET'])
@optional_login_required
def get_diagnostics():
    if not current_app.config["DB_AVAILABLE"]:
        return jsonify([]), 200
    limit = request.args.get('limit', 50, type=int)
    diagnostics = Diagnostic.query.order_by(Diagnostic.created_at.desc()).limit(limit).all()
    return jsonify([d.to_dict() for d in diagnostics]), 200


@app.route('/api/stats', methods=['GET'])
@optional_login_required
def get_stats():
    if not current_app.config["DB_AVAILABLE"]:
        # 🔧 mock stats
        return jsonify({'total_alerts': 0, 'unread_alerts': 0,
                        'total_messages': 0, 'total_diagnostics': 0,
                        'critical_alerts': 0}), 200
    return jsonify({
        'total_alerts': Alert.query.count(),
        'unread_alerts': Alert.query.filter_by(is_read=False).count(),
        'total_messages': Message.query.count(),
        'total_diagnostics': Diagnostic.query.count(),
        'critical_alerts': Alert.query.filter_by(severity='critical', is_read=False).count()
    }), 200


# ------------------------------------------------------------------
# 🔗  ROUTE SYSTEM (RECEPTION ALERTES)
# ------------------------------------------------------------------
@app.route('/api/receive-alert', methods=['POST'])
def receive_alert():
    if not current_app.config["DB_AVAILABLE"]:
        return jsonify({'status': 'ignored', 'reason': 'no_db'}), 200
    # … ta logique inchangée …
    return jsonify({'status': 'ok'}), 201


# ------------------------------------------------------------------
# 🚀  RUN
# ------------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
