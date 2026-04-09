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
    company_domain = safe(job.get("company_domain", ""))
    job_id = safe(job.get("id", ""))

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

    if company_domain:
        lines.append(
            f"🏢 Empresa: <code>/empresa {company_domain}</code>"
        )

    if job_id and job.get("provider") in {"jsearch", "active_jobs_db"}:
        lines.append(
            f"🧾 Detalle: <code>/detalle_job {job_id}</code>"
        )

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

    # ============================================================
    # SMART SUMMARY UX - Nuevo flujo de notificaciones
    # ============================================================
    
    # Determinar source para analytics
    source = "alert" if respect_channel else "manual"
    
    # Preparar preferencias del usuario para mostrar en el resumen
    user_preferences = {
        "location": location,
        "experience_level": exp_level,
        "technologies": ", ".join(keywords[:3]) if keywords else None,
        "job_modality": modality
    }
    
    # Crear batch y enviar resumen con botón
    batch_id = await create_and_send_batch_summary(
        bot=bot,
        telegram_id=telegram_id,
        jobs=new_jobs,
        db=db,
        source=source,
        user_preferences=user_preferences
    )
    
    if batch_id > 0:
        logger.info("[SMART] Batch %d creado para usuario %s (%d jobs, source=%s)",
                    batch_id, telegram_id, len(new_jobs), source)
    else:
        # Fallback: si falla el batch, enviar como antes
        logger.warning("[SMART] Fallback a envío tradicional para usuario %s", telegram_id)
        await _send_jobs_traditional(bot, telegram_id, new_jobs, user_interval, db)


async def _send_jobs_traditional(bot: Bot, telegram_id: int, jobs: List[Dict], 
                                  user_interval: int, db: Database):
    """
    Método tradicional de envío de jobs (fallback si Smart Summary falla).
    """
    # --- Enviar encabezado ---
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=format_summary_header(len(jobs), interval_hours=user_interval),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError as e:
        logger.error("Error enviando encabezado a %s: %s", telegram_id, e)
        return

    # --- Enviar cada oferta (máximo MAX_JOBS_PER_NOTIFICATION) ---
    sent = 0
    jobs_to_send = jobs[: config.MAX_JOBS_PER_NOTIFICATION]

    for job in jobs_to_send:
        if not job.get("url"):
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
            await asyncio.sleep(0.5)
        except TelegramError as e:
            logger.error("Error enviando job a %s: %s", telegram_id, e)

    # --- Avisar si hay más ofertas ---
    remaining = len(jobs) - config.MAX_JOBS_PER_NOTIFICATION
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

    logger.info("[TRADITIONAL] Enviadas %d ofertas al usuario %s", sent, telegram_id)


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

    # ---- Procesar batches de alertas expirados (fallback) ----
    try:
        await process_expired_alert_batches(bot, db)
    except Exception as e:
        logger.error("Error procesando batches expirados: %s", e)
    
    # ---- Limpieza de batches antiguos ----
    try:
        deleted = db.expire_old_batches(max_age_hours=24)
        if deleted > 0:
            logger.info("🧹 Limpieza: %d batches antiguos eliminados", deleted)
    except Exception as e:
        logger.error("Error en limpieza de batches: %s", e)

    logger.info("⏰ Ciclo del scheduler completado")


# ----------------------------------------------------------
# SMART SUMMARY UX - Nuevo flujo de notificaciones
# ----------------------------------------------------------

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def format_summary_message_smart(
    total_count: int,
    high_match: int,
    medium_match: int,
    regular_match: int,
    user_preferences: Dict = None
) -> tuple:
    """
    Formatea el mensaje resumen del nuevo flujo Smart Summary.
    
    Returns:
        tuple: (mensaje_texto, keyboard_markup)
    """
    # Emojis según calidad
    high_emoji = "🟢"
    medium_emoji = "🟡"
    regular_emoji = "⚪"
    
    lines = [
        f"🎯 <b>Encontramos {total_count} propuestas para vos</b>",
        "",
        "📊 <b>Análisis por match:</b>"
    ]
    
    if high_match > 0:
        lines.append(f"{high_emoji} {high_match} Super match (80%+)")
    if medium_match > 0:
        lines.append(f"{medium_emoji} {medium_match} Buen match (60-80%)")
    if regular_match > 0:
        lines.append(f"{regular_emoji} {regular_match} Match regular")
    
    # Agregar preferencias del usuario si están disponibles
    if user_preferences:
        lines.append("")
        lines.append("💼 <b>Filtros aplicados:</b>")
        if user_preferences.get('location'):
            lines.append(f"📍 {user_preferences['location']}")
        if user_preferences.get('experience_level'):
            lines.append(f"👤 {user_preferences['experience_level']}")
        if user_preferences.get('technologies'):
            techs = user_preferences['technologies'][:30]
            lines.append(f"💻 {techs}")
    
    lines.append("")
    lines.append(f"⏳ Disponible {config.JOB_BATCH_TTL_MINUTES} minutos")
    
    message_text = "\n".join(lines)
    
    # Crear botón inline
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Ver todas las ofertas", callback_data=f"view_jobs_batch")]
    ])
    
    return message_text, keyboard


async def create_and_send_batch_summary(
    bot: Bot,
    telegram_id: int,
    jobs: List[Dict],
    db: Database,
    source: str = "manual",
    user_preferences: Dict = None
) -> int:
    """
    Crea un batch de jobs y envía el mensaje resumen Smart Summary.
    
    Args:
        bot: Instancia del bot de Telegram
        telegram_id: ID del usuario
        jobs: Lista de trabajos encontrados
        db: Instancia de Database
        source: 'manual' o 'alert'
        user_preferences: Dict con preferencias del usuario para mostrar
    
    Returns:
        ID del batch creado, o -1 si hay error
    """
    if not jobs:
        return -1
    
    # Calcular conteos por match
    high = sum(1 for j in jobs if j.get('match_score', 0) >= 80)
    medium = sum(1 for j in jobs if 60 <= j.get('match_score', 0) < 80)
    regular = sum(1 for j in jobs if j.get('match_score', 0) < 60)
    
    # Crear batch en DB
    batch_id = db.create_job_batch(
        telegram_id=telegram_id,
        jobs=jobs,
        source=source,
        ttl_minutes=config.JOB_BATCH_TTL_MINUTES
    )
    
    if batch_id == -1:
        logger.error(f"[SMART] Error creando batch para usuario {telegram_id}")
        return -1
    
    # Preparar mensaje y botón
    message_text, keyboard = format_summary_message_smart(
        total_count=len(jobs),
        high_match=high,
        medium_match=medium,
        regular_match=regular,
        user_preferences=user_preferences
    )
    
    # Actualizar callback data con el ID real del batch
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📋 Ver todas las ofertas", 
            callback_data=f"view_jobs_batch:{batch_id}"
        )]
    ])
    
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        logger.info(f"[SMART] Batch {batch_id} enviado a usuario {telegram_id} ({len(jobs)} jobs)")
        return batch_id
    except TelegramError as e:
        logger.error(f"[SMART] Error enviando batch {batch_id}: {e}")
        return -1


async def send_jobs_from_batch(
    bot: Bot,
    telegram_id: int,
    batch_id: int,
    db: Database
) -> bool:
    """
    Envía los jobs de un batch uno por uno cuando el usuario confirma.
    
    Returns:
        True si se enviaron correctamente, False en caso contrario
    """
    batch = db.get_job_batch(batch_id)
    if not batch:
        logger.warning(f"[SMART] Batch {batch_id} no encontrado o expirado")
        await bot.send_message(
            chat_id=telegram_id,
            text="⏰ Este batch de ofertas ha expirado. Usá /buscar para ver ofertas actuales."
        )
        return False
    
    # Marcar como visto
    db.mark_batch_viewed(batch_id)
    
    # Obtener límite según plan del usuario
    user = db.get_web_user(telegram_id)
    plan = user.get("plan", "free") if user else "free"
    max_jobs = config.MAX_JOBS_PER_BATCH.get(plan, config.MAX_JOBS_PER_BATCH["free"])
    
    jobs = batch["jobs"][:max_jobs]
    
    # Enviar mensaje de inicio
    await bot.send_message(
        chat_id=telegram_id,
        text=f"📋 Mostrando {len(jobs)} ofertas:\n"
    )
    
    # Enviar cada job con botón de empresa
    sent = 0
    for idx, job in enumerate(jobs, 1):
        if not job.get("url"):
            db.mark_job_seen(telegram_id, job)
            continue
        
        try:
            msg = format_job_message_with_button(job, idx, len(jobs))
            await bot.send_message(
                chat_id=telegram_id,
                text=msg["text"],
                parse_mode=ParseMode.HTML,
                reply_markup=msg.get("keyboard"),
                disable_web_page_preview=True
            )
            db.mark_job_seen(telegram_id, job)
            sent += 1
            await asyncio.sleep(0.5)
        except TelegramError as e:
            logger.error(f"[SMART] Error enviando job {idx} del batch {batch_id}: {e}")
    
    # Mensaje final
    if sent > 0:
        remaining = len(batch["jobs"]) - max_jobs
        if remaining > 0:
            await bot.send_message(
                chat_id=telegram_id,
                text=f"ℹ️ Hay {remaining} oferta{'s' if remaining > 1 else ''} más disponible{'s' if remaining > 1 else ''} en tu batch.\n"
                     f"💡 Actualizá tu plan para ver más ofertas por búsqueda."
            )
        else:
            await bot.send_message(
                chat_id=telegram_id,
                text=f"✅ ¡Listo! Enviadas {sent} ofertas.\n"
                     f"💡 Si querés más, usá /buscar de nuevo."
            )
    
    logger.info(f"[SMART] Batch {batch_id}: enviadas {sent}/{len(jobs)} jobs")
    return sent > 0


def format_job_message_with_button(job: Dict, index: int, total: int) -> Dict:
    """
    Formatea un mensaje de job con botón inline para ver info de empresa.
    
    Returns:
        Dict con 'text' y 'keyboard'
    """
    base_msg = format_job_message(job)
    
    # Agregar contador al inicio
    counter = f"<b>{index}/{total}</b> "
    text = counter + base_msg.split("\n", 1)[1]  # Reemplazar "🆕" por el contador
    
    # Crear keyboard con botón de empresa si hay domain
    keyboard = None
    company_domain = job.get("company_domain")
    if company_domain:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🏢 Saber más de la empresa", 
                callback_data=f"company_info:{company_domain}"
            )]
        ])
    
    return {"text": text, "keyboard": keyboard}


async def process_expired_alert_batches(bot: Bot, db: Database):
    """
    Procesa batches de alertas que expiraron sin ser vistos.
    Las envía por fallback (directo) al usuario.
    
    Esta función se ejecuta periódicamente (ej: cada 5 minutos).
    """
    expired_batches = db.get_expired_alert_batches(
        min_age_minutes=config.JOB_BATCH_FALLBACK_MINUTES
    )
    
    if not expired_batches:
        return
    
    logger.info(f"[SMART] Procesando {len(expired_batches)} batches expirados para fallback")
    
    for batch in expired_batches:
        try:
            # Enviar directamente (fallback)
            await send_jobs_from_batch(
                bot=bot,
                telegram_id=batch["telegram_id"],
                batch_id=batch["id"],
                db=db
            )
            # Marcar que se envió por fallback
            db.mark_batch_fallback_sent(batch["id"])
            logger.info(f"[SMART] Fallback enviado para batch {batch['id']}")
            
            await asyncio.sleep(1)  # Rate limit entre usuarios
        except Exception as e:
            logger.error(f"[SMART] Error en fallback para batch {batch['id']}: {e}")
