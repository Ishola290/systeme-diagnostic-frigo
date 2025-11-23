#!/usr/bin/env python3
"""
Script pour réinitialiser complètement la base de données et l'utilisateur admin
Utilise ceci si tu as des problèmes de login
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire chat au chemin
chat_dir = Path(__file__).parent
sys.path.insert(0, str(chat_dir))

from app_web import app, db, User
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def reset_database():
    """Réinitialiser complètement la base de données"""
    with app.app_context():
        logger.info("\n🗑️  Suppression de la base de données...")
        
        # Supprimer le fichier database
        db_path = chat_dir / "instance" / "chat_app.db"
        if db_path.exists():
            db_path.unlink()
            logger.info(f"✅ Base de données supprimée: {db_path}")
        else:
            logger.info(f"ℹ Pas de base de données trouvée à: {db_path}")
        
        logger.info("\n🗄️  Création des nouvelles tables...")
        db.create_all()
        logger.info("✅ Nouvelles tables créées")

def create_admin():
    """Créer l'utilisateur admin par défaut"""
    with app.app_context():
        logger.info("\n👤 Création de l'utilisateur admin...")
        
        # Vérifier si admin existe
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.warning("⚠️  Admin existe déjà, suppression...")
            db.session.delete(admin)
            db.session.commit()
        
        # Créer le nouvel admin
        new_admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        new_admin.set_password('admin123')
        
        db.session.add(new_admin)
        db.session.commit()
        
        logger.info("✅ Utilisateur admin créé!")
        logger.info(f"   Email: admin@example.com")
        logger.info(f"   Mot de passe: admin123")

def verify_admin():
    """Vérifier que l'admin existe et fonctionne"""
    with app.app_context():
        logger.info("\n✔️  Vérification de l'admin...")
        
        admin = User.query.filter_by(email='admin@example.com').first()
        
        if not admin:
            logger.error("❌ Admin introuvable!")
            return False
        
        logger.info(f"✅ Admin trouvé:")
        logger.info(f"   Username: {admin.username}")
        logger.info(f"   Email: {admin.email}")
        logger.info(f"   Is Admin: {admin.is_admin}")
        
        # Tester le mot de passe
        if admin.check_password('admin123'):
            logger.info("✅ Mot de passe correct!")
            return True
        else:
            logger.error("❌ Mot de passe incorrect!")
            return False

def main():
    print("\n" + "="*60)
    print("🔄 RÉINITIALISATION COMPLÈTE - DIAGNOSTIC FRIGO CHAT")
    print("="*60)
    
    try:
        # Réinitialiser
        reset_database()
        
        # Créer admin
        create_admin()
        
        # Vérifier
        if verify_admin():
            logger.info("\n" + "="*60)
            logger.info("✅ BASE DE DONNÉES RÉINITIALISÉE AVEC SUCCÈS!")
            logger.info("="*60)
            logger.info("\n🚀 Tu peux maintenant redémarrer l'app:")
            logger.info("   python app_web.py")
            logger.info("\n📝 Login avec:")
            logger.info("   Email: admin@example.com")
            logger.info("   Mot de passe: admin123")
            logger.info("="*60 + "\n")
            return 0
        else:
            logger.error("\n❌ Vérification échouée!")
            return 1
            
    except Exception as e:
        logger.error(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
