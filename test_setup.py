"""
Script de test pour vérifier que la configuration est correcte
"""

import os
import sys
import json

def test_imports():
    """Tester les imports"""
    print("🔍 Test des imports...")
    
    try:
        # Test import chat_integration
        from chat_integration import ChatWebIntegration, init_chat_integration
        print("  ✅ chat_integration OK")
    except ImportError as e:
        print(f"  ❌ chat_integration ERROR: {e}")
        return False
    
    # Vérifier que le dossier chat existe
    if not os.path.exists('chat'):
        print("  ❌ Dossier chat/ n'existe pas")
        return False
    print("  ✅ Dossier chat/ OK")
    
    # Vérifier les fichiers essentiels
    required_files = [
        'chat/app_web.py',
        'chat/config.py',
        'chat/requirements.txt',
        'chat/init_db.py',
        'chat/templates/login.html',
        'chat/templates/dashboard.html',
        'chat/static/style.css',
        'chat/static/dashboard.js'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"  ❌ Fichier manquant: {file}")
            return False
    
    print("  ✅ Tous les fichiers OK")
    return True

def test_requirements():
    """Tester les requirements"""
    print("\n📦 Vérification des dépendances...")
    
    required = [
        'Flask',
        'flask-socketio',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'requests'
    ]
    
    try:
        import importlib
        for package in required:
            try:
                importlib.import_module(package.lower().replace('-', '_'))
                print(f"  ✅ {package} OK")
            except ImportError:
                print(f"  ⚠️  {package} NOT INSTALLED (installez avec: pip install -r chat/requirements.txt)")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False
    
    return True

def test_configuration():
    """Tester la configuration"""
    print("\n⚙️  Vérification de la configuration...")
    
    # Vérifier .env
    if not os.path.exists('chat/.env'):
        print("  ⚠️  chat/.env n'existe pas")
        print("     Créer avec: Copy-Item chat/.env.example chat/.env")
    else:
        print("  ✅ chat/.env existe")
    
    # Vérifier .env.example
    if os.path.exists('chat/.env.example'):
        print("  ✅ chat/.env.example existe")
    else:
        print("  ❌ chat/.env.example manquant")
        return False
    
    return True

def test_database():
    """Tester la base de données"""
    print("\n🗄️  Vérification de la base de données...")
    
    try:
        import sqlite3
        print("  ✅ SQLite disponible")
        
        # Vérifier si init_db.py peut être exécuté
        if os.path.exists('chat/init_db.py'):
            print("  ✅ init_db.py existe")
            print("  ℹ️  Exécutez: cd chat && python init_db.py")
        else:
            print("  ❌ init_db.py manquant")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Erreur BD: {e}")
        return False

def test_structure():
    """Tester la structure des fichiers"""
    print("\n📁 Vérification de la structure...")
    
    directories = [
        'chat/templates',
        'chat/static'
    ]
    
    for dir_name in directories:
        if os.path.isdir(dir_name):
            print(f"  ✅ {dir_name} existe")
            # Lister les fichiers
            files = os.listdir(dir_name)
            for file in files:
                print(f"      └─ {file}")
        else:
            print(f"  ❌ {dir_name} manquant")
            return False
    
    return True

def main():
    print("=" * 60)
    print("🍺 TEST DE CONFIGURATION - Chat Web Diagnostic Frigo")
    print("=" * 60)
    
    results = {
        'imports': test_imports(),
        'requirements': test_requirements(),
        'configuration': test_configuration(),
        'database': test_database(),
        'structure': test_structure(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ OK" if result else "❌ ERREUR"
        print(f"  {test_name.upper()}: {status}")
    
    if all(results.values()):
        print("\n" + "=" * 60)
        print("✨ TOUT EST PRÊT! 🎉")
        print("=" * 60)
        print("\n🚀 Prochaines étapes:\n")
        print("1. Installer les dépendances:")
        print("   cd chat")
        print("   pip install -r requirements.txt\n")
        print("2. Initialiser la base de données:")
        print("   python init_db.py\n")
        print("3. Démarrer le serveur:")
        print("   python app_web.py\n")
        print("4. Ouvrir dans le navigateur:")
        print("   http://localhost:5001\n")
        print("5. Se connecter avec:")
        print("   Username: admin")
        print("   Password: admin123\n")
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠️  DES ERREURS ONT ÉTÉ DÉTECTÉES")
        print("=" * 60)
        print("\nVeuillez corriger les problèmes ci-dessus\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
