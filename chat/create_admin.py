#!/usr/bin/env python3
"""Script simple pour créer l'utilisateur admin"""

import sys
from pathlib import Path

# Ajouter le répertoire chat au chemin
sys.path.insert(0, str(Path(__file__).parent))

from app_web import app, db, User

import os

# Vérifier si on doit utiliser la DB
if os.getenv("USE_DB", "true").lower() != "true":
    print("⚠️ USE_DB=false -> Initialisation de la base ignorée")
    exit(0)


def create_admin():
    with app.app_context():
        try:
            # Créer toutes les tables
            print("🗄️  Création des tables...")
            db.create_all()
            print("✅ Tables créées")
            
            # Chercher admin existant
            admin = User.query.filter_by(email='admin@example.com').first()
            
            if admin:
                print("⚠️  Admin existe, suppression...")
                db.session.delete(admin)
                db.session.commit()
            
            # Créer nouvel admin
            print("👤 Création du nouvel admin...")
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            print("\n✅ SUCCÈS!")
            print("━" * 50)
            print("📧 Email: admin@example.com")
            print("🔐 Mot de passe: admin123")
            print("━" * 50)
            print("\nTu peux maintenant te connecter!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_admin()
    sys.exit(0 if success else 1)
