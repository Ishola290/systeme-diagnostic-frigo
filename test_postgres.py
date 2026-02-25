"""
Script de test de connexion PostgreSQL
Vérifie que la connexion à Render fonctionne correctement
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_postgres import is_postgres_enabled, get_db_url, init_db, get_connection

def test_postgres_setup():
    """Test complet de la configuration PostgreSQL"""
    print("=" * 60)
    print("🔍 TEST DE CONNEXION POSTGRESQL")
    print("=" * 60)
    
    # 1. Vérifier que DATABASE_URL est chargé
    db_url = get_db_url()
    if db_url:
        # Masquer le mot de passe pour l'affichage
        masked_url = db_url.replace(db_url.split(':')[2].split('@')[0], '***')
        print(f"✅ DATABASE_URL trouvé: {masked_url}")
    else:
        print("❌ DATABASE_URL non défini")
        return False
    
    # 2. Vérifier que PostgreSQL est disponible
    if is_postgres_enabled():
        print("✅ PostgreSQL est activé")
    else:
        print("❌ PostgreSQL n'est pas activé (psycopg2 manquant?)")
        return False
    
    # 3. Tester la connexion
    print("\n📡 Test de connexion à la base de données...")
    conn = get_connection()
    if conn:
        print("✅ Connexion réussie!")
        conn.close()
    else:
        print("❌ Échec de connexion")
        return False
    
    # 4. Initialiser les tables
    print("\n🗄️ Initialisation des tables...")
    init_db()
    print("✅ Tables initialisées!")
    
    print("\n" + "=" * 60)
    print("🎉 POSTGRESQL EST COMPLÈTEMENT CONFIGURÉ!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_postgres_setup()
    sys.exit(0 if success else 1)
