"""
Service Agent IA - Communication avec l'agent de prédiction
"""

import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AgentIAService:
    """Service pour communiquer avec l'agent IA de prédiction"""
    
    def __init__(self, agent_url: str, timeout: int = 30):
        """
        Initialise le service Agent IA
        
        Args:
            agent_url: URL de l'agent IA
            timeout: Timeout des requêtes en secondes
        """
        self.agent_url = agent_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"Agent IA configuré: {agent_url}")
    
    def predict(self, donnees_capteurs: Dict) -> Dict:
        """
        Effectue une prédiction de panne
        
        Args:
            donnees_capteurs: Données des capteurs
            
        Returns:
            Résultat de la prédiction
        """
        try:
            logger.info("Appel Agent IA /predict")
            
            response = requests.post(
                f"{self.agent_url}/predict",
                json=donnees_capteurs,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Prédiction reçue: {result.get('panne_detectee', 'Aucune')}")
            
            return self._normaliser_prediction(result)
            
        except requests.Timeout:
            logger.error("Timeout lors de l'appel à l'agent IA")
            return self._prediction_fallback("timeout")
            
        except requests.RequestException as e:
            logger.error(f"Erreur HTTP Agent IA: {e}")
            return self._prediction_fallback("http_error")
            
        except Exception as e:
            logger.error(f"Erreur inattendue Agent IA: {e}")
            return self._prediction_fallback("unknown_error")
    
    def _normaliser_prediction(self, result: Dict) -> Dict:
        """
        Normalise la réponse de l'agent IA
        
        Args:
            result: Résultat brut de l'agent
            
        Returns:
            Résultat normalisé
        """
        # Gérer les différents formats de réponse
        panne_detectee = result.get('panne_detectee') or result.get('panne_detectée')
        
        # Construire la liste des pannes détectées
        pannes_detectees = []
        
        # Si l'agent renvoie plusieurs pannes
        if 'diagnostic_complet' in result:
            for panne, detectee in result['diagnostic_complet'].items():
                if detectee == 1:
                    pannes_detectees.append({
                        'panne': panne,
                        'score': result.get('score', 0) if panne == panne_detectee else 0,
                        'variable': result.get('variable_dominante', 'N/A')
                    })
        
        # Si une seule panne
        elif panne_detectee:
            pannes_detectees.append({
                'panne': panne_detectee,
                'score': result.get('score', 0),
                'variable': result.get('variable_dominante', 'N/A')
            })
        
        return {
            'panne_detectee': panne_detectee,
            'pannes_detectees': pannes_detectees,
            'score': result.get('score', 0),
            'variable_dominante': result.get('variable_dominante', 'N/A'),
            'diagnostic_complet': result.get('diagnostic_complet', {}),
            'timestamp': result.get('timestamp'),
            'avertissement': result.get('avertissement')
        }
    
    def _prediction_fallback(self, error_type: str) -> Dict:
        """
        Retourne une prédiction par défaut en cas d'erreur
        
        Args:
            error_type: Type d'erreur
            
        Returns:
            Prédiction par défaut
        """
        return {
            'panne_detectee': None,
            'pannes_detectees': [],
            'score': 0,
            'variable_dominante': f'Erreur: {error_type}',
            'diagnostic_complet': {},
            'error': error_type
        }
    
    def retrain(self, dataset_path: str = None, compteur: int = 0) -> Dict:
        """
        Lance un réentraînement des modèles
        
        Args:
            dataset_path: Chemin du dataset
            compteur: Nombre total de diagnostics
            
        Returns:
            Résultat du réentraînement
        """
        try:
            logger.info(f"Lancement réentraînement (compteur: {compteur})")
            
            response = requests.post(
                f"{self.agent_url}/retrain",
                json={
                    'dataset_path': dataset_path or './dataset_apprentissage.csv',
                    'compteur': compteur
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Réentraînement terminé")
            return result
            
        except Exception as e:
            logger.error(f"Erreur réentraînement: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_new_fault(self, nouvelle_panne: Dict) -> Dict:
        """
        Entraîne un modèle pour une nouvelle panne
        
        Args:
            nouvelle_panne: Informations sur la nouvelle panne
            
        Returns:
            Résultat de l'entraînement
        """
        try:
            logger.info(f"Entraînement nouvelle panne: {nouvelle_panne.get('signature')}")
            
            response = requests.post(
                f"{self.agent_url}/train_new_fault",
                json={
                    'fault_signature': nouvelle_panne.get('signature'),
                    'dataset_content': nouvelle_panne.get('csv_content'),
                    'sample_count': nouvelle_panne.get('count')
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Nouvelle panne entraînée")
            return result
            
        except Exception as e:
            logger.error(f"Erreur entraînement nouvelle panne: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        """
        Vérifie le statut de l'agent IA
        
        Returns:
            Statut de l'agent
        """
        try:
            response = requests.get(f"{self.agent_url}/status", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Agent IA inaccessible: {e}")
            return {'status': 'offline', 'error': str(e)}
