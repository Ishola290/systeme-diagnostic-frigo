"""
API Flask - Service IA Local
Endpoints pour traiter les messages et alertes
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

# Import du service IA
from ia_service import get_ia_service

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ia_service.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialisation Flask
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False

# URLs des services
CHAT_SERVICE_URL = os.environ.get('CHAT_API_URL', 'http://localhost:5001')
TELEGRAM_SERVICE_URL = os.environ.get('MAIN_API_URL', 'http://localhost:5000')  # Pour appel Telegram via app.py

# Service IA
ia_service = None
_initialized = False

def init_ia_service():
    """Initialiser le service IA au démarrage"""
    global ia_service, _initialized
    if not _initialized:
        # Lire le modèle depuis env var IA_MODEL
        # Si non spécifié, auto-sélection selon ressources
        model_choice = os.environ.get('IA_MODEL')
        
        if model_choice:
            logger.info(f"📦 Modèle IA depuis env IA_MODEL: {model_choice}")
        else:
            logger.info(f"📦 Auto-sélection du modèle IA selon ressources disponibles")
        
        ia_service = get_ia_service(model_choice)
        _initialized = True
        logger.info("✅ Service IA initialisé")

# Hook pour initialiser avant la première requête (compatible Flask 3.0)
@app.before_request
def ensure_initialized():
    """Assurer l'initialisation du service IA"""
    global _initialized
    if not _initialized:
        init_ia_service()

# ==================== ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check du service"""
    return jsonify({
        'status': 'ok',
        'service': 'IA Local',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/chat/message', methods=['POST'])
def process_chat_message():
    """
    Traiter un message du chat
    Fluide + Logging détaillé + Gestion erreurs gracieuse
    
    Request:
        {
            "message": "Message utilisateur",
            "user_id": "user123",
            "user_name": "admin",
            "source": "websocket|rest"
        }
    
    Response:
        {
            "success": true,
            "response": "Réponse du service IA",
            "intent": "diagnostic",
            "processing_time_ms": 1234,
            "model": "phi",
            "timestamp": "..."
        }
    """
    import time
    start_time = time.time()
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        user_name = data.get('user_name', 'Utilisateur')
        source = data.get('source', 'rest')
        
        if not message:
            logger.warning(f"⚠️ Message vide reçu de {user_id}")
            return jsonify({
                'success': False,
                'error': 'Message vide'
            }), 400
        
        logger.info(f"💬 [{source}] Message de {user_name} ({user_id}): {message[:50]}...")
        
        # Traiter le message via le service IA
        if not ia_service:
            logger.error("❌ Service IA non initialisé")
            return jsonify({
                'success': False,
                'error': 'Service IA non disponible'
            }), 503
        
        result = ia_service.process_chat_message(message, user_id)
        
        # Ajouter temps de traitement
        processing_time_ms = int((time.time() - start_time) * 1000)
        result['processing_time_ms'] = processing_time_ms
        
        logger.info(f"✅ Réponse générée en {processing_time_ms}ms pour {user_name}")
        
        return jsonify(result), 200 if result['success'] else 500
    
    except Exception as e:
        logger.error(f"❌ ERREUR traitement message: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erreur traitement: {str(e)}'
        }), 500

@app.route('/api/alerts/process', methods=['POST'])
def process_alert():
    """
    Traiter une alerte depuis app.py
    Enrichir → Envoyer au Chat Web → Envoyer à Telegram
    
    Request:
        {
            "type": "error",
            "title": "Titre alerte",
            "message": "Message d'alerte",
            "severity": "critical",
            "diagnostic_id": "..."
        }
    
    Response:
        {
            "success": true,
            "alert": {
                "...original fields...",
                "processed": true,
                "severity_score": 3.5,
                "suggested_solutions": [...]
            }
        }
    """
    try:
        alert_data = request.get_json()
        logger.info(f"🚨 Alerte reçue: {alert_data.get('title', 'N/A')}")
        
        # 1️⃣ Traiter l'alerte avec le service IA
        processed_alert = ia_service.process_alert(alert_data)
        
        # 2️⃣ Envoyer au Chat Web
        try:
            chat_payload = {
                'type': alert_data.get('type', 'error'),
                'title': alert_data.get('title', 'Alerte'),
                'message': processed_alert.get('analysis', alert_data.get('message', '')),
                'diagnostic_id': alert_data.get('diagnostic_id'),
                'severity': alert_data.get('severity', 'medium')
            }
            
            chat_response = requests.post(
                f"{CHAT_SERVICE_URL}/api/receive-alert",
                json=chat_payload,
                timeout=5
            )
            
            if chat_response.status_code == 201:
                logger.info(f"✅ Alerte envoyée au Chat Web")
            else:
                logger.warning(f"⚠️ Chat Web retourné {chat_response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erreur envoi Chat Web: {e}")
        
        # 3️⃣ Envoyer notification à Telegram via app.py
        try:
            telegram_payload = {
                'message': f"🚨 {alert_data.get('title', 'Alerte')}\n\n{processed_alert.get('analysis', alert_data.get('message', ''))}"
            }
            
            telegram_response = requests.post(
                f"{TELEGRAM_SERVICE_URL}/api/telegram/notify",
                json=telegram_payload,
                timeout=5
            )
            
            if telegram_response.status_code == 200:
                logger.info(f"✅ Notification Telegram envoyée")
            else:
                logger.warning(f"⚠️ Telegram retourné {telegram_response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erreur envoi Telegram: {e}")
        
        return jsonify({
            'success': True,
            'alert': processed_alert,
            'chat_notified': True,
            'telegram_notified': True
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur traitement alerte: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/knowledge/add', methods=['POST'])
def add_knowledge():
    """
    Ajouter une entrée à la base de connaissances
    
    Request:
        {
            "topic": "Clé",
            "content": "Contenu"
        }
    
    Response:
        {
            "success": true,
            "message": "Entrée ajoutée"
        }
    """
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        content = data.get('content', '').strip()
        
        if not topic or not content:
            return jsonify({'error': 'Topic et content requis'}), 400
        
        ia_service.add_to_knowledge_base(topic, content)
        
        logger.info(f"✅ Entrée KB ajoutée: {topic}")
        return jsonify({
            'success': True,
            'message': f'Entrée "{topic}" ajoutée'
        }), 201
    
    except Exception as e:
        logger.error(f"❌ Erreur ajout KB: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Obtenir les statistiques du service
    
    Response:
        {
            "model": "phi",
            "messages_processed": 123,
            "knowledge_base_size": 45,
            "uptime": "..."
        }
    """
    try:
        stats = ia_service.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"❌ Erreur récupération stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """
    Lister les modèles disponibles
    
    Response:
        {
            "available_models": {
                "mistral": "mistral-7b-instruct",
                ...
            },
            "current_model": "phi"
        }
    """
    from ia_service import IAConfig
    config = IAConfig()
    return jsonify({
        'available_models': config.MODEL_OPTIONS,
        'current_model': ia_service.model_name
    }), 200

@app.route('/api/diagnostic/analyze', methods=['POST'])
def analyze_diagnostic():
    """
    Analyser les données de diagnostic et proposer des solutions
    
    Request:
        {
            "symptoms": ["température élevée", "bruit"],
            "measurements": {
                "temperature": 35,
                "pressure_hp": 15,
                ...
            }
        }
    
    Response:
        {
            "success": true,
            "diagnosis": "...",
            "solutions": [...],
            "confidence": 0.85
        }
    """
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        measurements = data.get('measurements', {})
        
        logger.info(f"🔍 Diagnostic: {symptoms}")
        
        # Construire un message pour le service IA
        diagnostic_msg = f"Diagnostic: {', '.join(symptoms)}"
        
        # Traiter via le service IA
        result = ia_service.process_chat_message(diagnostic_msg, 'diagnostic_system')
        
        return jsonify({
            'success': True,
            'diagnosis': result['response'],
            'symptoms': symptoms,
            'intent': result['intent']
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur diagnostic: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/learn', methods=['POST'])
def learn():
    """
    Permettre au système d'apprendre de nouveaux cas
    
    Request:
        {
            "case": "Description du cas",
            "solution": "Solution trouvée",
            "confidence": 0.9
        }
    
    Response:
        {
            "success": true,
            "message": "Cas d'apprentissage enregistré"
        }
    """
    try:
        data = request.get_json()
        case = data.get('case', '').strip()
        solution = data.get('solution', '').strip()
        confidence = data.get('confidence', 0.8)
        
        if not case or not solution:
            return jsonify({'error': 'Case et solution requis'}), 400
        
        # Sauvegarder comme entrée KB
        ia_service.add_to_knowledge_base(
            f"learned_{case[:20]}",
            {
                'case': case,
                'solution': solution,
                'confidence': confidence,
                'learned_at': datetime.now().isoformat()
            }
        )
        
        logger.info(f"📚 Apprentissage: {case[:30]}...")
        return jsonify({
            'success': True,
            'message': 'Cas d\'apprentissage enregistré'
        }), 201
    
    except Exception as e:
        logger.error(f"❌ Erreur apprentissage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/finetune/info', methods=['GET'])
def finetune_info():
    """
    📊 Endpoint pour obtenir les infos du fine-tuning
    
    Utilisation:
        GET http://localhost:5002/api/finetune/info
    
    Réponse:
        {
            "available": true,
            "description": "Fine-tuning sur mesure des modèles...",
            "supported_models": [...],
            "supported_formats": ["csv", "jsonl"],
            "examples": {...}
        }
    """
    return jsonify({
        'available': True,
        'description': 'Fine-tuning sur mesure pour domaine frigorifique',
        'supported_models': ['phi', 'phi2', 'mistral', 'neural'],
        'supported_formats': ['csv', 'jsonl'],
        'endpoints': {
            'start': {
                'method': 'POST',
                'path': '/api/finetune/start',
                'description': 'Démarre le fine-tuning asynchrone',
                'params': {
                    'model': 'Modèle à fine-tuner (phi, mistral, etc)',
                    'dataset_url': 'URL ou chemin du dataset',
                    'epochs': 'Nombre epochs (default: 3)',
                    'batch_size': 'Batch size (default: 4)',
                    'learning_rate': 'Learning rate (default: 2e-5)'
                }
            },
            'status': {
                'method': 'GET',
                'path': '/api/finetune/status/{job_id}',
                'description': 'Obtenir le statut du fine-tuning'
            },
            'models': {
                'method': 'GET',
                'path': '/api/finetune/models',
                'description': 'Lister les modèles fine-tunés'
            }
        },
        'examples': {
            'quick_start': {
                'description': 'Fine-tune phi sur données locales',
                'curl': 'curl -X POST http://localhost:5002/api/finetune/start -H "Content-Type: application/json" -d \'{"model": "phi", "dataset_url": "data/frigo_training.csv"}\'',
                'python': 'requests.post("http://localhost:5002/api/finetune/start", json={"model": "phi", "dataset_url": "data/frigo_training.csv"})'
            },
            'full_config': {
                'description': 'Fine-tune mistral avec config complète',
                'curl': 'curl -X POST http://localhost:5002/api/finetune/start -H "Content-Type: application/json" -d \'{"model": "mistral", "dataset_url": "https://example.com/data.jsonl", "epochs": 5, "batch_size": 2, "learning_rate": 1e-5}\'',
                'python': 'requests.post("http://localhost:5002/api/finetune/start", json={"model": "mistral", "dataset_url": "https://example.com/data.jsonl", "epochs": 5, "batch_size": 2})'
            }
        }
    }), 200


@app.route('/api/finetune/start', methods=['POST'])
def start_finetune():
    """
    🎯 Endpoint pour démarrer le fine-tuning en production
    
    Déclenche le réentraînement asynchrone d'un modèle sur des données frigo-spécifiques
    
    Utilisation:
        POST http://localhost:5002/api/finetune/start
        Content-Type: application/json
        
        {
            "model": "phi",
            "dataset_url": "data/frigo_training.csv",
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 2e-5
        }
    
    Réponse:
        {
            "status": "started",
            "job_id": "ft_20240115_103045_12345",
            "message": "Fine-tuning lancé",
            "config": {...}
        }
    """
    try:
        import subprocess
        import threading
        import uuid
        from datetime import datetime as dt
        
        # Paramètres par défaut
        params = request.get_json() or {}
        model = params.get('model', 'phi')
        dataset_url = params.get('dataset_url')
        epochs = params.get('epochs', 3)
        batch_size = params.get('batch_size', 4)
        learning_rate = params.get('learning_rate', 2e-5)
        
        # Validation
        if not dataset_url:
            logger.warning("⚠️  Pas de dataset_url fourni")
            return jsonify({'error': 'dataset_url requis'}), 400
        
        if model not in ['phi', 'phi2', 'mistral', 'neural', 'gpt2']:
            return jsonify({'error': f'Modèle non supporté: {model}'}), 400
        
        if not (1 <= epochs <= 20):
            return jsonify({'error': 'epochs doit être entre 1 et 20'}), 400
        
        if not (1 <= batch_size <= 16):
            return jsonify({'error': 'batch_size doit être entre 1 et 16'}), 400
        
        # Générer job ID unique
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        job_id = f"ft_{timestamp}_{str(uuid.uuid4())[:8]}"
        
        # Préparer la commande fine-tuning
        cmd = [
            'python',
            'fine_tune.py',
            '--model', model,
            '--data', dataset_url,
            '--epochs', str(epochs),
            '--batch-size', str(batch_size),
            '--learning-rate', str(learning_rate),
            '--job-id', job_id
        ]
        
        logger.info(f"🚀 Démarrage fine-tuning [JOB: {job_id}]")
        logger.info(f"   Modèle: {model}")
        logger.info(f"   Dataset: {dataset_url}")
        logger.info(f"   Config: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")
        
        # Lancer le fine-tuning en arrière-plan (thread daemon)
        def run_finetune():
            try:
                # Changer vers le répertoire parent (où fine_tune.py existe)
                import os
                original_dir = os.getcwd()
                os.chdir('..')
                
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                os.chdir(original_dir)
                logger.info(f"✅ Fine-tuning terminé [JOB: {job_id}]")
                logger.info(f"   Modèle fine-tuné sauvegardé: models/{model}-finetuned-{timestamp}/")
            
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Fine-tuning échoué [JOB: {job_id}]: {e.stderr}")
            except Exception as e:
                logger.error(f"❌ Exception fine-tuning [JOB: {job_id}]: {e}")
        
        # Lancer dans un thread séparé (non-bloquant)
        thread = threading.Thread(target=run_finetune, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'started',
            'job_id': job_id,
            'message': f'Fine-tuning lancé pour {model}',
            'config': {
                'model': model,
                'dataset': dataset_url,
                'epochs': epochs,
                'batch_size': batch_size,
                'learning_rate': learning_rate
            },
            'timestamp': dt.now().isoformat()
        }), 202
    
    except Exception as e:
        logger.error(f"❌ Erreur démarrage fine-tuning: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Erreur lors du démarrage du fine-tuning'
        }), 500


@app.route('/api/finetune/status/<job_id>', methods=['GET'])
def finetune_status(job_id):
    """
    📊 Vérifier le statut du fine-tuning
    
    Utilisation:
        GET http://localhost:5002/api/finetune/status/ft_20240115_103045_abc123
    
    Réponse:
        {
            "job_id": "ft_...",
            "status": "running|completed|failed",
            "progress": 0.65,
            "eta_seconds": 180,
            "model_path": "models/phi-finetuned-20240115_103045/"
        }
    """
    try:
        import os
        from pathlib import Path
        
        # Chercher le modèle fine-tuné associé
        models_dir = Path('../models')
        
        # Format du dossier: {model}-finetuned-{timestamp}
        timestamp = job_id.split('_')[1:3]  # Extraire timestamp du job_id
        timestamp_str = '_'.join(timestamp) if len(timestamp) >= 2 else None
        
        status = 'unknown'
        model_path = None
        progress = 0.0
        
        if timestamp_str and models_dir.exists():
            # Chercher un dossier correspondant
            for model_dir in models_dir.glob('*-finetuned-*'):
                if timestamp_str in str(model_dir):
                    status = 'completed'
                    model_path = str(model_dir)
                    progress = 1.0
                    break
        
        return jsonify({
            'job_id': job_id,
            'status': status,
            'progress': progress,
            'model_path': model_path,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur statut fine-tuning: {e}")
        return jsonify({
            'error': str(e),
            'job_id': job_id,
            'status': 'unknown'
        }), 500


@app.route('/api/finetune/models', methods=['GET'])
def list_finetuned_models():
    """
    📚 Lister les modèles fine-tunés disponibles
    
    Utilisation:
        GET http://localhost:5002/api/finetune/models
    
    Réponse:
        {
            "models": [
                {
                    "name": "phi-finetuned-20240115_103045",
                    "base_model": "phi",
                    "created": "2024-01-15T10:30:45",
                    "size_mb": 2540,
                    "latest": true
                },
                ...
            ]
        }
    """
    try:
        from pathlib import Path
        import os
        
        models_dir = Path('../models')
        finetuned_models = []
        
        if models_dir.exists():
            for model_dir in models_dir.glob('*-finetuned-*'):
                if model_dir.is_dir():
                    # Extraire infos
                    model_name = model_dir.name
                    base_model = model_name.split('-finetuned-')[0]
                    
                    # Taille du dossier
                    size_mb = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, _, filenames in os.walk(model_dir)
                        for filename in filenames
                    ) / (1024 * 1024)
                    
                    # Date de création
                    created = datetime.fromtimestamp(model_dir.stat().st_mtime).isoformat()
                    
                    finetuned_models.append({
                        'name': model_name,
                        'base_model': base_model,
                        'created': created,
                        'size_mb': round(size_mb, 2),
                        'path': str(model_dir)
                    })
        
        # Trier par date décroissante
        finetuned_models.sort(key=lambda x: x['created'], reverse=True)
        
        # Marquer le plus récent
        if finetuned_models:
            finetuned_models[0]['latest'] = True
        
        return jsonify({
            'models': finetuned_models,
            'total': len(finetuned_models),
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Erreur listing modèles: {e}")
        return jsonify({
            'error': str(e),
            'models': []
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Endpoint non trouvé"""
    return jsonify({'error': 'Endpoint non trouvé'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Erreur interne"""
    logger.error(f"❌ Erreur interne: {error}")
    return jsonify({'error': 'Erreur interne du serveur'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info("🚀 Démarrage du service IA local")
    logger.info("📝 Endpoints disponibles:")
    logger.info("   POST /api/chat/message - Traiter message chat")
    logger.info("   POST /api/alerts/process - Traiter alerte")
    logger.info("   POST /api/knowledge/add - Ajouter à KB")
    logger.info("   GET  /api/stats - Statistiques")
    logger.info("   GET  /api/models - Modèles disponibles")
    logger.info("   POST /api/diagnostic/analyze - Analyser diagnostic")
    logger.info("   POST /api/learn - Apprentissage")
    logger.info("   🔬 FINE-TUNING:")
    logger.info("   GET  /api/finetune/info - Info fine-tuning")
    logger.info("   POST /api/finetune/start - Démarrer fine-tuning")
    logger.info("   GET  /api/finetune/status/{job_id} - Statut job")
    logger.info("   GET  /api/finetune/models - Lister modèles")
    logger.info("   GET  /health - Health check")
    
    app.run(host='0.0.0.0', port=5002, debug=False)
