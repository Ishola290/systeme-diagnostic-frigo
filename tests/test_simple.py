"""
Tests simples pour vérifier le système
"""

import pytest
import json
from utils.validation import valider_donnees_capteurs
from utils.helpers import generer_diagnostic_id, calculer_score_sante_global
from config import Config


def test_validation_donnees_valides():
    """Test validation avec données valides"""
    donnees = {
        'Température': -18,
        'Pression_BP': 2.5,
        'Pression_HP': 12,
        'Courant': 5.5,
        'Tension': 220,
        'Humidité': 55,
        'Débit_air': 150,
        'Vibration': 2
    }
    
    validated = valider_donnees_capteurs(donnees)
    
    assert validated['Température'] == -18.0
    assert validated['Pression_BP'] == 2.5
    assert len(validated) == 8


def test_validation_donnees_manquantes():
    """Test validation avec données manquantes"""
    donnees = {
        'Température': -18,
        'Pression_BP': 2.5
    }
    
    with pytest.raises(ValueError, match="Champs manquants"):
        valider_donnees_capteurs(donnees)


def test_generer_diagnostic_id():
    """Test génération d'ID unique"""
    id1 = generer_diagnostic_id()
    id2 = generer_diagnostic_id()
    
    assert id1.startswith('DIAG_')
    assert id2.startswith('DIAG_')
    assert id1 != id2


def test_score_sante():
    """Test calcul score de santé"""
    donnees = {
        'Température': -18,
        'Pression_BP': 2.5,
        'Pression_HP': 12,
        'Courant': 5.5,
        'Tension': 220,
        'Humidité': 55,
        'Débit_air': 150,
        'Vibration': 2
    }
    
    score = calculer_score_sante_global(donnees, Config.SEUILS)
    
    assert 0 <= score <= 100
    assert score > 80  # Données normales = score élevé


def test_score_sante_anomalie():
    """Test score avec anomalie"""
    donnees = {
        'Température': 50,  # Anomalie !
        'Pression_BP': 2.5,
        'Pression_HP': 12,
        'Courant': 5.5,
        'Tension': 220,
        'Humidité': 55,
        'Débit_air': 150,
        'Vibration': 2
    }
    
    score = calculer_score_sante_global(donnees, Config.SEUILS)
    
    assert score < 80  # Avec anomalie = score plus bas


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
