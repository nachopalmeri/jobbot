-- Esquema para Supabase (PostgreSQL)
-- JobBot v2

-- 1. Tabla de Usuarios
CREATE TABLE IF NOT EXISTS users (
    telegram_id        BIGINT PRIMARY KEY,
    name               TEXT    NOT NULL,
    active_alerts      SMALLINT DEFAULT 0,
    alert_channel      TEXT    DEFAULT 'telegram',
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
    weekly_goal_apps   INTEGER DEFAULT 5,
    blocked_companies  TEXT    DEFAULT '',
    preferred_companies TEXT   DEFAULT '',
    digest_mode        TEXT    DEFAULT 'realtime',
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_check         TIMESTAMPTZ
);

-- 2. Keywords por usuario
CREATE TABLE IF NOT EXISTS keywords (
    id          BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    keyword     TEXT    NOT NULL,
    UNIQUE(telegram_id, keyword)
);

-- 3. Trabajos vistos (Deduplicación)
CREATE TABLE IF NOT EXISTS jobs_seen (
    id          BIGSERIAL PRIMARY KEY,
    job_hash    TEXT    NOT NULL,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    source      TEXT,
    title       TEXT,
    company     TEXT,
    url         TEXT,
    seen_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_hash, telegram_id)
);

-- 4. Feeds RSS personalizados
CREATE TABLE IF NOT EXISTS custom_feeds (
    id          BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    feed_url    TEXT    NOT NULL,
    feed_name   TEXT    NOT NULL
);

-- Índices para performance (query-missing-indexes rule)
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active_alerts) WHERE active_alerts = 1;
CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs_seen(job_hash, telegram_id);
CREATE INDEX IF NOT EXISTS idx_keywords_user ON keywords(telegram_id);
