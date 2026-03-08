"""
database.py - Capa de base de datos usando SQLite
Sin dependencias externas de DB, funciona out-of-the-box en cualquier PC.
"""

import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class Database:
    """Maneja todas las operaciones de la base de datos SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Retorna una conexión con row_factory para acceso por nombre de columna."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Mejor performance concurrente
        return conn

    def _init_db(self):
        """Crea las tablas si no existen."""
        with self._get_conn() as conn:
            conn.executescript("""
                -- Usuarios registrados en el bot
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id      INTEGER PRIMARY KEY,
                    name             TEXT    NOT NULL,
                    active_alerts    INTEGER DEFAULT 0,
                    cv_path          TEXT,
                    location         TEXT    DEFAULT 'Buenos Aires Argentina',
                    experience_level TEXT    DEFAULT 'junior',
                    role_type        TEXT    DEFAULT '',
                    technologies     TEXT    DEFAULT '',
                    job_modality     TEXT    DEFAULT 'cualquiera',
                    max_job_age_days INTEGER DEFAULT 30,
                    created_at       TEXT    DEFAULT CURRENT_TIMESTAMP,
                    last_check       TEXT
                );

                -- Keywords de búsqueda por usuario
                CREATE TABLE IF NOT EXISTS keywords (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    keyword     TEXT    NOT NULL,
                    FOREIGN KEY(telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                    UNIQUE(telegram_id, keyword)
                );

                -- Trabajos ya vistos (para evitar duplicados)
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

                -- Feeds RSS personalizados por usuario
                CREATE TABLE IF NOT EXISTS custom_feeds (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    feed_url    TEXT    NOT NULL,
                    feed_name   TEXT    NOT NULL,
                    FOREIGN KEY(telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                );
            """)

            # Migración: agregar columnas nuevas a DBs existentes
            for col, default in [
                ("experience_level", "'junior'"),
                ("role_type", "''"),
                ("technologies", "''"),
                ("job_modality", "'cualquiera'"),
                ("max_job_age_days", "30"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {default}")
                except sqlite3.OperationalError:
                    pass  # Columna ya existe

            logger.info("✅ Base de datos inicializada: %s", self.db_path)

    # ----------------------------------------------------------
    # USUARIOS
    # ----------------------------------------------------------

    def create_user_if_not_exists(self, telegram_id: int, name: str):
        """Registra un usuario nuevo y le asigna keywords por defecto."""
        import config  # Import tardío para evitar importación circular
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO users (telegram_id, name)
                VALUES (?, ?)
            """, (telegram_id, name))

            # Verificar si ya tenía keywords
            count = conn.execute(
                "SELECT COUNT(*) FROM keywords WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()[0]

            if count == 0:
                for kw in config.DEFAULT_KEYWORDS:
                    conn.execute("""
                        INSERT OR IGNORE INTO keywords (telegram_id, keyword)
                        VALUES (?, ?)
                    """, (telegram_id, kw))

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Retorna los datos de un usuario o None si no existe."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_active_users(self) -> List[Dict]:
        """Retorna todos los usuarios con alertas activas."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE active_alerts = 1"
            ).fetchall()
            return [dict(r) for r in rows]

    def set_alerts_active(self, telegram_id: int, active: bool):
        """Activa o desactiva las alertas automáticas de un usuario."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE users SET active_alerts = ? WHERE telegram_id = ?",
                (1 if active else 0, telegram_id)
            )

    def set_user_location(self, telegram_id: int, location: str):
        """Actualiza la ubicación de búsqueda de un usuario."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE users SET location = ? WHERE telegram_id = ?",
                (location, telegram_id)
            )

    def set_user_cv(self, telegram_id: int, cv_path: str):
        """Guarda la ruta del CV del usuario."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE users SET cv_path = ? WHERE telegram_id = ?",
                (cv_path, telegram_id)
            )

    def update_last_check(self, telegram_id: int):
        """Actualiza el timestamp del último chequeo."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE users SET last_check = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                (telegram_id,)
            )

    def set_user_profile(self, telegram_id: int, experience_level: str,
                         role_type: str, technologies: str, job_modality: str,
                         max_job_age_days: int = 30):
        """Guarda el perfil completo del usuario."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE users SET
                    experience_level = ?,
                    role_type = ?,
                    technologies = ?,
                    job_modality = ?,
                    max_job_age_days = ?
                WHERE telegram_id = ?
            """, (experience_level, role_type, technologies, job_modality, max_job_age_days, telegram_id))

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
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT keyword FROM keywords WHERE telegram_id = ? ORDER BY keyword",
                (telegram_id,)
            ).fetchall()
            return [r["keyword"] for r in rows]

    def set_user_keywords(self, telegram_id: int, keywords: List[str]):
        """Reemplaza completamente las keywords del usuario."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM keywords WHERE telegram_id = ?", (telegram_id,))
            for kw in keywords:
                kw = kw.strip()
                if kw:
                    conn.execute(
                        "INSERT OR IGNORE INTO keywords (telegram_id, keyword) VALUES (?, ?)",
                        (telegram_id, kw)
                    )

    def add_keyword(self, telegram_id: int, keyword: str) -> bool:
        """Agrega una keyword individual. Retorna True si fue nueva."""
        with self._get_conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO keywords (telegram_id, keyword) VALUES (?, ?)",
                    (telegram_id, keyword.strip())
                )
                return True
            except sqlite3.IntegrityError:
                return False  # Ya existía

    def remove_keyword(self, telegram_id: int, keyword: str):
        """Elimina una keyword específica."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM keywords WHERE telegram_id = ? AND keyword = ?",
                (telegram_id, keyword.strip())
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
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM jobs_seen WHERE telegram_id = ? AND job_hash = ?",
                (telegram_id, job_hash)
            ).fetchone()
            return row is not None

    def mark_job_seen(self, telegram_id: int, job: Dict):
        """Marca un trabajo como visto para este usuario."""
        if not job.get("url"):
            return
        job_hash = self._hash_url(job["url"])
        with self._get_conn() as conn:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO jobs_seen
                        (job_hash, telegram_id, source, title, company, url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    job_hash,
                    telegram_id,
                    job.get("source", ""),
                    job.get("title", "")[:200],
                    job.get("company", "")[:100],
                    job.get("url", "")[:500],
                ))
            except Exception as e:
                logger.error("Error marcando job como visto: %s", e)

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
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM custom_feeds WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_custom_feed(self, telegram_id: int, url: str, name: str):
        """Agrega un feed RSS personalizado."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO custom_feeds (telegram_id, feed_url, feed_name) VALUES (?, ?, ?)",
                (telegram_id, url.strip(), name.strip())
            )

    def remove_custom_feed(self, telegram_id: int, feed_id: int):
        """Elimina un feed RSS personalizado."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM custom_feeds WHERE id = ? AND telegram_id = ?",
                (feed_id, telegram_id)
            )

    # ----------------------------------------------------------
    # ESTADÍSTICAS (para la landing page)
    # ----------------------------------------------------------

    def get_stats(self) -> Dict:
        """Retorna estadísticas generales del bot para la API pública."""
        with self._get_conn() as conn:
            total_users = conn.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            active_users = conn.execute(
                "SELECT COUNT(*) FROM users WHERE active_alerts = 1"
            ).fetchone()[0]

            total_jobs = conn.execute(
                "SELECT COUNT(*) FROM jobs_seen"
            ).fetchone()[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_jobs_found": total_jobs,
            }
