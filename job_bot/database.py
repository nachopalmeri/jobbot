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


class Database:
    """Maneja las operaciones de base de datos (SQLite o PostgreSQL)."""

    def __init__(self):
        import config
        self.db_type = config.DATABASE_TYPE
        self.db_path = config.DATABASE_PATH
        self.pg_url = config.DATABASE_URL
        
        if self.db_type == "supabase" and not POSTGRES_AVAILABLE:
            logger.error("❌ 'psycopg2' no está instalado. Reinstalá con: pip install psycopg2-binary")
            self.db_type = "sqlite"

        self._init_db()

    def _get_conn(self):
        """Retorna una conexión activa según el motor configurado."""
        if self.db_type == "supabase":
            conn = psycopg2.connect(self.pg_url, cursor_factory=RealDictCursor)
            conn.autocommit = True
            return conn
        else:
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
                if "users" in query: query += " ON CONFLICT (telegram_id) DO NOTHING"
                elif "keywords" in query: query += " ON CONFLICT (telegram_id, keyword) DO NOTHING"
                elif "jobs_seen" in query: query += " ON CONFLICT (job_hash, telegram_id) DO NOTHING"
            
            conn = self._get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
            finally:
                conn.close()
        else:
            with self._get_conn() as conn:
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
            with self._get_conn() as conn:
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
            with self._get_conn() as conn:
                rows = conn.execute(query, params).fetchall()
                return [dict(r) for r in rows]

    def _init_db(self):
        """Crea las tablas si no existen."""
        if self.db_type == "supabase":
            # Usar el archivo schema_supabase.sql si es posible o replicar aquí
            # Por ahora replicamos las tablas básicas para que el bot arranque
            queries = [
                "CREATE TABLE IF NOT EXISTS users (telegram_id BIGINT PRIMARY KEY, name TEXT NOT NULL, active_alerts SMALLINT DEFAULT 0, cv_path TEXT, location TEXT, experience_level TEXT, role_type TEXT, technologies TEXT, job_modality TEXT, max_job_age_days INTEGER, check_interval_hours INTEGER, alert_start_hour INTEGER, alert_end_hour INTEGER, timezone TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, last_check TIMESTAMPTZ)",
                "CREATE TABLE IF NOT EXISTS keywords (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, keyword TEXT, UNIQUE(telegram_id, keyword))",
                "CREATE TABLE IF NOT EXISTS jobs_seen (id BIGSERIAL PRIMARY KEY, job_hash TEXT, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, source TEXT, title TEXT, company TEXT, url TEXT, seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, UNIQUE(job_hash, telegram_id))",
                "CREATE TABLE IF NOT EXISTS custom_feeds (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, feed_url TEXT, feed_name TEXT)",
                "CREATE TABLE IF NOT EXISTS applications (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, job_title TEXT, company TEXT, url TEXT, status TEXT DEFAULT 'aplicado', notes TEXT, applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)"
            ]
            for q in queries:
                self._execute(q)
            logger.info("✅ Supabase DB inicializada")
        else:
            with self._get_conn() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id        INTEGER PRIMARY KEY,
                        name               TEXT    NOT NULL,
                        active_alerts      INTEGER DEFAULT 0,
                        cv_path            TEXT,
                        location           TEXT    DEFAULT 'Buenos Aires Argentina',
                        experience_level   TEXT    DEFAULT 'junior',
                        role_type          TEXT    DEFAULT '',
                        technologies       TEXT    DEFAULT '',
                        job_modality       TEXT    DEFAULT 'cualquiera',
                        max_job_age_days   INTEGER DEFAULT 30,
                        check_interval_hours INTEGER DEFAULT 6,
                        alert_start_hour   INTEGER DEFAULT 8,
                        alert_end_hour     INTEGER DEFAULT 22,
                        timezone           TEXT    DEFAULT 'America/Buenos_Aires',
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
                """)
                # Migraciones para SQLite si faltan columnas
                for col, default in [
                    ("experience_level", "'junior'"), ("role_type", "''"), ("technologies", "''"),
                    ("job_modality", "'cualquiera'"), ("max_job_age_days", "30"),
                    ("check_interval_hours", "6"), ("alert_start_hour", "8"),
                    ("alert_end_hour", "22"), ("timezone", "'America/Buenos_Aires'"),
                    ("github_url", "''")
                ]:
                    try: conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {default}")
                    except: pass
            logger.info("✅ SQLite DB inicializada")

            logger.info("✅ Base de datos inicializada: %s", self.db_path)

    # ----------------------------------------------------------
    # USUARIOS
    # ----------------------------------------------------------

    def create_user_if_not_exists(self, telegram_id: int, name: str):
        """Registra un usuario nuevo y le asigna keywords por defecto."""
        import config
        self._execute(
            "INSERT OR IGNORE INTO users (telegram_id, name) VALUES (?, ?)",
            (telegram_id, name)
        )

        row = self._fetchone("SELECT COUNT(*) as count FROM keywords WHERE telegram_id = ?", (telegram_id,))
        count = row["count"] if row else 0

        if count == 0:
            for kw in config.DEFAULT_KEYWORDS:
                self._execute(
                    "INSERT OR IGNORE INTO keywords (telegram_id, keyword) VALUES (?, ?)",
                    (telegram_id, kw)
                )

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Retorna los datos de un usuario o None si no existe."""
        return self._fetchone("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))

    def get_all_active_users(self) -> List[Dict]:
        """Retorna todos los usuarios con alertas activas."""
        res = self._fetchall("SELECT * FROM users WHERE active_alerts = 1")
        return res if res is not None else []

    def get_users_due_for_check(self) -> List[Dict]:
        """Retorna usuarios cuyo intervalo de chequeo ya venció."""
        import datetime
        try: import zoneinfo
        except: from backports import zoneinfo

        active_res = self._fetchall("SELECT * FROM users WHERE active_alerts = 1")
        active = active_res if active_res is not None else []
        due_users = []
        
        for user in active:
            tz_name = user.get("timezone") or "America/Buenos_Aires"
            try: tz = zoneinfo.ZoneInfo(tz_name)
            except: tz = zoneinfo.ZoneInfo("America/Buenos_Aires")

            now_user = datetime.datetime.now(tz)
            current_hour = now_user.hour

            start_h = int(user.get("alert_start_hour") or 8)
            end_h = int(user.get("alert_end_hour") or 22)
            
            if start_h <= end_h:
                if not (start_h <= current_hour < end_h): continue
            else:
                if end_h <= current_hour < start_h: continue

            interval_h = int(user.get("check_interval_hours") or 6)
            last_check_str = user.get("last_check")
            if last_check_str:
                try:
                    # En Postgres el resultado ya suele ser un datetime si RealDictCursor hace su magia,
                    # pero sqlite devuelve string. Manejamos ambos.
                    if isinstance(last_check_str, str):
                        last_check = datetime.datetime.fromisoformat(last_check_str.replace("Z", "+00:00"))
                    else:
                        last_check = last_check_str
                        
                    if last_check.tzinfo is None:
                        last_check = last_check.replace(tzinfo=datetime.timezone.utc)
                    
                    elapsed = (now_user - last_check).total_seconds() / 3600
                    if elapsed < interval_h: continue
                except: pass

            due_users.append(user)
        return due_users

    def set_alerts_active(self, telegram_id: int, active: bool):
        """Activa o desactiva las alertas automáticas de un usuario."""
        self._execute("UPDATE users SET active_alerts = ? WHERE telegram_id = ?", (1 if active else 0, telegram_id))

    def set_user_location(self, telegram_id: int, location: str):
        """Actualiza la ubicación de búsqueda de un usuario."""
        self._execute("UPDATE users SET location = ? WHERE telegram_id = ?", (location, telegram_id))

    def set_user_cv(self, telegram_id: int, cv_path: str):
        """Guarda la ruta del CV del usuario."""
        self._execute("UPDATE users SET cv_path = ? WHERE telegram_id = ?", (cv_path, telegram_id))

    def update_last_check(self, telegram_id: int):
        """Actualiza el timestamp del último chequeo."""
        if self.db_type == "supabase":
            self._execute("UPDATE users SET last_check = CURRENT_TIMESTAMP WHERE telegram_id = ?", (telegram_id,))
        else:
            self._execute("UPDATE users SET last_check = CURRENT_TIMESTAMP WHERE telegram_id = ?", (telegram_id,))

    def set_user_profile(self, telegram_id: int, experience_level: str,
                         role_type: str, technologies: str, job_modality: str,
                         max_job_age_days: int = 30):
        """Guarda el perfil completo del usuario."""
        self._execute("""
            UPDATE users SET
                experience_level = ?, role_type = ?, technologies = ?,
                job_modality = ?, max_job_age_days = ?
            WHERE telegram_id = ?
        """, (experience_level, role_type, technologies, job_modality, max_job_age_days, telegram_id))

    def set_user_schedule(self, telegram_id: int, interval_hours: int,
                          start_hour: int, end_hour: int,
                          timezone: str = "America/Buenos_Aires"):
        """Configura el horario de alertas personalizado del usuario."""
        self._execute("""
            UPDATE users SET
                check_interval_hours = ?, alert_start_hour = ?,
                alert_end_hour = ?, timezone = ?
            WHERE telegram_id = ?
        """, (interval_hours, start_hour, end_hour, timezone, telegram_id))

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
        return {
            "check_interval_hours": int(user.get("check_interval_hours") or 6),
            "alert_start_hour": int(user.get("alert_start_hour") or 8),
            "alert_end_hour": int(user.get("alert_end_hour") or 22),
            "timezone": user.get("timezone") or "America/Buenos_Aires",
        }

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
            }
        return {
            "experience_level": user.get("experience_level", "junior"),
            "role_type": user.get("role_type", ""),
            "technologies": user.get("technologies", ""),
            "job_modality": user.get("job_modality", "cualquiera"),
            "max_job_age_days": int(user.get("max_job_age_days", 30)),
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
            "sin_experiencia": ["trainee", "pasantía", "pasantia", "aprendiz", "entry level", "junior"],
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
        rows = self._fetchall("SELECT keyword FROM keywords WHERE telegram_id = ? ORDER BY keyword", (telegram_id,))
        return [r["keyword"] for r in rows] if rows else []

    def set_user_keywords(self, telegram_id: int, keywords: List[str]):
        """Reemplaza completamente las keywords del usuario."""
        self._execute("DELETE FROM keywords WHERE telegram_id = ?", (telegram_id,))
        for kw in keywords:
            kw = kw.strip()
            if kw:
                self._execute("INSERT OR IGNORE INTO keywords (telegram_id, keyword) VALUES (?, ?)", (telegram_id, kw))

    def add_keyword(self, telegram_id: int, keyword: str) -> bool:
        """Agrega una keyword individual."""
        try:
            self._execute("INSERT INTO keywords (telegram_id, keyword) VALUES (?, ?)", (telegram_id, keyword.strip()))
            return True
        except:
            return False

    def remove_keyword(self, telegram_id: int, keyword: str):
        """Elimina una keyword específica."""
        self._execute("DELETE FROM keywords WHERE telegram_id = ? AND keyword = ?", (telegram_id, keyword.strip()))

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
        row = self._fetchone("SELECT id FROM jobs_seen WHERE telegram_id = ? AND job_hash = ?", (telegram_id, job_hash))
        return row is not None

    def mark_job_seen(self, telegram_id: int, job: Dict):
        """Marca un trabajo como visto para este usuario."""
        if not job.get("url"): return
        job_hash = self._hash_url(job["url"])
        self._execute("""
            INSERT OR IGNORE INTO jobs_seen (job_hash, telegram_id, source, title, company, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_hash, telegram_id, job.get("source", ""),
            job.get("title", "")[:200], job.get("company", "")[:100], job.get("url", "")[:500]
        ))

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
        res = self._fetchall("SELECT * FROM custom_feeds WHERE telegram_id = ?", (telegram_id,))
        return res if res is not None else []

    def add_custom_feed(self, telegram_id: int, url: str, name: str):
        """Agrega un feed RSS personalizado."""
        self._execute("INSERT INTO custom_feeds (telegram_id, feed_url, feed_name) VALUES (?, ?, ?)", (telegram_id, url.strip(), name.strip()))

    def remove_custom_feed(self, telegram_id: int, feed_id: int):
        """Elimina un feed RSS personalizado."""
        self._execute("DELETE FROM custom_feeds WHERE id = ? AND telegram_id = ?", (feed_id, telegram_id))

    # ----------------------------------------------------------
    # ESTADÍSTICAS (para la landing page)
    # ----------------------------------------------------------

    def get_stats(self) -> Dict:
        """Retorna estadísticas generales del bot."""
        u = self._fetchone("SELECT COUNT(*) as count FROM users")
        a = self._fetchone("SELECT COUNT(*) as count FROM users WHERE active_alerts = 1")
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
    def add_application(self, telegram_id: int, job_title: str, company: str, url: str, notes: str = ""):
        """Registra una nueva postulación."""
        self._execute("""
            INSERT INTO applications (telegram_id, job_title, company, url, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, job_title, company, url, notes))

    def get_user_applications(self, telegram_id: int) -> List[Dict]:
        """Retorna todas las postulaciones de un usuario."""
        return self._fetchall("SELECT * FROM applications WHERE telegram_id = ? ORDER BY applied_at DESC", (telegram_id,))

    def update_application_status(self, app_id: int, telegram_id: int, status: str):
        """Actualiza el estado de una postulación (aplicado, entrevista, rechazado, oferta)."""
        self._execute("UPDATE applications SET status = ? WHERE id = ? AND telegram_id = ?", (status, app_id, telegram_id))

    def set_github_url(self, telegram_id: int, github_url: str):
        """Guarda la URL de GitHub del usuario."""
        self._execute("UPDATE users SET github_url = ? WHERE telegram_id = ?", (github_url.strip(), telegram_id))
