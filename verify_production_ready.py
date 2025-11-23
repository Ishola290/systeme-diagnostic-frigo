#!/usr/bin/env python3
"""
SCRIPT DE VÉRIFICATION PRE-PRODUCTION
Checklist complète avant de lancer le système
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def check_file_exists(path, description):
    """Vérifier qu'un fichier existe"""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_file_contains(path, text, description):
    """Vérifier qu'un fichier contient un texte"""
    if not Path(path).exists():
        print(f"❌ {description}: fichier non trouvé")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        found = text in content
        status = "✅" if found else "❌"
        print(f"{status} {description}")
        return found

def check_directory(path, description):
    """Vérifier qu'un répertoire existe"""
    exists = Path(path).is_dir()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def main():
    print("\n" + "="*70)
    print("🔍 VÉRIFICATION PRE-PRODUCTION")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire: {Path.cwd()}")
    
    results = {
        'files': [],
        'code': [],
        'config': [],
        'all_passed': True
    }
    
    # ==================== 1️⃣ FICHIERS REQUIS ====================
    print("\n" + "-"*70)
    print("1️⃣ FICHIERS REQUIS")
    print("-"*70)
    
    required_files = [
        ('app.py', 'Application principale'),
        ('chat/app_web.py', 'Service Chat Web'),
        ('gpt/app_ia.py', 'Service IA'),
        ('gpt/ia_service.py', 'Classe IAService'),
        ('docker-compose.yml', 'Configuration Docker'),
        ('requirements.txt', 'Dépendances principales'),
        ('chat/requirements.txt', 'Dépendances Chat'),
        ('gpt/requirements.txt', 'Dépendances Service IA'),
    ]
    
    for file_path, description in required_files:
        ok = check_file_exists(file_path, description)
        results['files'].append(ok)
    
    # ==================== 2️⃣ VÉRIFICATION INTÉGRATION CODE ====================
    print("\n" + "-"*70)
    print("2️⃣ VÉRIFICATION INTÉGRATION CODE")
    print("-"*70)
    
    checks = [
        ('chat/app_web.py', 'IA_SERVICE_URL', 'Service IA URL configurée dans Chat'),
        ('chat/app_web.py', 'requests.post', 'Chat appelle Service IA via HTTP'),
        ('chat/app_web.py', 'calculate_confidence', 'Méthode confidence scoring présente'),
        ('gpt/app_ia.py', 'CHAT_SERVICE_URL', 'URL Chat Web configurée'),
        ('gpt/app_ia.py', 'TELEGRAM_SERVICE_URL', 'URL Telegram configurée'),
        ('gpt/app_ia.py', '@app.route', 'Endpoints API définies'),
        ('app.py', '/api/telegram/notify', 'Endpoint notification Telegram'),
        ('app.py', 'IA_SERVICE_URL', 'Service IA configuré'),
    ]
    
    for file_path, text, description in checks:
        ok = check_file_contains(file_path, text, description)
        results['code'].append(ok)
    
    # ==================== 3️⃣ CONFIGURATION ====================
    print("\n" + "-"*70)
    print("3️⃣ CONFIGURATION")
    print("-"*70)
    
    # Vérifier docker-compose
    docker_ok = True
    if Path('docker-compose.yml').exists():
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
            docker_ok = all([
                'main-app' in content,
                'chat-web' in content,
                'ia-service' in content,
                'IA_SERVICE_URL' in content,
            ])
        status = "✅" if docker_ok else "❌"
        print(f"{status} Docker-compose configuré avec 3 services")
    
    results['config'].append(docker_ok)
    
    # Vérifier requirements.txt
    req_ok = True
    for req_file in ['requirements.txt', 'chat/requirements.txt', 'gpt/requirements.txt']:
        if Path(req_file).exists():
            with open(req_file, 'r') as f:
                content = f.read()
                # Éviter les versions problématiques
                if 'chromadb==0.5.0' in content:
                    print(f"❌ {req_file}: chromadb==0.5.0 détecté (à supprimer)")
                    req_ok = False
    
    if req_ok:
        print(f"✅ Requirements.txt nettoyés (pas de dépendances problématiques)")
    
    results['config'].append(req_ok)
    
    # ==================== 4️⃣ MODÈLES DB ====================
    print("\n" + "-"*70)
    print("4️⃣ MODÈLES BASE DE DONNÉES")
    print("-"*70)
    
    db_checks = [
        ('chat/app_web.py', 'class User', 'Modèle User'),
        ('chat/app_web.py', 'class Alert', 'Modèle Alert'),
        ('chat/app_web.py', 'class Message', 'Modèle Message'),
        ('chat/app_web.py', 'first_seen', 'Champ first_seen (alerte)'),
        ('chat/app_web.py', 'last_seen', 'Champ last_seen (alerte)'),
        ('chat/app_web.py', 'confidence', 'Champ confidence (alerte)'),
        ('chat/app_web.py', 'calculate_confidence', 'Méthode calculate_confidence'),
    ]
    
    for file_path, text, description in db_checks:
        ok = check_file_contains(file_path, text, description)
        results['code'].append(ok)
    
    # ==================== 5️⃣ SERVICE IA ====================
    print("\n" + "-"*70)
    print("5️⃣ SERVICE IA (Phi-2 Model)")
    print("-"*70)
    
    ia_checks = [
        ('gpt/ia_service.py', 'class IAService', 'Classe IAService'),
        ('gpt/ia_service.py', 'AutoTokenizer', 'Tokenizer HuggingFace'),
        ('gpt/ia_service.py', 'AutoModelForCausalLM', 'Modèle LLM'),
        ('gpt/ia_service.py', 'process_chat_message', 'Méthode traitement message'),
        ('gpt/ia_service.py', 'process_alert', 'Méthode traitement alerte'),
        ('gpt/app_ia.py', '/health', 'Endpoint health check'),
        ('gpt/app_ia.py', '/api/chat/message', 'Endpoint message chat'),
        ('gpt/app_ia.py', '/api/alerts/process', 'Endpoint alerte'),
    ]
    
    for file_path, text, description in ia_checks:
        ok = check_file_contains(file_path, text, description)
        results['code'].append(ok)
    
    # ==================== 6️⃣ DÉPENDANCES ====================
    print("\n" + "-"*70)
    print("6️⃣ DÉPENDANCES VERSIONS")
    print("-"*70)
    
    dep_checks = [
        ('gpt/requirements.txt', 'torch==2.5.1', 'PyTorch 2.5.1 (correct)'),
        ('gpt/requirements.txt', 'transformers==4.41.0', 'Transformers 4.41.0'),
        ('chat/requirements.txt', 'Flask', 'Flask installé'),
        ('chat/requirements.txt', 'Flask-SocketIO', 'Flask-SocketIO installé'),
    ]
    
    for file_path, text, description in dep_checks:
        ok = check_file_contains(file_path, text, description)
        results['code'].append(ok)
    
    # ==================== RÉSUMÉ ====================
    print("\n" + "="*70)
    print("📊 RÉSUMÉ VÉRIFICATION")
    print("="*70)
    
    total_checks = len(results['files']) + len(results['code']) + len(results['config'])
    passed_checks = sum(results['files']) + sum(results['code']) + sum(results['config'])
    
    print(f"\nFichiers: {sum(results['files'])}/{len(results['files'])} ✓")
    print(f"Code: {sum(results['code'])}/{len(results['code'])} ✓")
    print(f"Config: {sum(results['config'])}/{len(results['config'])} ✓")
    print(f"\nTotal: {passed_checks}/{total_checks} ✓")
    
    if passed_checks == total_checks:
        print("\n✅ ✅ ✅ TOUS LES CONTRÔLES PASSÉS! ✅ ✅ ✅")
        print("\n🚀 PRÊT POUR PRODUCTION!")
        print("\nEtapes pour lancer:")
        print("  1. docker-compose build")
        print("  2. docker-compose up -d")
        print("  3. Attendre ~30s pour que les services démarrent")
        print("  4. Accéder à http://localhost:5001 pour le chat")
        return 0
    else:
        print(f"\n⚠️ {total_checks - passed_checks} vérifications échouées")
        print("   Corriger les éléments marqués ❌ avant le déploiement")
        return 1


if __name__ == '__main__':
    exit(main())
