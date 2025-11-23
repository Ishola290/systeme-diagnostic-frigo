# 🧪 RÔLE DES TESTS DANS LE SYSTÈME

## 📋 Vue d'Ensemble

Le dossier `tests/` contient les **tests unitaires** qui vérifient que toutes les fonctionnalités du système fonctionnent correctement.

```
tests/
├── test_simple.py          ← Tests unitaires (validation, helpers, etc.)
└── __init__.py             ← Marque le dossier comme package Python
```

---

## 🎯 RÔLE PRINCIPAL

### ✅ Assurance Qualité
Les tests s'assurent que :
- Les données sont validées correctement
- Les IDs diagnostics sont générés de manière unique
- Le score de santé est calculé correctement
- Les helpers fonctionnent comme prévu
- Aucune régression entre versions

### 🔍 Détection de Bugs
Les tests détectent immédiatement :
- ❌ Si validation échoue
- ❌ Si données manquantes
- ❌ Si calcul score incorrect
- ❌ Si helpers ne fonctionnent pas

### 📊 Documentation Vivante
Les tests servent aussi de documentation :
- Montrent comment utiliser les fonctions
- Donnent des exemples concrets
- Expliquent les cas normaux ET limites

---

## 📝 TESTS ACTUELS

### Test 1: `test_validation_donnees_valides()`

**Que teste-t-il ?**
```python
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
```

**Vérifie :**
- ✅ Données valides sont acceptées
- ✅ Chaque valeur est convertie en float
- ✅ Tous les capteurs sont traités

**Utilité :** S'assurer que le service de validation ne rejette pas les bonnes données

---

### Test 2: `test_validation_donnees_manquantes()`

**Que teste-t-il ?**
```python
def test_validation_donnees_manquantes():
    """Test validation avec données manquantes"""
    donnees = {
        'Température': -18,
        'Pression_BP': 2.5
        # Autres capteurs MANQUANTS!
    }
    
    with pytest.raises(ValueError, match="Champs manquants"):
        valider_donnees_capteurs(donnees)
```

**Vérifie :**
- ✅ Données incomplètes sont rejetées
- ✅ Un ValueError est levé
- ✅ Message d'erreur approprié

**Utilité :** S'assurer que les données incomplètes sont détectées

---

### Test 3: `test_generer_diagnostic_id()`

**Que teste-t-il ?**
```python
def test_generer_diagnostic_id():
    """Test génération d'ID unique"""
    id1 = generer_diagnostic_id()
    id2 = generer_diagnostic_id()
    
    assert id1.startswith('DIAG_')
    assert id2.startswith('DIAG_')
    assert id1 != id2  # Chaque ID est unique!
```

**Vérifie :**
- ✅ IDs commencent par 'DIAG_'
- ✅ Chaque ID est unique
- ✅ Format cohérent

**Utilité :** Garantir que chaque diagnostic a un identifiant unique

---

### Test 4: `test_score_sante()`

**Que teste-t-il ?**
```python
def test_score_sante():
    """Test calcul score de santé"""
    donnees = {
        'Température': -18,      # Optimal
        'Pression_BP': 2.5,      # Optimal
        'Pression_HP': 12,       # Optimal
        # ... tous normaux
    }
    
    score = calculer_score_sante_global(donnees, Config.SEUILS)
    
    assert 0 <= score <= 100
    assert score > 80  # Score élevé = système sain
```

**Vérifie :**
- ✅ Score est entre 0 et 100
- ✅ Données normales = score > 80
- ✅ Calcul cohérent

**Utilité :** S'assurer que le système sain a bon score

---

### Test 5: `test_score_sante_anomalie()`

**Que teste-t-il ?**
```python
def test_score_sante_anomalie():
    """Test score avec anomalie"""
    donnees = {
        'Température': 50,  # ⚠️ ANOMALIE! (devrait être -18)
        'Pression_BP': 2.5,
        # ... autres normaux
    }
    
    score = calculer_score_sante_global(donnees, Config.SEUILS)
    
    assert score < 80  # Score plus bas = anomalie détectée
```

**Vérifie :**
- ✅ Anomalies sont détectées
- ✅ Score baisse avec anomalies
- ✅ Distinction normal vs anormal

**Utilité :** S'assurer que les pannes sont détectées

---

## 🔄 FLUX DE TEST

```
┌─────────────────────────────────┐
│  Développeur modify le code     │
└────────────┬────────────────────┘
             │
             ↓
    ┌────────────────────┐
    │  pytest test_*.py  │  ← Lance tous les tests
    └────────┬───────────┘
             │
        ┌────┴────────────────────────┐
        │                             │
        ↓                             ↓
    ✅ PASS                       ❌ FAIL
    │                             │
    └─→ Code OK                   └─→ BUG DÉTECTÉ!
        Deploy possible               Fix required
```

---

## 💻 COMMENT LANCER LES TESTS

### Méthode 1: Pytest (Recommandé)
```bash
# Activer environnement
venv\Scripts\Activate.ps1

# Lancer tous les tests
pytest tests/

# Lancer avec verbosité (plus de détails)
pytest tests/ -v

# Lancer un test spécifique
pytest tests/test_simple.py::test_validation_donnees_valides -v

# Lancer avec coverage (couverture de code)
pytest tests/ --cov=utils --cov=services
```

### Méthode 2: Python Direct
```bash
# Lancer directement le fichier de test
python -m pytest tests/test_simple.py

# Ou
python tests/test_simple.py
```

### Méthode 3: Depuis VS Code
```
1. Ouvrir test_simple.py
2. Clic droit → "Run Tests"
3. Voir résultats dans panneau "Test Explorer"
```

---

## 📊 RÉSULTATS ATTENDUS

### Succès ✅
```
tests/test_simple.py::test_validation_donnees_valides PASSED
tests/test_simple.py::test_validation_donnees_manquantes PASSED
tests/test_simple.py::test_generer_diagnostic_id PASSED
tests/test_simple.py::test_score_sante PASSED
tests/test_simple.py::test_score_sante_anomalie PASSED

====== 5 passed in 0.23s ======
```

### Échec ❌
```
tests/test_simple.py::test_validation_donnees_valides FAILED
FAILED tests/test_simple.py::test_validation_donnees_valides
AssertionError: 0 != 1
```

---

## 🏗️ ARCHITECTURE DES TESTS

### Structure Logique
```
test_simple.py
│
├─ Imports
│  └─ pytest, validation, helpers, config
│
├─ Test Suite 1: Validation
│  ├─ test_validation_donnees_valides()      ← Cas normal
│  └─ test_validation_donnees_manquantes()   ← Cas erreur
│
├─ Test Suite 2: Helpers
│  └─ test_generer_diagnostic_id()           ← Unicité
│
└─ Test Suite 3: Calculs
   ├─ test_score_sante()                     ← Cas normal
   └─ test_score_sante_anomalie()            ← Détection
```

### Dépendances Testées
```
test_simple.py teste:
├─ utils/validation.py
│  └─ valider_donnees_capteurs()
├─ utils/helpers.py
│  ├─ generer_diagnostic_id()
│  └─ calculer_score_sante_global()
└─ config.py
   └─ Config.SEUILS
```

---

## ✨ BONNES PRATIQUES

### 1️⃣ Noms Clairs
```python
# ✅ BON
def test_validation_donnees_valides():
    """Test validation avec données valides"""

# ❌ MAUVAIS
def test_1():
    """Test"""
```

### 2️⃣ Un Cas par Test
```python
# ✅ BON - Un test = un cas
def test_validation_donnees_valides():
    # Teste SEULEMENT les données valides

def test_validation_donnees_manquantes():
    # Teste SEULEMENT les données manquantes

# ❌ MAUVAIS - Plusieurs cas dans un test
def test_validation():
    # Test données valides
    # Test données manquantes
    # Test données invalides
    # ... Trop de logique!
```

### 3️⃣ Setup/Teardown si Nécessaire
```python
import pytest

@pytest.fixture
def donnees_test():
    """Setup: Prépare les données de test"""
    return {
        'Température': -18,
        'Pression_BP': 2.5,
        # ...
    }

def test_avec_fixture(donnees_test):
    """Utilise les données pré-préparées"""
    result = valider_donnees_capteurs(donnees_test)
    assert result is not None
```

### 4️⃣ Assertions Claires
```python
# ✅ BON - Clair et spécifique
assert score > 80, f"Score devrait être > 80, got {score}"

# ❌ MAUVAIS - Trop général
assert score
```

---

## 🚨 QUAND LANCER LES TESTS

| Moment | Raison |
|--------|--------|
| 📝 Avant commit | Vérifier que code fonctionne |
| 🔧 Après modification | S'assurer pas de régression |
| 🐛 Bug détecté | Reproduire et tester fix |
| 📦 Avant deploy | Validation complète |
| 🔄 CI/CD | Tests automatiques |

---

## 📈 COUVERTURE DE CODE

**Couverture de code** = % de code testé

```bash
# Voir la couverture
pytest tests/ --cov=utils --cov=services --cov-report=html

# Affiche dans HTML report quelles lignes ne sont pas testées
```

**Objectif:** ≥ 80% couverture

---

## 🎯 TESTS FUTURS À AJOUTER

### Services IA
```python
def test_gemini_analyse():
    """Test service Gemini"""
    
def test_apprentissage_traiter():
    """Test service apprentissage"""
    
def test_telegram_send():
    """Test Telegram notification"""
```

### Simulateur
```python
def test_simulateur_pannes():
    """Test génération pannes"""
    
def test_simulateur_signature():
    """Test signature panne appliquée"""
```

### API
```python
def test_health_endpoint():
    """Test GET /health"""
    
def test_diagnostic_endpoint():
    """Test POST /webhook/diagnostic-frigo"""
```

### Integration
```python
def test_flux_complet():
    """Test workflow end-to-end"""
```

---

## 🔍 EXEMPLE: AJOUTER UN TEST

### Pas 1: Identifier ce à tester
```
Je veux tester le simulateur qui génère des pannes
```

### Pas 2: Écrire le test
```python
def test_simulateur_panne():
    """Test génération d'une panne"""
    from simulateur import SimulateurCapteurs
    
    sim = SimulateurCapteurs(prob_panne=1.0)  # 100% chance
    diag = sim.generer_donnees_diagnostic()
    
    # Si prob=1.0, une panne DOIT être générée
    assert sim.panne_active is not None
```

### Pas 3: Lancer et voir échouer
```bash
pytest tests/test_simple.py::test_simulateur_panne -v
# FAILED - attendu, on n'a pas encore le code!
```

### Pas 4: Implémenter le code
```python
# Dans simulateur.py
class SimulateurCapteurs:
    def generer_donnees_diagnostic(self):
        if random.random() < self.prob_panne:
            self.panne_active = random.choice(list(self.PANNES_SIGNATURES.keys()))
        # ...
```

### Pas 5: Relancer et vérifier le succès
```bash
pytest tests/test_simple.py::test_simulateur_panne -v
# PASSED ✅
```

---

## 📚 RESSOURCES

- **Pytest Documentation** : https://docs.pytest.org/
- **Python unittest** : https://docs.python.org/3/library/unittest.html
- **Testing Best Practices** : https://realpython.com/python-testing/

---

## ✅ RÉSUMÉ

| Aspect | Détail |
|--------|--------|
| **Rôle** | Assurer la qualité du code |
| **Lieu** | `tests/` dossier |
| **Fichier** | `test_simple.py` (5 tests) |
| **Framework** | Pytest |
| **Fréquence** | À chaque modification |
| **Couverture** | Validation, Helpers, Calculs |
| **Succès** | 5/5 tests doivent passer |

---

## 🚀 COMMANDES RAPIDES

```bash
# Lancer tous les tests
pytest tests/ -v

# Lancer un test spécifique
pytest tests/test_simple.py::test_validation_donnees_valides -v

# Lancer avec couverture
pytest tests/ --cov --cov-report=html

# Lancer en watch mode (relance auto)
pytest-watch tests/

# Lancer avec résultat verbeux
pytest tests/ -vv
```

---

**Les tests = Filet de sécurité du système ! 🛡️**

Sans tests → Bugs se glissent facilement  
Avec tests → Qualité garantie ✅
