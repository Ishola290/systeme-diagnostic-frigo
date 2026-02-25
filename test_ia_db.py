"""
Script de test pour vérifier que l'IA lit correctement le diagnostic
"""
import sys
from pathlib import Path

# Ajouter les chemins nécessaires
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "gpt"))

# Import direct sans passer par __init__.py
import ia_service
from ia_service import IAService

# Créer une instance du service IA
ia_service_instance = IAService()

# Tester la requête BD
print("\n=== TEST 1: query_database('latest') ===")
result = ia_service_instance.query_database('latest')
print(f"Résultat: {result}")

print("\n=== TEST 2: _detect_database_query ===")
message = "Quelle est la dernière panne ?"
query_type = ia_service_instance._detect_database_query(message)
print(f"Message: '{message}'")
print(f"Type détecté: {query_type}")

print("\n=== TEST 3: process_chat ===")
response = ia_service_instance.process_chat(message, user_id='test', user_name='Test')
print(f"Réponse: {response}")

print("\n=== VÉRIFICATION FICHIER ===")
data_file = Path(__file__).parent / "data" / "dernier_diagnostic.json"
print(f"Chemin: {data_file}")
print(f"Existe: {data_file.exists()}")
if data_file.exists():
    import json
    with open(data_file) as f:
        data = json.load(f)
    print(f"Type panne dans fichier: {data.get('apprentissage', {}).get('type_panne', 'NON TROUVÉ')}")
    print(f"Panne détectée: {data.get('panne_detectee')}")

print("\n=== TERMINÉ ===")
