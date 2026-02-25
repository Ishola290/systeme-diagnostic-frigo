-- Script d'initialisation PostgreSQL pour Chat App
-- Crée les schémas et rôles de base

-- Créer des extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Pour les recherches texte

-- Créer un utilisateur avec permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'frigo_user') THEN
        CREATE USER frigo_user WITH PASSWORD 'frigo_secure_pass_change_me';
    END IF;
END
$$;

-- Permissions
GRANT CONNECT ON DATABASE chat_app TO frigo_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO frigo_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO frigo_user;

COMMIT;
