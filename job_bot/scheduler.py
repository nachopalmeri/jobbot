"""
scheduler.py - Lógica de chequeo periódico y formato de notificaciones.

Ejecutado cada SCHEDULER_POLL_MINUTES minutos para usuarios cuyo
intervalo personal haya vencido y estén dentro de su ventana horaria.
"""

import html
import asyncio
import logging
from typing import List, Dict

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Imports tolerantes al contexto de ejecución
try:
    import config
except ImportError:
    from job_bot import config

try:
    from database import Database
except ImportError:
    from job_bot.database import Database

try:
    from job_scraper import JobScraper
except ImportError:
    from job_bot.job_scraper import JobScraper

try:
    from cv_analyzer import parse_cv, format_job_with_score
except ImportError:
    from job_bot.cv_analyzer import parse_cv, format_job_with_score

logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# FORMATO DE MENSAJES
# ----------------------------------------------------------

def format_job_message(job: Dict) -> str:
    """
    Convierte un dict de trabajo en un mensaje formateado para Telegram usando HTML.
    Esto es más robusto ante caracteres especiales que el Markdown.
    """
    def safe(text: str) -> str:
        if not text: return ""
        # Escapar caracteres HTML y truncar
        return html.escape(str(text))[:200]

    title   = safe(job.get("title",    "Sin título"))
    company = safe(job.get("company",  "N/A"))
    loc     = safe(job.get("location", "N/A"))
    source  = safe(job.get("source",   "Desconocida"))
    url     = html.escape(job.get("url", "")) # Escapar URL también por seguridad
    date    = safe(job.get("date",     ""))
    desc    = safe(job.get("description", ""))

    lines = [
        "🆕 <b>Nueva oportunidad encontrada</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"💼 <b>{title}</b>",
        f"🏢 {company}",
        f"📍 {loc}",
        f"🌐 Fuente: <i>{source}</i>",
    ]

    if desc:
        lines.append(f"📝 <i>{desc[:180]}...</i>")

    if date:
        lines.append(f"📅 {date}")

    if url:
        lines.append(f"\n🔗 <a href='{url}'>Ver oferta completa</a>")

    # Si el job tiene match info (del CV analyzer)
    if job.get("match_score") is not None:
        score = job["match_score"]
        if score >= 80:
            score_emoji = "🟢"
        elif score >= 60:
            score_emoji = "🟡"
        elif score >= 40:
            score_emoji = "🟠"
        else:
            score_emoji = "🔴"
        lines.append(f"\n{score_emoji} <b>Match con tu CV: {score}%</b>")
        if job.get("match_info"):
            lines.append(f"📝 {job['match_info']}")

    return "\n".join(lines)


def format_summary_header(count: int, interval_hours: int = 6) -> str:
    """Mensaje de resumen antes de listar las ofertas usando HTML."""
    plural = "s" if count > 1 else ""
    return (
        f"🔔 <b>¡Encontré {count} nueva{plural} oferta{plural} para vos!</b>\n"
        f"<i>Monitoreo cada {interval_hours}h</i>"
    )


# ----------------------------------------------------------
# LÓGICA DE CHEQUEO POR USUARIO
# ----------------------------------------------------------

async def check_jobs_for_user(
    bot: Bot,
    telegram_id: int,
    db: Database,
    scraper: JobScraper,
    notify_if_empty: bool = False,
    respect_channel: bool = True,
):
    """
    Ejecuta una búsqueda completa para un usuario y le notifica
    únicamente las ofertas nuevas que no haya visto antes.

    Args:
        bot: Instancia del bot de Telegram
        telegram_id: ID del usuario en Telegram
        db: Instancia de la base de datos
        scraper: Instancia del JobScraper
        notify_if_empty: Si True, avisa cuando no hay nada nuevo (para /buscar manual)
    """
    user = db.get_user(telegram_id)
    if not user:
        logger.warning("Usuario %s no encontrado en DB", telegram_id)
        return

    keywords = db.get_user_keywords(telegram_id)
    if not keywords:
        # Intentar generar keywords inteligentes basadas en el perfil
        smart_keywords = db.generate_smart_keywords(telegram_id)
        if smart_keywords:
            keywords = smart_keywords
            logger.info(
                "Usuario %s sin keywords manuales, usando smart keywords: %s",
                telegram_id,
                ", ".join(smart_keywords),
            )
        else:
            keywords = config.DEFAULT_KEYWORDS
            logger.info("Usuario %s sin keywords ni perfil, usando defaults", telegram_id)

    location = user.get("location") or config.DEFAULT_LOCATION
    logger.info(
        "Chequeando trabajos para %s | %d keywords | %s",
        telegram_id, len(keywords), location
    )
    # --- Perfil del usuario ---
    profile = db.get_user_profile(telegram_id)
    exp_level = profile.get("experience_level", "junior")
    max_age_days = profile.get("max_job_age_days", 30)
    modality = profile.get("job_modality", "cualquiera")

    # --- Buscar en todas las fuentes estándar ---
    all_jobs = scraper.search_all(keywords, location, max_age_days=max_age_days)

    # --- Agregar feeds personalizados del usuario ---
    custom_feeds = db.get_custom_feeds(telegram_id)
    for feed in custom_feeds:
        try:
            custom_jobs = scraper.search_custom_rss(feed["feed_url"], feed["feed_name"])
            # Aplicar filtro de fecha a los custom feeds
            custom_jobs = JobScraper.apply_date_filter(custom_jobs, max_days=max_age_days)
            all_jobs.extend(custom_jobs)
        except Exception as e:
            logger.error("Error en custom feed '%s': %s", feed["feed_name"], e)

    # --- Aplicar filtro de keywords negativas y de modalidad ---
    all_jobs = JobScraper.apply_negative_filter(all_jobs, experience_level=exp_level)
    all_jobs = JobScraper.apply_modality_filter(all_jobs, modality=modality)

    # --- Filtros por empresas (lista negra / preferidos) ---
    company_filters = db.get_company_filters(telegram_id)
    blocked = company_filters.get("blocked", set())
    preferred = company_filters.get("preferred", set())

    if blocked:
        filtered_by_company = []
        for job in all_jobs:
            name = (job.get("company") or "").strip().lower()
            if name and name in blocked:
                continue
            filtered_by_company.append(job)
        all_jobs = filtered_by_company

    # --- Filtrar los que ya se enviaron ---
    new_jobs = db.filter_new_jobs(telegram_id, all_jobs)

    db.update_last_check(telegram_id)

    if not new_jobs:
        logger.info("Sin nuevas ofertas para %s (total encontradas: %d)", telegram_id, len(all_jobs))
        if notify_if_empty:
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    "🔍 Búsqueda completada.\n"
                    f"📊 Se revisaron {len(all_jobs)} ofertas en total.\n"
                    "✅ No hay nada nuevo que no hayas visto.\n\n"
                    "<i>Las alertas automáticas siguen activas</i>"
                ),
                parse_mode=ParseMode.HTML,
            )
        return

    # --- Enriquecer con CV match si el usuario tiene CV ---
    cv_text = None
    if user.get("cv_path"):
        cv_text = parse_cv(user["cv_path"])

    if cv_text:
        enriched_jobs = []
        for job in new_jobs:
            enriched_job, score = format_job_with_score(job, cv_text)
            enriched_jobs.append(enriched_job)
        # Ordenar por relevancia (mayor score primero)
        new_jobs = sorted(enriched_jobs, key=lambda j: j.get("match_score", 0), reverse=True)
        logger.info("Jobs enriquecidos con match de CV para usuario %s", telegram_id)

    # Ordenar para priorizar empresas preferidas, si hubiera
    if preferred:
        def pref_key(job):
            name = (job.get("company") or "").strip().lower()
            return 0 if name in preferred else 1

        new_jobs = sorted(new_jobs, key=pref_key)

    logger.info("Enviando %d nuevas ofertas al usuario %s", len(new_jobs), telegram_id)

    # --- Obtener intervalo del usuario para el header ---
    schedule = db.get_user_schedule(telegram_id)
    user_interval = schedule.get("check_interval_hours", 6)

    # --- Respetar canal de alertas configurado (solo para scheduler/monitoreo) ---
    send_via_telegram = True
    if respect_channel:
        channel = db.get_alert_channel(telegram_id)
        if channel != "telegram":
            send_via_telegram = False

    # Si no se envía por Telegram, igualmente marcamos como vistos para no repetirlos
    if not send_via_telegram:
        jobs_to_mark = new_jobs[: config.MAX_JOBS_PER_NOTIFICATION]
        for job in jobs_to_mark:
            db.mark_job_seen(telegram_id, job)
        logger.info(
            "Usuario %s con canal '%s': ofertas registradas solo para panel/web, sin push Telegram",
            telegram_id,
            db.get_alert_channel(telegram_id),
        )
        return

    # --- Enviar encabezado ---
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=format_summary_header(len(new_jobs), interval_hours=user_interval),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError as e:
        logger.error("Error enviando encabezado a %s: %s", telegram_id, e)
        return

    # --- Enviar cada oferta (máximo MAX_JOBS_PER_NOTIFICATION) ---
    sent = 0
    jobs_to_send = new_jobs[: config.MAX_JOBS_PER_NOTIFICATION]

    for job in jobs_to_send:
        if not job.get("url"):
            # Marcar igualmente para no repetir
            db.mark_job_seen(telegram_id, job)
            continue
        try:
            msg = format_job_message(job)
            await bot.send_message(
                chat_id=telegram_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            db.mark_job_seen(telegram_id, job)
            sent += 1
            await asyncio.sleep(0.5)   # Rate limit de Telegram: max ~30 msgs/seg
        except TelegramError as e:
            logger.error("Error enviando job a %s: %s", telegram_id, e)

    # --- Avisar si hay más ofertas que no se mostraron ---
    remaining = len(new_jobs) - config.MAX_JOBS_PER_NOTIFICATION
    if remaining > 0:
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    f"ℹ️ Hay {remaining} oferta{'s' if remaining > 1 else ''} más disponible{'s' if remaining > 1 else ''}.\n"
                    "Usá /buscar para verlas en el próximo ciclo."
                ),
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            pass

    logger.info("✅ Enviadas %d ofertas al usuario %s", sent, telegram_id)


# ----------------------------------------------------------
# CALLBACK DEL SCHEDULER (llamado por JobQueue)
# ----------------------------------------------------------

async def scheduled_job_check(context):
    """
    Callback que ejecuta el JobQueue de python-telegram-bot.
    Se llama automáticamente cada CHECK_INTERVAL_HOURS horas.
    context.bot es la instancia del bot inyectada por el framework.
    """
    bot = context.bot
    db = Database(config.DATABASE_PATH)
    scraper = JobScraper()

    active_users = db.get_all_active_users()
    logger.info(
        "⏰ Scheduler ejecutado | %d usuario(s) con alertas activas",
        len(active_users)
    )

    for user in active_users:
        tid = user["telegram_id"]
        try:
            await check_jobs_for_user(bot, tid, db, scraper, notify_if_empty=False, respect_channel=True)
        except Exception as e:
            logger.error("Error procesando usuario %s en scheduler: %s", tid, e)
        # Pequeña pausa entre usuarios para no saturar la API de Telegram
        await asyncio.sleep(2)

    logger.info("⏰ Ciclo del scheduler completado")
