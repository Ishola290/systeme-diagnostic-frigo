"""
Application Flask - Système de Diagnostic Frigorifique avec IA
Remplace le workflow n8n avec toutes les fonctionnalités intégrées
"""

from flask import Flask, request, jsonify
from datetime import datetime
import logging
import sys
import os
import requests

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Services
from services.agent_ia import AgentIAService
from services.apprentissage_service import ApprentissageService
from db_postgres import save_diagnostic, is_postgres_enabled

# Utils
from utils.validation import valider_donnees_capteurs
from utils.helpers import generer_diagnostic_id

# Config
from config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('diagnostic_frigo.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialisation Flask
app = Flask(__name__)
app.config.from_object(Config)

# Configuration du service IA
IA_SERVICE_URL = os.environ.get('IA_SERVICE_URL', 'http://localhost:5002')
CHAT_SERVICE_URL = os.environ.get('CHAT_SERVICE_URL', 'http://localhost:5001')

# Initialisation des services
logger.info(f"🤖 IA Service URL: {IA_SERVICE_URL}")
logger.info(f"💬 Chat Service URL: {CHAT_SERVICE_URL}")
agent_ia = AgentIAService(Config.AGENT_IA_URL)
apprentissage = ApprentissageService()

# Test IA Service au démarrage
try:
    ia_health = requests.get(f"{IA_SERVICE_URL}/health", timeout=3).json()
    logger.info(f"✅ Service IA connexion réussie: {ia_health.get('status', 'online')}")
except Exception as e:
    logger.warning(f"⚠️ Service IA indisponible (normal au démarrage): {e}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })


# Stockage du processus simulateur en cours (pour pouvoir l'arrêter)
simulator_process = None
simulator_thread = None
simulator_running = False


@app.route('/api/simulator/start', methods=['POST'])
def start_simulator():
    """
    🎯 Endpoint pour démarrer le simulateur en production
    
    Utilisation:
        POST http://localhost:5000/api/simulator/start
        Content-Type: application/json
        
        {
            "cycles": 50,
            "interval": 30,
            "prob_panne": 0.1
        }
    
    Réponse:
        {
            "status": "started",
            "process_id": 12345,
            "config": {...}
        }
    """
    try:
        global simulator_process, simulator_thread, simulator_running
        
        # Vérifier si déjà en cours
        if simulator_running and simulator_process and simulator_process.poll() is None:
            return jsonify({
                'status': 'already_running',
                'message': 'Un simulateur est déjà en cours d\'exécution',
                'pid': simulator_process.pid
            }), 409
        
        import subprocess
        import threading
        
        # Paramètres par défaut
        params = request.get_json() or {}
        cycles = params.get('cycles', 100)
        interval = params.get('interval', 30)
        prob_panne = params.get('prob_panne', 0.1)
        
        # Valider les paramètres
        if not (1 <= cycles <= 10000):
            return jsonify({'error': 'cycles doit être entre 1 et 10000'}), 400
        if not (1 <= interval <= 3600):
            return jsonify({'error': 'interval doit être entre 1 et 3600 secondes'}), 400
        if not (0.0 <= prob_panne <= 1.0):
            return jsonify({'error': 'prob_panne doit être entre 0.0 et 1.0'}), 400
        
        # Déterminer l'URL de l'app (pour l'auto-référence)
        app_url = request.base_url.rstrip('/')
        
        # Préparer la commande
        cmd = [
            'python',
            'simulateur_production.py',
            '--app-url', app_url,
            '--interval', str(interval),
            '--prob-panne', str(prob_panne),
            '--cycles', str(cycles)
        ]
        
        logger.info(f"🚀 Démarrage simulateur avec: cycles={cycles}, interval={interval}s, prob_panne={prob_panne}")
        
        # Lancer le simulateur en arrière-plan
        def run_simulator():
            global simulator_process, simulator_running
            try:
                simulator_running = True
                simulator_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info(f"✅ Simulateur démarré avec PID {simulator_process.pid}")
                
                # Attendre la fin du processus
                stdout, stderr = simulator_process.communicate()
                
                if simulator_process.returncode == 0:
                    logger.info("✅ Simulateur terminé avec succès")
                else:
                    logger.warning(f"⚠️ Simulateur terminé avec code {simulator_process.returncode}")
                    
            except Exception as e:
                logger.error(f"❌ Exception simulateur: {e}")
            finally:
                simulator_running = False
                simulator_process = None
        
        # Exécuter dans un thread séparé (non-bloquant)
        simulator_thread = threading.Thread(target=run_simulator, daemon=True)
        simulator_thread.start()
        
        return jsonify({
            'status': 'started',
            'message': f'Simulateur lancé avec {cycles} cycles',
            'config': {
                'cycles': cycles,
                'interval': interval,
                'prob_panne': prob_panne,
                'app_url': app_url
            },
            'timestamp': datetime.now().isoformat()
        }), 202
    
    except Exception as e:
        logger.error(f"❌ Erreur démarrage simulateur: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Erreur lors du démarrage du simulateur'
        }), 500


@app.route('/api/simulator/stop', methods=['POST'])
def stop_simulator():
    """
    🛑 Arrêter le simulateur en cours
    
    Utilisation:
        POST http://localhost:5000/api/simulator/stop
    
    Réponse:
        {
            "status": "stopped",
            "message": "Simulateur arrêté avec succès"
        }
    """
    global simulator_process, simulator_running
    
    try:
        if not simulator_process or not simulator_running:
            return jsonify({
                'status': 'not_running',
                'message': 'Aucun simulateur en cours d\'exécution'
            }), 200
        
        # Vérifier si le processus est encore actif
        if simulator_process.poll() is None:
            # Processus encore actif, l'arrêter
            import signal
            import os
            
            # Envoyer SIGTERM pour arrêt gracieux
            if os.name == 'nt':  # Windows
                simulator_process.terminate()
            else:  # Unix/Linux/Mac
                os.kill(simulator_process.pid, signal.SIGTERM)
            
            # Attendre un peu pour l'arrêt gracieux
            try:
                simulator_process.wait(timeout=5)
                logger.info("✅ Simulateur arrêté gracieusement")
            except:
                # Forcer l'arrêt si nécessaire
                simulator_process.kill()
                simulator_process.wait()
                logger.info("✅ Simulateur arrêté forcé")
        
        simulator_running = False
        pid = simulator_process.pid if simulator_process else None
        simulator_process = None
        
        return jsonify({
            'status': 'stopped',
            'message': 'Simulateur arrêté avec succès',
            'pid': pid,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur arrêt simulateur: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur lors de l\'arrêt: {str(e)}'
        }), 500


@app.route('/api/simulator/status', methods=['GET'])
def simulator_status():
    """
    📊 Obtenir le statut du simulateur
    
    Utilisation:
        GET http://localhost:5000/api/simulator/status
    
    Réponse:
        {
            "running": true,
            "pid": 12345,
            "started_at": "2026-02-25T20:00:00"
        }
    """
    global simulator_process, simulator_running
    
    is_running = simulator_running and simulator_process and simulator_process.poll() is None
    
    return jsonify({
        'running': is_running,
        'pid': simulator_process.pid if is_running else None,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/simulator/info', methods=['GET'])
def simulator_info():
    """
    📊 Endpoint pour obtenir les infos du simulateur
    
    Utilisation:
        GET http://localhost:5000/api/simulator/info
    
    Réponse:
        {
            "available": true,
            "description": "Lance diagnostics réalistes...",
            "endpoints": [...]
        }
    """
    return jsonify({
        'available': True,
        'description': 'Simulateur de capteurs frigorifiques production-ready',
        'endpoints': {
            'start': {
                'method': 'POST',
                'path': '/api/simulator/start',
                'description': 'Démarre le simulateur avec diagnostics',
                'params': {
                    'cycles': 'Nombre de diagnostics (default: 100)',
                    'interval': 'Secondes entre envois (default: 30)',
                    'prob_panne': 'Probabilité panne 0-1 (default: 0.1)'
                }
            },
            'stop': {
                'method': 'POST',
                'path': '/api/simulator/stop',
                'description': 'Arrête le simulateur en cours'
            },
            'status': {
                'method': 'GET',
                'path': '/api/simulator/status',
                'description': 'Obtient le statut du simulateur'
            },
            'info': {
                'method': 'GET',
                'path': '/api/simulator/info',
                'description': 'Infos disponibles sur le simulateur'
            }
        },
        'examples': {
            'quick_test': {
                'description': '5 diagnostics rapides',
                'curl': 'curl -X POST http://localhost:5000/api/simulator/start -H "Content-Type: application/json" -d \'{"cycles": 5, "interval": 5}\'',
                'python': 'requests.post("http://localhost:5000/api/simulator/start", json={"cycles": 5, "interval": 5})'
            },
            'stop_simulation': {
                'description': 'Arrêter le simulateur',
                'curl': 'curl -X POST http://localhost:5000/api/simulator/stop',
                'python': 'requests.post("http://localhost:5000/api/simulator/stop")'
            },
            'production_mode': {
                'description': '100 diagnostics avec pannes',
                'curl': 'curl -X POST http://localhost:5000/api/simulator/start -H "Content-Type: application/json" -d \'{"cycles": 100, "interval": 60, "prob_panne": 0.15}\'',
                'python': 'requests.post("http://localhost:5000/api/simulator/start", json={"cycles": 100, "interval": 60, "prob_panne": 0.15})'
            }
        }
    }), 200


@app.route('/webhook/diagnostic-frigo', methods=['POST'])
def diagnostic_frigo():
    """
    Endpoint principal - Remplace le webhook n8n
    Traite un diagnostic complet de bout en bout
    """
    try:
        # 1️⃣ VALIDATION DES DONNÉES
        logger.info("Réception nouvelle requête de diagnostic")
        donnees = request.get_json(force=True)
        
        donnees_validees = valider_donnees_capteurs(donnees)
        diagnostic_id = generer_diagnostic_id()
        timestamp = datetime.now().isoformat()
        
        diagnostic_data = {
            'diagnostic_id': diagnostic_id,
            'timestamp': timestamp,
            'donnees_capteurs': donnees_validees,
            'source': donnees.get('source', 'capteur_principal'),
            'localisation': donnees.get('localisation', 'Zone non spécifiée')
        }
        
        logger.info(f"Données validées - ID: {diagnostic_id}")
        
        # 2️⃣ APPEL AGENT IA POUR PRÉDICTION
        logger.info("Appel de l'agent IA...")
        prediction = agent_ia.predict(donnees_validees)
        
        # Fusion des résultats
        diagnostic_data['prediction_ia'] = prediction
        diagnostic_data['panne_detectee'] = prediction.get('panne_detectee') is not None
        
        logger.info(f"Prédiction: {prediction.get('panne_detectee', 'Aucune')}")
        
        # 3️⃣ SI PANNE DÉTECTÉE → ANALYSE IA + CHAT
        if diagnostic_data['panne_detectee']:
            logger.info("Panne détectée - Envoi au service IA pour analyse complète")
            
            try:
                # Préparer les données de prédiction pour le service IA
                # Filtrer les pannes avec une confiance >= 50%
                pannes_list = prediction.get('pannes_detectees', [])
                pannes_list = [p for p in pannes_list if p.get('score', 0) >= 50]
                
                if not pannes_list and prediction.get('panne_detectee'):
                    # Fallback si seulement panne_detectee est présent et score >= 50
                    if prediction.get('score', 0) >= 50:
                        pannes_list = [{
                            'panne': prediction.get('panne_detectee'),
                            'score': prediction.get('score', 0),
                            'type': prediction.get('type_panne', 'Inconnu')
                        }]
                
                prediction_data = {
                    'pannes': pannes_list,  # Liste de toutes les pannes
                    'nombre_pannes': len(pannes_list),
                    'capteurs': donnees_validees,
                    'timestamp': timestamp,
                    'diagnostic_id': diagnostic_id,
                    'localisation': diagnostic_data.get('localisation', 'Zone non spécifiée')
                }
                
                logger.info(f"📋 Envoi de {len(pannes_list)} panne(s) au service IA pour analyse")
                
                # Envoyer au service IA pour analyse (nouvel endpoint)
                ia_response = requests.post(
                    f"{IA_SERVICE_URL}/api/prediction/alert",
                    json=prediction_data,
                    timeout=15
                )
                
                if ia_response.status_code == 201:
                    alert_result = ia_response.json()
                    alert_data = alert_result.get('alert', {})
                    texte_analyse = alert_data.get('message', 'Analyse non disponible')
                    logger.info(f"✅ Alerte prédiction traitée: {alert_data.get('alert_id')}")
                    
                    # Envoyer l'alerte avec l'analyse IA détaillée au Chat Web
                    _send_alert_to_chat(diagnostic_id, prediction, donnees_validees, texte_analyse)
                    logger.info("✅ Alerte avec analyse IA détaillée envoyée au Chat Web")
                else:
                    logger.warning(f"Service IA retourné {ia_response.status_code}")
                    texte_analyse = f"Panne détectée: {prediction.get('panne_detectee', 'Anomalie')} - Score: {prediction.get('score', 0)}%"
                    
                    # Fallback: envoyer directement au chat avec message basique
                    _send_alert_to_chat(diagnostic_id, prediction, donnees_validees, texte_analyse)
            except Exception as e:
                logger.error(f"Erreur appel service IA: {e}")
                texte_analyse = f"Alerte: Panne détectée - {prediction.get('panne_detectee', 'Inconnue')}"
                
                # Fallback: envoyer directement au chat
                try:
                    _send_alert_to_chat(diagnostic_id, prediction, donnees_validees, texte_analyse)
                except Exception as chat_e:
                    logger.error(f"❌ Erreur envoi alerte fallback: {chat_e}")
        
        # 4️⃣ GESTION APPRENTISSAGE CONTINU
        logger.info("Mise à jour compteur apprentissage")
        apprentissage_data = apprentissage.traiter_diagnostic(diagnostic_data)
        diagnostic_data['apprentissage'] = apprentissage_data
        
        # 5️⃣ RÉENTRAÎNEMENT SI SEUIL ATTEINT
        if apprentissage_data.get('retraining_requis'):
            logger.info("Seuil atteint - Lancement réentraînement")
            resultat_retraining = agent_ia.retrain()
            
            # Notification via le service IA
            try:
                ia_response = requests.post(
                    f"{IA_SERVICE_URL}/api/learn",
                    json={'learning_data': apprentissage_data, 'event': 'retraining'},
                    timeout=10
                )
                if ia_response.status_code == 200:
                    message_retraining = "✅ Réentraînement complété - Service IA mis à jour"
                    logger.info("Service IA notifié du réentraînement")
                else:
                    message_retraining = f"⚠️ Réentraînement effectué mais erreur IA: {ia_response.status_code}"
            except Exception as e:
                logger.error(f"Erreur notification IA retraining: {e}")
                message_retraining = "✅ Réentraînement effectué"
            
            if message_retraining:
                # Envoyer notification au Chat Web
                try:
                    chat_response = requests.post(
                        f"{CHAT_SERVICE_URL}/api/receive-alert",
                        json={
                            'type': 'info',
                            'title': 'Réentraînement modèle',
                            'message': message_retraining,
                            'severity': 'medium'
                        },
                        timeout=5
                    )
                    if chat_response.status_code == 201:
                        logger.info("✅ Notification réentraînement envoyée au Chat")
                except Exception as e:
                    logger.error(f"❌ Erreur notification Chat: {e}")
        
        # 6️⃣ NOUVELLE PANNE DÉTECTÉE
        if apprentissage_data.get('nouvelles_pannes_a_entrainer'):
            logger.info("Nouvelle panne identifiée")
            for nouvelle_panne in apprentissage_data['nouvelles_pannes_a_entrainer']:
                agent_ia.train_new_fault(nouvelle_panne)
                
                # Notification via le service IA
                try:
                    ia_response = requests.post(
                        f"{IA_SERVICE_URL}/api/learn",
                        json={'fault_data': nouvelle_panne, 'event': 'new_fault'},
                        timeout=10
                    )
                    if ia_response.status_code == 200:
                        message_nouvelle = f"🆕 Nouvelle panne entraînée: {nouvelle_panne.get('name', 'Inconnue')}"
                        logger.info("Service IA notifié de la nouvelle panne")
                    else:
                        message_nouvelle = f"🆕 Nouvelle panne détectée: {nouvelle_panne.get('name', 'Inconnue')}"
                except Exception as e:
                    logger.error(f"Erreur notification IA nouvelle panne: {e}")
                    message_nouvelle = f"🆕 Nouvelle panne: {nouvelle_panne.get('name', 'Inconnue')}"
                
                if message_nouvelle:
                    # Envoyer notification au Chat Web
                    try:
                        chat_response = requests.post(
                            f"{CHAT_SERVICE_URL}/api/receive-alert",
                            json={
                                'type': 'warning',
                                'title': 'Nouvelle panne détectée',
                                'message': message_nouvelle,
                                'severity': 'high'
                            },
                            timeout=5
                        )
                        if chat_response.status_code == 201:
                            logger.info("✅ Notification nouvelle panne envoyée au Chat")
                    except Exception as e:
                        logger.error(f"❌ Erreur notification Chat: {e}")
        
        # 7️⃣ ARCHIVAGE
        apprentissage.archiver_diagnostic(diagnostic_data)
        
        # 7️⃣b SAUVEGARDE POSTGRES (si disponible)
        if is_postgres_enabled():
            try:
                save_diagnostic(diagnostic_data)
                logger.info(f"✅ Diagnostic sauvegardé en Postgres: {diagnostic_id}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur sauvegarde Postgres (fallback fichiers): {e}")
        
        # 8️⃣ RÉPONSE
        logger.info(f"Diagnostic {diagnostic_id} terminé avec succès")
        return jsonify({
            'success': True,
            'diagnostic_id': diagnostic_id,
            'timestamp': timestamp,
            'panne_detectee': diagnostic_data['panne_detectee'],
            'type_panne': prediction.get('panne_detectee'),
            'score_confiance': prediction.get('score', 0),
            'alerte_envoyee': diagnostic_data['panne_detectee'],
            'apprentissage': {
                'compteur': apprentissage_data.get('compteur_total', 0),
                'retraining_requis': apprentissage_data.get('retraining_requis', False),
                'nouvelle_panne': apprentissage_data.get('nouvelle_panne_detectee', False)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'diagnostic_id': diagnostic_id if 'diagnostic_id' in locals() else None
        }), 500


def _send_alert_to_chat(diagnostic_id, prediction, donnees, texte_analyse):
    """Envoie une alerte au service Chat Web (fallback) - Gère plusieurs pannes"""
    try:
        # Récupérer la liste des pannes et filtrer par confiance >= 50%
        pannes_list = prediction.get('pannes_detectees', [])
        pannes_list = [p for p in pannes_list if p.get('score', 0) >= 50]
        
        if not pannes_list and prediction.get('panne_detectee'):
            # Fallback si seulement panne_detectee est présent et score >= 50
            if prediction.get('score', 0) >= 50:
                pannes_list = [{
                    'panne': prediction.get('panne_detectee'),
                    'score': prediction.get('score', 0)
                }]
        
        # Si aucune panne significative, ne pas envoyer d'alerte
        if not pannes_list:
            logger.info(f"ℹ️ Aucune panne significative (score >= 50%) pour {diagnostic_id}, alerte non envoyée")
            return
        
        # Construire le titre avec toutes les pannes filtrées
        if len(pannes_list) == 1:
            titre = f"🔴 Alerte: {pannes_list[0].get('panne', 'Anomalie')}"
        else:
            pannes_noms = [p.get('panne', 'Inconnue') for p in pannes_list]
            if len(pannes_noms) > 3:
                titre = f"🔴 Alerte: {len(pannes_noms)} pannes détectées"
            else:
                titre = f"🔴 Alerte: {', '.join(pannes_noms)}"
        
        # Construire le message avec le nombre de pannes
        message_complet = f"""
🚨 **{len(pannes_list)} PANNE(S) DÉTECTÉE(S)**

{texte_analyse}

---
**Pannes identifiées:**
"""
        for idx, panne in enumerate(pannes_list, 1):
            panne_name = panne.get('panne', 'Inconnue')
            panne_score = panne.get('score', 0)
            message_complet += f"{idx}. {panne_name} (confiance: {panne_score:.1f}%)\n"
        
        alert_payload = {
            'type': 'prediction_alert',
            'title': titre,
            'message': message_complet,
            'diagnostic_id': diagnostic_id,
            'severity': 'high',
            'capteurs': donnees,
            'timestamp': datetime.now().isoformat(),
            'pannes_count': len(pannes_list),
            'pannes_list': pannes_list
        }

        response = requests.post(
            f"{CHAT_SERVICE_URL}/api/receive-alert",
            json=alert_payload,
            timeout=10
        )

        if response.status_code == 201:
            logger.info(f"✅ Alerte fallback avec {len(pannes_list)} panne(s) envoyée au Chat: {diagnostic_id}")
        else:
            logger.warning(f"⚠️ Chat a retourné {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Erreur envoi alerte fallback: {e}")


def generer_prompt_alerte(diagnostic_data):
    """Génère le prompt pour Gemini (alerte panne)"""
    donnees = diagnostic_data['donnees_capteurs']
    prediction = diagnostic_data['prediction_ia']
    pannes = prediction.get('pannes_detectees', [])
    
    liste_pannes = '\n'.join([
        f"{i+1}. {p.get('panne', 'Inconnue')} - Score: {p.get('score', 0)}%"
        for i, p in enumerate(pannes)
    ])
    
    return f"""Tu es un expert en diagnostic de systèmes frigorifiques industriels.
Génère une alerte CRITIQUE pour le système de chat en MAX 3500 caractères.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DIAGNOSTIC SYSTÈME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ÉQUIPEMENT: {diagnostic_data['diagnostic_id']}
SITE: {diagnostic_data['localisation']}
DATE: {diagnostic_data['timestamp']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 PANNES DÉTECTÉES ({len(pannes)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{liste_pannes}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️ MESURES ACTUELLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Température: {donnees['Température']}°C
• Pression HP: {donnees['Pression_HP']} bar
• Pression BP: {donnees['Pression_BP']} bar
• Courant: {donnees['Courant']} A
• Tension: {donnees['Tension']} V
• Humidité: {donnees['Humidité']}%
• Débit air: {donnees['Débit_air']} m³/h
• Vibration: {donnees['Vibration']}

TÂCHE:
1. Analyse chaque panne détectée
2. Explique la cause probable
3. Identifie les valeurs anormales
4. Évalue l'urgence globale
5. Propose un plan d'action priorisé"""


@app.route('/stats', methods=['GET'])
def get_stats():
    """Endpoint pour obtenir les statistiques du système"""
    stats = apprentissage.get_statistiques()
    return jsonify(stats)


@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Endpoint pour traiter les messages du chat web"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        user = data.get('user', 'Anonymous')
        
        if not message:
            return jsonify({'error': 'Message vide'}), 400
        
        logger.info(f"💬 Message du chat reçu de {user}: {message[:100]}")
        
        # Analyser le message et générer une réponse
        response_text = generer_reponse_chat(message)
        
        return jsonify({
            'success': True,
            'response': response_text,
            'user': user,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement chat: {e}")
        return jsonify({'error': str(e)}), 500


def generer_reponse_chat(message):
    """Génère une réponse intelligente au message du chat"""
    msg_lower = message.lower()
    
    # Commandes système
    if msg_lower.startswith('/status'):
        return "✅ Système actif et fonctionnel"
    
    if msg_lower.startswith('/diagnostics') or msg_lower.startswith('/stats'):
        return "📊 Statistiques système: Voir le tableau de bord"
    
    if msg_lower.startswith('/alerts'):
        return "🚨 Alertes actuelles: Aucune alerte critique"
    
    # Diagnostics
    if 'diagnostic' in msg_lower:
        symptomes = extraire_symptomes(message)
        if symptomes:
            return f"🔍 Diagnostic basé sur: {', '.join(symptomes)}\n\n✅ Analyse en cours...\n\nRésultat: Voir le rapport complet"
        return "📋 Pour un diagnostic, décrivez les symptômes (température, bruit, froid, etc.)"
    
    # Pannes
    if 'panne' in msg_lower or 'erreur' in msg_lower:
        return "⚠️ Panne détectée\n\n🔧 Solutions recommandées:\n1. Vérifier l'alimentation\n2. Vérifier le thermostat\n3. Contacter un technicien si problème persiste"
    
    # Solutions
    if 'solution' in msg_lower or 'comment réparer' in msg_lower or 'fix' in msg_lower:
        return "🔧 Étapes de réparation:\n\n1. Débrancher l'appareil\n2. Laisser refroidir 5 minutes\n3. Rebrancher et tester\n\nSi le problème persiste, consultez un professionnel"
    
    # Apprentissage
    if 'apprendre' in msg_lower or 'learn' in msg_lower:
        return "✅ Apprentissage enregistré!\n\nCe diagnostic sera utilisé pour améliorer les futurs diagnostics"
    
    # Aide générale
    if 'aide' in msg_lower or 'help' in msg_lower or 'quoi' in msg_lower:
        return """📖 Guide d'utilisation:

1️⃣ Diagnostic: "Diagnostic: symptômes"
2️⃣ Signaler: "Panne: description"
3️⃣ Réparer: "Solution: problème"
4️⃣ Apprendre: "Apprendre: diagnostic -> solution"

Consultez CHAT_GUIDE.md pour plus d'infos"""
    
    # Réponse par défaut avec Gemini si disponible
    try:
        prompt = f"""Tu es un expert en diagnostic de frigorifiques. 
        L'utilisateur demande: "{message}"
        
        Donne une réponse concise et utile (max 200 caractères)."""
        
        response = gemini.generer_analyse_sync(prompt)
        if response:
            return response.get('analyse', str(response)) if isinstance(response, dict) else str(response)
    except:
        pass
    
    # Réponse par défaut
    return "🤔 Je n'ai pas bien compris votre question. Consultez le guide ou décrivez vos symptômes"


def extraire_symptomes(message):
    """Extrait les symptômes du message"""
    symptomes_cles = [
        'température', 'bruit', 'condensation', 'froid', 'compresseur',
        'thermostat', 'ventilateur', 'fuite', 'vibration', 'humidité',
        'erreur', 'code', 'pression', 'courant', 'tension'
    ]
    
    symptomes = [s for s in symptomes_cles if s in message.lower()]
    return symptomes


# ============================================================
# DASHBOARD ENDPOINTS - Monitoring en temps réel
# ============================================================

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Serve le dashboard HTML"""
    return send_from_directory('templates', 'dashboard.html')


@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """
    Endpoint API pour les métriques du dashboard
    Retourne: stats système, état services, alertes récentes
    """
    try:
        # Récupérer les statistiques d'apprentissage
        stats = apprentissage.get_statistiques()
        
        # Calculer les métriques
        total_diagnostics = stats.get('compteur_total', 0)
        total_pannes = stats.get('total_pannes_detectees', 0)
        detection_rate = (total_pannes / total_diagnostics * 100) if total_diagnostics > 0 else 0
        total_retrains = total_diagnostics // 1000  # Approximation
        
        # Vérifier l'état des services
        services_status = []
        
        # App principale (moi-même)
        services_status.append({
            'name': 'App Principale (5000)',
            'online': True,
            'url': 'http://localhost:5000'
        })
        
        # Chat Service
        try:
            chat_health = requests.get(f"{CHAT_SERVICE_URL}/health", timeout=2)
            services_status.append({
                'name': 'Chat Service (5001)',
                'online': chat_health.status_code == 200,
                'url': CHAT_SERVICE_URL
            })
        except:
            services_status.append({
                'name': 'Chat Service (5001)',
                'online': False,
                'url': CHAT_SERVICE_URL
            })
        
        # IA Service
        try:
            ia_health = requests.get(f"{IA_SERVICE_URL}/health", timeout=2)
            services_status.append({
                'name': 'IA Service (5002)',
                'online': ia_health.status_code == 200,
                'url': IA_SERVICE_URL
            })
        except:
            services_status.append({
                'name': 'IA Service (5002)',
                'online': False,
                'url': IA_SERVICE_URL
            })
        
        # Simuler des alertes récentes (à remplacer par vraies données si disponible)
        recent_alerts = []
        if total_pannes > 0:
            recent_alerts.append({
                'title': f'{total_pannes} pannes détectées au total',
                'severity': 'medium',
                'time': 'Historique'
            })
        
        # Réentraînements
        if total_retrains > 0:
            recent_alerts.append({
                'title': f'{total_retrains} réentraînement(s) effectué(s)',
                'severity': 'low',
                'time': f'Dernier: {total_retrains * 1000} cas'
            })
        
        return jsonify({
            'total_diagnostics': total_diagnostics,
            'total_pannes': total_pannes,
            'detection_rate': round(detection_rate, 1),
            'total_retrains': total_retrains,
            'next_retrain_at': (total_retrains + 1) * 1000,
            'pannes_today': stats.get('pannes_aujourd_hui', 0),
            'services': services_status,
            'recent_alerts': recent_alerts,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur dashboard metrics: {e}")
        return jsonify({
            'error': str(e),
            'total_diagnostics': 0,
            'detection_rate': 0,
            'services': []
        }), 500


# ============================================================

if __name__ == '__main__':
    logger.info("Démarrage du système de diagnostic frigorifique")
    logger.info(f"Environnement: {Config.ENV}")
    
    # Mode développement ou production
    if Config.ENV == 'development':
        app.run(host='0.0.0.0', port=Config.PORT, debug=True)
    else:
        # En production, utiliser gunicorn
        import gunicorn.app.base
        
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{Config.PORT}',
            'workers': 4,
            'worker_class': 'gevent',
            'timeout': 120
        }
        
        StandaloneApplication(app, options).run()
