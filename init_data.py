"""
Script d'initialisation du projet
Crée les dossiers et fichiers nécessaires
"""

import os
import json
from config import Config

def init_projet():
    """Initialise la structure du projet"""
    
    print("🚀 Initialisation du Système de Diagnostic Frigorifique")
    print("=" * 60)
    
    # 1. Créer le dossier data
    print("\n📁 Création des dossiers...")
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    print(f"✅ {Config.DATA_DIR}/ créé")
    
    # 2. Créer le fichier compteur
    print("\n📊 Initialisation du compteur d'apprentissage...")
    compteur_initial = {
        'total': 0,
        'par_panne': {},
        'nouvelles_pannes': {},
        'seuil': Config.SEUIL_RETRAINING,
        'created_at': '2025-01-01T00:00:00Z'
    }
    
    with open(Config.COMPTEUR_FILE, 'w') as f:
        json.dump(compteur_initial, f, indent=2)
    print(f"✅ {Config.COMPTEUR_FILE} créé")
    
    # 3. Créer le fichier dataset avec header
    print("\n📈 Initialisation du dataset...")
    header = 'Température,Pression_BP,Pression_HP,Courant,Tension,Humidité,Débit_air,Vibration,Label,Type_Panne,Timestamp\n'
    
    with open(Config.DATASET_FILE, 'w') as f:
        f.write(header)
    print(f"✅ {Config.DATASET_FILE} créé")
    
    # 4. Créer un diagnostic initial vide
    print("\n💾 Initialisation du dernier diagnostic...")
    diagnostic_initial = {
        'diagnostic_id': 'DIAG_INIT',
        'timestamp': '2025-01-01T00:00:00Z',
        'message': 'Système initialisé'
    }
    
    with open(Config.DERNIER_DIAGNOSTIC_FILE, 'w') as f:
        json.dump(diagnostic_initial, f, indent=2)
    print(f"✅ {Config.DERNIER_DIAGNOSTIC_FILE} créé")
    
    # 5. Vérifier le fichier .env
    print("\n🔐 Vérification de la configuration...")
    if not os.path.exists('.env'):
        print("⚠️  Fichier .env non trouvé !")
        print("   Copie .env.example vers .env et configure tes credentials")
        print("\n   cp .env.example .env")
        print("   # Puis édite .env avec tes clés API")
    else:
        print("✅ Fichier .env trouvé")
        
        # Vérifier les variables critiques
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        
        if not gemini_key or gemini_key == 'AIzaSy...VotreClÃ©Ici':
            print("⚠️  GEMINI_API_KEY non configuré")
        else:
            print("✅ GEMINI_API_KEY configuré")
        
        if not telegram_token:
            print("⚠️  TELEGRAM_BOT_TOKEN non configuré")
        else:
            print("✅ TELEGRAM_BOT_TOKEN configuré")
    
    # 6. Résumé
    print("\n" + "=" * 60)
    print("✅ Initialisation terminée !")
    print("=" * 60)
    
    print("\n📋 Prochaines étapes:")
    print("   1. Configure ton fichier .env avec tes credentials")
    print("   2. Lance l'application: python app.py")
    print("   3. Teste avec le simulateur: python simulateur.py")
    
    print("\n💡 Aide:")
    print("   Documentation: README.md")
    print("   Tests: python simulateur.py --mode stress --iterations 10")


if __name__ == '__main__':
    try:
        init_projet()
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        exit(1)