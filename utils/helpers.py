"""
Helpers utilitaires - Fonctions communes
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generer_diagnostic_id() -> str:
    """
    Génère un ID unique pour un diagnostic
    
    Returns:
        ID format: DIAG_TIMESTAMP_UUID
    """
    timestamp = int(time.time() * 1000)
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"DIAG_{timestamp}_{unique_id}"


def generer_timestamp() -> str:
    """
    Génère un timestamp ISO 8601
    
    Returns:
        Timestamp au format ISO
    """
    return datetime.utcnow().isoformat() + 'Z'


def formater_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Formate une datetime
    
    Args:
        dt: Datetime à formater
        format_str: Format de sortie
        
    Returns:
        Datetime formatée
    """
    if isinstance(dt, str):
        return dt
    return dt.strftime(format_str) if dt else ""


def calculer_duree(debut: float, fin: float = None) -> float:
    """
    Calcule la durée en secondes
    
    Args:
        debut: Temps de début (time.time())
        fin: Temps de fin (défaut: maintenant)
        
    Returns:
        Durée en secondes
    """
    fin = fin or time.time()
    return round(fin - debut, 3)


def formater_duree(secondes: float) -> str:
    """
    Formate une durée en format lisible
    
    Args:
        secondes: Durée en secondes
        
    Returns:
        Format: "1h 23m 45s"
    """
    if secondes < 60:
        return f"{secondes:.1f}s"
    
    minutes = int(secondes // 60)
    secondes = secondes % 60
    
    if minutes < 60:
        return f"{minutes}m {secondes:.0f}s"
    
    heures = minutes // 60
    minutes = minutes % 60
    return f"{heures}h {minutes}m {secondes:.0f}s"


def classer_urgence(score_confiance: float) -> str:
    """
    Classe l'urgence basée sur le score de confiance
    
    Args:
        score_confiance: Score 0-1
        
    Returns:
        Niveau d'urgence: 'critique', 'haute', 'normale', 'basse'
    """
    if score_confiance >= 0.9:
        return 'critique'
    elif score_confiance >= 0.7:
        return 'haute'
    elif score_confiance >= 0.5:
        return 'normale'
    else:
        return 'basse'


def calculer_moyenne(values: List[float]) -> float:
    """
    Calcule la moyenne de valeurs
    
    Args:
        values: Liste de valeurs
        
    Returns:
        Moyenne arrondie à 2 décimales
    """
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def calculer_ecart_type(values: List[float]) -> float:
    """
    Calcule l'écart-type
    
    Args:
        values: Liste de valeurs
        
    Returns:
        Écart-type
    """
    if len(values) < 2:
        return 0.0
    
    moyenne = calculer_moyenne(values)
    variance = sum((x - moyenne) ** 2 for x in values) / len(values)
    return round(variance ** 0.5, 2)


def detecter_anomalie(valeur: float, moyenne: float, ecart: float, seuil: float = 2.0) -> bool:
    """
    Détecte une anomalie (valeur > seuil écarts-type)
    
    Args:
        valeur: Valeur à tester
        moyenne: Moyenne de référence
        ecart: Écart-type de référence
        seuil: Nombre d'écarts-types (défaut: 2)
        
    Returns:
        True si anomalie détectée
    """
    if ecart == 0:
        return False
    
    nb_ecarts = abs((valeur - moyenne) / ecart)
    return nb_ecarts > seuil


def regrouper_par_cle(items: List[Dict], cle: str) -> Dict[str, List]:
    """
    Regroupe les items par clé
    
    Args:
        items: Liste de dicts
        cle: Clé de regroupement
        
    Returns:
        Dict groupé
    """
    groupes = {}
    for item in items:
        valeur = item.get(cle, 'autre')
        if valeur not in groupes:
            groupes[valeur] = []
        groupes[valeur].append(item)
    return groupes


def fusionner_dicts(*dicts: Dict) -> Dict:
    """
    Fusionne plusieurs dicts
    
    Returns:
        Dict fusionné
    """
    resultat = {}
    for d in dicts:
        if isinstance(d, dict):
            resultat.update(d)
    return resultat


def truncate_string(texte: str, max_len: int = 100, suffix: str = '...') -> str:
    """
    Tronque une chaîne
    
    Args:
        texte: Texte à tronquer
        max_len: Longueur maximale
        suffix: Suffixe d'ajout
        
    Returns:
        Texte tronqué
    """
    if len(texte) <= max_len:
        return texte
    
    return texte[:max_len - len(suffix)] + suffix


def to_bool(valeur: Any) -> bool:
    """
    Convertit une valeur en booléen
    
    Args:
        valeur: Valeur à convertir
        
    Returns:
        Booléen
    """
    if isinstance(valeur, bool):
        return valeur
    
    if isinstance(valeur, str):
        return valeur.lower() in ('true', 'yes', '1', 'on')
    
    return bool(valeur)


def safe_get(obj: Dict, path: str, default: Any = None) -> Any:
    """
    Récupère une valeur en toute sécurité avec chemin point
    
    Exemple: safe_get({'a': {'b': 'c'}}, 'a.b') -> 'c'
    
    Args:
        obj: Dict à parcourir
        path: Chemin "a.b.c"
        default: Valeur par défaut
        
    Returns:
        Valeur trouvée ou défaut
    """
    try:
        keys = path.split('.')
        valeur = obj
        for key in keys:
            valeur = valeur.get(key) if isinstance(valeur, dict) else None
            if valeur is None:
                return default
        return valeur
    except Exception:
        return default