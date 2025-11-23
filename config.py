"""
Configuration centralisée du système
Utilise les variables d'environnement
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration générale"""
    
    # Environnement
    ENV = os.getenv('ENV', 'development')
    DEBUG = ENV == 'development'
    PORT = int(os.getenv('PORT', 5000))
    
    # Agent IA
    AGENT_IA_URL = os.getenv('AGENT_IA_URL', 'https://agent-ia-frigo-tdmm.onrender.com')
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.3'))
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8278706239:AAFnCW_N3_ZyffpSDcBIQQAB8i0A9Dsm6jA')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '6607560503')
    
    # Apprentissage
    SEUIL_RETRAINING = int(os.getenv('SEUIL_RETRAINING', '1000'))
    SEUIL_NOUVELLE_PANNE = int(os.getenv('SEUIL_NOUVELLE_PANNE', '50'))
    
    # Chemins de fichiers
    DATA_DIR = os.getenv('DATA_DIR', './data')
    COMPTEUR_FILE = os.path.join(DATA_DIR, 'compteur_apprentissage.json')
    DATASET_FILE = os.path.join(DATA_DIR, 'dataset_apprentissage.csv')
    DERNIER_DIAGNOSTIC_FILE = os.path.join(DATA_DIR, 'dernier_diagnostic.json')
    
    # Simulateur
    SIMULATEUR_ENABLED = os.getenv('SIMULATEUR_ENABLED', 'true').lower() == 'true'
    SIMULATEUR_INTERVAL = int(os.getenv('SIMULATEUR_INTERVAL', '30'))  # secondes
    SIMULATEUR_PROB_PANNE = float(os.getenv('SIMULATEUR_PROB_PANNE', '0.3'))  # 30% de chance de panne
    
    # Seuils normaux pour détection d'anomalies
    SEUILS = {
        'Température': {'min': -30, 'max': 10, 'optimal': -18},
        'Pression_BP': {'min': 1.0, 'max': 5.0, 'optimal': 2.5},
        'Pression_HP': {'min': 8, 'max': 20, 'optimal': 12},
        'Courant': {'min': 0.5, 'max': 15, 'optimal': 6},
        'Tension': {'min': 200, 'max': 240, 'optimal': 220},
        'Humidité': {'min': 40, 'max': 70, 'optimal': 55},
        'Débit_air': {'min': 50, 'max': 250, 'optimal': 150},
        'Vibration': {'min': 0, 'max': 5, 'optimal': 2}
    }
    
    @staticmethod
    def init_app():
        """Initialise les dossiers nécessaires"""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
