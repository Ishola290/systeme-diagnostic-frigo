"""
Script de migration SQLite → PostgreSQL
Lance les migrations avec Alembic et initialise les données
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Effectue les migrations PostgreSQL"""
    
    # Vérifier que les env vars sont configurées
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL n'est pas défini!")
        logger.info("Pour PostgreSQL local, configurer:")
        logger.info("  export DATABASE_URL=postgresql://user:password@localhost/chat_app")
        sys.exit(1)
    
    if 'postgresql' not in db_url:
        logger.error("❌ DATABASE_URL doit utiliser postgresql://")
        sys.exit(1)
    
    logger.info(f"📊 Connexion à PostgreSQL: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    # Importer après vérification de DATABASE_URL
    from app_web import app, db
    
    with app.app_context():
        try:
            # Tester la connexion
            from sqlalchemy import text
            with db.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Connexion PostgreSQL réussie!")
            
            # Créer les tables
            logger.info("📝 Création des schémas...")
            db.create_all()
            logger.info("✅ Schémas créés/vérifiés!")
            
            # Initialiser l'admin (optionnel)
            from app_web import User
            admin_exists = User.query.filter_by(username='admin').first()
            if not admin_exists:
                logger.info("👤 Création utilisateur admin...")
                admin = User(
                    username='admin',
                    email='admin@frigo.local',
                    is_admin=True
                )
                admin.set_password('admin123')  # À changer en production!
                db.session.add(admin)
                db.session.commit()
                logger.info("✅ Utilisateur admin créé (login: admin / mot de passe: admin123)")
            else:
                logger.info("ℹ️  Utilisateur admin existe déjà")
            
            logger.info("🎉 Migration PostgreSQL complétée!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la migration: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
