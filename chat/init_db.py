"""
Script d'initialisation de la base de données et création d'un utilisateur admin
"""

from app_web import app, db, User
import sys
import os

import os

# Vérifier si on doit utiliser la DB
if os.getenv("USE_DB", "true").lower() != "true":
    print("⚠️ USE_DB=false -> Initialisation de la base ignorée")
    exit(0)


def init_database():
    """Créer les tables de la base de données"""
    with app.app_context():
        print("🗄️  Création des tables...")
        db.create_all()
        print("✅ Tables créées avec succès!")

def create_admin_user(username='admin', password='admin123', email='admin@example.com'):
    """Créer un utilisateur admin"""
    with app.app_context():
        # Vérifier si l'utilisateur existe déjà par username
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"⚠️  L'utilisateur '{username}' existe déjà")
            print(f"   Email: {existing_user.email}")
            return False
        
        # Vérifier aussi par email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"⚠️  L'email '{email}' existe déjà")
            return False
        
        # Créer l'admin
        admin = User(
            username=username,
            email=email,
            is_admin=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Utilisateur admin créé!")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   Mot de passe: {password}")
        return True

def main():
    print("=" * 50)
    print("🍺 Initialisation - Diagnostic Frigo Chat")
    print("=" * 50)
    
    # Initialiser la base de données
    init_database()
    
    # Créer l'utilisateur admin
    create_admin_user()
    
    print("\n" + "=" * 50)
    print("✅ Initialisation terminée!")
    print("=" * 50)
    print("\n📝 Prochaines étapes:")
    print("1. Copier .env.example en .env et configurer les variables")
    print("2. Lancer le serveur: python app_web.py")
    print("3. Accéder à http://localhost:5001")
    print("\n")

if __name__ == '__main__':
    main()
