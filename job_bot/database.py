import sqlite3
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional

# Importación condicional para Postgres
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


POSTGRES_DB_TYPES = {"postgres", "postgresql", "supabase"}


class Database:
    """Maneja las operaciones de base de datos (SQLite o PostgreSQL).

    Permite inyectar parámetros opcionales en tests (por ejemplo, un path
    de SQLite temporal) pero sigue utilizando config.py por defecto en
    producción.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        db_type: Optional[str] = None,
        pg_url: Optional[str] = None,
    ):
        try:
            import config  # Ejecución directa desde job_bot/
        except ImportError:
            from job_bot import config  # Import como paquete job_bot.database

        # Valores por defecto desde config, sobreescribibles en tests
        configured_db_type = (db_type or config.DATABASE_TYPE).lower()
        self.db_type = (
            "supabase" if configured_db_type in POSTGRES_DB_TYPES else configured_db_type
        )
        self.db_path = db_path or config.DATABASE_PATH
        self.pg_url = pg_url or config.DATABASE_URL
        self._sqlite_memory_conn = None

        if self.db_type == "supabase" and not POSTGRES_AVAILABLE:
            logger.error(
                "❌ 'psycopg2' no está instalado. Reinstalá con: pip install psycopg2-binary"
            )
            self.db_type = "sqlite"

        self._init_db()

    def _get_conn(self):
        """Retorna una conexión activa según el motor configurado."""
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
            if self.db_path == ":memory:":
                conn.execute(query, params)
                conn.commit()
            else:
                with conn:
                    conn.execute(query, params)

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
            if self.db_path == ":memory:":
                row = conn.execute(query, params).fetchone()
            else:
                with conn:
                    row = conn.execute(query, params).fetchone()
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
            if self.db_path == ":memory:":
                rows = conn.execute(query, params).fetchall()
            else:
                with conn:
                    rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def _init_db(self):
        """Crea las tablas si no existen."""
        if self.db_type == "supabase":
            # Usar el archivo schema_supabase.sql si es posible o replicar aquí
            # Por ahora replicamos las tablas básicas para que el bot arranque
            queries = [
                "CREATE TABLE IF NOT EXISTS users (telegram_id BIGINT PRIMARY KEY, name TEXT NOT NULL, active_alerts SMALLINT DEFAULT 0, alert_channel TEXT DEFAULT 'telegram', cv_path TEXT, location TEXT, experience_level TEXT, role_type TEXT, technologies TEXT, job_modality TEXT, max_job_age_days INTEGER, check_interval_hours INTEGER, alert_start_hour INTEGER, alert_end_hour INTEGER, timezone TEXT, weekly_goal_apps INTEGER DEFAULT 5, blocked_companies TEXT DEFAULT '', preferred_companies TEXT DEFAULT '', digest_mode TEXT DEFAULT 'realtime', is_admin SMALLINT DEFAULT 0, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, last_check TIMESTAMPTZ)",
                "CREATE TABLE IF NOT EXISTS keywords (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, keyword TEXT, UNIQUE(telegram_id, keyword))",
                "CREATE TABLE IF NOT EXISTS jobs_seen (id BIGSERIAL PRIMARY KEY, job_hash TEXT, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, source TEXT, title TEXT, company TEXT, url TEXT, seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, UNIQUE(job_hash, telegram_id))",
                "CREATE TABLE IF NOT EXISTS custom_feeds (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, feed_url TEXT, feed_name TEXT)",
                "CREATE TABLE IF NOT EXISTS applications (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, job_title TEXT, company TEXT, url TEXT, status TEXT DEFAULT 'aplicado', notes TEXT, applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS web_users (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, plan TEXT DEFAULT 'free', subscription_status TEXT, subscription_provider TEXT, subscription_id TEXT, subscription_expires_at TIMESTAMPTZ, ai_analyses_used INTEGER DEFAULT 0, ai_analyses_limit INTEGER DEFAULT 2, searches_used INTEGER DEFAULT 0, searches_limit INTEGER DEFAULT 5, interviews_used INTEGER DEFAULT 0, interviews_limit INTEGER DEFAULT 20, job_tracker_enabled SMALLINT DEFAULT 0, usage_period_start TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS payments (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, provider TEXT NOT NULL, amount DOUBLE PRECISION NOT NULL, currency TEXT DEFAULT 'USD', status TEXT NOT NULL, provider_payment_id TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS ai_analyses (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, cv_analyzed SMALLINT DEFAULT 0, job_matched SMALLINT DEFAULT 0, prompt_tokens INTEGER, response_tokens INTEGER, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS webhook_events (id BIGSERIAL PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, provider TEXT NOT NULL, event_type TEXT NOT NULL, processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS web_login_codes (code TEXT PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ)",
                "CREATE TABLE IF NOT EXISTS telegram_link_codes (code TEXT PRIMARY KEY, web_telegram_id BIGINT NOT NULL, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ)",
                "CREATE TABLE IF NOT EXISTS companies (domain TEXT PRIMARY KEY, data TEXT NOT NULL, cached_at BIGINT NOT NULL, expires_at BIGINT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS stock_data (ticker TEXT PRIMARY KEY, data TEXT NOT NULL, cached_at BIGINT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS pending_job_batches (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, jobs_json TEXT NOT NULL, total_count INTEGER DEFAULT 0, high_match_count INTEGER DEFAULT 0, medium_match_count INTEGER DEFAULT 0, regular_match_count INTEGER DEFAULT 0, source TEXT DEFAULT 'manual', created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL, viewed SMALLINT DEFAULT 0, fallback_sent SMALLINT DEFAULT 0)",
                "CREATE TABLE IF NOT EXISTS batch_interactions (id BIGSERIAL PRIMARY KEY, batch_id BIGINT NOT NULL REFERENCES pending_job_batches(id) ON DELETE CASCADE, telegram_id BIGINT NOT NULL, action TEXT NOT NULL, timestamp BIGINT NOT NULL)",
            ]
            for q in queries:
                self._execute(q)
            # Migración defensiva para agregar alert_channel si faltara
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
                (
                    "is_admin",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin SMALLINT DEFAULT 0",
                ),
            ]:
                try:
                    self._execute(ddl)
                except Exception:
                    pass
            logger.info("✅ Supabase DB inicializada")
        else:
            conn = self._get_conn()
            context = conn if self.db_path == ":memory:" else conn
            with context as conn:
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
                        is_admin           INTEGER DEFAULT 0,
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
                    ("is_admin", "0"),
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
                    
                    -- Tabla de análisis IA realizados
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
                """)

                # Migración defensiva: columna para controlar el periodo de uso diario
                try:
                    conn.execute(
                        "ALTER TABLE web_users ADD COLUMN usage_period_start TEXT"
                    )
                except Exception:
                    # Si ya existe, ignoramos el error
                    pass
                
                # Migración: columna para contar entrevistas usadas
                try:
                    conn.execute(
                        "ALTER TABLE web_users ADD COLUMN interviews_used INTEGER DEFAULT 0"
                    )
                except Exception:
                    pass
                
                # Migración: columna para límite de entrevistas
                try:
                    conn.execute(
                        "ALTER TABLE web_users ADD COLUMN interviews_limit INTEGER DEFAULT 20"
                    )
                except Exception:
                    pass
            logger.info("✅ SQLite DB inicializada")

            logger.info("✅ Base de datos inicializada: %s", self.db_path)

    # ----------------------------------------------------------
    # USUARIOS
    # ----------------------------------------------------------

    def create_user_if_not_exists(self, telegram_id: int, name: str):
        """Registra un usuario nuevo y le asigna keywords por defecto."""
        try:
            import config
        except ImportError:
            from job_bot import config

        # Ver si el usuario ya existía para no sobreescribir su configuración
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

    def is_admin(self, telegram_id: int) -> bool:
        """Retorna True si el usuario tiene permisos administrativos."""
        user = self.get_user(telegram_id)
        if not user:
            return False
        return bool(user.get("is_admin") or 0)

    def set_admin(self, telegram_id: int, is_admin: bool = True):
        """Promueve o revoca permisos administrativos para un usuario."""
        self._execute(
            "UPDATE users SET is_admin = ? WHERE telegram_id = ?",
            (1 if is_admin else 0, telegram_id),
        )

    def get_all_active_users(self) -> List[Dict]:
        """Retorna todos los usuarios con alertas activas."""
        res = self._fetchall("SELECT * FROM users WHERE active_alerts = 1")
        return res if res is not None else []

    def get_users_due_for_check(self) -> List[Dict]:
        """Retorna usuarios cuyo intervalo de chequeo ya venció."""
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

            # Normalizar zonas horarias antiguas o inválidas
            if tz_name == "America/Buenos_Aires":
                mapped_tz = "America/Argentina/Buenos_Aires"
            else:
                mapped_tz = tz_name

            try:
                tz = zoneinfo.ZoneInfo(mapped_tz)
            except Exception:
                # Fallback robusto: si no existe, usar UTC para no romper el scheduler
                logger.warning(
                    "Timezone '%s' inválida, usando UTC para scheduler", tz_name
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
        """Activa o desactiva las alertas automáticas de un usuario."""
        self._execute(
            "UPDATE users SET active_alerts = ? WHERE telegram_id = ?",
            (1 if active else 0, telegram_id),
        )

    def set_user_location(self, telegram_id: int, location: str):
        """Actualiza la ubicación de búsqueda de un usuario."""
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
        """Actualiza el timestamp del último chequeo."""
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
        """Retorna la configuración de horarios del usuario."""
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
        """Configura el modo de búsqueda (volumen o calidad)."""
        valid_modes = ["volumen", "calidad"]
        if mode not in valid_modes:
            return

        # Migración defensiva: agregar columna si no existe
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
        """Retorna el modo de búsqueda del usuario."""
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

        def _int_or(value, default):
            try:
                return default if value is None else int(value)
            except (TypeError, ValueError):
                return default

        return {
            "experience_level": user.get("experience_level") or "junior",
            "role_type": user.get("role_type") or "",
            "technologies": user.get("technologies") or "",
            "job_modality": user.get("job_modality") or "cualquiera",
            "max_job_age_days": _int_or(user.get("max_job_age_days"), 30),
            "match_threshold": _int_or(user.get("match_threshold"), 70),
        }

    def generate_smart_keywords(self, telegram_id: int) -> List[str]:
        """
        Genera keywords de búsqueda inteligentes basadas en el perfil.
        Combina tecnologías + nivel + rol para crear búsquedas efectivas.
        """
        profile = self.get_user_profile(telegram_id)
        techs = [t.strip() for t in profile["technologies"].split(",") if t.strip()]
        role = profile.get("role_type", "").strip()
        level = profile.get("experience_level", "junior")

        # Mapear nivel a términos de búsqueda
        level_terms = {
            "sin_experiencia": [
                "trainee",
                "pasantía",
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

        # Combinar cada tecnología con el nivel
        for tech in techs[:5]:  # Máximo 5 tecnologías
            # "python junior", "python trainee"
            for lkw in level_kws[:2]:  # Top 2 level terms
                keywords.append(f"{tech} {lkw}")
            # También buscar solo la tecnología
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

        return unique_kws[:10]  # Máximo 10 keywords

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
        """Elimina una keyword específica."""
        self._execute(
            "DELETE FROM keywords WHERE telegram_id = ? AND keyword = ?",
            (telegram_id, keyword.strip()),
        )

    # ----------------------------------------------------------
    # DEDUPLICACIÓN DE TRABAJOS
    # ----------------------------------------------------------

    @staticmethod
    def _hash_url(url: str) -> str:
        """Genera un hash MD5 de la URL para identificar trabajos únicos."""
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
    # ESTADÍSTICAS (para la landing page)
    # ----------------------------------------------------------

    def get_stats(self) -> Dict:
        """Retorna estadísticas generales del bot."""
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
        """Elimina toda la información de un usuario (GDPR)."""
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
        """Registra una nueva postulación."""
        self._execute(
            """
            INSERT INTO applications (telegram_id, job_title, company, url, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (telegram_id, job_title, company, url, notes),
        )

    def get_user_applications(self, telegram_id: int) -> List[Dict]:
        """Retorna todas las postulaciones de un usuario."""
        return self._fetchall(
            "SELECT * FROM applications WHERE telegram_id = ? ORDER BY applied_at DESC",
            (telegram_id,),
        )

    def get_weekly_applications_count(self, telegram_id: int) -> int:
        """Cuenta las postulaciones de la última semana calendario para el usuario."""
        import datetime

        apps = self.get_user_applications(telegram_id) or []
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
                # Normalizar sin tz para comparación simple
                if created_dt.tzinfo is not None:
                    created_dt = created_dt.astimezone(datetime.timezone.utc).replace(
                        tzinfo=None
                    )
            except Exception:
                continue
            if created_dt >= seven_days_ago:
                count += 1
        return count

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
        """Actualiza el estado de una postulación (aplicado, entrevista, rechazado, oferta)."""
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
        self._execute(
            """INSERT OR IGNORE INTO web_users 
               (telegram_id, email, password_hash, plan, created_at)
               VALUES (?, ?, ?, 'free', CURRENT_TIMESTAMP)""",
            (telegram_id, email, password_hash),
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
        """Consume un codigo de vinculación Telegram y devuelve la cuenta web asociada."""
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
            raise ValueError("Ese usuario de Telegram ya está vinculado a otra cuenta")

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
        """Actualiza el plan del usuario."""
        # Actualizar plan + metadatos de suscripción
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

        # Ajustar límites según el plan elegido
        plan = (plan or "free").lower()
        if plan == "free":
            # Valores conservadores para el tier gratuito
            self._execute(
                """UPDATE web_users SET 
                        ai_analyses_limit = 2,
                        searches_limit    = 5,
                        job_tracker_enabled = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif plan == "pro":
            # Pro: búsquedas y análisis prácticamente ilimitados + tracker
            self._execute(
                """UPDATE web_users SET 
                        ai_analyses_limit = 0,
                        searches_limit    = 0,
                        job_tracker_enabled = 1
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif plan == "premium":
            # Premium: igual que Pro pero lo usamos para gatear features extra
            self._execute(
                """UPDATE web_users SET 
                        ai_analyses_limit = 0,
                        searches_limit    = 0,
                        job_tracker_enabled = 1
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )

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
                        searches_limit    = 5,
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
                        searches_limit    = 30,
                        job_tracker_enabled = 1,
                        interviews_limit = 0,
                        interviews_used = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif normalized_plan == "pro":
            self._execute(
                """UPDATE web_users SET
                        ai_analyses_limit = 5,
                        searches_limit    = 80,
                        job_tracker_enabled = 1,
                        interviews_limit = 0,
                        interviews_used = 0
                   WHERE telegram_id = ?""",
                (telegram_id,),
            )
        elif normalized_plan == "premium":
            self._execute(
                """UPDATE web_users SET
                        ai_analyses_limit = 30,
                        searches_limit    = 0,
                        job_tracker_enabled = 1,
                        interviews_limit = 20,
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
        """Incrementa el uso de un tipo específico."""
        column = f"{usage_type}_used"
        self._execute(
            f"UPDATE web_users SET {column} = {column} + 1 WHERE telegram_id = ?",
            (telegram_id,),
        )

    def check_usage_limit(self, telegram_id: int, usage_type: str) -> bool:
        """Verifica si el usuario puede usar un recurso.

        Para SQLite se interpretan los límites como "por día": al primer uso
        de cada día se resetean los contadores *_used y se marca la fecha
        actual en usage_period_start. En Supabase se mantiene el comportamiento
        anterior (contadores acumulativos), ya que el esquema vive en
        schema_supabase.sql.
        """
        import datetime

        user = self.get_web_user(telegram_id)
        if not user:
            return True  # Si no tiene cuenta web, usamos comportamiento por defecto

        # Solo aplicamos lógica de periodo diario en SQLite, donde controlamos el esquema
        if self.db_type != "supabase":
            today = datetime.date.today().isoformat()
            period_start = user.get("usage_period_start")

            # Si es un nuevo día (o nunca se seteo), reseteamos contadores diarios
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
    # SAAS: ANÁLISIS IA
    # ----------------------------------------------------------

    def record_ai_analysis(
        self,
        telegram_id: int,
        cv_analyzed: bool = False,
        job_matched: bool = False,
        prompt_tokens: int = 0,
        response_tokens: int = 0,
    ):
        """Registra un análisis de IA."""
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
        """Obtiene historial de análisis de IA del usuario."""
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
            Dict con 'data' (dict) y 'cached_at' (int timestamp) o None si no existe o expiró
        """
        import time
        
        domain = domain.strip().lower()
        row = self._fetchone(
            "SELECT data, cached_at, expires_at FROM companies WHERE domain = ?",
            (domain,),
        )
        
        if not row:
            return None
        
        # Verificar si expiró
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
        Guarda datos de empresa en caché.
        
        Args:
            domain: Dominio de la empresa (ej: google.com)
            data: Dict con datos de la empresa
            ttl_seconds: Tiempo de vida del caché (default 7 días = 604800 seg)
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
        cursor = self._get_conn().cursor()
        cursor.execute(
            "DELETE FROM pending_job_batches WHERE created_at < ?",
            (cutoff,)
        )
        deleted = cursor.rowcount
        
        if self.db_path != ":memory:":
            self._get_conn().commit()
        
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
