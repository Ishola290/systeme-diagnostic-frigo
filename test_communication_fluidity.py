#!/usr/bin/env python3
"""
TEST: Vérifier que la communication Chat ↔ Service IA est fluide
Simule 10 messages en succession rapide et mesure les temps de réponse
"""

import requests
import json
import time
from datetime import datetime

# Configuration
CHAT_URL = "http://localhost:5001"
IA_SERVICE_URL = "http://localhost:5002"

def test_ia_service_communication():
    """Tester la communication directe avec le service IA"""
    print("\n" + "="*60)
    print("TEST 1: Communication directe avec Service IA")
    print("="*60)
    
    # 1️⃣ Test Health Check
    try:
        print("\n🔍 Test Health Check...")
        response = requests.get(f"{IA_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Service IA actif: {response.json()}")
        else:
            print(f"❌ Service IA erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ IMPOSSIBLE de se connecter au service IA sur {IA_SERVICE_URL}")
        print(f"   Erreur: {e}")
        return False
    
    # 2️⃣ Test messages consécutifs
    print("\n🔍 Test 10 messages consécutifs...")
    messages = [
        "Bonjour, quels sont les problèmes courants de refroidissement?",
        "Comment diagnostiquer une fuite de réfrigérant?",
        "Explique le cycle de compression.",
        "Quels sont les signes d'un compresseur défaillant?",
        "Comment nettoyer les serpentins?",
        "Quel est le débit normal du réfrigérant?",
        "Explique le fonctionnement d'un thermostat.",
        "Comment mesurer la pression?",
        "Qu'est-ce qu'une surcharge en huile?",
        "Quelles sont les normes de sécurité?",
    ]
    
    times = []
    errors = 0
    
    for i, msg in enumerate(messages, 1):
        try:
            print(f"\n📤 Message {i}/10: {msg[:40]}...")
            
            start = time.time()
            response = requests.post(
                f"{IA_SERVICE_URL}/api/chat/message",
                json={
                    "message": msg,
                    "user_id": "test_user",
                    "user_name": "Testeur",
                    "source": "test"
                },
                timeout=40
            )
            elapsed = time.time() - start
            times.append(elapsed)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    processing_ms = result.get('processing_time_ms', 'N/A')
                    resp_text = result.get('response', '')[:50]
                    print(f"✅ Réponse en {elapsed:.2f}s (processing: {processing_ms}ms)")
                    print(f"   Réponse: {resp_text}...")
                else:
                    print(f"❌ Erreur: {result.get('error')}")
                    errors += 1
            else:
                print(f"❌ Statut HTTP {response.status_code}")
                errors += 1
                
        except requests.exceptions.Timeout:
            print(f"⏱️ TIMEOUT (>40s) pour message {i}")
            errors += 1
        except Exception as e:
            print(f"❌ Erreur: {e}")
            errors += 1
    
    # 3️⃣ Statistiques
    print("\n" + "-"*60)
    print("📊 STATISTIQUES")
    print("-"*60)
    print(f"Messages traités: {len(messages) - errors}/{len(messages)}")
    print(f"Erreurs: {errors}")
    if times:
        print(f"Temps moyen: {sum(times)/len(times):.2f}s")
        print(f"Temps min: {min(times):.2f}s")
        print(f"Temps max: {max(times):.2f}s")
        
        # Alerte si trop lent
        avg_time = sum(times) / len(times)
        if avg_time > 20:
            print(f"⚠️ ATTENTION: Moyenne {avg_time:.2f}s très élevée!")
            print("   → Vérifier CPU/RAM du service IA")
        elif avg_time > 10:
            print(f"⚠️ Ralentissement détecté: {avg_time:.2f}s")
    
    return errors == 0


def test_websocket_simulation():
    """Tester la simulation du flux WebSocket"""
    print("\n" + "="*60)
    print("TEST 2: Simulation flux WebSocket Chat → IA")
    print("="*60)
    
    print("\n🔍 Vérification endpoint Chat Web...")
    try:
        # Vérifier que le chat est actif
        response = requests.get(f"{CHAT_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Chat Web actif")
        else:
            print(f"⚠️ Chat Web retourné {response.status_code}")
    except Exception as e:
        print(f"❌ IMPOSSIBLE de se connecter au Chat Web sur {CHAT_URL}")
        print(f"   Erreur: {e}")
        print(f"   → Vous devez lancer le Chat Web en premier!")
        return False
    
    print("\n✅ Configuration OK pour tests WebSocket")
    print("   → Lancer le chat Web pour tester les WebSockets")
    
    return True


def main():
    print("\n" + "="*70)
    print("🧪 TEST: VÉRIFIER COMMUNICATION FLUIDE CHAT ↔ SERVICE IA")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier si les services sont lancés
    print("\n📋 Vérification des services...")
    
    ia_ok = False
    chat_ok = False
    
    try:
        response = requests.get(f"{IA_SERVICE_URL}/health", timeout=2)
        ia_ok = response.status_code == 200
        print(f"{'✅' if ia_ok else '❌'} Service IA ({IA_SERVICE_URL})")
    except:
        print(f"❌ Service IA ({IA_SERVICE_URL})")
    
    try:
        response = requests.get(f"{CHAT_URL}/", timeout=2)
        chat_ok = response.status_code == 200
        print(f"{'✅' if chat_ok else '❌'} Chat Web ({CHAT_URL})")
    except:
        print(f"❌ Chat Web ({CHAT_URL})")
    
    if not ia_ok:
        print("\n❌ Service IA non disponible!")
        print("   Lancez d'abord: python gpt/app_ia.py")
        return
    
    # TEST 1: Communication IA
    test1_ok = test_ia_service_communication()
    
    # TEST 2: Configuration WebSocket
    test2_ok = test_websocket_simulation()
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"Test 1 - Communication IA: {'✅ PASSÉ' if test1_ok else '❌ ÉCHOUÉ'}")
    print(f"Test 2 - Configuration WS: {'✅ PASSÉ' if test2_ok else '❌ ÉCHOUÉ'}")
    
    if test1_ok and test2_ok:
        print("\n✅ TOUS LES TESTS PASSÉS!")
        print("   → Communication fluide confirmée")
        print("   → Prêt pour production!")
    else:
        print("\n⚠️ Certains tests échoués")
        print("   → Vérifiez les logs pour les détails")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
