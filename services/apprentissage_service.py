"""
Service d'Apprentissage Continu - Gestion du machine learning adaptatif
"""

import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class ApprentissageService:
    """Service de gestion de l'apprentissage continu et archivage"""
    
    def __init__(self, 
                 compteur_file: str = './data/compteur_apprentissage.json',
                 dataset_file: str = './data/dataset_apprentissage.csv',
                 dernier_diagnostic_file: str = './data/dernier_diagnostic.json',
                 seuil_retraining: int = 1000,
                 seuil_nouvelle_panne: int = 50):
        """
        Initialise le service d'apprentissage
        
        Args:
            compteur_file: Chemin du fichier compteur d'apprentissage
            dataset_file: Chemin du dataset d'apprentissage
            dernier_diagnostic_file: Chemin du dernier diagnostic
            seuil_retraining: Nombre de diagnostics avant réentraînement
            seuil_nouvelle_panne: Nombre d'occurrences avant considérer comme "nouvelle panne"
        """
        self.compteur_file = compteur_file
        self.dataset_file = dataset_file
        self.dernier_diagnostic_file = dernier_diagnostic_file
        self.seuil_retraining = seuil_retraining
        self.seuil_nouvelle_panne = seuil_nouvelle_panne
        
        # Créer les répertoires s'ils n'existent pas
        Path(self.compteur_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.compteur = self._charger_compteur()
        
        # Assurer que les clés nécessaires existent
        if 'pannes_par_type' not in self.compteur:
            self.compteur['pannes_par_type'] = {}
        if 'derniers_retraining' not in self.compteur:
            self.compteur['derniers_retraining'] = []
        if 'total' not in self.compteur:
            self.compteur['total'] = 0
            
        logger.info(f"Service apprentissage initialisé - Compteur: {self.compteur['total']}")
    
    def traiter_diagnostic(self, diagnostic_data: Dict) -> Dict:
        """
        Traite un diagnostic pour apprentissage continu (version synchrone)
        
        Args:
            diagnostic_data: Données complètes du diagnostic
            
        Returns:
            Dict avec infos d'apprentissage
        """
        try:
            logger.info("Traitement diagnostic pour apprentissage")
            
            # 1. Extraire les infos de la prédiction
            panne_detectee = diagnostic_data.get('panne_detectee', False)
            type_panne = diagnostic_data.get('prediction_ia', {}).get('panne_detectee')
            score_confiance = diagnostic_data.get('prediction_ia', {}).get('score', 0)
            
            # 2. Incrémenter compteur
            self.compteur['total'] += 1
            self.compteur['last_update'] = datetime.now().isoformat()
            
            apprentissage_result = {
                'compteur_total': self.compteur['total'],
                'panne_detectee': panne_detectee,
                'type_panne': type_panne,
                'retraining_requis': False,
                'nouvelle_panne_detectee': False,
                'nouvelles_pannes_a_entrainer': []
            }
            
            # 3. Si panne détectée, mettre à jour stats
            if panne_detectee and type_panne:
                if type_panne not in self.compteur['pannes_par_type']:
                    self.compteur['pannes_par_type'][type_panne] = 0
                
                self.compteur['pannes_par_type'][type_panne] += 1
                
                # Vérifier si c'est une nouvelle panne
                if self.compteur['pannes_par_type'][type_panne] == self.seuil_nouvelle_panne:
                    logger.info(f"🆕 Nouvelle panne identifiée: {type_panne}")
                    apprentissage_result['nouvelle_panne_detectee'] = True
                    apprentissage_result['nouvelles_pannes_a_entrainer'].append({
                        'type': type_panne,
                        'confiance': score_confiance,
                        'capteurs_affectes': list(diagnostic_data.get('donnees_capteurs', {}).keys())
                    })
            
            # 4. Vérifier si réentraînement requis
            if self.compteur['total'] % self.seuil_retraining == 0:
                logger.info(f"📊 Seuil réentraînement atteint: {self.compteur['total']}/{self.seuil_retraining}")
                apprentissage_result['retraining_requis'] = True
                apprentissage_result['panne_plus_frequente'] = self._get_panne_plus_frequente()
                
                # Réinitialiser compteur après retraining
                self.compteur['derniers_retraining'].append({
                    'timestamp': datetime.now().isoformat(),
                    'diagnostics_traites': self.compteur['total']
                })
            
            # 5. Sauvegarder les mises à jour
            self._sauvegarder_compteur()
            
            # 6. Ajouter au dataset
            self._ajouter_au_dataset(diagnostic_data, apprentissage_result)
            
            logger.info(f"Apprentissage traité - Total: {self.compteur['total']}")
            return apprentissage_result
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement apprentissage: {e}")
            return {
                'compteur_total': self.compteur['total'],
                'panne_detectee': False,
                'retraining_requis': False,
                'nouvelle_panne_detectee': False,
                'error': str(e)
            }
    
    def archiver_diagnostic(self, diagnostic_data: Dict) -> bool:
        """
        Archive un diagnostic complet (version synchrone)
        
        Args:
            diagnostic_data: Données du diagnostic à archiver
            
        Returns:
            True si succès
        """
        try:
            # Sauvegarder le dernier diagnostic
            with open(self.dernier_diagnostic_file, 'w', encoding='utf-8') as f:
                json.dump(diagnostic_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Diagnostic {diagnostic_data.get('diagnostic_id')} archivé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur archivage diagnostic: {e}")
            return False
    
    def get_statistiques(self) -> Dict:
        """
        Retourne les statistiques d'apprentissage (version synchrone)
        
        Returns:
            Dict avec stats
        """
        try:
            panne_plus_frequente = max(self.compteur['pannes_par_type'].items(), 
                                     key=lambda x: x[1])[0] if self.compteur['pannes_par_type'] else 'Aucune'
            
            return {
                'compteur_total': self.compteur['total'],
                'pannes_par_type': self.compteur['pannes_par_type'],
                'panne_plus_frequente': panne_plus_frequente,
                'dernier_retraining': self.compteur['derniers_retraining'][-1] if self.compteur['derniers_retraining'] else None
            }
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {}
    
    def _charger_compteur(self) -> Dict:
        """Charge ou crée le compteur d'apprentissage"""
        try:
            if Path(self.compteur_file).exists():
                with open(self.compteur_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Erreur chargement compteur: {e}")
        
        # Créer un nouveau compteur par défaut
        return {
            'total': 0,
            'pannes_par_type': {},
            'derniers_retraining': [],
            'first_update': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
    
    def _sauvegarder_compteur(self) -> bool:
        """Sauvegarde le compteur d'apprentissage"""
        try:
            with open(self.compteur_file, 'w', encoding='utf-8') as f:
                json.dump(self.compteur, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde compteur: {e}")
            return False
    
    def _ajouter_au_dataset(self, diagnostic_data: Dict, apprentissage_info: Dict) -> bool:
        """
        Ajoute un diagnostic au dataset d'apprentissage (version synchrone)
        
        Args:
            diagnostic_data: Données du diagnostic
            apprentissage_info: Info d'apprentissage
            
        Returns:
            True si succès
        """
        try:
            # Préparer les données pour le dataset
            donnees_capteurs = diagnostic_data.get('donnees_capteurs', {})
            prediction = diagnostic_data.get('prediction_ia', {})
            
            row = {
                'timestamp': diagnostic_data.get('timestamp'),
                'diagnostic_id': diagnostic_data.get('diagnostic_id'),
                'source': diagnostic_data.get('source', 'capteur_principal'),
                'localisation': diagnostic_data.get('localisation', ''),
                'panne_detectee': apprentissage_info.get('panne_detectee', False),
                'type_panne': apprentissage_info.get('type_panne', 'Aucune'),
                'score_confiance': prediction.get('score', 0),
                **donnees_capteurs  # Ajouter tous les capteurs
            }
            
            # Charger ou créer le dataset
            if Path(self.dataset_file).exists():
                try:
                    # Essayer UTF-8 d'abord
                    df = pd.read_csv(self.dataset_file, encoding='utf-8')
                except UnicodeDecodeError:
                    # Si UTF-8 échoue, essayer latin-1
                    logger.warning("UTF-8 échoué, essai avec latin-1")
                    df = pd.read_csv(self.dataset_file, encoding='latin-1')
                
                # Ajouter la nouvelle ligne
                new_row = pd.DataFrame([row])
                df = pd.concat([df, new_row], ignore_index=True, sort=False)
            else:
                df = pd.DataFrame([row])
            
            # Sauvegarder avec encoding UTF-8
            df.to_csv(self.dataset_file, index=False, encoding='utf-8-sig')
            logger.info(f"Diagnostic ajouté au dataset - Total: {len(df)} lignes")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur ajout dataset: {e}")
            return False
    
    def _get_panne_plus_frequente(self) -> str:
        """Retourne le type de panne le plus fréquent"""
        if not self.compteur['pannes_par_type']:
            return "Aucune"
        
        panne_max = max(
            self.compteur['pannes_par_type'].items(),
            key=lambda x: x[1]
        )
        return f"{panne_max[0]} ({panne_max[1]} occurrences)"
    
    def get_statistiques(self) -> Dict:
        """Retourne les statistiques d'apprentissage"""
        total_pannes = sum(self.compteur['pannes_par_type'].values())
        
        return {
            'total_diagnostics': self.compteur['total'],
            'total_pannes_detectees': total_pannes,
            'taux_pannes': (total_pannes / self.compteur['total'] * 100) if self.compteur['total'] > 0 else 0,
            'pannes_par_type': self.compteur['pannes_par_type'],
            'retrainings_effectues': len(self.compteur['derniers_retraining']),
            'compteur_depuis_dernier_retraining': self.compteur['total'] % self.seuil_retraining,
            'last_update': self.compteur['last_update']
        }
    
    async def reset_compteur(self) -> bool:
        """Réinitialise le compteur après réentraînement"""
        try:
            # Garder un historique
            retraining_record = {
                'timestamp': datetime.now().isoformat(),
                'diagnostics_traites': self.compteur['total'],
                'pannes_detectees': sum(self.compteur['pannes_par_type'].values())
            }
            
            self.compteur['derniers_retraining'].append(retraining_record)
            
            # Réinitialiser compteur (garder l'historique)
            self.compteur['total'] = 0
            self.compteur['pannes_par_type'] = {}
            self.compteur['last_update'] = datetime.now().isoformat()
            
            self._sauvegarder_compteur()
            logger.info(f"🔄 Compteur réinitialisé - Retraining #{len(self.compteur['derniers_retraining'])}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur réinitialisation compteur: {e}")
            return False
