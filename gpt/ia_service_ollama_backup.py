"""
Service IA Local - Point central de traitement
Architecture simplifiée: OLLAMA UNIQUEMENT
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IAConfig:
    """Configuration du service IA - OLLAMA UNIQUEMENT"""
    
    # ========== OLLAMA ONLY ==========
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    DEFAULT_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')
    
    # Paramètres LLM
    MAX_TOKENS = 500
    TEMPERATURE = 0.7
    TOP_P = 0.90
    
    # Contexte persistant
    CONTEXT_SIZE = 10
    
    # Bases de données
    DB_PATH = Path(__file__).parent / "data"
    CACHE_PATH = Path(__file__).parent / "cache"
    
    def __init__(self):
        self.DB_PATH.mkdir(exist_ok=True)
        self.CACHE_PATH.mkdir(exist_ok=True)

class IAService:
    """Service IA principal - OLLAMA UNIQUEMENT"""
    
    def __init__(self, model_name=None):
        self.config = IAConfig()
        self.conversation_history = []
        self.knowledge_base = {}
        self.model_info = {}
        
        self.model_name = model_name or self.config.DEFAULT_MODEL
        logger.info(f"🤖 Initialisation service IA - OLLAMA ONLY")
        logger.info(f"📋 Modèle: {self.model_name}")
        logger.info(f"🔗 URL: {self.config.OLLAMA_URL}")
        
        # Vérifier la connexion Ollama
        self._check_ollama_connection()
        self._load_knowledge_base()
    
    def _check_ollama_connection(self):
        """Vérifier la connexion à Ollama"""
        try:
            response = requests.get(
                f"{self.config.OLLAMA_URL}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                logger.info(f"✅ Ollama connecté - Modèles disponibles: {len(models)}")
                logger.info(f"   Modèles: {', '.join(model_names[:5])}")
                
                # Vérifier si le modèle par défaut est disponible
                if self.model_name not in str(model_names):
                    logger.warning(f"⚠️ Modèle '{self.model_name}' non trouvé")
                    logger.info(f"   Installez-le avec: ollama pull {self.model_name}")
            else:
                logger.error(f"❌ Ollama retourné HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Ollama non accessible: {e}")
            logger.info("   Installez Ollama: https://ollama.com/download")
            logger.info(f"   Puis téléchargez: ollama pull {self.model_name}")
    
    def process_chat(self, message, user_id='user', user_name='Utilisateur', 
                     context=None, source='chat'):
        """
        Traiter un message de chat avec Ollama
        """
        try:
            logger.info(f"💬 Traitement message de {user_name}: {message[:50]}...")
            
            # Construire le prompt avec contexte frigorifique
            system_prompt = self._build_system_prompt(context)
            
            # Appeler Ollama
            response = requests.post(
                f"{self.config.OLLAMA_URL}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"{system_prompt}\n\nUtilisateur: {message}\n\nAssistant:",
                    "stream": False,
                    "options": {
                        "temperature": self.config.TEMPERATURE,
                        "top_p": self.config.TOP_P,
                        "num_predict": self.config.MAX_TOKENS
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Nettoyer la réponse
                response_text = self._clean_response(response_text)
                
                logger.info(f"✅ Réponse générée ({len(response_text)} caractères)")
                
                return {
                    'success': True,
                    'response': response_text,
                    'user_id': user_id,
                    'user_name': user_name,
                    'model': self.model_name,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Erreur Ollama HTTP {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'response': "Service IA temporairement indisponible."
                }
                
        except requests.Timeout:
            logger.error("❌ Timeout Ollama")
            return {
                'success': False,
                'error': 'timeout',
                'response': "Le service IA met trop de temps à répondre."
            }
        except Exception as e:
            logger.error(f"❌ Erreur traitement: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Erreur de communication avec l'IA."
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
            
            response = requests.post(
                f"{self.config.OLLAMA_URL}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": diagnostic_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,  # Plus précis pour diagnostics
                        "top_p": 0.95,
                        "num_predict": self.config.MAX_TOKENS
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '').strip()
                analysis = self._clean_response(analysis)
                
                logger.info("✅ Diagnostic généré")
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'alert_id': alert_data.get('diagnostic_id'),
                    'model': self.model_name,
                    'timestamp': datetime.now().isoformat()
                }
            else:
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
        # Supprimer les balises markdown excessives
        text = text.replace("```", "")
        # Supprimer les répétitions du prompt
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            if not line.strip().startswith("Utilisateur:") and \
               not line.strip().startswith("Assistant:") and \
               not line.strip().startswith("Tu es un"):
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
        try:
            response = requests.get(
                f"{self.config.OLLAMA_URL}/api/tags",
                timeout=3
            )
            ollama_status = 'online' if response.status_code == 200 else 'offline'
        except:
            ollama_status = 'offline'
        
        return {
            'status': 'online' if ollama_status == 'online' else 'degraded',
            'model': self.model_name,
            'ollama_status': ollama_status,
            'ollama_url': self.config.OLLAMA_URL,
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
ia_service = None

def get_service():
    """Obtenir l'instance singleton du service IA"""
    global ia_service
    if ia_service is None:
        ia_service = IAService()
    return ia_service
