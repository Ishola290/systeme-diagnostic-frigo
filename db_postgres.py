"""
Module de persistance PostgreSQL commune
Utilisé par app.py, gpt/ia_service.py et chat/app_web.py
Fallback sur fichiers si DATABASE_URL non défini
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"✅ Variables d'environnement chargées depuis {env_path}")
    else:
        load_dotenv()  # Chercher dans le dossier courant
except ImportError:
    logger.debug("python-dotenv non installé, utilisation des variables système")

# Flag de disponibilité Postgres
DB_AVAILABLE = False
conn_pool = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    DB_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ psycopg2 non installé - mode fichiers uniquement")
    DB_AVAILABLE = False


def get_db_url() -> Optional[str]:
    """Récupère DATABASE_URL depuis les variables d'environnement"""
    return os.environ.get('DATABASE_URL')


def is_postgres_enabled() -> bool:
    """Vérifie si Postgres est disponible et configuré"""
    if not DB_AVAILABLE:
        return False
    return get_db_url() is not None


def get_connection():
    """Obtient une connexion à la base de données avec SSL pour Render"""
    if not is_postgres_enabled():
        return None
    
    try:
        db_url = get_db_url()
        # Ajouter sslmode=require pour Render PostgreSQL
        if 'sslmode' not in db_url:
            db_url += '&sslmode=require' if '?' in db_url else '?sslmode=require'
        
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"❌ Erreur connexion Postgres: {e}")
        return None


def init_tables():
    """Crée les tables si elles n'existent pas"""
    if not is_postgres_enabled():
        logger.info("ℹ️ Postgres désactivé - tables non créées")
        return
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            # Table diagnostics
            cur.execute("""
                CREATE TABLE IF NOT EXISTS diagnostics (
                    id SERIAL PRIMARY KEY,
                    diagnostic_id VARCHAR(255) UNIQUE,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    panne_detectee BOOLEAN DEFAULT FALSE,
                    type_panne VARCHAR(255),
                    score_confiance DOUBLE PRECISION DEFAULT 0,
                    donnees_capteurs JSONB DEFAULT '{}',
                    prediction_ia JSONB DEFAULT '{}',
                    apprentissage JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Index sur diagnostic_id et timestamp
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_diagnostics_id 
                ON diagnostics(diagnostic_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_diagnostics_timestamp 
                ON diagnostics(timestamp DESC)
            """)
            
            # Table alerts
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(255) UNIQUE,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    severity VARCHAR(50) DEFAULT 'medium',
                    title TEXT,
                    message TEXT,
                    payload JSONB DEFAULT '{}',
                    source VARCHAR(100) DEFAULT 'system',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Index sur alert_id et timestamp
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_id 
                ON alerts(alert_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                ON alerts(timestamp DESC)
            """)
            
            # Table pannes (pour sauvegarder chaque panne individuellement)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pannes (
                    id SERIAL PRIMARY KEY,
                    panne_id VARCHAR(255) UNIQUE,
                    diagnostic_id VARCHAR(255),
                    alert_id VARCHAR(255),
                    panne_name VARCHAR(255),
                    score DOUBLE PRECISION DEFAULT 0,
                    type VARCHAR(100) DEFAULT 'Inconnu',
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    localisation VARCHAR(255) DEFAULT 'Inconnue',
                    severity VARCHAR(50) DEFAULT 'medium',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Index sur panne_id et diagnostic_id
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_pannes_id 
                ON pannes(panne_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_pannes_diagnostic_id 
                ON pannes(diagnostic_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_pannes_timestamp 
                ON pannes(timestamp DESC)
            """)
            
    except Exception as e:
        logger.error(f"❌ Erreur création tables: {e}")
    finally:
        conn.close()


# ==================== DIAGNOSTICS ====================

def save_diagnostic(diagnostic_data: Dict) -> bool:
    """
    Sauvegarde un diagnostic dans Postgres (si disponible)
    Retourne True si succès, False sinon (fallback fichiers géré par l'appelant)
    """
    if not is_postgres_enabled():
        return False
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO diagnostics 
                (diagnostic_id, timestamp, panne_detectee, type_panne, score_confiance, 
                 donnees_capteurs, prediction_ia, apprentissage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (diagnostic_id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    panne_detectee = EXCLUDED.panne_detectee,
                    type_panne = EXCLUDED.type_panne,
                    score_confiance = EXCLUDED.score_confiance,
                    donnees_capteurs = EXCLUDED.donnees_capteurs,
                    prediction_ia = EXCLUDED.prediction_ia,
                    apprentissage = EXCLUDED.apprentissage
            """, (
                diagnostic_data.get('diagnostic_id'),
                diagnostic_data.get('timestamp', datetime.now().isoformat()),
                diagnostic_data.get('panne_detectee', False),
                diagnostic_data.get('prediction_ia', {}).get('panne_detectee'),
                diagnostic_data.get('prediction_ia', {}).get('score', 0),
                Json(diagnostic_data.get('donnees_capteurs', {})),
                Json(diagnostic_data.get('prediction_ia', {})),
                Json(diagnostic_data.get('apprentissage', {}))
            ))
            conn.commit()
            logger.info(f"✅ Diagnostic sauvegardé en DB: {diagnostic_data.get('diagnostic_id')}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde diagnostic DB: {e}")
        return False
    finally:
        conn.close()


def get_latest_diagnostic() -> Optional[Dict]:
    """
    Récupère le dernier diagnostic depuis Postgres
    Retourne None si pas de DB ou si erreur
    """
    if not is_postgres_enabled():
        return None
    
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM diagnostics 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            result = cur.fetchone()
            if result:
                # Convertir les JSONB en dict Python
                result['donnees_capteurs'] = result['donnees_capteurs'] if result['donnees_capteurs'] else {}
                result['prediction_ia'] = result['prediction_ia'] if result['prediction_ia'] else {}
                result['apprentissage'] = result['apprentissage'] if result['apprentissage'] else {}
                return dict(result)
            return None
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération dernier diagnostic: {e}")
        return None
    finally:
        conn.close()


def get_diagnostics_stats() -> Dict:
    """Récupère les statistiques des diagnostics depuis Postgres"""
    if not is_postgres_enabled():
        return {}
    
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE panne_detectee = TRUE) as pannes_detectees,
                    COUNT(DISTINCT type_panne) as types_pannes_distincts
                FROM diagnostics
            """)
            return dict(cur.fetchone())
            
    except Exception as e:
        logger.error(f"❌ Erreur stats diagnostics: {e}")
        return {}
    finally:
        conn.close()


# ==================== ALERTS ====================

def save_alert(alert_data: Dict) -> bool:
    """Sauvegarde une alerte dans Postgres"""
    if not is_postgres_enabled():
        return False
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO alerts 
                (alert_id, timestamp, severity, title, message, payload, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (alert_id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    severity = EXCLUDED.severity,
                    title = EXCLUDED.title,
                    message = EXCLUDED.message,
                    payload = EXCLUDED.payload,
                    source = EXCLUDED.source
            """, (
                alert_data.get('alert_id'),
                alert_data.get('timestamp', datetime.now().isoformat()),
                alert_data.get('severity', 'medium'),
                alert_data.get('title', ''),
                alert_data.get('message', ''),
                Json(alert_data.get('payload', {})),
                alert_data.get('source', 'system')
            ))
            conn.commit()
            logger.info(f"✅ Alerte sauvegardée en DB: {alert_data.get('alert_id')}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde alerte DB: {e}")
        return False
    finally:
        conn.close()


def get_alerts(limit: int = 10, severity: Optional[str] = None) -> List[Dict]:
    """Récupère les alertes depuis Postgres"""
    if not is_postgres_enabled():
        return []
    
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if severity:
                cur.execute("""
                    SELECT * FROM alerts 
                    WHERE severity = %s
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (severity, limit))
            else:
                cur.execute("""
                    SELECT * FROM alerts 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (limit,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération alertes: {e}")
        return []
    finally:
        conn.close()


def get_alerts_stats() -> Dict:
    """Récupère les statistiques des alertes"""
    if not is_postgres_enabled():
        return {}
    
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
                    COUNT(*) FILTER (WHERE severity = 'high') as high_alerts
                FROM alerts
            """)
            return dict(cur.fetchone())
            
    except Exception as e:
        logger.error(f"❌ Erreur stats alertes: {e}")
        return {}
    finally:
        conn.close()


def save_panne(panne_data: Dict) -> bool:
    """
    Sauvegarde une panne individuelle dans Postgres (si disponible)
    Retourne True si succès, False sinon (fallback fichiers géré par l'appelant)
    """
    if not is_postgres_enabled():
        return False
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pannes 
                (panne_id, diagnostic_id, alert_id, panne_name, score, type, timestamp, localisation, severity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (panne_id) DO UPDATE SET
                    diagnostic_id = EXCLUDED.diagnostic_id,
                    alert_id = EXCLUDED.alert_id,
                    panne_name = EXCLUDED.panne_name,
                    score = EXCLUDED.score,
                    type = EXCLUDED.type,
                    timestamp = EXCLUDED.timestamp,
                    localisation = EXCLUDED.localisation,
                    severity = EXCLUDED.severity
            """, (
                panne_data.get('panne_id'),
                panne_data.get('diagnostic_id'),
                panne_data.get('alert_id'),
                panne_data.get('panne_name'),
                panne_data.get('score', 0),
                panne_data.get('type', 'Inconnu'),
                panne_data.get('timestamp', datetime.now().isoformat()),
                panne_data.get('localisation', 'Inconnue'),
                panne_data.get('severity', 'medium')
            ))
            conn.commit()
            logger.info(f"✅ Panne sauvegardée en DB: {panne_data.get('panne_id')} - {panne_data.get('panne_name')}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde panne DB: {e}")
        return False
    finally:
        conn.close()


def get_pannes(diagnostic_id: str = None, limit: int = 10) -> List[Dict]:
    """
    Récupère les pannes depuis Postgres
    Si diagnostic_id est fourni, filtre par diagnostic
    """
    if not is_postgres_enabled():
        return []
    
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if diagnostic_id:
                cur.execute("""
                    SELECT * FROM pannes 
                    WHERE diagnostic_id = %s
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (diagnostic_id, limit))
            else:
                cur.execute("""
                    SELECT * FROM pannes 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (limit,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération pannes: {e}")
        return []
    finally:
        conn.close()
def init_db():
    """Initialise la base de données (tables)"""
    if is_postgres_enabled():
        init_tables()
    else:
        logger.info("ℹ️ Mode fichiers - pas d'initialisation Postgres")


# Appel d'initialisation
init_db()
