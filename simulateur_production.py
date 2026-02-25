#!/usr/bin/env python3
"""
Simulateur de capteurs frigorifiques - Production Ready
Synchronise automatiquement les URLs des services déployés
Envoie les données en temps réel à l'API principale

Architecture:
- Service 1 (app.py) : http://app:5000 (ou https://app-service.onrender.com)
- Service 2 (chat/app_web.py) : http://chat:5001 (ou https://chat-service.onrender.com)
- Service 3 (gpt/app_ia.py) : http://gpt:5002 (ou https://gpt-service.onrender.com)
- Simulateur : Lance les diagnostics vers app:5000

Les URLs sont auto-détectées via variables d'environnement ou service discovery.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

import requests
import io

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulateur.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION DES PANNES
# ============================================================

PANNES = {
    "surchauffe_compresseur": ["Température", "Courant", "Vibration"],
    "fuite_fluide": ["Pression_BP", "Température", "Courant"],
    "givrage_evaporateur": ["Température", "Humidité", "Débit_air"],
    "panne_electrique": ["Tension", "Courant"],
    "obstruction_conduit": ["Débit_air", "Pression_BP"],
    "défaillance_ventilateur": ["Débit_air", "Humidité"],
    "capteur_defectueux": ["Température", "Courant"],
    "pression_anormale_HP": ["Pression_HP", "Courant"],
    "pression_anormale_BP": ["Pression_BP", "Température"],
    "défaut_dégivrage": ["Température", "Débit_air"],
    "défaillance_thermostat": ["Température", "Courant"],
    "défaillance_compresseur": ["Courant", "Vibration"]
}

VALEURS_NORMALES = {
    "Température": 5.0,
    "Pression_BP": 2.5,
    "Pression_HP": 12.0,
    "Courant": 15.0,
    "Tension": 380.0,
    "Vibration": 0.5,
    "Humidité": 65.0,
    "Débit_air": 100.0
}

ECARTS_NORMAUX = {
    "Température": 2.0,
    "Pression_BP": 0.3,
    "Pression_HP": 1.0,
    "Courant": 2.0,
    "Tension": 10.0,
    "Vibration": 0.1,
    "Humidité": 5.0,
    "Débit_air": 10.0
}

class ServiceDiscovery:
    """Découverte automatique des services (Docker/Render)"""
    
    @staticmethod
    def get_service_urls() -> Dict[str, str]:
        """Détecte automatiquement les URLs des services"""
        
        logger.info("🔍 Détection des services...")
        
        # 1. Vérifier les env vars (Render/Docker)
        urls = {
            'app': os.environ.get('MAIN_APP_URL', 'http://localhost:5000'),
            'chat': os.environ.get('CHAT_API_URL', 'http://localhost:5001'),
            'ia': os.environ.get('IA_SERVICE_URL', 'http://localhost:5002'),
        }
        
        # 2. Vérifier si en Docker (avec noms de service)
        import socket
        for name in ['app', 'chat', 'gpt']:
            try:
                # Tenter résolution du nom Docker
                ip = socket.gethostbyname(name)
                if name == 'app':
                    urls['app'] = f'http://{name}:5000'
                elif name == 'chat':
                    urls['chat'] = f'http://{name}:5001'
                elif name == 'gpt':
                    urls['ia'] = f'http://{name}:5002'
                logger.info(f"✅ Service Docker trouvé: {name}")
            except socket.gaierror:
                pass
        
        logger.info(f"📋 URLs détectées:")
        logger.info(f"   App: {urls['app']}")
        logger.info(f"   Chat: {urls['chat']}")
        logger.info(f"   IA: {urls['ia']}")
        
        return urls
    
    @staticmethod
    def health_check(urls: Dict[str, str]) -> bool:
        """Vérifier que tous les services sont accessibles"""
        logger.info("\n🏥 Vérification santé des services...")
        
        all_ok = True
        for name, url in urls.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {name}: OK")
                else:
                    logger.warning(f"⚠️  {name}: Statut {response.status_code}")
                    all_ok = False
            except Exception as e:
                logger.warning(f"⚠️  {name}: Inaccessible ({e})")
                all_ok = False
        
        return all_ok

class SimulateurCapteurs:
    """Simulateur de capteurs avec découverte de services"""
    
    def __init__(self, 
                 app_url: Optional[str] = None,
                 prob_panne: float = 0.3,
                 interval: int = 30,
                 auto_detect: bool = True):
        """
        Args:
            app_url: URL de l'app principale (auto-détecté si None)
            prob_panne: Probabilité panne (0.0-1.0)
            interval: Intervalle envoi en secondes
            auto_detect: Activer découverte automatique
        """
        
        logger.info(f"{'='*70}")
        logger.info(f"🚀 Simulateur Frigorifique - Production Ready")
        logger.info(f"{'='*70}\n")
        
        # Service discovery
        if auto_detect:
            self.urls = ServiceDiscovery.get_service_urls()
            if not ServiceDiscovery.health_check(self.urls):
                logger.warning("⚠️  Certains services ne sont pas accessibles")
        else:
            self.urls = {
                'app': app_url or 'http://localhost:5000',
                'chat': 'http://localhost:5001',
                'ia': 'http://localhost:5002',
            }
        
        self.app_url = self.urls['app']
        self.prob_panne = prob_panne
        self.interval = interval
        self.num_diagnostic = 0
        self.panne_active = None
        self.duree_panne = 0
        self.running = False
        
        logger.info(f"📊 Configuration:")
        logger.info(f"   App URL: {self.app_url}")
        logger.info(f"   Probabilité panne: {prob_panne*100}%")
        logger.info(f"   Intervalle: {interval}s\n")
    
    def generer_capteurs_normaux(self) -> Dict[str, float]:
        """Génère valeurs capteurs normales"""
        capteurs = {}
        for variable, valeur_normale in VALEURS_NORMALES.items():
            ecart = ECARTS_NORMAUX.get(variable, 0.5)
            variation = random.gauss(0, ecart)
            capteurs[variable] = round(valeur_normale + variation, 2)
        return capteurs
    
    def appliquer_panne(self, capteurs: Dict[str, float], panne: str) -> Dict[str, float]:
        """Applique une panne spécifique"""
        if panne not in PANNES:
            logger.warning(f"⚠️  Panne inconnue: {panne}")
            return capteurs
        
        # Signatures spécifiques par panne
        if panne == "surchauffe_compresseur":
            capteurs["Température"] = round(random.uniform(20, 40), 2)
            capteurs["Courant"] = round(random.uniform(25, 35), 2)
            capteurs["Vibration"] = round(random.uniform(3, 8), 2)
        
        elif panne == "fuite_fluide":
            capteurs["Pression_BP"] = round(random.uniform(0.3, 1.0), 2)
            capteurs["Température"] = round(random.uniform(15, 25), 2)
            capteurs["Courant"] = round(random.uniform(8, 12), 2)
        
        elif panne == "givrage_evaporateur":
            capteurs["Température"] = round(random.uniform(-10, 0), 2)
            capteurs["Humidité"] = round(random.uniform(85, 95), 2)
            capteurs["Débit_air"] = round(random.uniform(30, 60), 2)
        
        elif panne == "panne_electrique":
            capteurs["Tension"] = round(random.uniform(100, 200), 2)
            capteurs["Courant"] = 0
        
        elif panne == "obstruction_conduit":
            capteurs["Débit_air"] = round(random.uniform(10, 30), 2)
            capteurs["Pression_BP"] = round(random.uniform(1.0, 2.0), 2)
        
        elif panne == "défaillance_ventilateur":
            capteurs["Débit_air"] = round(random.uniform(5, 20), 2)
            capteurs["Humidité"] = round(random.uniform(80, 95), 2)
        
        elif panne == "capteur_defectueux":
            capteurs["Température"] = -999.0  # Valeur invalide
            capteurs["Courant"] = round(random.uniform(10, 20), 2)
        
        elif panne == "pression_anormale_HP":
            capteurs["Pression_HP"] = round(random.uniform(25, 35), 2)
            capteurs["Courant"] = round(random.uniform(20, 28), 2)
        
        elif panne == "pression_anormale_BP":
            capteurs["Pression_BP"] = round(random.uniform(4.0, 6.0), 2)
            capteurs["Température"] = round(random.uniform(10, 18), 2)
        
        elif panne == "défaut_dégivrage":
            capteurs["Température"] = round(random.uniform(-15, -5), 2)
            capteurs["Débit_air"] = round(random.uniform(20, 50), 2)
        
        elif panne == "défaillance_thermostat":
            capteurs["Température"] = round(random.uniform(25, 35), 2)
            capteurs["Courant"] = round(random.uniform(18, 25), 2)
        
        elif panne == "défaillance_compresseur":
            capteurs["Courant"] = 0
            capteurs["Vibration"] = round(random.uniform(2, 6), 2)
        
        return capteurs
    
    def envoyer_diagnostic(self, donnees: Dict) -> bool:
        """Envoie le diagnostic à l'API"""
        try:
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                f"{self.app_url}/webhook/diagnostic-frigo",
                json=donnees,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Diagnostic #{self.num_diagnostic} envoyé")
                return True
            else:
                logger.warning(f"⚠️  Erreur {response.status_code}: {response.text[:100]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️  Timeout - App non réactive")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"🔌 Connexion perdue - Vérifier app_url: {self.app_url}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur envoi: {e}")
            return False
    
    def executer_simulation(self, num_cycles: Optional[int] = None):
        """Exécute la simulation"""
        self.running = True
        logger.info(f"▶️  Démarrage simulation...")
        
        if num_cycles:
            logger.info(f"📍 {num_cycles} cycles à exécuter")
        else:
            logger.info(f"📍 Simulation continue (Ctrl+C pour arrêter)")
        
        cycle = 0
        try:
            while True:
                cycle += 1
                
                if num_cycles and cycle > num_cycles:
                    break
                
                # Générer capteurs normaux ou panne
                capteurs = self.generer_capteurs_normaux()
                
                # Décider si panne
                if random.random() < self.prob_panne and not self.panne_active:
                    self.panne_active = random.choice(list(PANNES.keys()))
                    self.duree_panne = random.randint(3, 8)  # Durée en cycles
                    logger.info(f"\n🚨 PANNE DÉTECTÉE: {self.panne_active}")
                
                # Appliquer panne si active
                if self.panne_active:
                    capteurs = self.appliquer_panne(capteurs, self.panne_active)
                    self.duree_panne -= 1
                    if self.duree_panne <= 0:
                        logger.info(f"✅ Panne résolue\n")
                        self.panne_active = None
                
                # Créer diagnostic - envoyer les capteurs directement
                self.num_diagnostic += 1
                diagnostic = {
                    'diagnostic_id': f"SIM_{self.num_diagnostic:06d}",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'simulation',
                    'source': 'simulateur'
                }
                
                # Ajouter les capteurs directement (pas encapsulés)
                diagnostic.update(capteurs)
                
                # Envoyer
                self.envoyer_diagnostic(diagnostic)
                
                # Attendre avant prochain cycle
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Arrêt de la simulation (Ctrl+C)")
        finally:
            self.running = False
            logger.info(f"\n📊 Statistiques:")
            logger.info(f"   Diagnostics envoyés: {self.num_diagnostic}")
            logger.info(f"   Durée: {(cycle * self.interval) / 60:.1f} min")

def main():
    parser = argparse.ArgumentParser(
        description='Simulateur de capteurs frigorifiques - Production Ready'
    )
    parser.add_argument(
        '--app-url',
        help='URL de l\'API principale (auto-détecté par défaut)',
        default=None
    )
    parser.add_argument(
        '--prob-panne',
        type=float,
        default=0.1,
        help='Probabilité panne: 0.0-1.0 (default: 0.1 = 10%)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Intervalle entre envois en secondes (default: 30)'
    )
    parser.add_argument(
        '--cycles',
        type=int,
        default=None,
        help='Nombre de cycles à exécuter (par défaut: infini)'
    )
    parser.add_argument(
        '--no-auto-detect',
        action='store_true',
        help='Désactiver découverte automatique'
    )
    
    args = parser.parse_args()
    
    # Initialiser simulateur
    simulateur = SimulateurCapteurs(
        app_url=args.app_url,
        prob_panne=args.prob_panne,
        interval=args.interval,
        auto_detect=not args.no_auto_detect
    )
    
    # Exécuter
    simulateur.executer_simulation(num_cycles=args.cycles)

if __name__ == '__main__':
    main()
