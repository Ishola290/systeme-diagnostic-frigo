"""
Simulateur de capteurs pour le système de diagnostic frigorifique
Génère des données réalistes avec 12 types de pannes différentes
Envoie les données en temps réel à l'API Flask
"""

import requests
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import asyncio
import sys
import os
import io

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration du logging
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

# Valeurs normales de référence
VALEURS_NORMALES = {
    "Température": 5.0,           # °C (zone normalement froide)
    "Pression_BP": 2.5,           # bar (basse pression)
    "Pression_HP": 12.0,          # bar (haute pression)
    "Courant": 15.0,              # A (ampères)
    "Tension": 380.0,             # V (volts)
    "Vibration": 0.5,             # mm/s
    "Humidité": 65.0,             # % (pourcentage)
    "Débit_air": 100.0            # m³/h (mètres cubes par heure)
}

# Écarts-types normaux (variation naturelle)
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


class SimulateurCapteurs:
    """Simulateur de capteurs pour le système frigorifique"""
    
    def __init__(self, 
                 api_url: str = "http://localhost:5000/webhook/diagnostic-frigo",
                 prob_panne: float = 0.3,
                 interval: int = 30):
        """
        Initialise le simulateur
        
        Args:
            api_url: URL de l'API Flask pour envoyer les données
            prob_panne: Probabilité d'occurrence d'une panne (0.0-1.0)
            interval: Intervalle entre les envois en secondes
        """
        self.api_url = api_url
        self.prob_panne = prob_panne
        self.interval = interval
        self.num_diagnostic = 0
        self.panne_active = None
        self.duree_panne = 0
        
        logger.info(f"✅ Simulateur initialisé")
        logger.info(f"   URL: {api_url}")
        logger.info(f"   Probabilité panne: {prob_panne*100}%")
        logger.info(f"   Intervalle: {interval}s")
    
    
    def generer_capteurs_normaux(self) -> Dict[str, float]:
        """
        Génère des valeurs capteurs normales avec variation naturelle
        
        Returns:
            Dict avec toutes les variables capteurs
        """
        capteurs = {}
        
        for variable, valeur_normale in VALEURS_NORMALES.items():
            ecart = ECARTS_NORMAUX.get(variable, 0.5)
            # Ajouter variation Gaussienne
            variation = random.gauss(0, ecart)
            capteurs[variable] = round(valeur_normale + variation, 2)
        
        return capteurs
    
    
    def appliquer_panne(self, 
                       capteurs: Dict[str, float], 
                       panne: str) -> Dict[str, float]:
        """
        Applique une panne spécifique aux capteurs
        
        Args:
            capteurs: Dict des valeurs capteurs
            panne: Nom de la panne
            
        Returns:
            Dict des capteurs avec anomalies
        """
        if panne not in PANNES:
            logger.warning(f"⚠️  Panne inconnue: {panne}")
            return capteurs
        
        variables_affectees = PANNES[panne]
        
        # Appliquer signature spécifique selon le type de panne
        if panne == "surchauffe_compresseur":
            capteurs["Température"] = round(random.uniform(20, 40), 2)  # Chaud!
            capteurs["Courant"] = round(random.uniform(25, 35), 2)      # Surcharge
            capteurs["Vibration"] = round(random.uniform(3, 8), 2)      # Vibrations fortes
        
        elif panne == "fuite_fluide":
            capteurs["Pression_BP"] = round(random.uniform(0.3, 1.0), 2)  # Basse pression très basse
            capteurs["Température"] = round(random.uniform(15, 25), 2)    # Température augmente
            capteurs["Courant"] = round(random.uniform(8, 12), 2)         # Courant réduit
        
        elif panne == "givrage_evaporateur":
            capteurs["Température"] = round(random.uniform(-35, -20), 2)  # Très froid
            capteurs["Humidité"] = round(random.uniform(85, 99), 2)       # Très humide
            capteurs["Débit_air"] = round(random.uniform(20, 50), 2)      # Débit réduit (obstruction)
        
        elif panne == "panne_electrique":
            capteurs["Tension"] = round(random.uniform(200, 300), 2)   # Tension instable
            capteurs["Courant"] = 0.0                                   # Plus de courant
        
        elif panne == "obstruction_conduit":
            capteurs["Débit_air"] = round(random.uniform(10, 30), 2)   # Débit très réduit
            capteurs["Pression_BP"] = round(random.uniform(1.0, 3.0), 2)  # Pression change
        
        elif panne == "défaillance_ventilateur":
            capteurs["Débit_air"] = round(random.uniform(5, 20), 2)    # Presque pas de débit
            capteurs["Humidité"] = round(random.uniform(80, 95), 2)    # Accumulation humidité
        
        elif panne == "capteur_defectueux":
            # Valeurs aléatoires erratiques
            capteurs["Température"] = round(random.uniform(-50, 60), 2)  # Complètement erratique
            capteurs["Courant"] = round(random.uniform(0, 50), 2)        # Valeurs folles
        
        elif panne == "pression_anormale_HP":
            capteurs["Pression_HP"] = round(random.uniform(25, 40), 2)   # Trop haute
            capteurs["Courant"] = round(random.uniform(20, 30), 2)       # Compresseur surchargé
        
        elif panne == "pression_anormale_BP":
            capteurs["Pression_BP"] = round(random.uniform(5, 8), 2)     # Trop haute
            capteurs["Température"] = round(random.uniform(10, 20), 2)   # Température augmente
        
        elif panne == "défaut_dégivrage":
            capteurs["Température"] = round(random.uniform(-40, -30), 2)  # Très froid
            capteurs["Débit_air"] = round(random.uniform(10, 40), 2)     # Débit réduit par glace
        
        elif panne == "défaillance_thermostat":
            capteurs["Température"] = round(random.uniform(15, 30), 2)   # Ne refroidit pas
            capteurs["Courant"] = round(random.uniform(5, 10), 2)        # Compresseur peu utilisé
        
        elif panne == "défaillance_compresseur":
            capteurs["Courant"] = round(random.uniform(1, 5), 2)         # Très peu de courant
            capteurs["Vibration"] = round(random.uniform(5, 10), 2)      # Vibrations anormales
        
        return capteurs
    
    
    def generer_donnees_diagnostic(self) -> Dict:
        """
        Génère un diagnostic complet
        
        Returns:
            Dict avec toutes les données du diagnostic
        """
        self.num_diagnostic += 1
        
        # Générer capteurs de base
        capteurs = self.generer_capteurs_normaux()
        
        # Vérifier si une panne se déclenche
        if random.random() < self.prob_panne:
            if self.panne_active is None:
                # Démarrer une nouvelle panne
                self.panne_active = random.choice(list(PANNES.keys()))
                self.duree_panne = random.randint(3, 10)  # 3-10 diagnostics
                logger.warning(f"⚠️  PANNE DÉCLENCHÉE: {self.panne_active}")
            
            # Appliquer la panne active
            capteurs = self.appliquer_panne(capteurs, self.panne_active)
            self.duree_panne -= 1
            
            # Fin de la panne si durée écoulée
            if self.duree_panne <= 0:
                logger.info(f"✅ FIN DE PANNE: {self.panne_active}")
                self.panne_active = None
        
        # Construire diagnostic
        diagnostic = {
            "num_diagnostic": self.num_diagnostic,
            "timestamp": datetime.now().isoformat(),
            "panne_active": self.panne_active,
            **capteurs  # Ajouter tous les capteurs
        }
        
        return diagnostic
    
    
    def envoyer_diagnostic(self, diagnostic: Dict) -> bool:
        """
        Envoie le diagnostic à l'API Flask
        
        Args:
            diagnostic: Dict du diagnostic
            
        Returns:
            True si succès, False sinon
        """
        try:
            response = requests.post(
                self.api_url,
                json=diagnostic,
                timeout=5
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Diagnostic #{diagnostic['num_diagnostic']} envoyé")
                return True
            else:
                logger.error(f"❌ Erreur API: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
        
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Impossible de se connecter à {self.api_url}")
            logger.error("   Assurez-vous que le serveur Flask est démarré: python app.py")
            return False
        
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout en tentant de contacter {self.api_url}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi: {str(e)}")
            return False
    
    
    def afficher_diagnostic(self, diagnostic: Dict):
        """
        Affiche le diagnostic de manière lisible
        
        Args:
            diagnostic: Dict du diagnostic
        """
        print("\n" + "="*70)
        print(f"📊 DIAGNOSTIC #{diagnostic['num_diagnostic']}")
        print("="*70)
        
        # Afficher timestamp
        print(f"⏱️  {diagnostic['timestamp']}")
        
        # Afficher panne active si présente
        if diagnostic['panne_active']:
            print(f"⚠️  PANNE ACTIVE: {diagnostic['panne_active'].upper()}")
            variables = PANNES[diagnostic['panne_active']]
            print(f"   Variables affectées: {', '.join(variables)}")
        else:
            print("✅ Système normal")
        
        print("\n📈 VALEURS CAPTEURS:")
        print("-"*70)
        
        # Afficher toutes les variables
        for var in sorted(VALEURS_NORMALES.keys()):
            if var in diagnostic:
                valeur = diagnostic[var]
                normal = VALEURS_NORMALES[var]
                diff = abs(valeur - normal)
                pct = (diff / abs(normal)) * 100 if normal != 0 else 0
                
                # Marquer si anormal
                marker = "⚠️ " if pct > 20 else "✅"
                print(f"  {marker} {var:20s}: {valeur:8.2f} (normal: {normal:6.2f})")
        
        print("="*70 + "\n")
    
    
    def boucle_simulation(self, duree: int = None):
        """
        Lance la boucle de simulation
        
        Args:
            duree: Durée en secondes (None = infini)
        """
        print("\n" + "🚀 "*20)
        print("DÉMARRAGE DU SIMULATEUR")
        print("🚀 "*20)
        logger.info("Appuyez sur Ctrl+C pour arrêter...")
        
        debut = time.time()
        diagnostics_envoyes = 0
        diagnostics_echoues = 0
        
        try:
            while True:
                # Vérifier si durée écoulée
                if duree and (time.time() - debut) > duree:
                    break
                
                # Générer diagnostic
                diagnostic = self.generer_donnees_diagnostic()
                
                # Afficher
                self.afficher_diagnostic(diagnostic)
                
                # Envoyer à l'API
                if self.envoyer_diagnostic(diagnostic):
                    diagnostics_envoyes += 1
                else:
                    diagnostics_echoues += 1
                
                # Attendre avant prochain diagnostic
                logger.info(f"⏳ Attente de {self.interval}s avant prochain diagnostic...")
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  ARRÊT DU SIMULATEUR")
        
        finally:
            # Afficher statistiques
            total = diagnostics_envoyes + diagnostics_echoues
            print("\n" + "="*70)
            print("📊 STATISTIQUES")
            print("="*70)
            print(f"Diagnostics générés: {self.num_diagnostic}")
            print(f"Envoyés avec succès: {diagnostics_envoyes}")
            print(f"Erreurs d'envoi: {diagnostics_echoues}")
            print("="*70 + "\n")


# ============================================================
# MAIN
# ============================================================

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Simulateur de capteurs pour système frigorifique"
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:5000/webhook/diagnostic-frigo',
        help='URL de l\'API Flask'
    )
    parser.add_argument(
        '--prob-panne',
        type=float,
        default=0.3,
        help='Probabilité de panne (0.0-1.0)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Intervalle entre diagnostics (secondes)'
    )
    parser.add_argument(
        '--duree',
        type=int,
        default=None,
        help='Durée totale de simulation (secondes)'
    )
    
    args = parser.parse_args()
    
    # Créer et lancer le simulateur
    simulateur = SimulateurCapteurs(
        api_url=args.api_url,
        prob_panne=args.prob_panne,
        interval=args.interval
    )
    
    simulateur.boucle_simulation(duree=args.duree)


if __name__ == '__main__':
    main()
