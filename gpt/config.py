"""
Configuration du service IA Local
"""

import os
from pathlib import Path

class Config:
    """Configuration de base"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JSON_SORT_KEYS = False
    
    # Service IA
    MODEL_NAME = os.environ.get('IA_MODEL', 'phi')
    MODEL_TYPE = os.environ.get('IA_MODEL_TYPE', 'transformers')  # transformers, llama, ollama
    
    # LLM Parameters
    MAX_TOKENS = int(os.environ.get('IA_MAX_TOKENS', 512))
    TEMPERATURE = float(os.environ.get('IA_TEMPERATURE', 0.7))
    TOP_P = float(os.environ.get('IA_TOP_P', 0.95))
    
    # Contexte
    CONTEXT_SIZE = int(os.environ.get('IA_CONTEXT_SIZE', 5))
    
    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    CACHE_DIR = BASE_DIR / 'cache'
    MODELS_DIR = BASE_DIR / 'models'
    
    # URLs
    CHAT_API_URL = os.environ.get('CHAT_API_URL', 'http://localhost:5001')
    MAIN_API_URL = os.environ.get('MAIN_API_URL', 'http://localhost:5000')
    IA_API_URL = os.environ.get('IA_API_URL', 'http://localhost:5002')
    
    # Performance
    USE_GPU = os.environ.get('IA_USE_GPU', 'true').lower() == 'true'
    QUANTIZE = os.environ.get('IA_QUANTIZE', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'ia_service.log'
    
    def __init__(self):
        """Initialiser les répertoires"""
        for path in [self.DATA_DIR, self.CACHE_DIR, self.MODELS_DIR, self.LOG_FILE.parent]:
            path.mkdir(exist_ok=True, parents=True)

class DevelopmentConfig(Config):
    """Configuration développement"""
    DEBUG = True
    USE_GPU = False
    QUANTIZE = False

class ProductionConfig(Config):
    """Configuration production"""
    DEBUG = False
    USE_GPU = True
    QUANTIZE = True

class TestingConfig(Config):
    """Configuration test"""
    TESTING = True
    USE_GPU = False

# Modèles disponibles
MODELS_INFO = {
    'phi': {
        'name': 'Microsoft/phi-2',
        'size': '2.7B',
        'speed': 'TRÈS RAPIDE',
        'quality': 'BON',
        'vram': '4GB',
        'recommended': True,
        'description': 'Petit modèle optimisé pour le chat'
    },
    'mistral': {
        'name': 'mistralai/Mistral-7B-Instruct-v0.1',
        'size': '7B',
        'speed': 'RAPIDE',
        'quality': 'TRÈS BON',
        'vram': '8GB',
        'recommended': True,
        'description': 'Modèle généraliste performant'
    },
    'neural': {
        'name': 'Intel/neural-chat-7b-v3-1',
        'size': '7B',
        'speed': 'RAPIDE',
        'quality': 'TRÈS BON',
        'vram': '8GB',
        'recommended': True,
        'description': 'Optimisé pour les instructions'
    },
    'llama2': {
        'name': 'meta-llama/Llama-2-7b-chat-hf',
        'size': '7B',
        'speed': 'MOYEN',
        'quality': 'EXCELLENT',
        'vram': '16GB',
        'recommended': False,
        'description': 'Nécessite accès HuggingFace'
    },
    'gpt2': {
        'name': 'openai/gpt2',
        'size': '124M',
        'speed': 'TRÈS RAPIDE',
        'quality': 'MOYEN',
        'vram': '1GB',
        'recommended': False,
        'description': 'Très léger, pour test'
    }
}

# Points de terminaison de l'API
API_ENDPOINTS = {
    'health': '/health',
    'chat_message': '/api/chat/message',
    'process_alert': '/api/alerts/process',
    'add_knowledge': '/api/knowledge/add',
    'get_stats': '/api/stats',
    'get_models': '/api/models',
    'analyze_diagnostic': '/api/diagnostic/analyze',
    'learn': '/api/learn'
}

if __name__ == '__main__':
    print("📋 Configuration du Service IA Local")
    print("\nModèles disponibles:")
    for name, info in MODELS_INFO.items():
        rec = "⭐ RECOMMANDÉ" if info['recommended'] else ""
        print(f"  {name:12} - {info['name']:40} ({info['size']:5}) {rec}")
        print(f"             Speed: {info['speed']:12} Quality: {info['quality']:12} RAM: {info['vram']}")
        print()
