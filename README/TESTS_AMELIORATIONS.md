# 🧪 AMÉLIORATIONS TESTS SUGGÉRÉES

Le fichier `tests/test_simple.py` est bon mais on peut l'améliorer. Voici comment :

---

## ⚠️ PROBLÈME ACTUEL

Le fichier test_simple.py teste les fonctions, MAIS il y a une fonction manquante :

```python
from utils.helpers import calculer_score_sante_global
```

Cette fonction n'existe pas dans `utils/helpers.py` !

**Solution :** Ajouter cette fonction à `utils/helpers.py`

---

## 🔧 SOLUTION: AJOUTER LA FONCTION MANQUANTE

Ajoutez ceci à `utils/helpers.py` :

```python
def calculer_score_sante_global(donnees: Dict, seuils: Dict) -> float:
    """
    Calcule un score de santé global du système frigorifique
    
    Score 0-100:
    - 100 = parfait
    - 80+ = système sain
    - 50-80 = attention
    - <50 = problème
    
    Args:
        donnees: Données capteurs actuelles
        seuils: Dict de seuils de référence
        
    Returns:
        Score 0-100
    """
    if not donnees or not seuils:
        return 50.0
    
    scores = []
    
    for capteur, seuil in seuils.items():
        if capteur not in donnees:
            scores.append(50)  # Capteur manquant = moyen
            continue
        
        valeur = donnees.get(capteur)
        min_val = seuil.get('min', 0)
        max_val = seuil.get('max', 100)
        optimal = seuil.get('optimal', (min_val + max_val) / 2)
        
        # Vérifier si dans limites
        if valeur < min_val or valeur > max_val:
            scores.append(20)  # Hors limites = mauvais
        # Vérifier écart par rapport optimal
        elif abs(valeur - optimal) > (max_val - min_val) * 0.3:
            scores.append(60)  # Loin de optimal = moyen
        else:
            scores.append(90)  # Proche optimal = bon
    
    # Moyenne des scores
    score_global = sum(scores) / len(scores) if scores else 50
    return round(score_global, 1)
```

---

## ✨ AMÉLIORATIONS À AJOUTER

### 1️⃣ Ajout du package pytest.ini

Créer `pytest.ini` pour configuration Pytest :

```ini
[pytest]
# Configuration Pytest
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers
markers =
    unit: Tests unitaires
    integration: Tests d'intégration
    slow: Tests lents
```

---

### 2️⃣ Améliorer test_simple.py

Remplacer le contenu par version améliorée :

```python
"""
Tests pour le système de diagnostic frigorifique
"""

import pytest
import json
import sys
from pathlib import Path

# Imports des modules à tester
from utils.validation import valider_donnees_capteurs
from utils.helpers import (
    generer_diagnostic_id,
    calculer_score_sante_global,
    calculer_moyenne,
    detecter_anomalie
)
from config import Config


# ============================================================
# FIXTURES (Setup données)
# ============================================================

@pytest.fixture
def donnees_capteurs_valides():
    """Données de test valides"""
    return {
        'Température': -18.0,
        'Pression_BP': 2.5,
        'Pression_HP': 12.0,
        'Intensité_Compresseur': 15.0,
        'Intensité_Ventilateur': 5.0,
        'Humidité_Evaporateur': 60.0,
        'Vibrations': 1.0
    }


@pytest.fixture
def donnees_capteurs_incompletes():
    """Données incomplètes (manquent 5 capteurs)"""
    return {
        'Température': -18.0,
        'Pression_BP': 2.5
    }


@pytest.fixture
def donnees_capteurs_anomalie():
    """Données avec une anomalie"""
    return {
        'Température': 50.0,  # ⚠️ ANOMALIE!
        'Pression_BP': 2.5,
        'Pression_HP': 12.0,
        'Intensité_Compresseur': 15.0,
        'Intensité_Ventilateur': 5.0,
        'Humidité_Evaporateur': 60.0,
        'Vibrations': 1.0
    }


# ============================================================
# TEST SUITE 1: VALIDATION
# ============================================================

@pytest.mark.unit
class TestValidation:
    """Tests du service de validation"""
    
    def test_validation_donnees_valides(self, donnees_capteurs_valides):
        """Test validation avec données valides"""
        validated = valider_donnees_capteurs(donnees_capteurs_valides)
        
        assert validated is not None
        assert isinstance(validated, dict)
        assert validated['Température'] == -18.0
        assert validated['Pression_BP'] == 2.5
        assert len(validated) == 7
    
    def test_validation_donnees_manquantes(self, donnees_capteurs_incompletes):
        """Test validation avec données manquantes"""
        with pytest.raises(ValueError, match="Données insuffisantes"):
            valider_donnees_capteurs(donnees_capteurs_incompletes)
    
    def test_validation_donnees_vides(self):
        """Test validation avec dict vide"""
        with pytest.raises(ValueError):
            valider_donnees_capteurs({})
    
    def test_validation_none_input(self):
        """Test validation avec None"""
        with pytest.raises((ValueError, AttributeError)):
            valider_donnees_capteurs(None)


# ============================================================
# TEST SUITE 2: HELPERS
# ============================================================

@pytest.mark.unit
class TestHelpers:
    """Tests des fonctions utilitaires"""
    
    def test_generer_diagnostic_id_unique(self):
        """Test que IDs générés sont uniques"""
        ids = [generer_diagnostic_id() for _ in range(100)]
        
        # Vérifier unicité
        assert len(ids) == len(set(ids)), "IDs ne sont pas uniques!"
    
    def test_generer_diagnostic_id_format(self):
        """Test format ID diagnostic"""
        id_diag = generer_diagnostic_id()
        
        assert id_diag.startswith('DIAG_')
        assert len(id_diag) > 10
    
    def test_calculer_moyenne(self):
        """Test calcul de moyenne"""
        valeurs = [10, 20, 30, 40, 50]
        moyenne = calculer_moyenne(valeurs)
        
        assert moyenne == 30.0
    
    def test_calculer_moyenne_vide(self):
        """Test moyenne liste vide"""
        moyenne = calculer_moyenne([])
        
        assert moyenne == 0.0
    
    def test_detecter_anomalie_positif(self):
        """Test détection anomalie (positif)"""
        valeur = 100  # Très loin de moyenne
        moyenne = 10
        ecart = 5
        
        assert detecter_anomalie(valeur, moyenne, ecart, seuil=2.0) is True
    
    def test_detecter_anomalie_negatif(self):
        """Test détection anomalie (négatif)"""
        valeur = 11  # Près de moyenne
        moyenne = 10
        ecart = 5
        
        assert detecter_anomalie(valeur, moyenne, ecart, seuil=2.0) is False


# ============================================================
# TEST SUITE 3: CALCULS SANTÉ
# ============================================================

@pytest.mark.unit
class TestSante:
    """Tests calcul score santé"""
    
    def test_score_sante_normal(self, donnees_capteurs_valides):
        """Test score santé système normal"""
        score = calculer_score_sante_global(donnees_capteurs_valides, Config.SEUILS)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 70, f"Score devrait être > 70, got {score}"
    
    def test_score_sante_anomalie(self, donnees_capteurs_anomalie):
        """Test score santé avec anomalie"""
        score = calculer_score_sante_global(donnees_capteurs_anomalie, Config.SEUILS)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 70, f"Score devrait être < 70, got {score}"
    
    def test_score_sante_empty(self):
        """Test score santé données vides"""
        score = calculer_score_sante_global({}, Config.SEUILS)
        
        # Pas données = score moyen
        assert 0 <= score <= 100


# ============================================================
# TEST SUITE 4: INTEGRATION
# ============================================================

@pytest.mark.integration
class TestIntegration:
    """Tests d'intégration"""
    
    def test_workflow_complet(self):
        """Test workflow complet"""
        # 1. Générer données
        donnees = {
            'Température': -18.0,
            'Pression_BP': 2.5,
            'Pression_HP': 12.0,
            'Intensité_Compresseur': 15.0,
            'Intensité_Ventilateur': 5.0,
            'Humidité_Evaporateur': 60.0,
            'Vibrations': 1.0
        }
        
        # 2. Valider
        validated = valider_donnees_capteurs(donnees)
        assert validated is not None
        
        # 3. Générer ID
        diag_id = generer_diagnostic_id()
        assert diag_id.startswith('DIAG_')
        
        # 4. Calculer score
        score = calculer_score_sante_global(validated, Config.SEUILS)
        assert score > 70
        
        print(f"✅ Workflow OK - ID: {diag_id}, Score: {score}")


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    # Lancer les tests
    pytest.main([__file__, '-v', '-m', 'unit'])
```

---

## 🚀 NOUVEAUX TESTS À AJOUTER

### Créer `tests/test_services.py`

```python
"""Tests pour les services"""

import pytest
from services.gemini_service import GeminiService
from services.apprentissage_service import ApprentissageService


@pytest.mark.unit
class TestGeminiService:
    """Tests service Gemini"""
    
    def test_gemini_init_sans_key(self):
        """Test init sans clé API"""
        service = GeminiService(api_key="")
        
        assert service.model is None
    
    def test_generer_fallback_analyse(self):
        """Test analyse fallback"""
        service = GeminiService(api_key="")
        result = service._generer_fallback_analyse()
        
        assert result['succes'] is False
        assert 'analyse' in result


@pytest.mark.unit
class TestApprentissageService:
    """Tests service apprentissage"""
    
    def test_init_apprentissage(self):
        """Test initialisation service"""
        service = ApprentissageService()
        
        assert service.compteur is not None
        assert service.compteur['total'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

### Créer `tests/test_simulateur.py`

```python
"""Tests pour le simulateur"""

import pytest
from simulateur import SimulateurCapteurs


@pytest.mark.unit
class TestSimulateur:
    """Tests simulateur capteurs"""
    
    def test_init_simulateur(self):
        """Test initialisation"""
        sim = SimulateurCapteurs(prob_panne=0.3, interval=10)
        
        assert sim.prob_panne == 0.3
        assert sim.interval == 10
    
    def test_generer_capteurs_normaux(self):
        """Test génération capteurs normaux"""
        sim = SimulateurCapteurs()
        capteurs = sim.generer_capteurs_normaux()
        
        assert len(capteurs) == 7  # 7 capteurs
        assert all(isinstance(v, float) for v in capteurs.values())
    
    def test_generer_diagnostic(self):
        """Test génération diagnostic"""
        sim = SimulateurCapteurs()
        diag = sim.generer_donnees_diagnostic()
        
        assert 'timestamp' in diag
        assert 'num_diagnostic' in diag
        assert 'Température' in diag


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## 📊 STRUCTURE RECOMMANDÉE

```
tests/
├── __init__.py
├── conftest.py              ← Fixtures partagées
├── pytest.ini               ← Config pytest
├── test_simple.py           ← Tests validation + helpers
├── test_services.py         ← Tests services IA (NEW)
├── test_simulateur.py       ← Tests simulateur (NEW)
├── test_api.py              ← Tests endpoints (NEW)
└── fixtures/
    └── test_data.json       ← Données de test
```

---

## 🎯 CHECKLIST AMÉLIORATIONS

- [ ] Ajouter `calculer_score_sante_global()` à `utils/helpers.py`
- [ ] Créer `pytest.ini`
- [ ] Améliorer `test_simple.py` avec fixtures
- [ ] Créer `test_services.py`
- [ ] Créer `test_simulateur.py`
- [ ] Créer `test_api.py`
- [ ] Atteindre 80% couverture
- [ ] Ajouter tests CI/CD

---

## 💻 COMMANDS

```bash
# Lancer tous les tests
pytest tests/ -v

# Lancer tests unitaires seulement
pytest tests/ -v -m unit

# Lancer tests d'intégration
pytest tests/ -v -m integration

# Voir couverture de code
pytest tests/ --cov --cov-report=html

# Lancer un fichier de test spécifique
pytest tests/test_services.py -v

# Watch mode (relance auto)
pytest-watch tests/
```

---

**Les tests = Qualité assurée! 🎯**
