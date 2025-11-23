#!/usr/bin/env python3
"""
Script de vérification - Vérifie que tous les fichiers sont en place
"""

import os
import sys
from pathlib import Path

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def check_file(path, description):
    """Vérifie un fichier"""
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"{GREEN}✅{END} {description:50} ({size:,} bytes)")
        return True
    else:
        print(f"{RED}❌{END} {description:50} MANQUANT")
        return False

def check_dir(path, description):
    """Vérifie un répertoire"""
    if os.path.isdir(path):
        print(f"{GREEN}✅{END} {description:50}")
        return True
    else:
        print(f"{RED}❌{END} {description:50} MANQUANT")
        return False

def main():
    print(f"\n{BLUE}{'='*70}{END}")
    print(f"{BLUE}🔍 VÉRIFICATION COMPLÈTE - Système Diagnostic Frigorifique{END}")
    print(f"{BLUE}{'='*70}{END}\n")
    
    all_ok = True
    
    # Vérifier structure dossiers
    print(f"{YELLOW}📁 STRUCTURE DE DOSSIERS{END}")
    print("-" * 70)
    all_ok &= check_dir("data", "Dossier données")
    all_ok &= check_dir("logs", "Dossier logs")
    all_ok &= check_dir("models", "Dossier modèles")
    all_ok &= check_dir("services", "Dossier services")
    all_ok &= check_dir("utils", "Dossier utilitaires")
    all_ok &= check_dir("tests", "Dossier tests")
    
    # Vérifier fichiers configuration
    print(f"\n{YELLOW}🔧 FICHIERS CONFIGURATION{END}")
    print("-" * 70)
    all_ok &= check_file("app.py", "Application Flask principale")
    all_ok &= check_file("config.py", "Configuration centralisée")
    all_ok &= check_file("requirements.txt", "Dépendances Python")
    all_ok &= check_file(".env.example", "Template environnement")
    if os.path.exists(".env"):
        all_ok &= check_file(".env", "Fichier environnement (local)")
    else:
        print(f"{YELLOW}⚠️ {'.env':50} À CRÉER (copier depuis .env.example){END}")
    
    # Vérifier services
    print(f"\n{YELLOW}🤖 SERVICES IA{END}")
    print("-" * 70)
    all_ok &= check_file("services/__init__.py", "Init package services")
    all_ok &= check_file("services/agent_ia.py", "Service Agent IA")
    all_ok &= check_file("services/gemini_service.py", "Service Gemini (NEW)")
    all_ok &= check_file("services/telegram_service.py", "Service Telegram")
    all_ok &= check_file("services/apprentissage_service.py", "Service Apprentissage (NEW)")
    
    # Vérifier utilities
    print(f"\n{YELLOW}🛠️  UTILITAIRES{END}")
    print("-" * 70)
    all_ok &= check_file("utils/__init__.py", "Init package utils")
    all_ok &= check_file("utils/validation.py", "Validation données")
    all_ok &= check_file("utils/helpers.py", "Fonctions helpers")
    
    # Vérifier outils
    print(f"\n{YELLOW}🎮 OUTILS & SCRIPTS{END}")
    print("-" * 70)
    all_ok &= check_file("simulateur.py", "Simulateur capteurs (NEW)")
    all_ok &= check_file("init_data.py", "Script initialisation")
    all_ok &= check_file("quick_start.md", "Guide démarrage rapide")
    
    # Vérifier documentation
    print(f"\n{YELLOW}📚 DOCUMENTATION{END}")
    print("-" * 70)
    all_ok &= check_file("README.md", "Documentation principale")
    all_ok &= check_file("SETUP.md", "Guide setup (NEW)")
    all_ok &= check_file("IMPLEMENTATION_SUMMARY.md", "Résumé implémentation (NEW)")
    all_ok &= check_file("LIVRABLES_FINAUX.md", "Livrables finaux (NEW)")
    all_ok &= check_file("00_COMMENCER_ICI.md", "Point de départ (NEW)")
    
    # Vérifier données
    print(f"\n{YELLOW}📊 FICHIERS DONNÉES (après init_data.py){END}")
    print("-" * 70)
    if os.path.exists("data/compteur_apprentissage.json"):
        all_ok &= check_file("data/compteur_apprentissage.json", "Compteur apprentissage")
    else:
        print(f"{YELLOW}ℹ️  {'data/compteur_apprentissage.json':50} (généré lors de init_data.py){END}")
    
    if os.path.exists("data/dataset_apprentissage.csv"):
        all_ok &= check_file("data/dataset_apprentissage.csv", "Dataset apprentissage")
    else:
        print(f"{YELLOW}ℹ️  {'data/dataset_apprentissage.csv':50} (généré lors de init_data.py){END}")
    
    if os.path.exists("data/dernier_diagnostic.json"):
        all_ok &= check_file("data/dernier_diagnostic.json", "Dernier diagnostic")
    else:
        print(f"{YELLOW}ℹ️  {'data/dernier_diagnostic.json':50} (généré lors de init_data.py){END}")
    
    # Résumé
    print(f"\n{BLUE}{'='*70}{END}")
    
    if all_ok:
        print(f"{GREEN}✅ TOUS LES FICHIERS REQUIS SONT PRÉSENTS !{END}")
        print(f"\n{BLUE}🚀 PROCHAINES ÉTAPES :{END}")
        print(f"   1. {YELLOW}Éditer .env{END} avec vos credentials")
        print(f"   2. {YELLOW}python init_data.py{END} - Initialiser les données")
        print(f"   3. {YELLOW}python app.py{END} - Lancer l'API (Terminal 1)")
        print(f"   4. {YELLOW}python simulateur.py{END} - Simulateur (Terminal 2)")
        print(f"\n   📖 Voir {YELLOW}SETUP.md{END} pour guide détaillé")
        return 0
    else:
        print(f"{RED}❌ CERTAINS FICHIERS SONT MANQUANTS !{END}")
        print(f"\n{YELLOW}À FAIRE :{END}")
        print(f"   1. Vérifier les fichiers marqués ❌")
        print(f"   2. Relancer les scripts de création")
        print(f"   3. Vérifier les permissions d'accès")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"{RED}❌ Erreur vérification: {e}{END}")
        sys.exit(1)
