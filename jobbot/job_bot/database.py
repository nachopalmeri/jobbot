import sqlite3
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional

# ImportaciÃ³n condicional para Postgres
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


def _looks_like_password_hash(value: str) -> bool:
    return value.startswith("$pbkdf2-sha256$") or value.startswith("$2")


def _ensure_password_hash(password_or_hash: str) -> str:
    if not password_or_hash or _looks_like_password_hash(password_or_hash):
        return password_or_hash

    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(
            schemes=["pbkdf2_sha256", "bcrypt"],
            deprecated="auto",
        )
        return pwd_context.hash(password_or_hash)
    except Exception:
        return password_or_hash


class Database:
    """Maneja las operaciones de base de datos (SQLite o PostgreSQL).

    Permite inyectar parÃ¡metros opcionales en tests (por ejemplo, un path
    de SQLite temporal) pero sigue utilizando config.py por defecto en
    producciÃ³n.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        db_type: Optional[str] = None,
        pg_url: Optional[str] = None,
    ):
        try:
            import config  # EjecuciÃ³n directa desde job_bot/
        except ImportError:
            from job_bot import config  # Import como paquete job_bot.database

        # Valores por defecto desde config, sobreescribibles en tests
        self.db_type = (db_type or config.DATABASE_TYPE).lower()
        self.db_path = db_path or config.DATABASE_PATH
        self.pg_url = pg_url or config.DATABASE_URL
        self._sqlite_memory_conn = None

        if self.db_type == "supabase" and not POSTGRES_AVAILABLE:
            logger.error(
                "âŒ 'psycopg2' no estÃ¡ instalado. ReinstalÃ¡ con: pip install psycopg2-binary"
            )
            self.db_type = "sqlite"

        self._init_db()

    def close(self):
        """Cierra conexiones persistentes abiertas por la instancia."""
        if self._sqlite_memory_conn is not None:
            try:
                self._sqlite_memory_conn.close()
            except Exception:
                pass
            finally:
                self._sqlite_memory_conn = None

    def __del__(self):
        self.close()

    def _get_conn(self):
        """Retorna una conexiÃ³n activa segÃºn el motor configurado."""
        if self.db_type == "supabase":
            conn = psycopg2.connect(self.pg_url, cursor_factory=RealDictCursor)
            conn.autocommit = True
            return conn
        else:
            if self.db_path == ":memory:":
                if self._sqlite_memory_conn is None:
                    self._sqlite_memory_conn = sqlite3.connect(":memory:")
                    self._sqlite_memory_conn.row_factory = sqlite3.Row
                    self._sqlite_memory_conn.execute("PRAGMA journal_mode=WAL")
                return self._sqlite_memory_conn
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            return conn

    def _execute(self, query: str, params: tuple = ()):
        """Ejecuta un comando que no retorna filas."""
        if self.db_type == "supabase":
            query = query.replace("?", "%s")
            # Manejo de INSERT OR IGNORE para Postgres
            if "INSERT OR IGNORE" in query:
                query = query.replace("INSERT OR IGNORE", "INSERT")
                if "users" in query:
                    query += " ON CONFLICT (telegram_id) DO NOTHING"
                elif "keywords" in query:
                    query += " ON CONFLICT (telegram_id, keyword) DO NOTHING"
                elif "jobs_seen" in query:
                    query += " ON CONFLICT (job_hash, telegram_id) DO NOTHING"

            conn = self._get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
            finally:
                conn.close()
        else:
            conn = self._get_conn()
            try:
                if self.db_path == ":memory:":
                    conn.execute(query, params)
                    conn.commit()
                else:
                    with conn:
                        conn.execute(query, params)
            finally:
                if self.db_path != ":memory:":
                    conn.close()

    def _fetchone(self, query: str, params: tuple = ()):
        """Retorna una sola fila como dict."""
        if self.db_type == "supabase":
            query = query.replace("?", "%s")
            conn = self._get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchone()
            finally:
                conn.close()
        else:
            conn = self._get_conn()
            try:
                if self.db_path == ":memory:":
                    row = conn.execute(query, params).fetchone()
                else:
                    with conn:
                        row = conn.execute(query, params).fetchone()
            finally:
                if self.db_path != ":memory:":
                    conn.close()
            return dict(row) if row else None

    def _fetchall(self, query: str, params: tuple = ()):
        """Retorna todas las filas como lista de dicts."""
        if self.db_type == "supabase":
            query = query.replace("?", "%s")
            conn = self._get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchall()
            finally:
                conn.close()
        else:
            conn = self._get_conn()
            try:
                if self.db_path == ":memory:":
                    rows = conn.execute(query, params).fetchall()
                else:
                    with conn:
                        rows = conn.execute(query, params).fetchall()
            finally:
                if self.db_path != ":memory:":
                    conn.close()
            return [dict(r) for r in rows]

    def _init_db(self):
        """Crea las tablas si no existen."""
        if self.db_type == "supabase":
            # Usar el archivo schema_supabase.sql si es posible o replicar aquÃ­
            # Por ahora replicamos las tablas bÃ¡sicas para que el bot arranque
            queries = [
                "CREATE TABLE IF NOT EXISTS users (telegram_id BIGINT PRIMARY KEY, name TEXT NOT NULL, active_alerts SMALLINT DEFAULT 0, alert_channel TEXT DEFAULT 'telegram', cv_path TEXT, location TEXT, experience_level TEXT, role_type TEXT, technologies TEXT, job_modality TEXT, max_job_age_days INTEGER, check_interval_hours INTEGER, alert_start_hour INTEGER, alert_end_hour INTEGER, timezone TEXT, weekly_goal_apps INTEGER DEFAULT 5, blocked_companies TEXT DEFAULT '', preferred_companies TEXT DEFAULT '', digest_mode TEXT DEFAULT 'realtime', created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, last_check TIMESTAMPTZ)",
                "CREATE TABLE IF NOT EXISTS keywords (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, keyword TEXT, UNIQUE(telegram_id, keyword))",
                "CREATE TABLE IF NOT EXISTS jobs_seen (id BIGSERIAL PRIMARY KEY, job_hash TEXT, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, source TEXT, title TEXT, company TEXT, url TEXT, seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, UNIQUE(job_hash, telegram_id))",
                "CREATE TABLE IF NOT EXISTS custom_feeds (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, feed_url TEXT, feed_name TEXT)",
                "CREATE TABLE IF NOT EXISTS applications (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, job_title TEXT, company TEXT, url TEXT, status TEXT DEFAULT 'aplicado', notes TEXT, applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS webhook_events (id BIGSERIAL PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, provider TEXT NOT NULL, event_type TEXT NOT NULL, processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS web_login_codes (code TEXT PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ)",
                "CREATE TABLE IF NOT EXISTS telegram_link_codes (code TEXT PRIMARY KEY, web_telegram_id BIGINT NOT NULL, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ)",
                "CREATE INDEX IF NOT EXISTS idx_keywords_telegram_id ON keywords(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_seen_telegram_id_seen_at ON jobs_seen(telegram_id, seen_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_applications_telegram_id_applied_at ON applications(telegram_id, applied_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_applications_telegram_id_status ON applications(telegram_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_web_login_codes_telegram_id_expires_at ON web_login_codes(telegram_id, expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_web_telegram_id_expires_at ON telegram_link_codes(web_telegram_id, expires_at)",
            ]
            for q in queries:
                self._execute(q)
            # MigraciÃ³n defensiva para agregar alert_channel si faltara
            try:
                self._execute(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS alert_channel TEXT DEFAULT 'telegram'"
                )
            except Exception:
                pass
            # Migraciones defensivas para nuevas preferencias de usuario
            for col, ddl in [
                (
                    "weekly_goal_apps",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_goal_apps INTEGER DEFAULT 5",
                ),
                (
                    "blocked_companies",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_companies TEXT DEFAULT ''",
                ),
                (
                    "preferred_companies",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_companies TEXT DEFAULT ''",
                ),
                (
                    "digest_mode",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS digest_mode TEXT DEFAULT 'realtime'",
                ),
            ]:
                try:
                    self._execute(ddl)
                except Exception:
                    pass
            
            # ============================================================
            # SECURITY TABLES (PostgreSQL)
            # ============================================================
            security_queries = [
                # Audit logs table
                """CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    ip_address TEXT,
                    status_code INTEGER,
                    duration_ms REAL,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT,
                    request_id TEXT
                );""",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint ON audit_logs(endpoint);",
                
                # Token blacklist table
                """CREATE TABLE IF NOT EXISTS token_blacklist (
                    id SERIAL PRIMARY KEY,
                    token_hash TEXT UNIQUE NOT NULL,
                    expires_at BIGINT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );""",
                "CREATE INDEX IF NOT EXISTS idx_token_blacklist_hash ON token_blacklist(token_hash);",
                "CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);",
                
                # Refresh tokens table
                """CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    family_id TEXT NOT NULL,
                    device_info TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    expires_at BIGINT NOT NULL,
                    revoked_at TIMESTAMPTZ,
                    replaced_by_token_hash TEXT
                );""",
                "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);",
                "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens(family_id);",
                "CREATE INDEX IF NOT EXISTS idx_applications_telegram_applied_at ON applications (telegram_id, applied_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_applications_telegram_status ON applications (telegram_id, status);",
                "CREATE INDEX IF NOT EXISTS idx_jobs_seen_telegram_seen_at ON jobs_seen (telegram_id, seen_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_custom_feeds_telegram_id ON custom_feeds (telegram_id);",
                "CREATE INDEX IF NOT EXISTS idx_web_login_codes_telegram_expires ON web_login_codes (telegram_id, expires_at);",
                "CREATE INDEX IF NOT EXISTS idx_web_login_codes_expires ON web_login_codes (expires_at);",
                "CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_web_telegram_id ON telegram_link_codes (web_telegram_id);",
                "CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_expires ON telegram_link_codes (expires_at);",
                "CREATE INDEX IF NOT EXISTS idx_pending_job_batches_telegram_expires ON pending_job_batches (telegram_id, expires_at);",
                "CREATE INDEX IF NOT EXISTS idx_pending_job_batches_source_viewed_expires ON pending_job_batches (source, viewed, fallback_sent, expires_at);",
                "CREATE INDEX IF NOT EXISTS idx_pending_job_batches_created_at ON pending_job_batches (created_at);",
                "CREATE INDEX IF NOT EXISTS idx_batch_interactions_batch_id ON batch_interactions (batch_id);",
            ]
            
            for query in security_queries:
                try:
                    self._execute(query)
                except Exception as e:
                    logger.warning(f"Error creating security table: {e}")
            
            # ============================================================
            # END SECURITY TABLES
            # ============================================================
            
            logger.info("âœ… Supabase DB inicializada")
        else:
            conn = self._get_conn()
            with conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id        INTEGER PRIMARY KEY,
                        name               TEXT    NOT NULL,
                        active_alerts      INTEGER DEFAULT 0,
                        alert_channel      TEXT    DEFAULT 'telegram',
                        cv_path            TEXT,
                        location           TEXT    DEFAULT 'Buenos Aires Argentina',
                        experience_level   TEXT    DEFAULT 'junior',
                        role_type          TEXT    DEFAULT '',
                        technologies       TEXT    DEFAULT '',
                        job_modality       TEXT    DEFAULT 'cualquiera',
                        max_job_age_days   INTEGER DEFAULT 30,
                        match_threshold    INTEGER DEFAULT 70,
                        check_interval_hours INTEGER DEFAULT 6,
                        alert_start_hour   INTEGER DEFAULT 8,
                        alert_end_hour     INTEGER DEFAULT 22,
                        timezone           TEXT    DEFAULT 'America/Buenos_Aires',
                        weekly_goal_apps   INTEGER DEFAULT 5,
                        blocked_companies  TEXT    DEFAULT '',
                        preferred_companies TEXT   DEFAULT '',
                        digest_mode        TEXT    DEFAULT 'realtime',
                        created_at         TEXT    DEFAULT CURRENT_TIMESTAMP,
                        last_check         TEXT
                    );
                    CREATE TABLE IF NOT EXISTS keywords (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        keyword     TEXT    NOT NULL,
                        FOREIGN KEY(telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                        UNIQUE(telegram_id, keyword)
                    );
                    CREATE TABLE IF NOT EXISTS jobs_seen (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_hash    TEXT    NOT NULL,
                        telegram_id INTEGER NOT NULL,
                        source      TEXT,
                        title       TEXT,
                        company     TEXT,
                        url         TEXT,
                        seen_at     TEXT    DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(job_hash, telegram_id)
                    );
                    CREATE TABLE IF NOT EXISTS custom_feeds (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        feed_url    TEXT    NOT NULL,
                        feed_name   TEXT    NOT NULL,
                        FOREIGN KEY(telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS applications (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        job_title   TEXT,
                        company     TEXT,
                        url         TEXT,
                        status      TEXT    DEFAULT 'aplicado',
                        notes       TEXT,
                        applied_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS web_login_codes (
                        code        TEXT PRIMARY KEY,
                        telegram_id INTEGER NOT NULL,
                        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                        expires_at  TEXT NOT NULL,
                        used_at     TEXT,
                        FOREIGN KEY(telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS telegram_link_codes (
                        code            TEXT PRIMARY KEY,
                        web_telegram_id INTEGER NOT NULL,
                        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                        expires_at      TEXT NOT NULL,
                        used_at         TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_keywords_telegram_id ON keywords(telegram_id);
                    CREATE INDEX IF NOT EXISTS idx_jobs_seen_telegram_id_seen_at ON jobs_seen(telegram_id, seen_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_applications_telegram_id_applied_at ON applications(telegram_id, applied_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_applications_telegram_id_status ON applications(telegram_id, status);
                    CREATE INDEX IF NOT EXISTS idx_web_login_codes_telegram_id_expires_at ON web_login_codes(telegram_id, expires_at);
                    CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_web_telegram_id_expires_at ON telegram_link_codes(web_telegram_id, expires_at);
                """)
                # Migraciones para SQLite si faltan columnas
                for col, default in [
                    ("experience_level", "'junior'"),
                    ("role_type", "''"),
                    ("technologies", "''"),
                    ("job_modality", "'cualquiera'"),
                    ("max_job_age_days", "30"),
                    ("match_threshold", "70"),
                    ("check_interval_hours", "6"),
                    ("alert_start_hour", "8"),
                    ("alert_end_hour", "22"),
                    ("timezone", "'America/Buenos_Aires'"),
                    ("github_url", "''"),
                    ("alert_channel", "'telegram'"),
                    ("weekly_goal_apps", "5"),
                    ("blocked_companies", "''"),
                    ("preferred_companies", "''"),
                    ("digest_mode", "'realtime'"),
                ]:
                    try:
                        conn.execute(
                            f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {default}"
                        )
                    except:
                        pass

                conn.executescript("""
                    -- Tabla de usuarios web (SaaS)
                    CREATE TABLE IF NOT EXISTS web_users (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id     INTEGER UNIQUE NOT NULL,
                        email           TEXT UNIQUE NOT NULL,
                        password_hash   TEXT NOT NULL,
                        plan            TEXT DEFAULT 'free',
                        subscription_status TEXT,
                        subscription_provider TEXT,
                        subscription_id TEXT,
                        subscription_expires_at TEXT,
                        ai_analyses_used    INTEGER DEFAULT 0,
                        ai_analyses_limit   INTEGER DEFAULT 2,
                        searches_used       INTEGER DEFAULT 0,
                        searches_limit      INTEGER DEFAULT 5,
                        job_tracker_enabled INTEGER DEFAULT 0,
                        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Tabla de pagos
                    CREATE TABLE IF NOT EXISTS payments (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id     INTEGER NOT NULL,
                        provider        TEXT NOT NULL,
                        amount          REAL NOT NULL,
                        currency        TEXT DEFAULT 'USD',
                        status          TEXT NOT NULL,
                        provider_payment_id TEXT,
                        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Tabla de anÃ¡lisis IA realizados
                    CREATE TABLE IF NOT EXISTS ai_analyses (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id     INTEGER NOT NULL,
                        cv_analyzed     INTEGER DEFAULT 0,
                        job_matched     INTEGER DEFAULT 0,
                        prompt_tokens   INTEGER,
                        response_tokens INTEGER,
                        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Tabla de eventos de webhook procesados (idempotencia)
                    CREATE TABLE IF NOT EXISTS webhook_events (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id        TEXT UNIQUE NOT NULL,
                        provider        TEXT NOT NULL,
                        event_type      TEXT NOT NULL,
                        processed_at    TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Tabla de cache de datos de empresas (LinkedIn Data API)
                    CREATE TABLE IF NOT EXISTS companies (
                        domain          TEXT PRIMARY KEY,
                        data            TEXT NOT NULL,  -- JSON con datos de la empresa
                        cached_at       INTEGER NOT NULL,  -- timestamp Unix
                        expires_at      INTEGER NOT NULL   -- timestamp Unix + TTL
                    );
                    
                    -- Tabla de cache de datos financieros (Yahoo Finance API)
                    CREATE TABLE IF NOT EXISTS stock_data (
                        ticker          TEXT PRIMARY KEY,
                        data            TEXT NOT NULL,  -- JSON con datos financieros
                        cached_at       INTEGER NOT NULL  -- timestamp Unix
                    );
                    
                    -- Tabla de batches de jobs pendientes (Smart Summary UX)
                    CREATE TABLE IF NOT EXISTS pending_job_batches (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id     INTEGER NOT NULL,
                        jobs_json       TEXT NOT NULL,  -- JSON array de jobs
                        total_count     INTEGER DEFAULT 0,
                        high_match_count INTEGER DEFAULT 0,    -- >80%
                        medium_match_count INTEGER DEFAULT 0,  -- 60-80%
                        regular_match_count INTEGER DEFAULT 0, -- <60%
                        source          TEXT DEFAULT 'manual', -- 'manual' o 'alert'
                        created_at      INTEGER NOT NULL,        -- Unix timestamp
                        expires_at      INTEGER NOT NULL,      -- Unix timestamp + TTL
                        viewed          INTEGER DEFAULT 0,     -- 0=pending, 1=viewed, 2=expired
                        fallback_sent   INTEGER DEFAULT 0      -- 0=no, 1=yes (alertas expiradas)
                    );
                    
                    -- Tabla de interacciones con batches (analytics)
                    CREATE TABLE IF NOT EXISTS batch_interactions (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id        INTEGER NOT NULL,
                        telegram_id     INTEGER NOT NULL,
                        action          TEXT NOT NULL,  -- 'viewed', 'expired', 'fallback_sent', 'dismissed'
                        timestamp       INTEGER NOT NULL,
                        FOREIGN KEY(batch_id) REFERENCES pending_job_batches(id) ON DELETE CASCADE
                    );
                    
                    -- ============================================================
                    -- SECURITY TABLES
                    -- ============================================================
                    -- Audit logs table
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id     INTEGER,
                        endpoint    TEXT    NOT NULL,
                        method      TEXT    NOT NULL,
                        ip_address  TEXT,
                        status_code INTEGER,
                        duration_ms REAL,
                        timestamp   TEXT    DEFAULT CURRENT_TIMESTAMP,
                        user_agent  TEXT,
                        request_id  TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint ON audit_logs(endpoint);
                    
                    -- Token blacklist table
                    CREATE TABLE IF NOT EXISTS token_blacklist (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_hash  TEXT    UNIQUE NOT NULL,
                        expires_at  INTEGER NOT NULL,
                        created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_token_blacklist_hash ON token_blacklist(token_hash);
                    CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);
                    
                    -- Refresh tokens table
                    CREATE TABLE IF NOT EXISTS refresh_tokens (
                        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id                 INTEGER NOT NULL,
                        token_hash              TEXT    UNIQUE NOT NULL,
                        family_id               TEXT    NOT NULL,
                        device_info             TEXT,
                        created_at              TEXT    DEFAULT CURRENT_TIMESTAMP,
                        expires_at              INTEGER NOT NULL,
                        revoked_at              TEXT,
                        replaced_by_token_hash  TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
                    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
                    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens(family_id);

                    CREATE INDEX IF NOT EXISTS idx_applications_telegram_applied_at
                        ON applications (telegram_id, applied_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_applications_telegram_status
                        ON applications (telegram_id, status);
                    CREATE INDEX IF NOT EXISTS idx_jobs_seen_telegram_seen_at
                        ON jobs_seen (telegram_id, seen_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_custom_feeds_telegram_id
                        ON custom_feeds (telegram_id);
                    CREATE INDEX IF NOT EXISTS idx_web_login_codes_telegram_expires
                        ON web_login_codes (telegram_id, expires_at);
                    CREATE INDEX IF NOT EXISTS idx_web_login_codes_expires
                        ON web_login_codes (expires_at);
                    CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_web_telegram_id
                        ON telegram_link_codes (web_telegram_id);
                    CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_expires
                        ON telegram_link_codes (expires_at);
                    CREATE INDEX IF NOT EXISTS idx_pending_job_batches_telegram_expires
                        ON pending_job_batches (telegram_id, expires_at);
                    CREATE INDEX IF NOT EXISTS idx_pending_job_batches_source_viewed_expires
                        ON pending_job_batches (source, viewed, fallback_sent, expires_at);
                    CREATE INDEX IF NOT EXISTS idx_pending_job_batches_created_at
                        ON pending_job_batches (created_at);
                    CREATE INDEX IF NOT EXISTS idx_batch_interactions_batch_id
                        ON batch_interactions (batch_id);
                    
                    -- ============================================================
                    -- END SECURITY TABLES
                    -- ============================================================
                """)

                # MigraciÃ³n defensiva: columna para controlar el periodo de uso diario
                try:
                    conn.execute(
                        "ALTER TABLE web_users ADD COLUMN usage_period_start TEXT"
                    )
                except Exception:
                    # Si ya existe, ignoramos el error
                    pass
                
                # MigraciÃ³n: columna para contar entrevistas usadas
                try:
                    conn.execute(
                        "ALTER TABLE web_users ADD COLUMN interviews_used INTEGER DEFAULT 0"
                    )
                except Exception:
                    pass
                
                # MigraciÃ³n: columna para lÃ­mite de entrevistas
                try:
                    conn.execute(
                        "ALTER TABLE web_users ADD COLUMN interviews_limit INTEGER DEFAULT 20"
                    )
                except Exception:
                    pass
            logger.info("âœ… SQLite DB inicializada")

            logger.info("âœ… Base de datos inicializada: %s", self.db_path)
            if self.db_path != ":memory:":
                conn.close()

    # ----------------------------------------------------------
    # USUARIOS
    # ----------------------------------------------------------

    def create_user_if_not_exists(self, telegram_id: int, name: str):
        """Registra un usuario nuevo y le asigna keywords por defecto."""
        try:
            import config
        except ImportError:
            from job_bot import config

        # Ver si el usuario ya existÃ­a para no sobreescribir su configuraciÃ³n
        already = self.get_user(telegram_id)

        self._execute(
            "INSERT OR IGNORE INTO users (telegram_id, name) VALUES (?, ?)",
            (telegram_id, name),
        )

        row = self._fetchone(
            "SELECT COUNT(*) as count FROM keywords WHERE telegram_id = ?",
            (telegram_id,),
        )
        count = row["count"] if row else 0

        if count == 0:
            for kw in config.DEFAULT_KEYWORDS:
                self._execute(
                    "INSERT OR IGNORE INTO keywords (telegram_id, keyword) VALUES (?, ?)",
                    (telegram_id, kw),
                )

        # Si el usuario es NUEVO, forzamos modalidad por defecto 'cualquiera'
        # para alinear comportamiento entre SQLite/Postgres y con los tests.
        if already is None:
            self._execute(
                "UPDATE users SET job_modality = 'cualquiera' WHERE telegram_id = ?",
                (telegram_id,),
            )

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Retorna los datos de un usuario o None si no existe."""
        return self._fetchone(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )

    def get_all_active_users(self) -> List[Dict]:
        """Retorna todos los usuarios con alertas activas."""
        res = self._fetchall("SELECT * FROM users WHERE active_alerts = 1")
        return res if res is not None else []

    def get_users_due_for_check(self) -> List[Dict]:
        """Retorna usuarios cuyo intervalo de chequeo ya venciÃ³."""
        import datetime

        try:
            import zoneinfo
        except:
            from backports import zoneinfo

        active_res = self._fetchall("SELECT * FROM users WHERE active_alerts = 1")
        active = active_res if active_res is not None else []
        due_users = []

        def _int_or(value, default):
            return default if value is None else int(value)

        for user in active:
            tz_name = user.get("timezone") or "America/Buenos_Aires"

            # Normalizar zonas horarias antiguas o invÃ¡lidas
            if tz_name == "America/Buenos_Aires":
                mapped_tz = "America/Argentina/Buenos_Aires"
            else:
                mapped_tz = tz_name

            try:
                tz = zoneinfo.ZoneInfo(mapped_tz)
            except Exception:
                # Fallback robusto: si no existe, usar UTC para no romper el scheduler
                logger.warning(
                    "Timezone '%s' invÃ¡lida, usando UTC para scheduler", tz_name
                )
                tz = datetime.timezone.utc

            now_user = datetime.datetime.now(tz)
            current_hour = now_user.hour

            start_h = _int_or(user.get("alert_start_hour"), 8)
            end_h = _int_or(user.get("alert_end_hour"), 22)

            if start_h <= end_h:
                if not (start_h <= current_hour < end_h):
                    continue
            else:
                if end_h <= current_hour < start_h:
                    continue

            interval_h = _int_or(user.get("check_interval_hours"), 6)
            last_check_str = user.get("last_check")
            if last_check_str:
                try:
                    # En Postgres el resultado ya suele ser un datetime si RealDictCursor hace su magia,
                    # pero sqlite devuelve string. Manejamos ambos.
                    if isinstance(last_check_str, str):
                        last_check = datetime.datetime.fromisoformat(
                            last_check_str.replace("Z", "+00:00")
                        )
                    else:
                        last_check = last_check_str

                    if last_check.tzinfo is None:
                        last_check = last_check.replace(tzinfo=datetime.timezone.utc)

                    elapsed = (now_user - last_check).total_seconds() / 3600
                    if elapsed < interval_h:
                        continue
                except:
                    pass

            due_users.append(user)
        return due_users

    def set_alerts_active(self, telegram_id: int, active: bool):
        """Activa o desactiva las alertas automÃ¡ticas de un usuario."""
        self._execute(
            "UPDATE users SET active_alerts = ? WHERE telegram_id = ?",
            (1 if active else 0, telegram_id),
        )

    def set_user_location(self, telegram_id: int, location: str):
        """Actualiza la ubicaciÃ³n de bÃºsqueda de un usuario."""
        self._execute(
            "UPDATE users SET location = ? WHERE telegram_id = ?",
            (location, telegram_id),
        )

    def set_user_cv(self, telegram_id: int, cv_path: str):
        """Guarda la ruta del CV del usuario."""
        self._execute(
            "UPDATE users SET cv_path = ? WHERE telegram_id = ?", (cv_path, telegram_id)
        )

    def update_last_check(self, telegram_id: int):
        """Actualiza el timestamp del Ãºltimo chequeo."""
        if self.db_type == "supabase":
            self._execute(
                "UPDATE users SET last_check = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                (telegram_id,),
            )
        else:
            self._execute(
                "UPDATE users SET last_check = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                (telegram_id,),
            )

    def set_user_profile(
        self,
        telegram_id: int,
        experience_level: str,
        role_type: str,
        technologies: str,
        job_modality: str,
        max_job_age_days: int = 30,
        match_threshold: int = 70,
    ):
        """Guarda el perfil completo del usuario."""
        try:
            threshold = int(match_threshold)
        except (TypeError, ValueError):
            threshold = 70
        threshold = max(50, min(95, threshold))
        self._execute(
            """
            UPDATE users SET
                experience_level = ?, role_type = ?, technologies = ?,
                job_modality = ?, max_job_age_days = ?, match_threshold = ?
            WHERE telegram_id = ?
        """,
            (
                experience_level,
                role_type,
                technologies,
                job_modality,
                max_job_age_days,
                threshold,
                telegram_id,
            ),
        )

    def set_user_schedule(
        self,
        telegram_id: int,
        interval_hours: int,
        start_hour: int,
        end_hour: int,
        timezone: str = "America/Buenos_Aires",
    ):
        """Configura el horario de alertas personalizado del usuario."""
        self._execute(
            """
            UPDATE users SET
                check_interval_hours = ?, alert_start_hour = ?,
                alert_end_hour = ?, timezone = ?
            WHERE telegram_id = ?
        """,
            (interval_hours, start_hour, end_hour, timezone, telegram_id),
        )

    def get_user_schedule(self, telegram_id: int) -> Dict:
        """Retorna la configuraciÃ³n de horarios del usuario."""
        user = self.get_user(telegram_id)
        if not user:
            return {
                "check_interval_hours": 6,
                "alert_start_hour": 8,
                "alert_end_hour": 22,
                "timezone": "America/Buenos_Aires",
            }
        def _int_or(value, default):
            return default if value is None else int(value)
        return {
            "check_interval_hours": _int_or(user.get("check_interval_hours"), 6),
            "alert_start_hour": _int_or(user.get("alert_start_hour"), 8),
            "alert_end_hour": _int_or(user.get("alert_end_hour"), 22),
            "timezone": user.get("timezone") or "America/Buenos_Aires",
        }

    def get_alert_channel(self, telegram_id: int) -> str:
        """Retorna el canal de alertas preferido del usuario."""
        user = self.get_user(telegram_id)
        if not user:
            return "telegram"
        return (user.get("alert_channel") or "telegram").lower()

    def set_alert_channel(self, telegram_id: int, channel: str):
        """Actualiza el canal de notificaciones del usuario (telegram, web, email)."""
        normalized = (channel or "telegram").lower()
        self._execute(
            "UPDATE users SET alert_channel = ? WHERE telegram_id = ?",
            (normalized, telegram_id),
        )

    def get_digest_mode(self, telegram_id: int) -> str:
        """Retorna el modo de digest (realtime, daily, weekly)."""
        user = self.get_user(telegram_id)
        if not user:
            return "realtime"
        mode = (user.get("digest_mode") or "realtime").lower()
        if mode not in {"realtime", "daily", "weekly"}:
            return "realtime"
        return mode

    def set_digest_mode(self, telegram_id: int, mode: str):
        """Actualiza el modo de digest sin pisar la frecuencia real del scheduler."""
        normalized = (mode or "realtime").lower()
        if normalized not in {"realtime", "daily", "weekly"}:
            normalized = "realtime"

        self._execute(
            "UPDATE users SET digest_mode = ? WHERE telegram_id = ?",
            (normalized, telegram_id),
        )

    def get_weekly_goal(self, telegram_id: int) -> int:
        """Retorna el objetivo semanal de aplicaciones del usuario."""
        user = self.get_user(telegram_id)
        if not user:
            return 0
        try:
            return int(user.get("weekly_goal_apps") or 0)
        except (TypeError, ValueError):
            return 0

    def set_weekly_goal(self, telegram_id: int, goal: int):
        """Actualiza el objetivo semanal de aplicaciones."""
        try:
            goal_int = max(0, int(goal))
        except (TypeError, ValueError):
            goal_int = 0
        self._execute(
            "UPDATE users SET weekly_goal_apps = ? WHERE telegram_id = ?",
            (goal_int, telegram_id),
        )

    def set_search_mode(self, telegram_id: int, mode: str):
        """Configura el modo de bÃºsqueda (volumen o calidad)."""
        valid_modes = ["volumen", "calidad"]
        if mode not in valid_modes:
            return

        # MigraciÃ³n defensiva: agregar columna si no existe
        try:
            self._execute(
                "ALTER TABLE users ADD COLUMN search_mode TEXT DEFAULT 'calidad'"
            )
        except Exception:
            pass

        self._execute(
            "UPDATE users SET search_mode = ? WHERE telegram_id = ?",
            (mode, telegram_id),
        )

    def get_search_mode(self, telegram_id: int) -> str:
        """Retorna el modo de bÃºsqueda del usuario."""
        user = self.get_user(telegram_id)
        if not user:
            return "calidad"
        return user.get("search_mode", "calidad")

    def get_user_profile(self, telegram_id: int) -> Dict:
        """Retorna el perfil del usuario para filtrado."""
        user = self.get_user(telegram_id)
        if not user:
            return {
                "experience_level": "junior",
                "role_type": "",
                "technologies": "",
                "job_modality": "cualquiera",
                "max_job_age_days": 30,
                "match_threshold": 70,
            }
        return {
            "experience_level": user.get("experience_level", "junior"),
            "role_type": user.get("role_type", ""),
            "technologies": user.get("technologies", ""),
            "job_modality": user.get("job_modality", "cualquiera"),
            "max_job_age_days": int(user.get("max_job_age_days", 30)),
            "match_threshold": int(user.get("match_threshold", 70) or 70),
        }

    def generate_smart_keywords(self, telegram_id: int) -> List[str]:
        """
        Genera keywords de bÃºsqueda inteligentes basadas en el perfil.
        Combina tecnologÃ­as + nivel + rol para crear bÃºsquedas efectivas.
        """
        profile = self.get_user_profile(telegram_id)
        techs = [t.strip() for t in profile["technologies"].split(",") if t.strip()]
        role = profile.get("role_type", "").strip()
        level = profile.get("experience_level", "junior")

        # Mapear nivel a tÃ©rminos de bÃºsqueda
        level_terms = {
            "sin_experiencia": [
                "trainee",
                "pasantÃ­a",
                "pasantia",
                "aprendiz",
                "entry level",
                "junior",
            ],
            "junior": ["junior", "jr", "entry level", "trainee"],
            "semi_senior": ["semi senior", "ssr", "mid level"],
            "senior": ["senior", "sr", "lead"],
        }
        level_kws = level_terms.get(level, ["junior"])

        keywords = []

        # Combinar cada tecnologÃ­a con el nivel
        for tech in techs[:5]:  # MÃ¡ximo 5 tecnologÃ­as
            # "python junior", "python trainee"
            for lkw in level_kws[:2]:  # Top 2 level terms
                keywords.append(f"{tech} {lkw}")
            # TambiÃ©n buscar solo la tecnologÃ­a
            keywords.append(tech)

        # Si tiene rol, agregar combinaciones
        if role:
            for lkw in level_kws[:2]:
                keywords.append(f"{role} {lkw}")
            keywords.append(role)

        # Deduplicar y limitar
        seen = set()
        unique_kws = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_kws.append(kw)

        return unique_kws[:10]  # MÃ¡ximo 10 keywords

    # ----------------------------------------------------------
    # KEYWORDS
    # ----------------------------------------------------------

    def get_user_keywords(self, telegram_id: int) -> List[str]:
        """Retorna la lista de keywords de un usuario."""
        rows = self._fetchall(
            "SELECT keyword FROM keywords WHERE telegram_id = ? ORDER BY keyword",
            (telegram_id,),
        )
        return [r["keyword"] for r in rows] if rows else []

    def set_user_keywords(self, telegram_id: int, keywords: List[str]):
        """Reemplaza completamente las keywords del usuario."""
        self._execute("DELETE FROM keywords WHERE telegram_id = ?", (telegram_id,))
        for kw in keywords:
            kw = kw.strip()
            if kw:
                self._execute(
                    "INSERT OR IGNORE INTO keywords (telegram_id, keyword) VALUES (?, ?)",
                    (telegram_id, kw),
                )

    def add_keyword(self, telegram_id: int, keyword: str) -> bool:
        """Agrega una keyword individual."""
        try:
            self._execute(
                "INSERT INTO keywords (telegram_id, keyword) VALUES (?, ?)",
                (telegram_id, keyword.strip()),
            )
            return True
        except:
            return False

    def remove_keyword(self, telegram_id: int, keyword: str):
        """Elimina una keyword especÃ­fica."""
        self._execute(
            "DELETE FROM keywords WHERE telegram_id = ? AND keyword = ?",
            (telegram_id, keyword.strip()),
        )

    # ----------------------------------------------------------
    # DEDUPLICACIÃ“N DE TRABAJOS
    # ----------------------------------------------------------

    @staticmethod
    def _hash_url(url: str) -> str:
        """Genera un hash MD5 de la URL para identificar trabajos Ãºnicos."""
        return hashlib.md5(url.strip().encode("utf-8")).hexdigest()

    def is_job_seen(self, telegram_id: int, url: str) -> bool:
        """Retorna True si este trabajo ya fue enviado al usuario."""
        job_hash = self._hash_url(url)
        row = self._fetchone(
            "SELECT id FROM jobs_seen WHERE telegram_id = ? AND job_hash = ?",
            (telegram_id, job_hash),
        )
        return row is not None

    def mark_job_seen(self, telegram_id: int, job: Dict):
        """Marca un trabajo como visto para este usuario."""
        if not job.get("url"):
            return
        job_hash = self._hash_url(job["url"])
        self._execute(
            """
            INSERT OR IGNORE INTO jobs_seen (job_hash, telegram_id, source, title, company, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                job_hash,
                telegram_id,
                job.get("source", ""),
                job.get("title", "")[:200],
                job.get("company", "")[:100],
                job.get("url", "")[:500],
            ),
        )

    def filter_new_jobs(self, telegram_id: int, jobs: List[Dict]) -> List[Dict]:
        """Filtra y retorna solo los trabajos que NO fueron vistos antes."""
        new_jobs = []
        for job in jobs:
            if not job.get("url"):
                continue
            if not self.is_job_seen(telegram_id, job["url"]):
                new_jobs.append(job)
        return new_jobs

    # ----------------------------------------------------------
    # FEEDS PERSONALIZADOS
    # ----------------------------------------------------------

    def get_custom_feeds(self, telegram_id: int) -> List[Dict]:
        """Retorna los feeds RSS personalizados de un usuario."""
        res = self._fetchall(
            "SELECT * FROM custom_feeds WHERE telegram_id = ?", (telegram_id,)
        )
        return res if res is not None else []

    def add_custom_feed(self, telegram_id: int, url: str, name: str):
        """Agrega un feed RSS personalizado."""
        self._execute(
            "INSERT INTO custom_feeds (telegram_id, feed_url, feed_name) VALUES (?, ?, ?)",
            (telegram_id, url.strip(), name.strip()),
        )

    def remove_custom_feed(self, telegram_id: int, feed_id: int):
        """Elimina un feed RSS personalizado."""
        self._execute(
            "DELETE FROM custom_feeds WHERE id = ? AND telegram_id = ?",
            (feed_id, telegram_id),
        )

    # ----------------------------------------------------------
    # ESTADÃSTICAS (para la landing page)
    # ----------------------------------------------------------

    def get_stats(self) -> Dict:
        """Retorna estadÃ­sticas generales del bot."""
        u = self._fetchone("SELECT COUNT(*) as count FROM users")
        a = self._fetchone(
            "SELECT COUNT(*) as count FROM users WHERE active_alerts = 1"
        )
        j = self._fetchone("SELECT COUNT(*) as count FROM jobs_seen")
        return {
            "total_users": u["count"] if u else 0,
            "active_users": a["count"] if a else 0,
            "total_jobs_found": j["count"] if j else 0,
        }

    def delete_user_data(self, telegram_id: int):
        """Elimina toda la informaciÃ³n de un usuario (GDPR)."""
        self._execute("DELETE FROM keywords WHERE telegram_id = ?", (telegram_id,))
        self._execute("DELETE FROM jobs_seen WHERE telegram_id = ?", (telegram_id,))
        self._execute("DELETE FROM custom_feeds WHERE telegram_id = ?", (telegram_id,))
        self._execute("DELETE FROM applications WHERE telegram_id = ?", (telegram_id,))
        self._execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))

    # ----------------------------------------------------------
    # JOB TRACKER (PRO FEATURE)
    # ----------------------------------------------------------
    def add_application(
        self, telegram_id: int, job_title: str, company: str, url: str, notes: str = ""
    ):
        """Registra una nueva postulaciÃ³n."""
        self._execute(
            """
            INSERT INTO applications (telegram_id, job_title, company, url, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (telegram_id, job_title, company, url, notes),
        )

    def get_user_applications(self, telegram_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Retorna todas las postulaciones de un usuario."""
        query = "SELECT * FROM applications WHERE telegram_id = ? ORDER BY applied_at DESC"
        params: tuple = (telegram_id,)
        if limit is not None:
            query += " LIMIT ?"
            params = (telegram_id, int(limit))
        return self._fetchall(query, params)

    def get_application_funnel_counts(self, telegram_id: int) -> Dict[str, int]:
        """Obtiene el resumen del funnel sin cargar todo el historial en memoria."""
        rows = self._fetchall(
            """
            SELECT status, COUNT(*) AS count
            FROM applications
            WHERE telegram_id = ?
            GROUP BY status
            """,
            (telegram_id,),
        )
        funnel = {"applied": 0, "interview": 0, "rejected": 0, "offer": 0}
        status_map = {
            "aplicado": "applied",
            "entrevista": "interview",
            "rechazado": "rejected",
            "oferta": "offer",
        }
        for row in rows:
            bucket = status_map.get((row.get("status") or "").lower())
            if bucket:
                funnel[bucket] = int(row.get("count") or 0)
        return funnel

    def get_weekly_applications_count(
        self,
        telegram_id: int,
        apps: Optional[List[Dict]] = None,
    ) -> int:
        """Cuenta las postulaciones de la Ãºltima semana calendario para el usuario.

        Si el caller ya tiene `apps` cargadas, reutilizamos esa lista para evitar
        una consulta duplicada en el hot path del dashboard.
        """
        if apps is not None:
            import datetime

            if not apps:
                return 0

            now = datetime.datetime.utcnow()
            seven_days_ago = now - datetime.timedelta(days=7)
            count = 0
            for app in apps:
                created = app.get("applied_at") or app.get("created_at")
                if not created:
                    continue
                try:
                    if isinstance(created, str):
                        created_dt = datetime.datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        )
                    else:
                        created_dt = created
                    if created_dt.tzinfo is not None:
                        created_dt = created_dt.astimezone(datetime.timezone.utc).replace(
                            tzinfo=None
                        )
                except Exception:
                    continue
                if created_dt >= seven_days_ago:
                    count += 1
            return count

        try:
            if self.db_type == "supabase":
                row = self._fetchone(
                    """SELECT COUNT(*) AS count
                       FROM applications
                       WHERE telegram_id = ?
                         AND applied_at >= NOW() - INTERVAL '7 days'""",
                    (telegram_id,),
                )
            else:
                import datetime

                cutoff = (
                    datetime.datetime.utcnow() - datetime.timedelta(days=7)
                ).strftime("%Y-%m-%d %H:%M:%S")
                row = self._fetchone(
                    """SELECT COUNT(*) AS count
                       FROM applications
                       WHERE telegram_id = ?
                         AND applied_at >= ?""",
                    (telegram_id, cutoff),
                )
            return int(row["count"]) if row else 0
        except Exception:
            apps = self.get_user_applications(telegram_id) or []
            return self.get_weekly_applications_count(telegram_id, apps=apps)

    def get_company_filters(self, telegram_id: int) -> Dict:
        """Obtiene listas de empresas bloqueadas/preferidas para filtrado de ofertas."""
        user = self.get_user(telegram_id) or {}
        blocked_raw = user.get("blocked_companies") or ""
        preferred_raw = user.get("preferred_companies") or ""

        def _to_set(raw: str):
            items = []
            for part in raw.split(","):
                name = part.strip()
                if name:
                    items.append(name.lower())
            return set(items)

        return {
            "blocked": _to_set(blocked_raw),
            "preferred": _to_set(preferred_raw),
            "blocked_raw": blocked_raw,
            "preferred_raw": preferred_raw,
        }

    def set_company_filters(
        self,
        telegram_id: int,
        blocked_companies: str = "",
        preferred_companies: str = "",
    ):
        """Actualiza las cadenas crudas de empresas bloqueadas/preferidas."""
        blocked = (blocked_companies or "").strip()
        preferred = (preferred_companies or "").strip()
        self._execute(
            "UPDATE users SET blocked_companies = ?, preferred_companies = ? WHERE telegram_id = ?",
            (blocked, preferred, telegram_id),
        )

    def update_application_status(self, app_id: int, telegram_id: int, status: str):
        """Actualiza el estado de una postulaciÃ³n (aplicado, entrevista, rechazado, oferta)."""
        self._execute(
            "UPDATE applications SET status = ? WHERE id = ? AND telegram_id = ?",
            (status, app_id, telegram_id),
        )

    def set_github_url(self, telegram_id: int, github_url: str):
        """Guarda la URL de GitHub del usuario."""
        self._execute(
            "UPDATE users SET github_url = ? WHERE telegram_id = ?",
            (github_url.strip(), telegram_id),
        )

    # ----------------------------------------------------------
    # SAAS: WEB USERS
    # ----------------------------------------------------------

    def create_web_user(self, telegram_id: int, email: str, password_hash: str):
        """Crea un usuario web vinculado a Telegram."""
        normalized_hash = _ensure_password_hash(password_hash)
        self._execute(
            """INSERT OR IGNORE INTO web_users 
               (telegram_id, email, password_hash, plan, created_at)
               VALUES (?, ?, ?, 'free', CURRENT_TIMESTAMP)""",
            (telegram_id, email, normalized_hash),
        )

    def generate_web_account_id(self) -> int:
        """Genera un identificador interno para cuentas web sin Telegram vinculado."""
        row = self._fetchone(
            """
            SELECT MIN(telegram_id) AS min_id
            FROM (
                SELECT telegram_id FROM users
                UNION ALL
                SELECT telegram_id FROM web_users
            )
            """
        )
        min_id = row.get("min_id") if row else None
        if min_id is None or int(min_id) >= 0:
            return -1
        return int(min_id) - 1

    def get_web_user(self, telegram_id: int) -> Optional[Dict]:
        """Obtiene datos del usuario web."""
        return self._fetchone(
            "SELECT * FROM web_users WHERE telegram_id = ?", (telegram_id,)
        )

    def get_web_user_by_email(self, email: str) -> Optional[Dict]:
        """Obtiene usuario web por email."""
        return self._fetchone("SELECT * FROM web_users WHERE email = ?", (email,))

    def create_web_login_code(self, telegram_id: int, code: str, expires_at: str):
        """Guarda un codigo de login web de un solo uso generado desde Telegram."""
        self._execute(
            "DELETE FROM web_login_codes WHERE telegram_id = ? OR expires_at <= CURRENT_TIMESTAMP",
            (telegram_id,),
        )
        self._execute(
            """INSERT INTO web_login_codes (code, telegram_id, expires_at)
               VALUES (?, ?, ?)""",
            (code, telegram_id, expires_at),
        )

    def consume_web_login_code(self, code: str) -> Optional[Dict]:
        """Consume un codigo de login web y devuelve el usuario asociado si sigue vigente."""
        record = self._fetchone(
            """SELECT code, telegram_id, expires_at, used_at
               FROM web_login_codes
               WHERE code = ?""",
            (code,),
        )
        if not record:
            return None

        if record.get("used_at"):
            return None

        expires_at = record.get("expires_at")
        if expires_at:
            import datetime

            try:
                expiry = (
                    datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if isinstance(expires_at, str)
                    else expires_at
                )
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=datetime.timezone.utc)
                now = datetime.datetime.now(datetime.timezone.utc)
                if expiry < now:
                    self._execute(
                        "DELETE FROM web_login_codes WHERE code = ?",
                        (code,),
                    )
                    return None
            except Exception:
                self._execute(
                    "DELETE FROM web_login_codes WHERE code = ?",
                    (code,),
                )
                return None

        self._execute(
            "UPDATE web_login_codes SET used_at = CURRENT_TIMESTAMP WHERE code = ?",
            (code,),
        )
        return record

    def create_telegram_link_code(self, web_telegram_id: int, code: str, expires_at: str):
        """Guarda un codigo temporal para vincular una cuenta web con Telegram."""
        self._execute(
            "DELETE FROM telegram_link_codes WHERE web_telegram_id = ? OR expires_at <= CURRENT_TIMESTAMP",
            (web_telegram_id,),
        )
        self._execute(
            """INSERT INTO telegram_link_codes (code, web_telegram_id, expires_at)
               VALUES (?, ?, ?)""",
            (code, web_telegram_id, expires_at),
        )

    def consume_telegram_link_code(self, code: str) -> Optional[Dict]:
        """Consume un codigo de vinculaciÃ³n Telegram y devuelve la cuenta web asociada."""
        record = self._fetchone(
            """SELECT code, web_telegram_id, expires_at, used_at
               FROM telegram_link_codes
               WHERE code = ?""",
            (code,),
        )
        if not record:
            return None

        used_at = record.get("used_at")
        expires_at = record.get("expires_at")
        if used_at:
            return None

        try:
            from datetime import datetime, timezone

            expires_dt = datetime.fromisoformat(expires_at)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            if expires_dt <= datetime.now(timezone.utc):
                return None
        except Exception:
            return None

        self._execute(
            "UPDATE telegram_link_codes SET used_at = CURRENT_TIMESTAMP WHERE code = ?",
            (code,),
        )
        return record

    def link_web_account_to_telegram(
        self,
        web_telegram_id: int,
        telegram_id: int,
        telegram_name: str,
    ) -> Dict:
        """Migra una cuenta web temporal al telegram_id real del usuario."""
        web_user = self.get_web_user(web_telegram_id)
        if not web_user:
            raise ValueError("Cuenta web no encontrada")

        existing_link = self.get_web_user(telegram_id)
        if existing_link and int(existing_link.get("telegram_id")) != int(web_telegram_id):
            raise ValueError("Ese usuario de Telegram ya estÃ¡ vinculado a otra cuenta")

        for column, definition in (
            ("github_url", "TEXT DEFAULT ''"),
            ("search_mode", "TEXT DEFAULT 'calidad'"),
        ):
            try:
                self._execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
            except Exception:
                pass

        self.create_user_if_not_exists(telegram_id, telegram_name or "Usuario")
        source_user = self.get_user(web_telegram_id) or {}
        target_user = self.get_user(telegram_id) or {}

        def prefer_text(source_value, target_value, default_value=""):
            source_value = source_value or ""
            target_value = target_value or ""
            if source_value and source_value != default_value:
                return source_value
            if target_value:
                return target_value
            return source_value or target_value or default_value

        def prefer_numeric(source_value, target_value, default_value):
            source_value = default_value if source_value is None else source_value
            target_value = default_value if target_value is None else target_value
            if source_value != default_value:
                return source_value
            if target_value != default_value:
                return target_value
            return source_value

        merged_name = target_user.get("name") or source_user.get("name") or telegram_name or "Usuario"
        merged_active_alerts = 1 if target_user.get("active_alerts") or source_user.get("active_alerts") else 0
        merged_alert_channel = "telegram"
        merged_cv_path = target_user.get("cv_path") or source_user.get("cv_path")
        merged_location = prefer_text(source_user.get("location"), target_user.get("location"), "Buenos Aires Argentina")
        merged_experience = prefer_text(source_user.get("experience_level"), target_user.get("experience_level"), "junior")
        merged_role = prefer_text(source_user.get("role_type"), target_user.get("role_type"), "")
        merged_technologies = prefer_text(source_user.get("technologies"), target_user.get("technologies"), "")
        merged_modality = prefer_text(source_user.get("job_modality"), target_user.get("job_modality"), "cualquiera")
        merged_max_age = prefer_numeric(source_user.get("max_job_age_days"), target_user.get("max_job_age_days"), 30)
        merged_match_threshold = prefer_numeric(source_user.get("match_threshold"), target_user.get("match_threshold"), 70)
        merged_interval = prefer_numeric(source_user.get("check_interval_hours"), target_user.get("check_interval_hours"), 6)
        merged_start_hour = prefer_numeric(source_user.get("alert_start_hour"), target_user.get("alert_start_hour"), 8)
        merged_end_hour = prefer_numeric(source_user.get("alert_end_hour"), target_user.get("alert_end_hour"), 22)
        merged_timezone = prefer_text(source_user.get("timezone"), target_user.get("timezone"), "America/Buenos_Aires")
        merged_weekly_goal = prefer_numeric(source_user.get("weekly_goal_apps"), target_user.get("weekly_goal_apps"), 5)
        merged_blocked = prefer_text(source_user.get("blocked_companies"), target_user.get("blocked_companies"), "")
        merged_preferred = prefer_text(source_user.get("preferred_companies"), target_user.get("preferred_companies"), "")
        merged_digest = prefer_text(source_user.get("digest_mode"), target_user.get("digest_mode"), "realtime")
        merged_last_check = target_user.get("last_check") or source_user.get("last_check")
        merged_github = prefer_text(source_user.get("github_url"), target_user.get("github_url"), "")
        merged_search_mode = prefer_text(source_user.get("search_mode"), target_user.get("search_mode"), "calidad")

        self._execute(
            """
            UPDATE users SET
                name = ?, active_alerts = ?, alert_channel = ?, cv_path = ?, location = ?,
                experience_level = ?, role_type = ?, technologies = ?, job_modality = ?,
                max_job_age_days = ?, match_threshold = ?, check_interval_hours = ?,
                alert_start_hour = ?, alert_end_hour = ?, timezone = ?, weekly_goal_apps = ?,
                blocked_companies = ?, preferred_companies = ?, digest_mode = ?,
                last_check = ?, github_url = ?, search_mode = ?
            WHERE telegram_id = ?
            """,
            (
                merged_name,
                merged_active_alerts,
                merged_alert_channel,
                merged_cv_path,
                merged_location,
                merged_experience,
                merged_role,
                merged_technologies,
                merged_modality,
                merged_max_age,
                merged_match_threshold,
                merged_interval,
                merged_start_hour,
                merged_end_hour,
                merged_timezone,
                merged_weekly_goal,
                merged_blocked,
                merged_preferred,
                merged_digest,
                merged_last_check,
                merged_github,
                merged_search_mode,
                telegram_id,
            ),
        )

        self._execute(
            """INSERT OR IGNORE INTO keywords (telegram_id, keyword)
               SELECT ?, keyword FROM keywords WHERE telegram_id = ?""",
            (telegram_id, web_telegram_id),
        )
        self._execute("DELETE FROM keywords WHERE telegram_id = ?", (web_telegram_id,))

        self._execute(
            """INSERT OR IGNORE INTO jobs_seen (job_hash, telegram_id, source, title, company, url, seen_at)
               SELECT job_hash, ?, source, title, company, url, seen_at
               FROM jobs_seen WHERE telegram_id = ?""",
            (telegram_id, web_telegram_id),
        )
        self._execute("DELETE FROM jobs_seen WHERE telegram_id = ?", (web_telegram_id,))

        for table in (
            "custom_feeds",
            "applications",
            "payments",
            "ai_analyses",
            "web_login_codes",
            "pending_job_batches",
            "batch_interactions",
        ):
            try:
                self._execute(
                    f"UPDATE {table} SET telegram_id = ? WHERE telegram_id = ?",
                    (telegram_id, web_telegram_id),
                )
            except Exception:
                continue

        self._execute(
            "UPDATE web_users SET telegram_id = ? WHERE telegram_id = ?",
            (telegram_id, web_telegram_id),
        )
        self._execute("DELETE FROM users WHERE telegram_id = ?", (web_telegram_id,))
        self._execute("DELETE FROM telegram_link_codes WHERE web_telegram_id = ?", (web_telegram_id,))

        return {
            "telegram_id": telegram_id,
            "plan": self.get_user_plan(telegram_id),
            "has_telegram_link": True,
        }

    def update_user_plan(self, telegram_id: int, plan: str, expires_at: str = None):
        """Actualiza el plan del usuario con limites comerciales vigentes."""
        if expires_at:
            self._execute(
                """UPDATE web_users SET plan = ?, subscription_status = 'active',
                   subscription_expires_at = ? WHERE telegram_id = ?""",
                (plan, expires_at, telegram_id),
            )
        else:
            self._execute(
                "UPDATE web_users SET plan = ? WHERE telegram_id = ?",
                (plan, telegram_id),
            )

        normalized_plan = (plan or "free").lower()
        if normalized_plan == "free":
            self._execute(
                """UPDATE web_users SET
                        ai_analyses_limit = 0,
                        searches_limit    = 3,
                        job_tracker_enabled = 0,
                        interviews_limit = 0,
                        interviews_used = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif normalized_plan == "starter":
            self._execute(
                """UPDATE web_users SET
                        ai_analyses_limit = 0,
                        searches_limit    = 12,
                        job_tracker_enabled = 1,
                        interviews_limit = 0,
                        interviews_used = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif normalized_plan == "pro":
            self._execute(
                """UPDATE web_users SET
                        ai_analyses_limit = 4,
                        searches_limit    = 40,
                        job_tracker_enabled = 1,
                        interviews_limit = 0,
                        interviews_used = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif normalized_plan == "premium":
            self._execute(
                """UPDATE web_users SET
                        ai_analyses_limit = 20,
                        searches_limit    = 120,
                        job_tracker_enabled = 1,
                        interviews_limit = 10,
                        interviews_used = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )

    def get_user_plan(self, telegram_id: int) -> str:
        """Retorna el plan actual del usuario web vinculado.

        Si no existe entrada en web_users, asumimos 'free'. Esto permite
        usar planes sin obligar a que todos los usuarios pasen por el flujo web.
        """
        user = self.get_web_user(telegram_id)
        if not user:
            return "free"
        return (user.get("plan") or "free").lower()

    def increment_usage(self, telegram_id: int, usage_type: str):
        """Incrementa el uso de un tipo especÃ­fico."""
        column = f"{usage_type}_used"
        self._execute(
            f"UPDATE web_users SET {column} = {column} + 1 WHERE telegram_id = ?",
            (telegram_id,),
        )

    def check_usage_limit(self, telegram_id: int, usage_type: str) -> bool:
        """Verifica si el usuario puede usar un recurso.

        Para SQLite se interpretan los lÃ­mites como "por dÃ­a": al primer uso
        de cada dÃ­a se resetean los contadores *_used y se marca la fecha
        actual en usage_period_start. En Supabase se mantiene el comportamiento
        anterior (contadores acumulativos), ya que el esquema vive en
        schema_supabase.sql.
        """
        import datetime

        user = self.get_web_user(telegram_id)
        if not user:
            return True  # Si no tiene cuenta web, usamos comportamiento por defecto

        # Solo aplicamos lÃ³gica de periodo diario en SQLite, donde controlamos el esquema
        if self.db_type != "supabase":
            today = datetime.date.today().isoformat()
            period_start = user.get("usage_period_start")

            # Si es un nuevo dÃ­a (o nunca se seteo), reseteamos contadores diarios
            if period_start != today:
                try:
                    self._execute(
                        """UPDATE web_users SET 
                               ai_analyses_used = 0,
                               searches_used    = 0,
                               usage_period_start = ?
                           WHERE telegram_id = ?""",
                        (today, telegram_id),
                    )
                    # Releer el usuario con contadores reseteados
                    user = self.get_web_user(telegram_id) or user
                except Exception:
                    # Si algo falla, seguimos con los valores actuales para no romper el flujo
                    pass

        used = user.get(f"{usage_type}_used", 0)
        limit = user.get(f"{usage_type}_limit", 0)

        if limit == 0:
            return True  # Ilimitado

        return used < limit

    # ----------------------------------------------------------
    # SAAS: PAGOS
    # ----------------------------------------------------------

    def record_payment(
        self,
        telegram_id: int,
        provider: str,
        amount: float,
        currency: str,
        status: str,
        provider_payment_id: str = None,
    ):
        """Registra un pago."""
        self._execute(
            """INSERT INTO payments 
               (telegram_id, provider, amount, currency, status, provider_payment_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (telegram_id, provider, amount, currency, status, provider_payment_id),
        )

    def get_user_payments(self, telegram_id: int) -> List[Dict]:
        """Obtiene historial de pagos del usuario."""
        return self._fetchall(
            "SELECT * FROM payments WHERE telegram_id = ? ORDER BY created_at DESC",
            (telegram_id,),
        )

    # ----------------------------------------------------------
    # SAAS: ANÃLISIS IA
    # ----------------------------------------------------------

    def record_ai_analysis(
        self,
        telegram_id: int,
        cv_analyzed: bool = False,
        job_matched: bool = False,
        prompt_tokens: int = 0,
        response_tokens: int = 0,
    ):
        """Registra un anÃ¡lisis de IA."""
        self._execute(
            """INSERT INTO ai_analyses 
               (telegram_id, cv_analyzed, job_matched, prompt_tokens, response_tokens, created_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (
                telegram_id,
                1 if cv_analyzed else 0,
                1 if job_matched else 0,
                prompt_tokens,
                response_tokens,
            ),
        )

    def get_user_ai_analyses(self, telegram_id: int) -> List[Dict]:
        """Obtiene historial de anÃ¡lisis de IA del usuario."""
        return self._fetchall(
            "SELECT * FROM ai_analyses WHERE telegram_id = ? ORDER BY created_at DESC",
            (telegram_id,),
        )

    # ----------------------------------------------------------
    # WEBHOOK IDEMPOTENCIA
    # ----------------------------------------------------------

    def is_webhook_processed(self, event_id: str) -> bool:
        """Verifica si un evento de webhook ya fue procesado."""
        result = self._fetchone(
            "SELECT 1 FROM webhook_events WHERE event_id = ?",
            (event_id,),
        )
        return result is not None

    def mark_webhook_processed(self, event_id: str, provider: str, event_type: str):
        """Marca un evento de webhook como procesado."""
        try:
            self._execute(
                "INSERT OR IGNORE INTO webhook_events (event_id, provider, event_type) VALUES (?, ?, ?)",
                (event_id, provider, event_type),
            )
        except Exception as e:
            logger.error(f"Error marking webhook as processed: {e}")

    # ----------------------------------------------------------
    # COMPANY DATA CACHE (LinkedIn Data API)
    # ----------------------------------------------------------

    def get_company_data(self, domain: str) -> Optional[Dict]:
        """
        Obtiene datos cacheados de una empresa.
        
        Returns:
            Dict con 'data' (dict) y 'cached_at' (int timestamp) o None si no existe o expirÃ³
        """
        import time
        
        domain = domain.strip().lower()
        row = self._fetchone(
            "SELECT data, cached_at, expires_at FROM companies WHERE domain = ?",
            (domain,),
        )
        
        if not row:
            return None
        
        # Verificar si expirÃ³
        current_time = int(time.time())
        if current_time > row["expires_at"]:
            return None
        
        try:
            import json
            return {
                "data": json.loads(row["data"]),
                "cached_at": row["cached_at"]
            }
        except (json.JSONDecodeError, KeyError):
            return None

    def set_company_data(self, domain: str, data: Dict, ttl_seconds: int = 604800):
        """
        Guarda datos de empresa en cachÃ©.
        
        Args:
            domain: Dominio de la empresa (ej: google.com)
            data: Dict con datos de la empresa
            ttl_seconds: Tiempo de vida del cachÃ© (default 7 dÃ­as = 604800 seg)
        """
        import time
        import json
        
        domain = domain.strip().lower()
        current_time = int(time.time())
        expires_at = current_time + ttl_seconds
        
        data_json = json.dumps(data, ensure_ascii=False)
        
        try:
            self._execute(
                """INSERT OR REPLACE INTO companies 
                   (domain, data, cached_at, expires_at) 
                   VALUES (?, ?, ?, ?)""",
                (domain, data_json, current_time, expires_at),
            )
        except Exception as e:
            logger.error(f"Error caching company data for {domain}: {e}")

    # ----------------------------------------------------------
    # JOB BATCHES (Smart Summary UX)
    # ----------------------------------------------------------

    def create_job_batch(
        self,
        telegram_id: int,
        jobs: List[Dict],
        source: str = "manual",
        ttl_minutes: int = 30
    ) -> int:
        """
        Crea un batch de jobs pendientes para el nuevo flujo UX.
        
        Args:
            telegram_id: ID del usuario
            jobs: Lista de trabajos encontrados
            source: 'manual' (busqueda) o 'alert' (alerta automatica)
            ttl_minutes: Tiempo de vida del batch (default 30 min)
        
        Returns:
            ID del batch creado
        """
        import json
        import time
        
        current_time = int(time.time())
        expires_at = current_time + (ttl_minutes * 60)
        
        # Calcular conteos por match score
        high = sum(1 for j in jobs if j.get('match_score', 0) >= 80)
        medium = sum(1 for j in jobs if 60 <= j.get('match_score', 0) < 80)
        regular = sum(1 for j in jobs if j.get('match_score', 0) < 60)
        
        jobs_json = json.dumps(jobs, ensure_ascii=False)
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO pending_job_batches 
                   (telegram_id, jobs_json, total_count, high_match_count, 
                    medium_match_count, regular_match_count, source,
                    created_at, expires_at, viewed, fallback_sent)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)""",
                (telegram_id, jobs_json, len(jobs), high, medium, regular,
                 source, current_time, expires_at)
            )
            batch_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"[BATCH] Creado batch {batch_id} para usuario {telegram_id} con {len(jobs)} jobs")
            return batch_id
            
        except Exception as e:
            logger.error(f"Error creando batch para usuario {telegram_id}: {e}")
            return -1
        finally:
            if "conn" in locals() and self.db_path != ":memory:":
                conn.close()

    def get_job_batch(self, batch_id: int) -> Optional[Dict]:
        """Recupera un batch por su ID."""
        import json
        
        row = self._fetchone(
            """SELECT id, telegram_id, jobs_json, total_count, high_match_count,
                      medium_match_count, regular_match_count, source,
                      created_at, expires_at, viewed, fallback_sent
               FROM pending_job_batches 
               WHERE id = ?""",
            (batch_id,)
        )
        
        if not row:
            return None
        
        try:
            return {
                "id": row["id"],
                "telegram_id": row["telegram_id"],
                "jobs": json.loads(row["jobs_json"]),
                "total_count": row["total_count"],
                "high_match_count": row["high_match_count"],
                "medium_match_count": row["medium_match_count"],
                "regular_match_count": row["regular_match_count"],
                "source": row["source"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
                "viewed": row["viewed"],
                "fallback_sent": row["fallback_sent"]
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parseando batch {batch_id}: {e}")
            return None

    def mark_batch_viewed(self, batch_id: int):
        """Marca un batch como visto."""
        self._execute(
            "UPDATE pending_job_batches SET viewed = 1 WHERE id = ?",
            (batch_id,)
        )
        self._log_batch_interaction(batch_id, 'viewed')

    def mark_batch_fallback_sent(self, batch_id: int):
        """Marca que el fallback (envio directo) fue ejecutado."""
        self._execute(
            "UPDATE pending_job_batches SET fallback_sent = 1, viewed = 2 WHERE id = ?",
            (batch_id,)
        )
        self._log_batch_interaction(batch_id, 'fallback_sent')

    def expire_old_batches(self, max_age_hours: int = 24) -> int:
        """
        Limpia batches expirados.
        
        Returns:
            Cantidad de batches eliminados
        """
        import time
        
        cutoff = int(time.time()) - (max_age_hours * 3600)
        
        # Primero marcar como expirados los que vencieron pero no fueron vistos
        self._execute(
            """UPDATE pending_job_batches 
               SET viewed = 2 
               WHERE expires_at < ? AND viewed = 0""",
            (int(time.time()),)
        )
        
        # Log interacciones
        rows = self._fetchall(
            """SELECT id FROM pending_job_batches 
               WHERE expires_at < ? AND viewed = 0""",
            (int(time.time()),)
        )
        for row in rows:
            self._log_batch_interaction(row["id"], 'expired')
        
        # Eliminar batches muy viejos
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM pending_job_batches WHERE created_at < ?",
                (cutoff,)
            )
            deleted = cursor.rowcount
            conn.commit()
        finally:
            if self.db_path != ":memory:":
                conn.close()
        
        if deleted > 0:
            logger.info(f"[BATCH] Eliminados {deleted} batches antiguos")
        
        return deleted

    def get_expired_alert_batches(self, min_age_minutes: int = 30) -> List[Dict]:
        """
        Obtiene batches de ALERTAS que expiraron sin ser vistos.
        Estos se enviaran por fallback.
        
        Returns:
            Lista de batches expirados no vistos
        """
        import time
        import json
        
        cutoff = int(time.time()) - (min_age_minutes * 60)
        
        rows = self._fetchall(
            """SELECT id, telegram_id, jobs_json, total_count,
                      high_match_count, medium_match_count, regular_match_count
               FROM pending_job_batches 
               WHERE source = 'alert' 
                 AND expires_at < ?
                 AND viewed = 0
                 AND fallback_sent = 0""",
            (cutoff,)
        )
        
        batches = []
        for row in rows:
            try:
                batches.append({
                    "id": row["id"],
                    "telegram_id": row["telegram_id"],
                    "jobs": json.loads(row["jobs_json"]),
                    "total_count": row["total_count"],
                    "high_match_count": row["high_match_count"],
                    "medium_match_count": row["medium_match_count"],
                    "regular_match_count": row["regular_match_count"]
                })
            except json.JSONDecodeError:
                continue
        
        return batches

    def _log_batch_interaction(self, batch_id: int, action: str):
        """Loguea una interaccion con el batch (analytics)."""
        import time
        
        # Obtener telegram_id del batch
        row = self._fetchone(
            "SELECT telegram_id FROM pending_job_batches WHERE id = ?",
            (batch_id,)
        )
        
        if row:
            try:
                self._execute(
                    """INSERT INTO batch_interactions 
                       (batch_id, telegram_id, action, timestamp)
                       VALUES (?, ?, ?, ?)""",
                    (batch_id, row["telegram_id"], action, int(time.time()))
                )
            except Exception:
                pass  # No critico, ignorar errores

    # ----------------------------------------------------------
    # SECURITY: AUDIT LOGS
    # ----------------------------------------------------------

    def create_audit_log(
        self,
        user_id: int = None,
        endpoint: str = "",
        method: str = "",
        ip_address: str = "",
        status_code: int = 0,
        duration_ms: float = 0.0,
        timestamp: str = None,
        user_agent: str = None,
        request_id: str = None
    ):
        """
        Create a new audit log entry.
        
        Args:
            user_id: ID of the user making the request
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            ip_address: Client IP address
            status_code: HTTP response status code
            duration_ms: Request duration in milliseconds
            timestamp: ISO format timestamp
            user_agent: Client user agent string
            request_id: Unique request identifier
        """
        try:
            if timestamp:
                self._execute(
                    """INSERT INTO audit_logs 
                       (user_id, endpoint, method, ip_address, status_code, 
                        duration_ms, timestamp, user_agent, request_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, endpoint, method, ip_address, status_code, 
                     duration_ms, timestamp, user_agent, request_id)
                )
            else:
                self._execute(
                    """INSERT INTO audit_logs 
                       (user_id, endpoint, method, ip_address, status_code, 
                        duration_ms, user_agent, request_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, endpoint, method, ip_address, status_code, 
                     duration_ms, user_agent, request_id)
                )
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")

    def get_audit_logs(
        self,
        user_id: int = None,
        start_date: str = None,
        end_date: str = None,
        endpoint: str = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Retrieve audit logs with optional filters.
        
        Args:
            user_id: Filter by user ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            endpoint: Filter by endpoint path
            limit: Maximum number of records
            offset: Pagination offset
        
        Returns:
            List of audit log records
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if endpoint:
            query += " AND endpoint = ?"
            params.append(endpoint)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return self._fetchall(query, tuple(params))

    def cleanup_old_audit_logs(self, days: int = 90) -> int:
        """
        Delete audit logs older than specified days.
        
        Args:
            days: Number of days to keep (default 90)
        
        Returns:
            Number of deleted records
        """
        if self.db_type == "supabase":
            query = """DELETE FROM audit_logs 
                       WHERE timestamp < NOW() - INTERVAL '%s days'"""
            query = query % days
        else:
            query = """DELETE FROM audit_logs 
                       WHERE timestamp < datetime('now', '-%d days')""" % days
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(query)
            deleted = cursor.rowcount
            
            if self.db_path != ":memory:":
                conn.commit()
            
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}")
            return 0
        finally:
            if "conn" in locals() and self.db_path != ":memory:":
                conn.close()

    # ----------------------------------------------------------
    # SECURITY: TOKEN BLACKLIST
    # ----------------------------------------------------------

    def add_to_token_blacklist(self, token_hash: str, expires_at: int):
        """
        Add a token hash to the blacklist.
        
        Args:
            token_hash: SHA256 hash of the token
            expires_at: Unix timestamp when the token expires
        """
        try:
            self._execute(
                "INSERT OR IGNORE INTO token_blacklist (token_hash, expires_at) VALUES (?, ?)",
                (token_hash, expires_at)
            )
        except Exception as e:
            logger.error(f"Error adding token to blacklist: {e}")

    def is_token_blacklisted(self, token_hash: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token_hash: SHA256 hash of the token
        
        Returns:
            True if the token is blacklisted
        """
        try:
            result = self._fetchone(
                "SELECT 1 FROM token_blacklist WHERE token_hash = ?",
                (token_hash,)
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False

    def cleanup_token_blacklist(self) -> int:
        """
        Remove expired tokens from the blacklist.
        
        Returns:
            Number of removed tokens
        """
        import time
        current_time = int(time.time())
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM token_blacklist WHERE expires_at < ?",
                (current_time,)
            )
            deleted = cursor.rowcount
            
            if self.db_path != ":memory:":
                conn.commit()
            
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up token blacklist: {e}")
            return 0
        finally:
            if "conn" in locals() and self.db_path != ":memory:":
                conn.close()

    # ----------------------------------------------------------
    # SECURITY: REFRESH TOKENS
    # ----------------------------------------------------------

    def store_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        family_id: str,
        device_info: str = None,
        expires_at: int = None
    ):
        """
        Store a new refresh token.
        
        Args:
            user_id: User ID
            token_hash: SHA256 hash of the token
            family_id: Token family ID for rotation tracking
            device_info: Optional device information
            expires_at: Unix timestamp when the token expires
        """
        try:
            self._execute(
                """INSERT INTO refresh_tokens 
                   (user_id, token_hash, family_id, device_info, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, token_hash, family_id, device_info, expires_at)
            )
        except Exception as e:
            logger.error(f"Error storing refresh token: {e}")

    def is_refresh_token_valid(self, token_hash: str, family_id: str) -> bool:
        """
        Check if a refresh token is valid (not revoked, not expired, correct family).
        
        Args:
            token_hash: SHA256 hash of the token
            family_id: Expected token family ID
        
        Returns:
            True if the token is valid
        """
        import time
        current_time = int(time.time())
        
        try:
            result = self._fetchone(
                """SELECT 1 FROM refresh_tokens 
                   WHERE token_hash = ? 
                     AND family_id = ?
                     AND expires_at > ?
                     AND revoked_at IS NULL""",
                (token_hash, family_id, current_time)
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error checking refresh token: {e}")
            return False

    def revoke_refresh_token(self, token_hash: str, replaced_by: str = None):
        """
        Mark a refresh token as revoked.
        
        Args:
            token_hash: SHA256 hash of the token to revoke
            replaced_by: Optional hash of the new token that replaced this one
        """
        try:
            if self.db_type == "supabase":
                self._execute(
                    """UPDATE refresh_tokens 
                       SET revoked_at = CURRENT_TIMESTAMP,
                           replaced_by_token_hash = ?
                       WHERE token_hash = ?""",
                    (replaced_by, token_hash)
                )
            else:
                self._execute(
                    """UPDATE refresh_tokens 
                       SET revoked_at = datetime('now'),
                           replaced_by_token_hash = ?
                       WHERE token_hash = ?""",
                    (replaced_by, token_hash)
                )
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")

    def revoke_token_family(self, family_id: str):
        """
        Revoke all tokens in a family (security breach response).
        
        Args:
            family_id: Token family ID to revoke
        """
        try:
            if self.db_type == "supabase":
                self._execute(
                    """UPDATE refresh_tokens 
                       SET revoked_at = CURRENT_TIMESTAMP
                       WHERE family_id = ?
                         AND revoked_at IS NULL""",
                    (family_id,)
                )
            else:
                self._execute(
                    """UPDATE refresh_tokens 
                       SET revoked_at = datetime('now')
                       WHERE family_id = ?
                         AND revoked_at IS NULL""",
                    (family_id,)
                )
        except Exception as e:
            logger.error(f"Error revoking token family: {e}")

    def revoke_all_user_refresh_tokens(self, user_id: int):
        """
        Revoke all refresh tokens for a user (logout all devices).
        
        Args:
            user_id: User ID
        """
        try:
            if self.db_type == "supabase":
                self._execute(
                    """UPDATE refresh_tokens 
                       SET revoked_at = CURRENT_TIMESTAMP
                       WHERE user_id = ?
                         AND revoked_at IS NULL""",
                    (user_id,)
                )
            else:
                self._execute(
                    """UPDATE refresh_tokens 
                       SET revoked_at = datetime('now')
                       WHERE user_id = ?
                         AND revoked_at IS NULL""",
                    (user_id,)
                )
        except Exception as e:
            logger.error(f"Error revoking user refresh tokens: {e}")

    def cleanup_expired_refresh_tokens(self) -> int:
        """
        Remove expired refresh tokens.
        
        Returns:
            Number of removed tokens
        """
        import time
        current_time = int(time.time())
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM refresh_tokens WHERE expires_at < ?",
                (current_time,)
            )
            deleted = cursor.rowcount
            
            if self.db_path != ":memory:":
                conn.commit()
            
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up refresh tokens: {e}")
            return 0
        finally:
            if "conn" in locals() and self.db_path != ":memory:":
                conn.close()

