"""
Service IA Local - Système d'IA indépendant
Remplace Gemini et Telegram avec des modèles open-source locaux
"""

__version__ = '1.0.0'
__author__ = 'Diagnostic Frigo Team'

from .ia_service import IAService, get_ia_service

__all__ = [
    'IAService',
    'get_ia_service'
]
