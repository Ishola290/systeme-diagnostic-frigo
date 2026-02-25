"""
Service OpenAI GPT-4 - Analyse intelligente des pannes
"""

import openai
import logging
from typing import Dict, List, Optional
import json
import re
import time

logger = logging.getLogger(__name__)


class GPT4Service:
    """Service pour l'analyse IA avec OpenAI GPT-4"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo-preview", temperature: float = 0.3, base_url: str = None):
        """
        Initialise le service GPT-4
        
        Args:
            api_key: Clé API OpenAI ou Azure
            model_name: Nom du modèle GPT à utiliser
            temperature: Température pour la génération (0-1)
            base_url: URL de base pour l'API (optionnel, pour Azure ou autres endpoints)
        """
        logger.info(f"🔍 Initialisation GPT-4 - API Key présente: {bool(api_key and api_key.strip())}")
        if base_url:
            logger.info(f"🔗 URL de base personnalisée: {base_url}")
        
        if not api_key or not api_key.strip():
            logger.warning("❌ OPENAI_API_KEY non configurée ou vide - Mode dégradé")
            self.api_key = None
            self.client = None
        else:
            self.api_key = api_key
            self.model_name = model_name
            self.temperature = temperature
            
            # Configurer le client avec ou sans base_url personnalisée
            client_kwargs = {'api_key': api_key}
            if base_url:
                client_kwargs['base_url'] = base_url
            
            self.client = openai.OpenAI(**client_kwargs)
            logger.info(f"✅ GPT-4 initialisé avec modèle: {model_name}")
    
    def generer_analyse_sync(self, prompt: str, max_tokens: int = 1000) -> Dict:
        """
        Génère une analyse avec GPT-4 (synchrone)
        
        Args:
            prompt: Prompt d'analyse
            max_tokens: Nombre maximum de tokens
            
        Returns:
            Dictionnaire avec le résultat de l'analyse
        """
        if not self.client:
            logger.warning("⚠️ GPT-4 non disponible - fallback")
            return {
                'success': False,
                'error': 'Service GPT-4 non configuré',
                'analyse': None,
                'model_used': 'fallback'
            }
        
        try:
            start_time = time.time()
            logger.info(f"🤖 GPT-4 analyse en cours...")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Tu es un expert en diagnostic de systèmes frigorifiques industriels."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            processing_time = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                analyse = response.choices[0].message.content.strip()
                
                logger.info(f"✅ GPT-4 analyse générée en {processing_time:.2f}s")
                
                return {
                    'success': True,
                    'analyse': analyse,
                    'model_used': 'gpt-4',
                    'processing_time': processing_time,
                    'tokens_used': response.usage.total_tokens if response.usage else 0
                }
            else:
                logger.error("❌ GPT-4 pas de réponse générée")
                return {
                    'success': False,
                    'error': 'Pas de réponse générée',
                    'model_used': 'gpt-4'
                }
                
        except openai.RateLimitError as e:
            logger.error(f"❌ GPT-4 rate limit: {e}")
            return {
                'success': False,
                'error': 'Limite de taux atteinte',
                'model_used': 'gpt-4'
            }
        except openai.APIError as e:
            logger.error(f"❌ GPT-4 API error: {e}")
            return {
                'success': False,
                'error': f'Erreur API GPT-4: {str(e)}',
                'model_used': 'gpt-4'
            }
        except Exception as e:
            logger.error(f"❌ GPT-4 erreur inattendue: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Erreur inattendue: {str(e)}',
                'model_used': 'gpt-4'
            }
    
    def generer_notification_retrainement(self, modele_name: str, performances: Dict, 
                                         donnees_entrainement: int) -> Dict:
        """
        Génère une notification de réentraînement avec GPT-4
        
        Args:
            modele_name: Nom du modèle réentraîné
            performances: Dictionnaire des performances
            donnees_entrainement: Nombre de données d'entraînement
            
        Returns:
            Dictionnaire avec la notification générée
        """
        prompt = f"""
        En tant qu'expert IA, génère une notification professionnelle pour le réentraînement du modèle "{modele_name}".
        
        Contexte:
        - Performances: {json.dumps(performances, indent=2)}
        - Données d'entraînement: {donnees_entrainement} échantillons
        
        Génère un message concis et informatif pour l'équipe technique.
        """
        
        return self.generer_analyse_sync(prompt, max_tokens=500)
    
    def generer_notification_nouvelle_panne(self, panne_info: Dict) -> Dict:
        """
        Génère une notification pour nouvelle panne détectée avec GPT-4
        
        Args:
            panne_info: Informations sur la nouvelle panne
            
        Returns:
            Dictionnaire avec la notification générée
        """
        prompt = f"""
        En tant qu'expert en diagnostic frigorifique, génère une alerte pour une nouvelle panne détectée.
        
        Informations:
        {json.dumps(panne_info, indent=2)}
        
        Génère une alerte claire avec:
        - Description de la panne
        - Causes possibles
        - Actions recommandées
        """
        
        return self.generer_analyse_sync(prompt, max_tokens=600)
    
    def nettoyer_reponse(self, reponse: str) -> str:
        """
        Nettoie la réponse de GPT-4 pour enlever les artefacts
        
        Args:
            reponse: Réponse brute de GPT-4
            
        Returns:
            Réponse nettoyée
        """
        if not reponse:
            return ""
        
        # Enlever les caractères spéciaux et formater
        reponse = re.sub(r'\*\*(.*?)\*\*', r'\1', reponse)  # Gras
        reponse = re.sub(r'\*(.*?)\*', r'\1', reponse)      # Italique
        reponse = re.sub(r'`(.*?)`', r'\1', reponse)        # Code
        
        # Nettoyer les espaces multiples
        reponse = re.sub(r'\s+', ' ', reponse).strip()
        
        return reponse
    
    def test_connexion(self) -> bool:
        """
        Teste la connexion à l'API GPT-4
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        if not self.client:
            return False
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"❌ Test connexion GPT-4 échoué: {e}")
            return False
