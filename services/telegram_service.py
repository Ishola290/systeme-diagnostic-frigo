import requests
import logging

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def envoyer_alerte_panne_sync(self, message):
        """Envoie une alerte de panne (version synchrone)"""
        return self.envoyer_notification_sync(message)
    
    def envoyer_notification_sync(self, message):
        """Envoie une notification Telegram (version synchrone)"""
        try:
            # Nettoyer le message et extraire le texte si nécessaire
            if isinstance(message, dict):
                # Si c'est un dict, essayer d'extraire 'analyse', 'text', 'message', etc.
                message = message.get('analyse') or message.get('text') or message.get('message') or str(message)
            
            # Convertir en string de manière robuste
            message_str = str(message) if message else ""
            
            # Si c'est un objet Google GenerativeAI Response, extraire le texte
            if 'GenerateContentResponse' in str(type(message_str)):
                logger.error(f"Objet Response non converti: {type(message_str)}")
                message_str = "Erreur: réponse non convertie"
            
            message = message_str
            
            # Supprimer les caractères HTML et spéciaux problématiques
            message = message.replace('<', '').replace('>', '').replace('&', 'et')
            
            # Limiter à 4096 caractères
            if len(message) > 4096:
                message = message[:4090] + "..."
            
            # LOG DU MESSAGE QUI SERA ENVOYÉ
            logger.info(f"📤 Message à envoyer Telegram (type: {type(message).__name__}, len: {len(str(message))}): {str(message)[:100]}...")
            
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Telegram API error {response.status_code}: {response.text}")
                return None
            
            logger.info("Message Telegram envoyé")
            return response.json()
            
        except Exception as e:
            logger.error(f"Erreur Telegram: {e}")
            return None