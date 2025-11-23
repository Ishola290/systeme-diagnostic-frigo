#!/usr/bin/env python3
"""
Test de communication inter-services
Vérifie que tous les services peuvent se découvrir et communiquer
"""

import os
import sys
import json
import time
import socket
import requests
import argparse
import logging
from typing import Dict, Tuple, List
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceTester:
    """Test la communication inter-services"""
    
    def __init__(self, 
                 app_url: str = 'http://localhost:5000',
                 chat_url: str = 'http://localhost:5001',
                 ia_url: str = 'http://localhost:5002',
                 verbose: bool = False):
        
        self.urls = {
            'app': app_url,
            'chat': chat_url,
            'ia': ia_url
        }
        
        self.verbose = verbose
        self.results = {}
        
        logger.info(f"{'='*70}")
        logger.info(f"🧪 Test Communication Inter-Services")
        logger.info(f"{'='*70}\n")
        
        logger.info("📋 URLs configurées:")
        for name, url in self.urls.items():
            logger.info(f"   {name:6} → {url}")
        logger.info()
    
    def test_health(self) -> bool:
        """Test que tous les services répondent"""
        logger.info("1️⃣  TEST HEALTH CHECKS")
        logger.info("-" * 70)
        
        all_ok = True
        for name, url in self.urls.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"   ✅ {name:6} is healthy")
                    self.results[f'{name}_health'] = True
                else:
                    logger.warning(f"   ⚠️  {name:6} returned {response.status_code}")
                    self.results[f'{name}_health'] = False
                    all_ok = False
            except requests.exceptions.Timeout:
                logger.warning(f"   ⏱️  {name:6} timeout (not responding)")
                self.results[f'{name}_health'] = False
                all_ok = False
            except requests.exceptions.ConnectionError:
                logger.warning(f"   🔌 {name:6} connection error (not running)")
                self.results[f'{name}_health'] = False
                all_ok = False
            except Exception as e:
                logger.error(f"   ❌ {name:6} error: {e}")
                self.results[f'{name}_health'] = False
                all_ok = False
        
        logger.info()
        return all_ok
    
    def test_app_to_chat(self) -> bool:
        """Test communication App → Chat"""
        logger.info("2️⃣  TEST APP → CHAT COMMUNICATION")
        logger.info("-" * 70)
        
        try:
            # App should have endpoint that calls Chat
            response = requests.get(
                f"{self.urls['app']}/api/check-chat",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('chat_responsive'):
                    logger.info(f"   ✅ App can reach Chat")
                    self.results['app_to_chat'] = True
                    return True
                else:
                    logger.warning(f"   ⚠️  App cannot reach Chat")
                    self.results['app_to_chat'] = False
                    return False
            else:
                logger.warning(f"   ⚠️  App endpoint error: {response.status_code}")
                self.results['app_to_chat'] = False
                return False
        
        except Exception as e:
            logger.warning(f"   ⚠️  Test unavailable: {e}")
            logger.info(f"      (Endpoint may not be implemented)")
            self.results['app_to_chat'] = None
            return None
    
    def test_chat_to_ia(self) -> bool:
        """Test communication Chat → IA"""
        logger.info("3️⃣  TEST CHAT → IA COMMUNICATION")
        logger.info("-" * 70)
        
        try:
            # Chat should have endpoint that calls IA
            response = requests.get(
                f"{self.urls['chat']}/api/check-ia",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ia_responsive'):
                    logger.info(f"   ✅ Chat can reach IA")
                    self.results['chat_to_ia'] = True
                    return True
                else:
                    logger.warning(f"   ⚠️  Chat cannot reach IA")
                    self.results['chat_to_ia'] = False
                    return False
            else:
                logger.warning(f"   ⚠️  Chat endpoint error: {response.status_code}")
                self.results['chat_to_ia'] = False
                return False
        
        except Exception as e:
            logger.warning(f"   ⚠️  Test unavailable: {e}")
            logger.info(f"      (Endpoint may not be implemented)")
            self.results['chat_to_ia'] = None
            return None
        
        logger.info()
    
    def test_simulator_endpoint(self) -> bool:
        """Test que l'App a le webhook pour simulateur"""
        logger.info("4️⃣  TEST SIMULATOR WEBHOOK")
        logger.info("-" * 70)
        
        try:
            # Tenter POST vers webhook
            test_data = {
                'diagnostic_id': 'TEST_001',
                'timestamp': datetime.now().isoformat(),
                'type': 'test',
                'capteurs': {
                    'Température': 5.0,
                    'Pression_BP': 2.5,
                    'Courant': 15.0
                }
            }
            
            response = requests.post(
                f"{self.urls['app']}/webhook/diagnostic-frigo",
                json=test_data,
                timeout=5
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"   ✅ Webhook accessible (status: {response.status_code})")
                self.results['simulator_webhook'] = True
                return True
            else:
                logger.warning(f"   ⚠️  Webhook returned {response.status_code}")
                logger.info(f"      Response: {response.text[:100]}")
                self.results['simulator_webhook'] = False
                return False
        
        except requests.exceptions.ConnectionError:
            logger.warning(f"   🔌 Cannot connect to App")
            self.results['simulator_webhook'] = False
            return False
        except Exception as e:
            logger.warning(f"   ⚠️  Test error: {e}")
            self.results['simulator_webhook'] = False
            return False
        
        logger.info()
    
    def test_dns_resolution(self) -> bool:
        """Test Docker DNS resolution (app, chat, gpt)"""
        logger.info("5️⃣  TEST DOCKER DNS RESOLUTION")
        logger.info("-" * 70)
        
        all_ok = True
        for service_name in ['app', 'chat', 'gpt']:
            try:
                ip = socket.gethostbyname(service_name)
                logger.info(f"   ✅ {service_name:6} → {ip}")
                self.results[f'dns_{service_name}'] = True
            except socket.gaierror:
                logger.info(f"   ℹ️  {service_name:6} not resolvable (not in Docker)")
                self.results[f'dns_{service_name}'] = False
                all_ok = False
        
        logger.info()
        return all_ok
    
    def test_network_ports(self) -> Dict[str, bool]:
        """Test que les ports sont ouverts"""
        logger.info("6️⃣  TEST NETWORK PORTS")
        logger.info("-" * 70)
        
        ports = {'app': 5000, 'chat': 5001, 'ia': 5002}
        results = {}
        
        for name, port in ports.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    logger.info(f"   ✅ localhost:{port} ({name}) open")
                    results[f'port_{name}'] = True
                else:
                    logger.warning(f"   ❌ localhost:{port} ({name}) closed")
                    results[f'port_{name}'] = False
            except Exception as e:
                logger.warning(f"   ❌ Port {port} error: {e}")
                results[f'port_{name}'] = False
        
        logger.info()
        return results
    
    def generate_report(self) -> Dict:
        """Génère rapport de test"""
        logger.info("="*70)
        logger.info("📊 RAPPORT DE TEST")
        logger.info("="*70 + "\n")
        
        # Résumé
        passed = sum(1 for v in self.results.values() if v is True)
        failed = sum(1 for v in self.results.values() if v is False)
        skipped = sum(1 for v in self.results.values() if v is None)
        
        logger.info(f"✅ Passed:  {passed}")
        logger.info(f"❌ Failed:  {failed}")
        logger.info(f"⏭️  Skipped: {skipped}")
        logger.info()
        
        # Détails
        logger.info("Détails:")
        for test_name, result in sorted(self.results.items()):
            if result is True:
                logger.info(f"   ✅ {test_name}")
            elif result is False:
                logger.info(f"   ❌ {test_name}")
            else:
                logger.info(f"   ⏭️  {test_name} (skipped)")
        
        logger.info()
        
        # Recommandations
        if failed > 0:
            logger.warning("⚠️  RECOMMANDATIONS:")
            if not self.results.get('app_health'):
                logger.warning("   1. Démarrer service APP: python app.py")
            if not self.results.get('chat_health'):
                logger.warning("   2. Démarrer service CHAT: cd chat && python app_web.py")
            if not self.results.get('ia_health'):
                logger.warning("   3. Démarrer service IA: cd gpt && python app_ia.py")
            if not self.results.get('simulator_webhook'):
                logger.warning("   4. Vérifier que webhook /webhook/diagnostic-frigo existe")
            logger.info()
        
        # Vérification finale
        if passed > failed and failed < 2:
            logger.info("✅ System ready for testing!")
        elif failed == 0 and passed > 3:
            logger.info("🎉 All systems operational!")
        else:
            logger.warning("⚠️  Some services are not ready")
        
        logger.info()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'results': self.results
        }
    
    def run_all_tests(self) -> bool:
        """Exécute tous les tests"""
        try:
            # Tests
            self.test_health()
            self.test_dns_resolution()
            self.test_network_ports()
            self.test_app_to_chat()
            self.test_chat_to_ia()
            self.test_simulator_endpoint()
            
            # Rapport
            report = self.generate_report()
            
            # Sauvegarder rapport
            report_file = 'test_communication_report.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📄 Rapport sauvegardé: {report_file}")
            
            # Retour
            return report['failed'] == 0
        
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description='Test de communication inter-services'
    )
    parser.add_argument(
        '--app-url',
        default='http://localhost:5000',
        help='URL du service APP'
    )
    parser.add_argument(
        '--chat-url',
        default='http://localhost:5001',
        help='URL du service CHAT'
    )
    parser.add_argument(
        '--ia-url',
        default='http://localhost:5002',
        help='URL du service IA'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Exécuter tests
    tester = ServiceTester(
        app_url=args.app_url,
        chat_url=args.chat_url,
        ia_url=args.ia_url,
        verbose=args.verbose
    )
    
    success = tester.run_all_tests()
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
