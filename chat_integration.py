"""
Module d'intégration avec l'application web chat
Permet à app.py de communiquer avec l'interface web
"""

import requests
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class ChatWebIntegration:
    """Classe pour intégrer avec l'application web chat"""
    
    def __init__(self, web_app_url: str = None):
        """
        Initialiser l'intégration
        
        Args:
            web_app_url: URL de l'application web (ex: http://localhost:5001)
        """
        self.web_app_url = web_app_url or os.environ.get('CHAT_WEB_URL', 'http://localhost:5001')
        self.timeout = 5
        self.enabled = True
    
    def send_alert(self, 
                   title: str, 
                   message: str, 
                   severity: str = 'medium',
                   alert_type: str = 'warning',
                   diagnostic_id: str = None) -> bool:
        """
        Envoyer une alerte à l'application web
        
        Args:
            title: Titre de l'alerte
            message: Message d'alerte
            severity: Sévérité (low, medium, high, critical)
            alert_type: Type (error, warning, info)
            diagnostic_id: ID du diagnostic associé
            
        Returns:
            True si succès, False sinon
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.web_app_url}/api/receive-alert"
            payload = {
                'title': title,
                'message': message,
                'severity': severity,
                'type': alert_type,
                'diagnostic_id': diagnostic_id
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 201:
                logger.info(f"✅ Alerte envoyée au web app: {title}")
                return True
            else:
                logger.warning(f"⚠️  Erreur envoi alerte web: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur communication web app: {e}")
            self.enabled = False  # Désactiver pour ne pas surcharger
            return False
    
    def send_diagnostic(self,
                       diagnostic_id: str,
                       description: str,
                       result: Dict[str, Any],
                       status: str = 'completed') -> bool:
        """
        Envoyer un diagnostic à l'application web
        
        Args:
            diagnostic_id: ID unique du diagnostic
            description: Description du diagnostic
            result: Résultat du diagnostic (dict)
            status: Statut (pending, completed, error)
            
        Returns:
            True si succès, False sinon
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.web_app_url}/api/receive-diagnostic"
            payload = {
                'diagnostic_id': diagnostic_id,
                'description': description,
                'result': result,
                'status': status
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 201:
                logger.info(f"✅ Diagnostic envoyé au web app: {diagnostic_id}")
                return True
            else:
                logger.warning(f"⚠️  Erreur envoi diagnostic web: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur communication web app: {e}")
            self.enabled = False
            return False
    
    def send_message(self,
                     content: str,
                     user: str = 'System',
                     is_from_system: bool = False) -> bool:
        """
        Envoyer un message au chat web
        
        Args:
            content: Contenu du message
            user: Utilisateur (pour identification)
            is_from_system: True si c'est une réponse système
            
        Returns:
            True si succès, False sinon
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.web_app_url}/api/messages"
            payload = {
                'content': content,
                'user': user,
                'is_from_system': is_from_system
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 201:
                logger.info(f"✅ Message envoyé au web app")
                return True
            else:
                logger.warning(f"⚠️  Erreur envoi message web: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur communication web app: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Vérifier si l'application web est accessible
        
        Returns:
            True si accessible, False sinon
        """
        try:
            response = requests.get(f"{self.web_app_url}/api/stats", timeout=2)
            self.enabled = response.status_code == 200
            return self.enabled
        except Exception:
            self.enabled = False
            return False

# Instance globale
chat_integration = None

def init_chat_integration(web_app_url: str = None) -> ChatWebIntegration:
    """Initialiser l'intégration chat"""
    global chat_integration
    chat_integration = ChatWebIntegration(web_app_url)
    logger.info(f"📱 Intégration chat web initialisée: {chat_integration.web_app_url}")
    return chat_integration

def get_chat_integration() -> Optional[ChatWebIntegration]:
    """Obtenir l'instance d'intégration"""
    return chat_integration

# Utilisation dans app.py:
# 
# from chat_integration import init_chat_integration, get_chat_integration
# 
# # Dans la configuration
# chat_web = init_chat_integration(Config.CHAT_WEB_URL)
# 
# # Utilisation
# chat_web.send_alert('Erreur température', 'Temp: 25°C', severity='high', diagnostic_id='DIAG-123')
# chat_web.send_diagnostic('DIAG-123', 'Diagnostic compresseur', {'status': 'OK'})
