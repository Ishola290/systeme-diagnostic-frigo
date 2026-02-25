"""
Validation des données - Vérification et sanitization des inputs
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Seuils acceptable pour les capteurs
SEUILS_VALIDES = {
    'Température': {'min': -50, 'max': 50, 'type': 'float'},
    'Pression_BP': {'min': 0, 'max': 20, 'type': 'float'},
    'Pression_HP': {'min': 0, 'max': 30, 'type': 'float'},
    'Courant': {'min': 0, 'max': 50, 'type': 'float'},
    'Tension': {'min': 0, 'max': 600, 'type': 'float'},
    'Vibration': {'min': 0, 'max': 100, 'type': 'float'},
    'Humidité': {'min': 0, 'max': 100, 'type': 'float'},
    'Débit_air': {'min': 0, 'max': 500, 'type': 'float'}
}


def valider_donnees_capteurs(donnees: Dict[str, Any]) -> Dict[str, float]:
    """
    Valide et nettoie les données des capteurs
    
    Args:
        donnees: Dict contenant les données des capteurs
        
    Returns:
        Dict validé et nettoyé
        
    Raises:
        ValueError: Si validation échoue
    """
    try:
        donnees_validees = {}
        erreurs = []
        
        for capteur, seuils in SEUILS_VALIDES.items():
            try:
                valeur = donnees.get(capteur)
                
                # Vérifier que la valeur existe
                if valeur is None:
                    erreurs.append(f"{capteur}: manquant")
                    continue
                
                # Convertir en float
                try:
                    valeur_float = float(valeur)
                except (ValueError, TypeError):
                    erreurs.append(f"{capteur}: valeur non numérique ({valeur})")
                    continue
                
                # Vérifier les limites
                if valeur_float < seuils['min'] or valeur_float > seuils['max']:
                    logger.warning(f"⚠️  {capteur} hors limites: {valeur_float} (attendu: {seuils['min']}-{seuils['max']})")
                    # On peut accepter avec warning ou rejeter strictement
                    # Pour maintenant, on accepte mais loggé
                
                donnees_validees[capteur] = round(valeur_float, 2)
                
            except Exception as e:
                erreurs.append(f"{capteur}: {str(e)}")
        
        # Vérifier qu'on a au moins 70% des capteurs
        if len(donnees_validees) < len(SEUILS_VALIDES) * 0.7:
            raise ValueError(f"Données insuffisantes: {len(donnees_validees)}/{len(SEUILS_VALIDES)}")
        
        if erreurs:
            logger.warning(f"⚠️  Erreurs de validation: {', '.join(erreurs)}")
        
        return donnees_validees
        
    except Exception as e:
        logger.error(f"❌ Erreur validation capteurs: {e}")
        raise ValueError(f"Validation échouée: {e}")


def valider_donnees_diagnostic(donnees: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valide les données complètes d'un diagnostic
    
    Args:
        donnees: Données du diagnostic
        
    Returns:
        Tuple (valide: bool, message: str)
    """
    try:
        # Vérifier champs obligatoires
        champs_requis = ['source', 'localisation']
        
        for champ in champs_requis:
            if champ not in donnees or not donnees[champ]:
                return False, f"Champ manquant: {champ}"
        
        # Vérifier données capteurs
        try:
            donnees_capteurs = donnees.get('donnees_capteurs', donnees)
            valider_donnees_capteurs(donnees_capteurs)
        except ValueError as e:
            return False, f"Erreur capteurs: {str(e)}"
        
        return True, "Validation réussie"
        
    except Exception as e:
        logger.error(f"❌ Erreur validation diagnostic: {e}")
        return False, str(e)


def sanitizer_string(texte: str, max_length: int = 500) -> str:
    """
    Nettoie et sanitize une chaîne de caractères
    
    Args:
        texte: Texte à nettoyer
        max_length: Longueur maximale
        
    Returns:
        Texte nettoyé
    """
    if not isinstance(texte, str):
        return ""
    
    # Supprimer les caractères de contrôle
    texte = ''.join(char for char in texte if ord(char) >= 32 or char in '\n\t')
    
    # Limiter la longueur
    if len(texte) > max_length:
        texte = texte[:max_length]
    
    return texte.strip()


def valider_adresse_url(url: str) -> bool:
    """
    Valide une adresse URL
    
    Args:
        url: URL à valider
        
    Returns:
        True si valide
    """
    try:
        if not isinstance(url, str):
            return False
        
        # Vérifications basiques
        if not url.startswith(('http://', 'https://')):
            return False
        
        if len(url) < 10 or len(url) > 2083:  # Longueur URL standard
            return False
        
        return True
        
    except Exception:
        return False


def valider_score_confiance(score: float) -> bool:
    """
    Valide un score de confiance (0-1)
    
    Args:
        score: Score à valider
        
    Returns:
        True si valide
    """
    try:
        score_float = float(score)
        return 0 <= score_float <= 1
    except (ValueError, TypeError):
        return False