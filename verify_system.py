"""
Script de vérification complète du système
Vérifie que tous les composants fonctionnent correctement
"""
import requests
import time
import sys

def check_health(url, name):
    """Vérifie le health check d'un service"""
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        if resp.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: Erreur {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: Non disponible ({e})")
        return False

def test_webhook():
    """Test le webhook de diagnostic"""
    try:
        data = {
            "Température": 25.5,
            "Pression_HP": 15.2,
            "Pression_BP": 3.1,
            "Courant": 8.5,
            "Tension": 230,
            "Humidité": 65,
            "Débit_air": 1200,
            "Vibration": 0.8,
            "localisation": "Test"
        }
        resp = requests.post("http://localhost:5000/webhook/diagnostic-frigo", json=data, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Webhook diagnostic: OK")
            return True
        else:
            print(f"⚠️ Webhook diagnostic: Code {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook diagnostic: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 VÉRIFICATION DU SYSTÈME")
    print("=" * 60)
    
    # Vérifier les services
    services_ok = True
    services_ok &= check_health("http://localhost:5000", "App Principale (5000)")
    services_ok &= check_health("http://localhost:5001", "Chat Service (5001)")
    services_ok &= check_health("http://localhost:5002", "IA Service (5002)")
    
    print()
    
    # Test webhook
    webhook_ok = test_webhook()
    
    print()
    print("=" * 60)
    if services_ok and webhook_ok:
        print("🎉 SYSTÈME COMPLÈTEMENT OPÉRATIONNEL!")
        print("=" * 60)
        print()
        print("📋 Prochaines étapes:")
        print("   1. Tester avec le simulateur:")
        print("      Invoke-RestMethod -Uri 'http://localhost:5000/api/simulator/start' -Method POST -ContentType 'application/json' -Body '{\"cycles\": 3, \"interval\": 5}'")
        return 0
    else:
        print("⚠️ Certains services ne sont pas disponibles")
        print("   Démarrez les services manquants et réessayez")
        return 1

if __name__ == "__main__":
    sys.exit(main())
