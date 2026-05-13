"""
Service IA Local - Point central de traitement
Architecture: GEMINI + GPT-4 (compatible Render + Local)
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import requests
from typing import Dict, Optional

# Import des services d'analyse
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from services.gemini_service import GeminiService
from services.gpt4_service import GPT4Service

# Import DB Postgres (fallback sur fichiers si pas dispo)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_postgres import get_latest_diagnostic, is_postgres_enabled, save_panne

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IAConfig:
    """Configuration du service IA - GEMINI + GPT-4"""
    
    # ========== GEMINI ==========
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # ========== GPT-4 / Azure ==========
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL')  # Pour Azure ou endpoints personnalisés
    GPT4_MODEL = os.environ.get('GPT4_MODEL', 'gpt-4.1-mini')
    
    # Paramètres LLM
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7
    TOP_P = 0.90
    
    # Stratégie d'analyse
    ANALYSIS_STRATEGY = os.environ.get('ANALYSIS_STRATEGY', 'gpt4_only')  # primary_fallback, dual_compare, gemini_only, gpt4_only
    PRIMARY_MODEL = os.environ.get('PRIMARY_MODEL', 'gpt4')  # gemini ou gpt4

    # Sécurité: désactiver Gemini (par défaut)
    DISABLE_GEMINI = os.environ.get('DISABLE_GEMINI', 'true').lower() == 'true'
    
    # Contexte persistant
    CONTEXT_SIZE = 10
    
    # Bases de données
    # Dossier data/ du système (racine projet) : contient dernier_diagnostic.json, dataset_apprentissage.csv, etc.
    DB_PATH = Path(__file__).resolve().parent.parent / "data"
    CACHE_PATH = Path(__file__).parent / "cache"
    
    def __init__(self):
        self.DB_PATH.mkdir(exist_ok=True)
        self.CACHE_PATH.mkdir(exist_ok=True)

class IAService:
    """Service IA principal - GEMINI + GPT-4"""
    
    def __init__(self):
        self.config = IAConfig()

        # Si Gemini est désactivé, forcer le mode GPT-4 only
        if self.config.DISABLE_GEMINI:
            self.config.ANALYSIS_STRATEGY = 'gpt4_only'
            self.config.PRIMARY_MODEL = 'gpt4'

        self.conversation_history = {}  # {user_id: [messages]}
        self.knowledge_base = {}
        self.model_info = {}

        # Initialiser Gemini uniquement si on l'utilise
        self.gemini_service = None
        if self.config.ANALYSIS_STRATEGY != 'gpt4_only' and not self.config.DISABLE_GEMINI:
            self.gemini_service = GeminiService(
                api_key=self.config.GEMINI_API_KEY,
                model_name=self.config.GEMINI_MODEL,
                temperature=self.config.TEMPERATURE
            )
        
        # Initialiser GPT-4 (avec support Azure)
        self.gpt4_service = GPT4Service(
            api_key=self.config.OPENAI_API_KEY,
            model_name=self.config.GPT4_MODEL,
            temperature=self.config.TEMPERATURE,
            base_url=self.config.OPENAI_BASE_URL
        )
        
        logger.info(f"🤖 Initialisation service IA - GEMINI + GPT-4")
        logger.info(f"📋 Modèle Gemini: {self.config.GEMINI_MODEL}")
        logger.info(f"📋 Modèle GPT-4: {self.config.GPT4_MODEL}")
        logger.info(f"🔑 Gemini API Key présente: {bool(self.config.GEMINI_API_KEY)}")
        logger.info(f"🔑 OpenAI API Key présente: {bool(self.config.OPENAI_API_KEY)}")
        logger.info(f"🎯 Stratégie d'analyse: {self.config.ANALYSIS_STRATEGY}")
        logger.info(f"🏆 Modèle principal: {self.config.PRIMARY_MODEL}")
        
        # Vérifier les connexions
        self._check_connections()
        self._load_knowledge_base()
    
    def _check_connections(self):
        """Vérifier les connexions aux services IA"""
        # Vérifier Gemini
        if self.gemini_service is None:
            logger.info("ℹ️ Gemini ignoré (ANALYSIS_STRATEGY=gpt4_only)")
        elif not self.config.GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY non configurée")
        else:
            try:
                test_result = self.gemini_service.generer_analyse_sync("Test connexion")
                if test_result.get('success'):
                    logger.info("✅ Gemini connecté avec succès")
                else:
                    logger.warning("⚠️ Gemini connecté mais test échoué")
            except Exception as e:
                logger.error(f"❌ Erreur connexion Gemini: {e}")
        
        # Vérifier GPT-4
        if not self.config.OPENAI_API_KEY:
            logger.warning("⚠️ OPENAI_API_KEY non configurée")
        else:
            try:
                if self.gpt4_service.test_connexion():
                    logger.info("✅ GPT-4 connecté avec succès")
                else:
                    logger.warning("⚠️ GPT-4 connexion échouée")
            except Exception as e:
                logger.error(f"❌ Erreur connexion GPT-4: {e}")
    
    def process_chat(self, message, user_id=None, user_name=None, source=None, model=None):
        try:
            logger.info(f"💬 Message reçu: {message[:50]}...")
            uid = str(user_id) if user_id else 'anonymous'
    
            # Historique isolé par utilisateur
            if uid not in self.conversation_history:
                self.conversation_history[uid] = []
            history = self.conversation_history[uid][-8:]
    
            # Contexte live du système
            system_context = self._get_system_context()
    
            # Prompt système enrichi
            system_prompt = f"""Tu es l'assistant IA intelligent du Système FrigoDiag. Tu es capable de répondre à TOUTES les questions — techniques ou générales. Tu peux discuter de n'importe quel sujet tout en étant spécialisé dans le diagnostic frigorifique.
Tu connais en temps réel l'état complet du système.
    
    === ÉTAT ACTUEL DU SYSTÈME ===
    {system_context}
    
    === TES CAPACITÉS ===
    - Répondre à toutes les questions, techniques ou générales
    - Analyser les pannes frigorifiques et donner des recommandations
    - Expliquer le fonctionnement des 12 modèles de prédiction
    - Guider les techniciens dans la résolution des pannes
    - Discuter de tout autre sujet si l'utilisateur le souhaite
    
    Réponds toujours en français, de façon naturelle et professionnelle. Ne refuse jamais de répondre."""
    
    Réponds toujours en français, de façon claire et professionnelle."""
    
    
            # Appel GPT-4
            # Appel GPT-4
            prompt_complet = f"{system_prompt}\n\nUtilisateur: {message}"
            gpt_result = self.gpt4_service.generer_analyse_sync(
                prompt=message,
                max_tokens=800,
                system_prompt=system_prompt
            )
            if gpt_result.get('success'):
                response_text = gpt_result.get('analyse', 'Pas de réponse.')
            else:
                response_text = f"Erreur GPT: {gpt_result.get('error', 'inconnue')}"
    
            # Sauvegarder dans l'historique de l'utilisateur
            self.conversation_history[uid].append({
                'message': message,
                'response': response_text,
                'timestamp': datetime.now().isoformat()
            })
            if len(self.conversation_history[uid]) > 20:
                self.conversation_history[uid] = self.conversation_history[uid][-20:]
    
            return {
                'success': True,
                'response': response_text,
                'intent': 'general',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': 'Erreur lors du traitement du message'
            }

    def _get_system_context(self):
        """Recupere etat live du systeme pour informer GPT"""
        try:
            import requests, os
            app_url = os.environ.get('MAIN_APP_URL', 'https://frigo-app.onrender.com')
            chat_url = os.environ.get('CHAT_API_URL', 'https://frigo-chat.onrender.com')

            context_parts = []

            # Stats app
            try:
                r = requests.get(f"{app_url}/stats", timeout=3)
                if r.ok:
                    s = r.json()
                    context_parts.append(f"- Total diagnostics effectués : {s.get('total_diagnostics', 0)}")
                    context_parts.append(f"- Total pannes détectées : {s.get('total_pannes_detectees', 0)}")
                    context_parts.append(f"- Taux de pannes : {s.get('taux_pannes', 0):.1f}%")
                    context_parts.append(f"- Réentraînements effectués : {s.get('retrainings_effectues', 0)}")
                    pannes = s.get('pannes_par_type', {})
                    if pannes:
                        context_parts.append(f"- Pannes par type : {', '.join([f'{k}({v})' for k,v in pannes.items()])}")
            except:
                context_parts.append("- Stats app : indisponibles")

            # Alertes récentes
            try:
                r2 = requests.get(f"{chat_url}/api/alerts?limit=3", timeout=3)
                if r2.ok:
                    alerts = r2.json()
                    if alerts:
                        context_parts.append(f"- Dernières alertes ({len(alerts)}) :")
                        for a in alerts[:3]:
                            context_parts.append(f"  • {a.get('title','?')} [{a.get('severity','?')}]")
                    else:
                        context_parts.append("- Aucune alerte récente")
            except:
                context_parts.append("- Alertes : indisponibles")

            return '\n'.join(context_parts) if context_parts else "Données système indisponibles"
        except Exception as e:
            return f"Erreur récupération contexte: {e}"
    
    def _detect_database_query(self, message):
        """
        Détecter si le message est une requête sur la base de données
        
        Returns:
            str: Type de requête ('latest', 'stats', 'critical', 'alerts') ou None
        """
        message_lower = message.lower()
        
        # Mots-clés pour la dernière panne
        latest_keywords = [
            'dernière panne', 'derniere panne', 'dernier problème', 'dernier diagnostic',
            'quelle est la dernière', 'quelle est la panne', 'dernière alerte',
            'dernière détection', 'derniere detection', 'dernière erreur'
        ]
        
        # Mots-clés pour les statistiques
        stats_keywords = [
            'statistiques', 'stats', 'combien de pannes', 'nombre de pannes',
            'historique', 'tendance', 'fréquence', 'combien d\'alertes'
        ]
        
        # Mots-clés pour les pannes critiques
        critical_keywords = [
            'panne critique', 'problème critique', 'alerte critique',
            'danger', 'urgence', 'surchauffe', 'compresseur en panne'
        ]
        
        # Mots-clés pour les alertes
        alerts_keywords = [
            'liste des alertes', 'toutes les alertes', 'alertes récentes',
            'notifications', 'avertissements'
        ]
        
        # Vérifier chaque catégorie
        for keyword in latest_keywords:
            if keyword in message_lower:
                return 'latest'
                
        for keyword in critical_keywords:
            if keyword in message_lower:
                return 'critical'
                
        for keyword in stats_keywords:
            if keyword in message_lower:
                return 'stats'
                
        for keyword in alerts_keywords:
            if keyword in message_lower:
                return 'alerts'
        
        return None
    
    def _handle_database_query(self, message, query_type, user_id, user_name):
        """
        Traiter une requête sur la base de données
        """
        try:
            # Récupérer les données
            if query_type == 'alerts':
                data = self.get_alerts(limit=10)
                response = self._format_alerts_response(data)
            else:
                results = self.query_database(query_type=query_type)
                response = self._format_database_response(results, query_type)
            
            logger.info(f"✅ Requête BD traitée: {query_type}")
            
            return {
                'success': True,
                'response': response,
                'user_id': user_id,
                'user_name': user_name,
                'model': 'database-query',
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0,
                'query_type': query_type
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement requête BD: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Erreur lors de l'accès à la base de données."
            }
    
    def _format_database_response(self, results, query_type):
        """
        Formater la réponse de la base de données pour l'utilisateur
        """
        if results.get('error'):
            return f"❌ Erreur: {results['error']}"
        
        summary = results.get('summary', {})
        
        if query_type == 'latest':
            panne = summary.get('derniere_panne', 'Inconnue')
            date = summary.get('date_detection', 'Non disponible')
            count = summary.get('nombre_pannes_detectees', 0)
            score = summary.get('score_confiance', 0)
            
            return f"""📊 **Dernière Panne Identifiée**

🔧 **Type:** {panne}
📅 **Date de détection:** {date}
🔢 **Nombre de pannes détectées:** {count}
📈 **Score de confiance:** {score}%

Cette information est basée sur les données du système de diagnostic."""
        
        elif query_type == 'stats':
            total = summary.get('total_pannes_possibles', 0)
            detected = summary.get('pannes_detectees', 0)
            pannes_list = summary.get('pannes_liste', [])
            
            pannes_text = '\n'.join([f"  • {p}" for p in pannes_list]) if pannes_list else "  Aucune"
            
            return f"""📈 **Statistiques du Système**

📊 **Total pannes possibles:** {total}
⚠️ **Pannes détectées:** {detected}

🔍 **Liste des pannes actives:**
{pannes_text}

📅 **Dernière mise à jour:** {summary.get('timestamp', 'Inconnue')}"""
        
        elif query_type == 'critical':
            count = summary.get('pannes_critiques_count', 0)
            pannes = summary.get('pannes_critiques_list', [])
            
            if count == 0:
                return "✅ **Aucune panne critique détectée**\n\nLe système fonctionne normalement."
            
            pannes_text = '\n'.join([f"  🚨 {p}" for p in pannes])
            
            return f"""🚨 **ALERTES CRITIQUES** 🚨

**Nombre de pannes critiques:** {count}

{pannes_text}

⚠️ **Action immédiate recommandée!**"""
        
        else:
            return f"📋 Données récupérées: {len(results.get('data', []))} enregistrements."
    
    def _format_alerts_response(self, alerts):
        """
        Formater la liste des alertes pour l'utilisateur
        """
        if not alerts:
            return "✅ **Aucune alerte enregistrée**\n\nLe système fonctionne normalement."
        
        lines = [f"📋 **Alertes Récentes ({len(alerts)})**\n"]
        
        for alert in alerts[:5]:  # Limiter à 5 alertes
            severity_emoji = {
                'critical': '🚨',
                'high': '⚠️',
                'medium': '⚡',
                'low': 'ℹ️'
            }.get(alert.get('severity'), 'ℹ️')
            
            title = alert.get('title', 'Sans titre')
            timestamp = alert.get('timestamp', 'Date inconnue')
            message = alert.get('message', '')[:100]  # Tronquer le message
            
            lines.append(f"{severity_emoji} **{title}**")
            lines.append(f"   📅 {timestamp}")
            lines.append(f"   📝 {message}...\n")
        
        return '\n'.join(lines)
    
    def _analyze_with_gemini(self, prompt):
        """Analyser avec Gemini uniquement"""
        if self.gemini_service is None:
            return {
                'success': False,
                'error': 'Gemini est désactivé (mode gpt4_only)',
                'model_used': 'gemini-disabled'
            }
        try:
            result = self.gemini_service.generer_analyse_sync(prompt)
            if result.get('success'):
                return {
                    'success': True,
                    'response': result.get('analyse', ''),
                    'model_used': 'gemini',
                    'processing_time': result.get('processing_time', 0)
                }
            else:
                # Si Gemini échoue à cause de la clé API, retourner un message informatif
                if 'non configuré' in result.get('error', '').lower() or 'api key' in result.get('error', '').lower():
                    return {
                        'success': True,
                        'response': "🔮 **Mode Démo - Gemini non configuré**\n\nPour utiliser Gemini gratuitement:\n1. Obtenez une clé sur https://makersuite.google.com/app/apikey\n2. Définissez GEMINI_API_KEY dans vos variables d'environnement\n\nGemini offre 1 million de tokens gratuits par jour!\n\nAlternative: Utilisez Ollama pour un modèle 100% local.",
                        'model_used': 'gemini-unconfigured',
                        'processing_time': 0
                    }
                return {
                    'success': False,
                    'error': result.get('error', 'Erreur Gemini'),
                    'model_used': 'gemini'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur Gemini: {str(e)}',
                'model_used': 'gemini'
            }
    
    def _analyze_with_gpt4(self, prompt):
        """Analyser avec GPT-4 uniquement"""
        try:
            result = self.gpt4_service.generer_analyse_sync(prompt)
            if result.get('success'):
                return {
                    'success': True,
                    'response': result.get('analyse', ''),
                    'model_used': 'gpt-4',
                    'processing_time': result.get('processing_time', 0)
                }
            else:
                # Si GPT-4 échoue à cause de la clé API, retourner un message informatif
                if 'non configuré' in result.get('error', '').lower() or 'api key' in result.get('error', '').lower():
                    return {
                        'success': True,
                        'response': "🤖 **Mode Démo - GPT-4 non configuré**\n\nPour utiliser GPT-4, configurez votre clé API OpenAI:\n1. Obtenez une clé sur https://platform.openai.com/api-keys\n2. Définissez OPENAI_API_KEY dans vos variables d'environnement\n\nAlternative: Utilisez Gemini (gratuit avec crédits) ou Ollama (local).",
                        'model_used': 'gpt-4-unconfigured',
                        'processing_time': 0
                    }
                return {
                    'success': False,
                    'error': result.get('error', 'Erreur GPT-4'),
                    'model_used': 'gpt-4'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur GPT-4: {str(e)}',
                'model_used': 'gpt-4'
            }
    
    def _analyze_with_primary_fallback(self, prompt):
        """Analyser avec modèle principal, fallback sur le second"""
        primary = self.config.PRIMARY_MODEL
        
        # Essayer le modèle principal d'abord
        if primary == 'gemini':
            result = self._analyze_with_gemini(prompt)
            if result.get('success'):
                return result
            logger.warning(f"⚠️ Échec modèle principal (Gemini), fallback sur GPT-4")
            return self._analyze_with_gpt4(prompt)
        else:  # primary == 'gpt4'
            result = self._analyze_with_gpt4(prompt)
            if result.get('success'):
                return result
            logger.warning(f"⚠️ Échec modèle principal (GPT-4), fallback sur Gemini")
            return self._analyze_with_gemini(prompt)
    
    def _analyze_with_comparison(self, prompt):
        """Analyser avec les deux modèles et comparer"""
        gemini_result = self._analyze_with_gemini(prompt)
        gpt4_result = self._analyze_with_gpt4(prompt)
        
        # Si les deux échouent
        if not gemini_result.get('success') and not gpt4_result.get('success'):
            return {
                'success': False,
                'error': 'Les deux modèles ont échoué',
                'model_used': 'none'
            }
        
        # Si un seul réussit
        if gemini_result.get('success') and not gpt4_result.get('success'):
            return gemini_result
        if gpt4_result.get('success') and not gemini_result.get('success'):
            return gpt4_result
        
        # Si les deux réussissent, choisir le plus rapide
        gemini_time = gemini_result.get('processing_time', 999)
        gpt4_time = gpt4_result.get('processing_time', 999)
        
        if gemini_time < gpt4_time:
            logger.info(f"🏆 Gemini plus rapide ({gemini_time:.2f}s vs {gpt4_time:.2f}s)")
            return gemini_result
        else:
            logger.info(f"🏆 GPT-4 plus rapide ({gpt4_time:.2f}s vs {gemini_time:.2f}s)")
            return gpt4_result
    
    def _detect_requested_model(self, message):
        """
        Détecte si un modèle spécifique est demandé dans le message
        
        Args:
            message: Message de l'utilisateur
            
        Returns:
            'gemini', 'gpt4', ou None
        """
        message_lower = message.lower()
        
        # Mots-clés pour Gemini
        gemini_keywords = ['gemini', 'google gemini', 'gemini-flash', 'gemini-pro']
        
        # Mots-clés pour GPT-4
        gpt4_keywords = ['gpt-4', 'gpt4', 'gpt 4', 'gpt-4.1-mini', 'chatgpt', 'openai']
        
        # Vérifier les mots-clés GPT-4 en premier (plus spécifiques)
        for keyword in gpt4_keywords:
            if keyword in message_lower:
                return 'gpt4'
        
        # Vérifier les mots-clés Gemini
        for keyword in gemini_keywords:
            if keyword in message_lower:
                return 'gemini'
        
        return None
    
    def _analyze_with_specific_model(self, message, model_type):
        """
        Analyse avec un modèle spécifique demandé
        
        Args:
            message: Message original de l'utilisateur
            model_type: 'gemini' ou 'gpt4'
            
        Returns:
            Résultat de l'analyse
        """
        # Construire le prompt avec contexte frigorifique
        system_prompt = self._build_system_prompt()
        full_prompt = f"{system_prompt}\n\nUtilisateur: {message}\n\nAssistant:"
        
        if model_type == 'gemini':
            result = self._analyze_with_gemini(full_prompt)
            if result.get('success'):
                result['response'] = f"🤖 **Réponse Gemini**\n\n{result['response']}"
            return result
        elif model_type == 'gpt4':
            result = self._analyze_with_gpt4(full_prompt)
            if result.get('success'):
                result['response'] = f"🧠 **Réponse GPT-4.1-mini**\n\n{result['response']}"
            return result
        else:
            return {
                'success': False,
                'error': f'Modèle {model_type} non reconnu',
                'model_used': 'none'
            }
    
    def process_alert(self, alert_data):
        """
        Traiter une alerte et générer un diagnostic détaillé
        """
        try:
            title = alert_data.get('title', 'Alerte')
            sensors = alert_data.get('sensors', {})
            prediction = alert_data.get('prediction', {})
            
            logger.info(f"🚨 Traitement alerte: {title}")
            
            # Construire le prompt de diagnostic
            diagnostic_prompt = self._build_diagnostic_prompt(sensors, prediction)

            # En mode gpt4_only, ne jamais appeler Gemini
            if self.config.ANALYSIS_STRATEGY == 'gpt4_only' or self.config.DISABLE_GEMINI:
                result = self._analyze_with_gpt4(diagnostic_prompt)
                if result.get('success'):
                    analysis = result.get('response', f"Panne détectée: {prediction.get('panne_detectee', 'Inconnue')}")
                else:
                    analysis = f"Panne détectée: {prediction.get('panne_detectee', 'Inconnue')}"
                analysis = self._clean_response(analysis)

                logger.info("✅ Diagnostic généré")

                return {
                    'success': True,
                    'analysis': analysis,
                    'alert_id': alert_data.get('diagnostic_id'),
                    'model': self.config.GPT4_MODEL,
                    'timestamp': datetime.now().isoformat()
                }

            # Sinon (modes legacy), utiliser la stratégie existante
            result = self._analyze_with_primary_fallback(diagnostic_prompt)

            if result.get('success'):
                analysis = result.get('response', f"Panne détectée: {prediction.get('panne_detectee', 'Inconnue')}")
                analysis = self._clean_response(analysis)
                
                logger.info("✅ Diagnostic généré")
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'alert_id': alert_data.get('diagnostic_id'),
                    'model': result.get('model_used', 'inconnu'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Erreur diagnostic: {result.get('error')}")
                return {
                    'success': False,
                    'analysis': f"Panne détectée: {prediction.get('panne_detectee', 'Inconnue')}"
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement alerte: {e}")
            return {
                'success': False,
                'analysis': f"Alerte: {alert_data.get('title', 'Erreur')}"
            }
    
    def _build_system_prompt(self, context=None):
        """Construire le prompt système avec contexte frigorifique"""
        base_prompt = """Tu es un expert en maintenance et diagnostic de systèmes frigorifiques industriels.

CONTEXTE:
- Tu aides des techniciens à diagnostiquer et réparer des équipements frigorifiques
- Tu analyses les données des capteurs (température, pression, courant, etc.)
- Tu proposes des solutions concrètes et sûres

RÈGLES:
1. Sois concis et pratique (max 200 mots)
2. Priorise la sécurité des techniciens
3. Donne des étapes d'action claires
4. Si incertain, suggère de contacter un expert

DOMAINES:
- Compresseurs, condenseurs, évaporateurs
- Fluides frigorigènes (R134a, R410A, etc.)
- Cycles de réfrigération
- Électricité et régulation"""
        
        if context:
            base_prompt += f"\n\nCONTEXTE ADDITIONNEL:\n{context}"
        
        return base_prompt
    
    def _build_diagnostic_prompt(self, sensors, prediction):
        """Construire le prompt pour diagnostic d'alerte"""
        panne = prediction.get('panne_detectee', 'Inconnue')
        score = prediction.get('score', 0)
        
        # Formater les données capteurs
        sensors_text = "\n".join([f"- {k}: {v}" for k, v in sensors.items()])
        
        prompt = f"""Tu es un expert en maintenance frigorifique. Analyse cette alerte et propose un diagnostic détaillé.

DONNÉES CAPTEURS:
{sensors_text}

PANNE DÉTECTÉE: {panne} (confiance: {score}%)

INSTRUCTIONS:
1. Résume la situation en 1 phrase
2. Explique pourquoi cette panne est détectée (bases-toi sur les valeurs anormales)
3. Propose 2-3 causes probables
4. Donne les étapes immédiates de vérification
5. Mentionne si une intervention urgente est nécessaire

Format de réponse: texte clair et concis, sans markdown complexe."""
        
        return prompt
    
    def _clean_response(self, text):
        """Nettoyer la réponse de l'IA"""
        if not isinstance(text, str):
            text = str(text)
        
        # Supprimer les balises markdown excessives
        text = text.replace("```", "")
        
        # Supprimer les répétitions du prompt
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line.startswith("Utilisateur:") and \
               not line.startswith("Assistant:") and \
               not line.startswith("Tu es un") and \
               not line.startswith("CONTEXTE:") and \
               not line.startswith("RÈGLES:"):
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines).strip()
    
    def _load_knowledge_base(self):
        """Charger la base de connaissances"""
        kb_file = self.config.DB_PATH / "knowledge_base.json"
        if kb_file.exists():
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"📚 Base de connaissances chargée: {len(self.knowledge_base)} entrées")
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement KB: {e}")
                self.knowledge_base = {}
        else:
            self.knowledge_base = {}
            logger.info("📚 Pas de base de connaissances (création au premier usage)")
    
    def get_status(self):
        """Obtenir le statut du service IA"""
        gemini_status = 'online' if (
            self.config.GEMINI_API_KEY and 
            self.gemini_service.model
        ) else 'offline'
        
        return {
            'status': 'online' if gemini_status == 'online' else 'degraded',
            'model': self.config.GEMINI_MODEL,
            'gemini_status': gemini_status,
            'api_key_present': bool(self.config.GEMINI_API_KEY),
            'timestamp': datetime.now().isoformat()
        }
    
    def query_database(self, query_type: str = 'latest', limit: int = 10) -> dict:
        """
        Interroger la base de données des diagnostics et pannes
        Postgres en priorité, fallback sur fichiers
        """
        logger.info(f"🔍 query_database appelé avec type={query_type}")
        
        # Essayer Postgres d'abord si disponible
        logger.info(f"🔍 is_postgres_enabled() = {is_postgres_enabled()}")
        
        if is_postgres_enabled():
            try:
                from db_postgres import get_latest_diagnostic, get_diagnostics_stats
                
                if query_type == 'latest':
                    diag = get_latest_diagnostic()
                    logger.info(f"🔍 Résultat Postgres get_latest_diagnostic: {diag is not None}")
                    if diag:
                        results = {
                            'query_type': query_type,
                            'timestamp': datetime.now().isoformat(),
                            'data': [diag],
                            'summary': {
                                'derniere_panne': diag.get('type_panne', 'Inconnue'),
                                'date_detection': diag.get('timestamp', 'Non disponible'),
                                'nombre_pannes_detectees': 1 if diag.get('panne_detectee') else 0,
                                'score_confiance': diag.get('score_confiance', 0)
                            }
                        }
                        logger.info(f"✅ Requête BD Postgres réussie: {query_type}")
                        return results
                
                elif query_type == 'stats':
                    stats = get_diagnostics_stats()
                    results = {
                        'query_type': query_type,
                        'timestamp': datetime.now().isoformat(),
                        'data': [],
                        'summary': {
                            'total_pannes_possibles': 8,
                            'pannes_detectees': stats.get('pannes_detectees', 0),
                            'pannes_liste': [],
                            'stats_postgres': stats
                        }
                    }
                    logger.info(f"✅ Requête BD Postgres stats: {stats}")
                    return results
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur Postgres (fallback fichiers): {e}")
        
        # Fallback sur fichiers
        logger.info("🔍 Fallback sur fichiers...")
        try:
            data_dir = Path(__file__).parent.parent / "data"
            diagnostic_file = data_dir / "dernier_diagnostic.json"
            dataset_file = data_dir / "dataset_apprentissage.csv"
            
            logger.info(f"🔍 Chemin fichier diagnostic: {diagnostic_file}")
            logger.info(f"🔍 Fichier existe: {diagnostic_file.exists()}")
            
            results = {
                'query_type': query_type,
                'timestamp': datetime.now().isoformat(),
                'data': []
            }
            
            if diagnostic_file.exists():
                with open(diagnostic_file, 'r', encoding='utf-8') as f:
                    dernier_diag = json.load(f)
                
                logger.info(f"🔍 Données chargées: diagnostic_id={dernier_diag.get('diagnostic_id')}, panne_detectee={dernier_diag.get('panne_detectee')}")
                    
                if query_type == 'latest':
                    results['data'] = [dernier_diag]
                    prediction = dernier_diag.get('prediction_ia', {})
                    type_panne = prediction.get('panne_detectee', 'Inconnue')
                    logger.info(f"🔍 Type de panne trouvé: {type_panne}")
                    results['summary'] = {
                        'derniere_panne': type_panne,
                        'date_detection': dernier_diag.get('timestamp', 'Non disponible'),
                        'nombre_pannes_detectees': len([p for p, v in prediction.get('diagnostic_complet', {}).items() if v == 1]),
                        'score_confiance': prediction.get('score', 0)
                    }
                    
                elif query_type == 'stats':
                    prediction = dernier_diag.get('prediction_ia', {})
                    diag_complet = prediction.get('diagnostic_complet', {})
                    pannes_actives = [p for p, v in diag_complet.items() if v == 1]
                    results['summary'] = {
                        'total_pannes_possibles': len(diag_complet),
                        'pannes_detectees': len(pannes_actives),
                        'pannes_liste': pannes_actives,
                        'timestamp': dernier_diag.get('timestamp')
                    }
                    results['data'] = [dernier_diag]
                    
                elif query_type == 'critical':
                    prediction = dernier_diag.get('prediction_ia', {})
                    diag_complet = prediction.get('diagnostic_complet', {})
                    pannes_critiques = []
                    for panne, valeur in diag_complet.items():
                        if valeur == 1 and panne in ['surchauffe_compresseur', 'défaillance_compresseur', 'fuite_fluide', 'panne_electrique']:
                            pannes_critiques.append(panne)
                    results['data'] = pannes_critiques
                    results['summary'] = {
                        'pannes_critiques_count': len(pannes_critiques),
                        'pannes_critiques_list': pannes_critiques
                    }
                    
                else:  # all
                    results['data'] = [dernier_diag]
                    
            # Lire le dataset d'apprentissage si disponible
            if dataset_file.exists() and query_type in ['stats', 'all']:
                import pandas as pd
                try:
                    df = pd.read_csv(dataset_file)
                    results['dataset_stats'] = {
                        'total_enregistrements': len(df),
                        'colonnes': list(df.columns)
                    }
                except:
                    pass
                    
            logger.info(f"✅ Requête BD fichiers réussie: {query_type}, {len(results['data'])} résultats, summary={results.get('summary', {})}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur requête BD fichiers: {e}")
            return {
                'query_type': query_type,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'data': []
            }
    
    def process_prediction_alert(self, prediction_data: dict) -> dict:
        """
        Traiter une alerte de prédiction du système avec plusieurs pannes
        
        Args:
            prediction_data: Données de prédiction contenant:
                - pannes: Liste des pannes détectées avec leurs scores
                - nombre_pannes: Nombre total de pannes
                - capteurs: Données des capteurs
                - timestamp: Date/heure
                - diagnostic_id: ID du diagnostic
                - localisation: Zone de détection
                
        Returns:
            dict: Résultat de l'analyse et alerte formatée
        """
        try:
            # Récupérer la liste des pannes et filtrer celles avec confiance >= 50%
            pannes_list = prediction_data.get('pannes', [])
            pannes_list = [p for p in pannes_list if p.get('score', 0) >= 50]
            nombre_pannes = len(pannes_list)
            capteurs = prediction_data.get('capteurs', {})
            timestamp = prediction_data.get('timestamp', datetime.now().isoformat())
            diagnostic_id = prediction_data.get('diagnostic_id', 'UNKNOWN')
            localisation = prediction_data.get('localisation', 'Zone non spécifiée')
            
            if not pannes_list:
                logger.warning("⚠️ Aucune panne significative (score >= 50%) dans les données de prédiction")
                return {
                    'error': 'Aucune panne significative à analyser',
                    'type': 'prediction',
                    'status': 'no_significant_faults'
                }
            
            logger.info(f"🔔 Traitement alerte prédiction: {nombre_pannes} panne(s) significative(s) détectée(s)")
            
            # Construire la liste des pannes pour le prompt
            pannes_details = []
            for idx, panne_info in enumerate(pannes_list, 1):
                panne_name = panne_info.get('panne', 'Inconnue')
                panne_score = panne_info.get('score', 0)
                panne_type = panne_info.get('type', 'Inconnu')
                pannes_details.append(f"{idx}. {panne_name} (confiance: {panne_score:.1f}%, type: {panne_type})")
            
            # Créer un prompt pour l'analyse IA de toutes les pannes
            prompt = f"""
Analyse de prédiction de panne frigorifique - MULTIPLES PANNES DÉTECTÉES

Diagnostic ID: {diagnostic_id}
Localisation: {localisation}
Timestamp: {timestamp}
Nombre de pannes détectées: {nombre_pannes}

PANNES IDENTIFIÉES:
{chr(10).join(pannes_details)}

Données capteurs:
"""
            for capteur, valeur in capteurs.items():
                prompt += f"- {capteur}: {valeur}\n"
            
            prompt += f"""
Fournis une analyse COMPLÈTE et DÉTAILLÉE. Sois précis et technique:

🔍 DIRECTIVES IMPORTANTES:
- Pour chaque panne, EXPLIQUE pourquoi les données des capteurs indiquent cette panne
- Donne des recommandations CONCRÈTES et ACTIONNABLES (pas de généralités)
- Utilise les VALEURS RÉELLES des capteurs dans ton analyse
- Identifie la cause racine avec des arguments techniques

1. SYNTHÈSE GLOBALE
   - Nombre total de pannes significatives: {nombre_pannes}
   - Niveau de criticité global (Faible/Moyen/Haut/Critique) avec justification
   - Urgence immédiate requise (Oui/Non) et pourquoi
   - Impact sur la production/système

2. ANALYSE TECHNIQUE DES DONNÉES CAPTEURS
   Pour chaque capteur, analyse sa valeur et son lien avec les pannes:
   - Température: valeur actuelle vs normale, écart, impact
   - Pression HP: valeur vs plage normale, risque associé
   - Pression BP: valeur vs plage normale, conséquences
   - Courant: consommation anormale? surchauffe?
   - Autres capteurs pertinents
   
   Lie EXPLICITEMENT chaque anomalie capteur à une panne spécifique.

3. ANALYSE DÉTAILLÉE PAR PANNE SIGNIFICATIVE
   Pour chaque panne détectée (score >= 50%):
   
   a) Description technique précise
      - Qu'est-ce que cette panne concrètement?
      - Composants physiques affectés
      - Mécanisme de défaillance
   
   b) Justification basée sur les capteurs
      - Quelles valeurs capteurs confirment cette panne?
      - Quel est le seuil normal vs la valeur actuelle?
      - Pourquoi ces valeurs indiquent-elles cette panne?
   
   c) Cause probable spécifique
      - Cause racine technique la plus vraisemblable
      - Facteurs contribuants
      - Scénario de défaillance
   
   d) Niveau de criticité individuel avec justification
   
   e) Impact opérationnel
      - Conséquences immédiates
      - Risques si non traité
      - Délai avant aggravation

4. DIAGNOSTIC FINAL - CAUSE RACINE
   - Identifie LA panne principale (root cause)
   - Explique le mécanisme causal complet en chaîne
   - Pourquoi les autres pannes sont des symptômes/conséquences
   - Preuves basées sur les données capteurs

5. ACTIONS RECOMMANDÉES PRIORISÉES (ACTIONNABLES)
   
   ⚠️ ACTIONS IMMÉDIATES (à faire en priorité):
   1. [Action concrète 1] - Objectif: [résultat attendu] - Délai: [X heures]
   2. [Action concrète 2] - Objectif: [résultat attendu] - Délai: [X heures]
   
   🔧 ACTIONS CORRECTIVES (réparation):
   1. [Étape technique 1] - Composants: [liste] - Compétence: [technicien/type]
   2. [Étape technique 2] - Composants: [liste] - Compétence: [technicien/type]
   
   ✅ ACTIONS DE VÉRIFICATION:
   - Tests à effectuer après réparation
   - Valeurs capteurs à surveiller
   - Critères de validation

6. MESURES DE PRÉVENTION
   - Fréquence de contrôle recommandée et pourquoi
   - Points de surveillance critiques (capteurs à monitorer)
   - Seuils d'alerte à configurer
   - Maintenance préventive spécifique

EXIGENCES:
- Utilise les VALEURS RÉELLES des capteurs dans ton analyse
- Sois CONCRET et TECHNIQUE, pas théorique
- Chaque recommandation doit être ACTIONNABLE
- Explique le POURQUOI derrière chaque diagnostic
"""
            
            # Analyser avec le modèle approprié
            if self.config.ANALYSIS_STRATEGY == 'gpt4_only' or self.config.DISABLE_GEMINI:
                result = self._analyze_with_gpt4(prompt)
            else:
                result = self._analyze_with_primary_fallback(prompt)
            
            # Calculer la sévérité globale basée sur toutes les pannes
            severities = []
            for panne_info in pannes_list:
                panne_name = panne_info.get('panne', 'Inconnue')
                panne_score = panne_info.get('score', 0)
                severities.append(self._calculate_severity(panne_name, panne_score))
            
            # La sévérité globale est la plus élevée des pannes
            severity_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            global_severity = max(severities, key=lambda s: severity_priority.get(s, 0))
            
            # Liste des noms de pannes pour le titre
            pannes_noms = [p.get('panne', 'Inconnue') for p in pannes_list]
            if len(pannes_noms) > 3:
                pannes_titre = f"{len(pannes_noms)} pannes détectées"
            else:
                pannes_titre = ", ".join(pannes_noms)
            
            # Créer l'alerte formatée
            alert = {
                'alert_id': f"PRED_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'type': 'prediction',
                'severity': global_severity,
                'title': f"🔮 Prédiction: {pannes_titre}",
                'message': result.get('response', 'Analyse non disponible'),
                'prediction_data': prediction_data,
                'analysis_result': result,
                'timestamp': timestamp,
                'diagnostic_id': diagnostic_id,
                'localisation': localisation,
                'pannes_count': nombre_pannes,
                'pannes_list': pannes_list,
                'requires_attention': global_severity in ['critical', 'high'] or nombre_pannes >= 3
            }
            
            # Sauvegarder l'alerte
            self._save_alert(alert)
            
            # Sauvegarder chaque panne individuellement dans un fichier dédié
            self._save_individual_pannes(alert, pannes_list, diagnostic_id)
            
            logger.info(f"✅ Alerte prédiction créée avec {nombre_pannes} panne(s): {alert['alert_id']}")
            return alert
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement prédiction: {e}")
            return {
                'error': str(e),
                'type': 'prediction',
                'status': 'failed'
            }
    
    def _save_individual_pannes(self, alert: dict, pannes_list: list, diagnostic_id: str):
        """Sauvegarder chaque panne individuellement dans un fichier dédié ET dans PostgreSQL"""
        try:
            pannes_dir = self.config.DB_PATH / "pannes"
            pannes_dir.mkdir(exist_ok=True)
            
            saved_to_db = 0
            saved_to_file = 0
            
            for idx, panne_info in enumerate(pannes_list):
                panne_record = {
                    'panne_id': f"{diagnostic_id}_P{idx+1}",
                    'diagnostic_id': diagnostic_id,
                    'alert_id': alert['alert_id'],
                    'panne_name': panne_info.get('panne', 'Inconnue'),
                    'score': panne_info.get('score', 0),
                    'type': panne_info.get('type', 'Inconnu'),
                    'timestamp': alert['timestamp'],
                    'localisation': alert.get('localisation', 'Inconnue'),
                    'severity': self._calculate_severity(
                        panne_info.get('panne', 'Inconnue'),
                        panne_info.get('score', 0)
                    )
                }
                
                # 1. Sauvegarder dans un fichier JSON individuel
                try:
                    panne_file = pannes_dir / f"{panne_record['panne_id']}.json"
                    with open(panne_file, 'w', encoding='utf-8') as f:
                        json.dump(panne_record, f, indent=2, ensure_ascii=False)
                    saved_to_file += 1
                except Exception as e:
                    logger.error(f"❌ Erreur sauvegarde fichier panne {panne_record['panne_id']}: {e}")
                
                # 2. Sauvegarder dans PostgreSQL si disponible
                try:
                    if is_postgres_enabled():
                        from db_postgres import save_panne
                        if save_panne(panne_record):
                            saved_to_db += 1
                except Exception as e:
                    logger.warning(f"⚠️ Erreur sauvegarde DB panne {panne_record['panne_id']}: {e}")
                
                logger.info(f"💾 Panne sauvegardée: {panne_record['panne_id']} - {panne_record['panne_name']} (fichier: {saved_to_file}, DB: {saved_to_db})")
                
            logger.info(f"✅ {len(pannes_list)} panne(s) sauvegardée(s): {saved_to_file} en fichier, {saved_to_db} en DB")
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde pannes individuelles: {e}")
    
    def _calculate_severity(self, panne_type: str, confiance: float) -> str:
        """Calculer le niveau de sévérité d'une panne"""
        pannes_critiques = [
            'surchauffe_compresseur', 
            'défaillance_compresseur', 
            'panne_electrique',
            'fuite_fluide',
            'pression_anormale_HP'
        ]
        
        if panne_type in pannes_critiques and confiance > 80:
            return 'critical'
        elif panne_type in pannes_critiques or confiance > 70:
            return 'high'
        elif confiance > 50:
            return 'medium'
        else:
            return 'low'
    
    def _save_alert(self, alert: dict):
        """Sauvegarder une alerte dans la base de données"""
        try:
            alerts_file = self.config.DB_PATH / "alerts.json"
            
            alerts = []
            if alerts_file.exists():
                with open(alerts_file, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            
            alerts.append(alert)
            
            # Garder uniquement les 100 dernières alertes
            if len(alerts) > 100:
                alerts = alerts[-100:]
            
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Alerte sauvegardée: {alert['alert_id']}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde alerte: {e}")
    
    def get_alerts(self, limit: int = 10, severity: str = None) -> list:
        """
        Récupérer les alertes stockées
        
        Args:
            limit: Nombre maximum d'alertes
            severity: Filtrer par sévérité (optional)
            
        Returns:
            list: Liste des alertes
        """
        try:
            alerts_file = self.config.DB_PATH / "alerts.json"
            
            if not alerts_file.exists():
                return []
            
            with open(alerts_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
            
            # Filtrer par sévérité si demandé
            if severity:
                alerts = [a for a in alerts if a.get('severity') == severity]
            
            # Trier par timestamp (plus récent en premier)
            alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération alertes: {e}")
            return []


# Singleton instance
ia_service = None

def get_service():
    """Obtenir l'instance singleton du service IA"""
    global ia_service
    if ia_service is None:
        ia_service = IAService()
    return ia_service
