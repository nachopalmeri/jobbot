#!/usr/bin/env python3
"""
bot.py — Punto de entrada del Job Monitor Bot
Nacho (PISCU) — Bot de búsqueda laboral IT para Buenos Aires

Ejecutar: python bot.py
"""

import asyncio
import logging
import os
import secrets
import threading
import time
import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Imports tolerantes al contexto de ejecución (script vs paquete)
try:
    import config  # Ejecutando dentro de job_bot/
except ImportError:  # Ejecutando como paquete: python -m job_bot.bot
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
    from scheduler import check_jobs_for_user
except ImportError:
    from job_bot.scheduler import check_jobs_for_user

try:
    from cv_analyzer import (
        parse_cv,
        analyze_with_gemini,
        compare_cv_with_offer,
        evaluate_interview_answer,
        format_cv_analysis,
        generate_cover_letter,
        generate_interview_questions,
    )
except ImportError:
    from job_bot.cv_analyzer import (
        parse_cv,
        analyze_with_gemini,
        compare_cv_with_offer,
        evaluate_interview_answer,
        format_cv_analysis,
        generate_cover_letter,
        generate_interview_questions,
    )

try:
    from company_service import get_company_by_domain, format_company_info
except ImportError:
    from job_bot.company_service import get_company_by_domain, format_company_info

try:
    from financial_service import (
        get_stock_data, 
        get_ticker_from_domain,
        format_company_full_message
    )
except ImportError:
    from job_bot.financial_service import (
        get_stock_data,
        get_ticker_from_domain,
        format_company_full_message
    )

try:
    from github_analyzer import fetch_github_repos, analyze_github_match
except ImportError:
    from job_bot.github_analyzer import fetch_github_repos, analyze_github_match

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ============================================================
# INSTANCIAS GLOBALES
# ============================================================
db = Database()
scraper = JobScraper()

(
    WAITING_LEVEL,
    WAITING_ROLE,
    WAITING_TECHS,
    WAITING_LOCATION,
    WAITING_MAX_AGE,
    WAITING_MODALITY,
) = range(6)
WAITING_INTERVAL, WAITING_START_HOUR, WAITING_END_HOUR = range(10, 13)
WAITING_INTERVIEW_START, WAITING_INTERVIEW_ANSWER = range(20, 22)


def _get_user_plan(telegram_id: int) -> str:
    """Devuelve el plan del usuario (free/pro/premium)."""
    try:
        return db.get_user_plan(telegram_id)
    except Exception:
        return "free"


# ============================================================
# SCHEDULER EN THREAD SEPARADO (reemplaza JobQueue)
# Funciona con cualquier versión de Python incluyendo 3.14
# ============================================================


def run_scheduler(app: Application, loop: asyncio.AbstractEventLoop):
    """
    Corre en un thread separado. Cada SCHEDULER_POLL_MINUTES minutos
    revisa qué usuarios tienen su intervalo personal vencido
    Y están dentro de su ventana horaria de alertas.
    """
    poll_minutes = config.SCHEDULER_POLL_MINUTES
    logger.info(
        "⏰ Scheduler inteligente iniciado. Polling cada %d min. Primer check en 3 min.",
        poll_minutes,
    )
    time.sleep(3 * 60)  # Esperar 3 min antes del primer chequeo

    while True:
        try:
            due_users = db.get_users_due_for_check()
            logger.info(
                "⏰ Scheduler poll | %d usuario(s) pendientes de chequeo",
                len(due_users),
            )

            for user in due_users:
                tid = user["telegram_id"]
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        check_jobs_for_user(
                            app.bot,
                            tid,
                            db,
                            scraper,
                            notify_if_empty=False,
                            respect_channel=True,
                        ),
                        loop,
                    )
                    future.result(timeout=120)
                except Exception as e:
                    logger.error("Error en scheduler para usuario %s: %s", tid, e)
                time.sleep(2)

            if due_users:
                logger.info("✅ Ciclo completado para %d usuario(s).", len(due_users))
        except Exception as e:
            logger.error("Error en ciclo del scheduler: %s", e)

        time.sleep(poll_minutes * 60)


# ============================================================
# ERROR HANDLER GLOBAL
# ============================================================


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler global para capturar excepciones de Telegram y loguearlas bien."""
    logger.error("Excepción en handler de Telegram", exc_info=context.error)


# ============================================================
# /start
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user_if_not_exists(user.id, user.first_name or "Usuario")
    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name}! Soy tu asistente de búsqueda laboral IT.\n\n"
        "🎯 Qué puedo hacer:\n"
        "• Monitorear ofertas con horarios personalizados (3-24h)\n"
        "• Buscar en LinkedIn AR, Remotive, Arbeitnow, Jobicy y más\n"
        "• Notificarte SOLO cuando hay algo nuevo\n"
        "• Guardar y analizar tu CV\n\n"
        "• Consultar ficha de empresas antes de aplicar\n\n"
        "📋 Comandos principales:\n"
        "/preferencias — Configurar tu perfil y zona\n"
        "/horarios — Elegir cada cuánto y en qué horarios buscamos\n"
        "/cargar_cv — Subir tu CV (PDF o TXT)\n"
        "/buscar — Búsqueda inmediata\n"
        "/activar_alertas — Monitoreo automático\n"
        "/desactivar_alertas — Pausar monitoreo\n"
        "/estado — Ver tu configuración\n"
        "/ayuda — Todos los comandos\n\n"
        "🚀 Empezá con /preferencias",
    )


# ============================================================
# /estado
# ============================================================
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user_if_not_exists(user.id, user.first_name or "Usuario")
    user_data = db.get_user(user.id)
    keywords = db.get_user_keywords(user.id)
    custom_feeds = db.get_custom_feeds(user.id)

    profile = db.get_user_profile(user.id)
    schedule = db.get_user_schedule(user.id)
    alert_channel = db.get_alert_channel(user.id)
    weekly_goal = db.get_weekly_goal(user.id)
    weekly_done = db.get_weekly_applications_count(user.id)
    digest_mode = db.get_digest_mode(user.id)
    level_names = {
        "sin_experiencia": "Sin experiencia",
        "junior": "Junior",
        "semi_senior": "Semi-Senior",
        "senior": "Senior",
    }
    exp = level_names.get(profile.get("experience_level", "junior"), "Junior")
    rol = profile.get("role_type") or "No definido"
    tec = profile.get("technologies") or "No definido"

    alertas = "✅ Activas" if user_data.get("active_alerts") else "❌ Inactivas"
    canal_map = {
        "telegram": "Telegram (mensajes directos)",
        "web": "Solo panel web (sin push)",
        "email": "Resumen por email (próximamente)",
        "whatsapp": "WhatsApp (en preparación)",
        "twitter": "Twitter/X (en preparación)",
    }
    canal_txt = canal_map.get(alert_channel, "Telegram (mensajes directos)")
    cv = (
        f"✅ {Path(user_data['cv_path']).name}"
        if user_data.get("cv_path")
        else "❌ No cargado"
    )
    last = user_data.get("last_check") or "Nunca"
    location = user_data.get("location") or config.DEFAULT_LOCATION
    kw_lines = (
        "\n".join(f"  • {kw}" for kw in keywords) if keywords else "  Sin keywords"
    )

    interval = schedule.get("check_interval_hours", 6)
    start_h = schedule.get("alert_start_hour", 8)
    end_h = schedule.get("alert_end_hour", 22)

    digest_map = {
        "realtime": "Tiempo real (varias veces al día)",
        "daily": "Resumen diario",
        "weekly": "Resumen semanal",
    }
    digest_txt = digest_map.get(digest_mode, "Tiempo real (varias veces al día)")

    feeds_section = ""
    if custom_feeds:
        feeds_section = "\n\nFeeds RSS personalizados:\n"
        feeds_section += "\n".join(
            f"  • {f['feed_name']} (ID: {f['id']})" for f in custom_feeds
        )

    msg = (
        f"📊 Tu configuración\n\n"
        f"👤 Nombre: {user_data['name']}\n"
        f"📍 Ubicación: {location}\n"
        f"🏅 Nivel: {exp}\n"
        f"💼 Rol: {rol}\n"
        f"🛠 Tecnología: {tec}\n"
        f"⏳ Antigüedad máx: {profile.get('max_job_age_days', 30)} días\n\n"
        f"🔔 Alertas: {alertas}\n"
        f"📡 Canal: {canal_txt}\n"
        f"⏰ Frecuencia: cada {interval}h (de {start_h}:00 a {end_h}:00)\n"
        f"🗓 Modo de resumen: {digest_txt}\n"
        f"🎯 Objetivo semanal: {weekly_goal or 0} aplicaciones (llevás {weekly_done})\n"
        f"📄 CV: {cv}\n"
        f"🕐 Último chequeo: {last}\n\n"
        f"🔍 Keywords generadas ({len(keywords)}):\n{kw_lines}"
        f"{feeds_section}"
    )
    await update.message.reply_text(msg)


# ============================================================
# /preferencias — Perfil inteligente en 4 pasos
# ============================================================
async def preferencias_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user_if_not_exists(user.id, user.first_name or "Usuario")
    await update.message.reply_text(
        "⚙️ Configurar tu perfil de búsqueda\n\n"
        "Respondé unas preguntas simples y yo armo las búsquedas.\n\n"
        "<b>Paso 1/6 — ¿Cuál es tu nivel de experiencia?</b>\n\n"
        "Escribí el número:\n"
        "1️⃣ Sin experiencia (busco mi primer empleo)\n"
        "2️⃣ Junior (menos de 2 años)\n"
        "3️⃣ Semi-Senior (2-5 años)\n"
        "4️⃣ Senior (5+ años)\n\n"
        "Escribí /cancelar para salir.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_LEVEL


async def preferencias_recibe_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    level_map = {
        "1": "sin_experiencia",
        "sin experiencia": "sin_experiencia",
        "2": "junior",
        "junior": "junior",
        "3": "semi_senior",
        "semi senior": "semi_senior",
        "ssr": "semi_senior",
        "4": "senior",
        "senior": "senior",
    }
    level = level_map.get(text.lower())
    if not level:
        await update.message.reply_text("❌ Respondé con 1, 2, 3 o 4.")
        return WAITING_LEVEL

    context.user_data["experience_level"] = level
    level_names = {
        "sin_experiencia": "Sin experiencia",
        "junior": "Junior",
        "semi_senior": "Semi-Senior",
        "senior": "Senior",
    }
    await update.message.reply_text(
        f"✅ Nivel: <b>{level_names[level]}</b>\n\n"
        "💼 <b>Paso 2/6 — ¿Qué tipo de rol buscás?</b>\n\n"
        "Escribí uno o varios separados por coma:\n"
        "• backend\n"
        "• frontend\n"
        "• fullstack\n"
        "• data / datos\n"
        "• devops\n"
        "• QA / testing\n"
        "• soporte IT\n"
        "• otro (escribí cuál)\n\n"
        "Ejemplo: backend, fullstack",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_ROLE


async def preferencias_recibe_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text or len(text) < 2:
        await update.message.reply_text("❌ Escribí al menos un tipo de rol.")
        return WAITING_ROLE

    context.user_data["role_type"] = text
    await update.message.reply_text(
        f"✅ Rol: <b>{text}</b>\n\n"
        "🛠 <b>Paso 3/6 — ¿Qué tecnologías sabés o estás aprendiendo?</b>\n\n"
        "Escribí separadas por coma:\n"
        "Ejemplo: Python, JavaScript, SQL, React, Java\n\n"
        "Si no sabés todavía, escribí: general",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_TECHS


async def preferencias_recibe_techs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text or len(text) < 2:
        await update.message.reply_text(
            "❌ Escribí al menos una tecnología o 'general'."
        )
        return WAITING_TECHS

    if text.lower() == "general":
        text = "programación, IT, desarrollo, software"

    context.user_data["technologies"] = text

    user_data = db.get_user(update.effective_user.id)
    curr_location_raw = (
        user_data.get("location", config.DEFAULT_LOCATION)
        if user_data
        else config.DEFAULT_LOCATION
    )
    curr_location = html.escape(str(curr_location_raw))

    await update.message.reply_text(
        f"✅ Tecnologías: <b>{text}</b>\n\n"
        "📍 <b>Paso 4/6 — ¿En qué zona buscás trabajo?</b>\n\n"
        f"Ubicación actual: {curr_location}\n\n"
        "Escribí la nueva ubicación o escribí 'misma' para mantener la actual.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_LOCATION


async def preferencias_recibe_location(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.lower() not in ["/misma", "misma"]:
        db.set_user_location(user_id, text)
        location = text
    else:
        user_data = db.get_user(user_id)
        location = (
            user_data.get("location", config.DEFAULT_LOCATION)
            if user_data
            else config.DEFAULT_LOCATION
        )

    context.user_data["location"] = location

    safe_location = html.escape(str(location))

    await update.message.reply_text(
        f"✅ Ubicación: <b>{safe_location}</b>\n\n"
        "🏠 <b>Paso 5/6 — ¿Qué modalidad de trabajo buscás?</b>\n\n"
        "Escribí una opción:\n"
        "1️⃣ Remoto\n"
        "2️⃣ Híbrido\n"
        "3️⃣ Presencial\n"
        "4️⃣ Cualquiera\n\n"
        "Respondé con el número o la palabra.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_MODALITY


async def preferencias_recibe_modality(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip().lower()
    mod_map = {
        "1": "remoto",
        "remoto": "remoto",
        "2": "híbrido",
        "hibrido": "híbrido",
        "3": "presencial",
        "presencial": "presencial",
        "4": "cualquiera",
        "cualquiera": "cualquiera",
    }
    modality = mod_map.get(text)
    if not modality:
        await update.message.reply_text("❌ Respondé con 1, 2, 3 o 4.")
        return WAITING_MODALITY

    context.user_data["job_modality"] = modality

    await update.message.reply_text(
        f"✅ Modalidad: <b>{modality.capitalize()}</b>\n\n"
        "⏳ <b>Paso 6/6 — ¿Qué antigüedad máxima pueden tener las ofertas?</b>\n\n"
        "Escribí el número:\n"
        "1️⃣ 24 horas\n"
        "2️⃣ 3 días\n"
        "3️⃣ 1 semana (7 días)\n"
        "4️⃣ 1 mes (30 días)\n"
        "5️⃣ 3 meses (90 días)\n"
        "6️⃣ Cualquiera",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_MAX_AGE


async def preferencias_recibe_max_age(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    age_map = {
        "1": 1,
        "24 horas": 1,
        "24hs": 1,
        "1 dia": 1,
        "1 día": 1,
        "2": 3,
        "3 dias": 3,
        "3 días": 3,
        "3": 7,
        "1 semana": 7,
        "7 dias": 7,
        "7 días": 7,
        "4": 30,
        "1 mes": 30,
        "30 dias": 30,
        "30 días": 30,
        "5": 90,
        "3 meses": 90,
        "90 dias": 90,
        "90 días": 90,
        "6": 3650,
        "cualquiera": 3650,
        "mas": 3650,
        "más": 3650,
    }

    max_age = age_map.get(text.lower())
    if not max_age:
        await update.message.reply_text("❌ Respondé con 1, 2, 3, 4, 5 o 6.")
        return WAITING_MAX_AGE

    # Guardar perfil
    exp_level = context.user_data.get("experience_level", "junior")
    role_type = context.user_data.get("role_type", "")
    technologies = context.user_data.get("technologies", "")
    location = context.user_data.get("location") or config.DEFAULT_LOCATION
    modality = context.user_data.get("job_modality", "cualquiera")

    db.set_user_profile(
        user_id, exp_level, role_type, technologies, modality, max_job_age_days=max_age
    )

    # Generar keywords automáticas
    smart_keywords = db.generate_smart_keywords(user_id)
    db.set_user_keywords(user_id, smart_keywords)

    level_names = {
        "sin_experiencia": "🟢 Sin experiencia",
        "junior": "🟡 Junior",
        "semi_senior": "🟠 Semi-Senior",
        "senior": "🔴 Senior",
    }

    age_labels = {
        1: "24 horas",
        3: "3 días",
        7: "1 semana",
        30: "1 mes",
        90: "3 meses",
        3650: "Sin límite",
    }

    kw_text = "\n".join(f"  • {kw}" for kw in smart_keywords)
    await update.message.reply_text(
        "✅ <b>¡Perfil configurado!</b>\n\n"
        f"📊 Nivel: {level_names.get(exp_level, exp_level)}\n"
        f"💼 Rol: {role_type}\n"
        f"🛠 Tecnologías: {technologies}\n"
        f"📍 Ubicación: {location}\n"
        f"🏠 Modalidad: {modality.capitalize()}\n"
        f"⏳ Antigüedad máx: {age_labels[max_age]}\n\n"
        f"🔍 Keywords generadas automáticamente:\n{kw_text}\n\n"
        "Ahora:\n"
        "• /buscar — buscar ahora mismo\n"
        "• /activar_alertas — monitoreo automático",
        parse_mode=ParseMode.HTML,
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END


# ============================================================
# /cargar_cv
# ============================================================
async def cargar_cv_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 Subir CV\n\n"
        "Enviame tu CV como archivo adjunto (PDF o TXT).\n"
        "Se guarda localmente en esta máquina.\n\n"
        "Simplemente arrastrá y soltá el archivo acá."
    )
    context.user_data["waiting_cv"] = True


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_cv"):
        await update.message.reply_text("Si querés subir tu CV, primero usá /cargar_cv")
        return

    doc = update.message.document
    user_id = update.effective_user.id

    allowed_types = {"application/pdf", "text/plain"}
    if doc.mime_type not in allowed_types:
        await update.message.reply_text("❌ Solo acepto PDF o TXT.")
        return
    if doc.file_size > 5 * 1024 * 1024:
        await update.message.reply_text("❌ Archivo muy grande. Máximo 5 MB.")
        return

    cv_dir = Path(config.CV_STORAGE_PATH)
    cv_dir.mkdir(parents=True, exist_ok=True)
    ext = ".pdf" if doc.mime_type == "application/pdf" else ".txt"
    file_name = f"cv_{user_id}{ext}"
    file_path = cv_dir / file_name

    try:
        telegram_file = await context.bot.get_file(doc.file_id)
        await telegram_file.download_to_drive(str(file_path))
        db.set_user_cv(user_id, str(file_path))
        context.user_data["waiting_cv"] = False
        await update.message.reply_text(
            f"✅ CV guardado: {doc.file_name} ({doc.file_size // 1024} KB)\n\n"
            "Usá /buscar para empezar a buscar trabajo."
        )
    except Exception as e:
        logger.error("Error guardando CV: %s", e)
        await update.message.reply_text(
            f"❌ Error al guardar. Intentá de nuevo.\nDetalle: {str(e)[:100]}"
        )


# ============================================================
# /buscar
# ============================================================
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user_if_not_exists(user_id, update.effective_user.first_name or "Usuario")

    # Límite de búsquedas manuales según plan (usa web_users.searches_limit)
    plan = _get_user_plan(user_id)
    if not db.check_usage_limit(user_id, "searches"):
        await update.message.reply_text(
            "🔒 Alcanzaste el límite de búsquedas manuales para tu plan actual.\n"
            "Actualizá tu suscripción para seguir usando /buscar sin límites.",
        )
        return

    keywords = db.get_user_keywords(user_id)
    if not keywords:
        await update.message.reply_text(
            "⚠️ No tenés keywords. Usá /preferencias primero."
        )
        return

    status_msg = await update.message.reply_text(
        f"🔍 Buscando trabajos...\n"
        f"({len(keywords)} keywords — puede tardar 15-30 segundos)"
    )
    try:
        # En búsquedas manuales siempre respondemos en Telegram,
        # aunque el canal de alertas automático sea "solo web".
        await check_jobs_for_user(
            context.bot,
            user_id,
            db,
            scraper,
            notify_if_empty=True,
            respect_channel=False,
        )
        # Contabilizar el uso de búsqueda manual
        db.increment_usage(user_id, "searches")
        await status_msg.delete()
    except Exception as e:
        logger.error("Error en búsqueda manual: %s", e)
        await status_msg.edit_text(
            f"❌ Error durante la búsqueda.\nDetalle: {str(e)[:100]}"
        )


# ============================================================
# /activar_alertas y /desactivar_alertas
# ============================================================
async def activar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user_if_not_exists(user_id, update.effective_user.first_name or "Usuario")
    keywords = db.get_user_keywords(user_id)
    if not keywords:
        await update.message.reply_text(
            "⚠️ Configurá tus keywords primero con /preferencias"
        )
        return
    db.set_alerts_active(user_id, True)
    schedule = db.get_user_schedule(user_id)
    interval = schedule.get("check_interval_hours", 6)
    start_h = schedule.get("alert_start_hour", 8)
    end_h = schedule.get("alert_end_hour", 22)
    await update.message.reply_text(
        f"✅ Alertas activadas!\n\n"
        f"⏰ Frecuencia: cada {interval} horas\n"
        f"🕐 Horario activo: {start_h}:00 a {end_h}:00\n"
        f"🔍 Monitoreando {len(keywords)} keywords\n\n"
        "Usá /horarios para cambiar la frecuencia.\n"
        "Usá /desactivar_alertas para pausar."
    )


async def desactivar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_alerts_active(update.effective_user.id, False)
    await update.message.reply_text(
        "🔕 Alertas desactivadas.\n\n"
        "• /buscar — búsquedas manuales\n"
        "• /activar_alertas — reactivar"
    )


# ============================================================
# /horarios — Configurar frecuencia y franja horaria
# ============================================================
async def horarios_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user_if_not_exists(user.id, user.first_name or "Usuario")
    schedule = db.get_user_schedule(user.id)
    current = schedule.get("check_interval_hours", 6)
    await update.message.reply_text(
        "⏰ <b>Configurar horarios de alerta</b>\n\n"
        f"Frecuencia actual: cada <b>{current}h</b>\n\n"
        "<b>Paso 1/3 — ¿Cada cuántas horas querés recibir alertas?</b>\n\n"
        "Escribí el número:\n"
        "1️⃣ Cada 3 horas (más frecuente)\n"
        "2️⃣ Cada 6 horas (recomendado)\n"
        "3️⃣ Cada 8 horas (3 veces al día)\n"
        "4️⃣ Cada 12 horas (2 veces al día)\n"
        "5️⃣ Cada 24 horas (1 vez al día)\n\n"
        "O escribí un número entre 3 y 24.\n"
        "Escribí /cancelar para salir.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_INTERVAL


async def horarios_recibe_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    interval_map = {"1": 3, "2": 6, "3": 8, "4": 12, "5": 24}
    interval = interval_map.get(text)
    if not interval:
        try:
            interval = int(text)
        except ValueError:
            await update.message.reply_text("❌ Escribí un número entre 3 y 24.")
            return WAITING_INTERVAL

    if interval < 3 or interval > 24:
        await update.message.reply_text("❌ El intervalo debe ser entre 3 y 24 horas.")
        return WAITING_INTERVAL

    context.user_data["sched_interval"] = interval
    await update.message.reply_text(
        f"✅ Intervalo: cada <b>{interval} horas</b>\n\n"
        "🌅 <b>Paso 2/3 — ¿Desde qué hora querés recibir alertas?</b>\n\n"
        "Escribí la hora (0-23):\n"
        "Ejemplo: <code>8</code> para las 8:00 AM\n"
        "Ejemplo: <code>6</code> para las 6:00 AM",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_START_HOUR


async def horarios_recibe_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        start_h = int(text)
    except ValueError:
        await update.message.reply_text("❌ Escribí un número entre 0 y 23.")
        return WAITING_START_HOUR

    if start_h < 0 or start_h > 23:
        await update.message.reply_text("❌ La hora debe ser entre 0 y 23.")
        return WAITING_START_HOUR

    context.user_data["sched_start"] = start_h
    await update.message.reply_text(
        f"✅ Alertas desde las <b>{start_h}:00</b>\n\n"
        "🌙 <b>Paso 3/3 — ¿Hasta qué hora querés recibir alertas?</b>\n\n"
        "Escribí la hora (0-23):\n"
        "Ejemplo: <code>22</code> para las 10:00 PM\n"
        "Ejemplo: <code>0</code> para medianoche",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_END_HOUR


async def horarios_recibe_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        end_h = int(text)
    except ValueError:
        await update.message.reply_text("❌ Escribí un número entre 0 y 23.")
        return WAITING_END_HOUR

    if end_h < 0 or end_h > 23:
        await update.message.reply_text("❌ La hora debe ser entre 0 y 23.")
        return WAITING_END_HOUR

    interval = context.user_data.get("sched_interval", 6)
    start_h = context.user_data.get("sched_start", 8)

    db.set_user_schedule(user_id, interval, start_h, end_h)

    await update.message.reply_text(
        "✅ <b>¡Horarios configurados!</b>\n\n"
        f"⏰ Frecuencia: cada <b>{interval} horas</b>\n"
        f"🌅 Desde: <b>{start_h}:00</b>\n"
        f"🌙 Hasta: <b>{end_h}:00</b>\n\n"
        "Las alertas solo llegarán dentro de esa franja.\n"
        "Usá /activar_alertas para activarlas.",
        parse_mode=ParseMode.HTML,
    )
    context.user_data.clear()
    return ConversationHandler.END


# ============================================================
# /analizar_cv — Análisis general del CV cargado
# ============================================================
async def analizar_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user_if_not_exists(user_id, update.effective_user.first_name or "Usuario")
    user_data = db.get_user(user_id)

    if not user_data or not user_data.get("cv_path"):
        await update.message.reply_text(
            "❌ No tenés un CV cargado.\nUsá /cargar_cv para subir tu CV primero."
        )
        return

    status_msg = await update.message.reply_text("🔍 Analizando tu CV...")

    cv_text = parse_cv(user_data["cv_path"])
    if not cv_text:
        await status_msg.edit_text(
            "❌ No pude leer tu CV. Intentá subirlo de nuevo con /cargar_cv"
        )
        return

    # Análisis local de keywords
    kws = extract_keywords(cv_text)
    tech_str = ", ".join(kws["tech"]) if kws["tech"] else "Ninguna detectada"
    soft_str = ", ".join(kws["soft"]) if kws["soft"] else "Ninguna detectada"

    msg = (
        "📋 <b>Análisis de tu CV</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛠 <b>Keywords técnicas ({len(kws['tech'])}):</b>\n"
        f"  {tech_str}\n\n"
        f"🤝 <b>Skills blandas ({len(kws['soft'])}):</b>\n"
        f"  {soft_str}\n\n"
    )

    # Si tiene Gemini key, dar tips avanzados
    gemini_tips = await analyze_with_gemini(cv_text)
    if gemini_tips:
        msg += f"🤖 <b>Sugerencias de IA:</b>\n{gemini_tips}\n\n"
    else:
        msg += (
            "💡 <b>Tip:</b> Usá /analizar_oferta para comparar tu CV \n"
            "contra una oferta específica y recibir sugerencias.\n\n"
        )

    msg += (
        "🔍 Para comparar con una oferta específica:\n"
        "<code>/analizar_oferta [pegá la descripción de la oferta]</code>"
    )

    await status_msg.edit_text(msg, parse_mode=ParseMode.HTML)


# ============================================================
# /analizar_oferta — Comparar CV vs oferta específica
# ============================================================
async def analizar_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user_if_not_exists(user_id, update.effective_user.first_name or "Usuario")
    user_data = db.get_user(user_id)

    # Gating básico por plan + límite de uso de IA
    plan = _get_user_plan(user_id)
    if plan == "free":
        await update.message.reply_text(
            "⚠️ Esta función forma parte de JobBot Pro.\n"
            "Podés seguir usando las alertas y la búsqueda básica, "
            "y actualizarte a Pro para comparar tu CV contra ofertas específicas.",
        )
        return

    if not db.check_usage_limit(user_id, "ai_analyses"):
        await update.message.reply_text(
            "🔒 Alcanzaste el límite de análisis de IA para tu plan actual.\n"
            "Actualizá tu suscripción para seguir usando /analizar_oferta.",
        )
        return

    if not user_data or not user_data.get("cv_path"):
        await update.message.reply_text(
            "❌ No tenés un CV cargado.\nUsá /cargar_cv para subir tu CV primero."
        )
        return

    # El texto de la oferta viene como argumentos del comando
    offer_text = " ".join(context.args) if context.args else ""
    if not offer_text or len(offer_text) < 10:
        await update.message.reply_text(
            "📝 <b>Analizar oferta vs tu CV</b>\n\n"
            "Uso: Pegá la descripción de la oferta después del comando:\n\n"
            "<code>/analizar_oferta Buscamos desarrollador Python "
            "con experiencia en Django, PostgreSQL y Docker.</code>\n\n"
            "También podés pegar el título + descripción completa.",
            parse_mode=ParseMode.HTML,
        )
        return

    status_msg = await update.message.reply_text("🔍 Comparando tu CV con la oferta...")

    cv_text = parse_cv(user_data["cv_path"])
    if not cv_text:
        await status_msg.edit_text(
            "❌ No pude leer tu CV. Intentá subirlo de nuevo con /cargar_cv"
        )
        return

    # Análisis local
    analysis = compare_cv_with_offer(cv_text, offer_text)
    msg = format_cv_analysis(analysis)

    # Si tiene Gemini key, agregar tips avanzados
    gemini_tips = await analyze_with_gemini(cv_text, offer_text)
    if gemini_tips:
        msg += f"\n\n🤖 <b>Sugerencias de IA:</b>\n{gemini_tips}"

    # Contabilizar uso de análisis IA para el plan del usuario
    try:
        db.increment_usage(user_id, "ai_analyses")
    except Exception as e:
        logger.error("Error incrementando uso de ai_analyses para %s: %s", user_id, e)

    await status_msg.edit_text(msg, parse_mode=ParseMode.HTML)


async def empresa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra información enriquecida de una empresa por dominio o URL.
    Uso: /empresa apple.com
    
    Ahora con caché y datos de LinkedIn Data API (RapidAPI).
    """
    if not context.args:
        await update.message.reply_text(
            "🏢 <b>Ficha de empresa</b>\n\n"
            "Uso: <code>/empresa apple.com</code>\n"
            "También podés pasar una URL: <code>/empresa https://apple.com</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    domain_or_url = " ".join(context.args).strip()
    status_msg = await update.message.reply_text(
        "🔎 Buscando información de la empresa..."
    )

    # Obtener info de empresa con caché (usa LinkedIn Data API)
    company_data = get_company_by_domain(domain_or_url, db=db)
    
    if not company_data:
        await status_msg.edit_text(
            "❌ No encontré información de esa empresa.\n"
            "Probá con el dominio directo, por ejemplo: <code>/empresa mercadolibre.com</code>\n\n"
            "ℹ️ Si la empresa es muy nueva o pequeña, puede no estar indexada."
        )
        return

    # Intentar obtener datos financieros si hay ticker disponible
    stock_data = None
    try:
        ticker = get_ticker_from_domain(company_data.get('domain', ''))
        if ticker:
            await status_msg.edit_text(
                "🔎 Buscando información de la empresa y datos financieros..."
            )
            stock_data = get_stock_data(ticker, db=db)
    except Exception as e:
        logger.info(f"No se pudieron obtener datos financieros: {e}")
        # Continuar sin datos financieros

    # Formatear y enviar respuesta combinada
    formatted = format_company_full_message(company_data, stock_data)
    await status_msg.edit_text(formatted, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def detalle_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Consulta detalle extendido de una oferta por job_id cuando el proveedor lo soporta.
    Uso: /detalle_job <job_id> [country]
    """
    if not context.args:
        await update.message.reply_text(
            "🧾 <b>Detalle de oferta</b>\n\n"
            "Uso: <code>/detalle_job JOB_ID [country]</code>\n"
            "Ejemplo: <code>/detalle_job cWq1wY1gQE8gXv8aAAAAAA== us</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    job_id = context.args[0].strip()
    country = context.args[1].strip().lower() if len(context.args) > 1 else "us"
    status_msg = await update.message.reply_text("🔎 Buscando detalle completo...")

    try:
        data = scraper.get_job_details(job_id, country=country)
    except Exception as e:
        logger.error("Error obteniendo detalle de job '%s': %s", job_id, e)
        await status_msg.edit_text(
            "❌ No pude obtener el detalle de esa oferta.\n"
            "Verificá el job_id o probá más tarde."
        )
        return

    title = html.escape(str(data.get("job_title") or data.get("title") or "Oferta"))
    company = html.escape(str(data.get("employer_name") or data.get("company_name") or "Empresa"))
    location = html.escape(
        str(
            data.get("job_city")
            or data.get("job_country")
            or data.get("location")
            or "N/A"
        )
    )
    description = html.escape(str(data.get("job_description") or data.get("description") or ""))[:1200]
    apply_url = html.escape(str(data.get("job_apply_link") or data.get("url") or ""))

    lines = [
        f"💼 <b>{title}</b>",
        f"🏢 {company}",
        f"📍 {location}",
    ]
    if description:
        lines.append(f"\n📝 <i>{description}</i>")
    if apply_url:
        lines.append(f"\n🔗 {apply_url}")

    await status_msg.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)


# ============================================================
# /agregar_feed
# ============================================================
async def agregar_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📡 Agregar feed RSS\n\n"
            "Uso: /agregar_feed [URL] [Nombre]\n\n"
            "Ejemplos:\n"
            "/agregar_feed https://www.getmanfred.com/es/rss ManFred\n"
            "/agregar_feed https://jobs.ashbyhq.com/globant/rss Globant"
        )
        return

    url = context.args[0].strip()
    name = " ".join(context.args[1:]).strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ La URL debe empezar con http:// o https://")
        return

    await update.message.reply_text("⏳ Verificando el feed...")
    import feedparser

    try:
        test = feedparser.parse(url)
        entries_count = len(test.entries)
        if test.bozo and entries_count == 0:
            await update.message.reply_text("❌ No pude leer ese RSS. Verificá la URL.")
            return
    except Exception as e:
        await update.message.reply_text(f"❌ Error al conectar: {str(e)[:100]}")
        return

    db.add_custom_feed(update.effective_user.id, url, name)
    await update.message.reply_text(
        f"✅ Feed agregado: {name}\n"
        f"Entradas encontradas: {entries_count}\n\n"
        "Se incluirá en las próximas búsquedas."
    )


async def mis_feeds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feeds = db.get_custom_feeds(update.effective_user.id)
    if not feeds:
        await update.message.reply_text(
            "No tenés feeds. Usá /agregar_feed para agregar uno."
        )
        return
    lines = ["📡 Tus feeds RSS:\n"]
    for f in feeds:
        lines.append(f"• {f['feed_name']} (ID: {f['id']})\n  {f['feed_url']}")
    lines.append("\nPara eliminar: /eliminar_feed [ID]")
    await update.message.reply_text("\n".join(lines))


async def eliminar_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /eliminar_feed [ID]")
        return
    try:
        feed_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número.")
        return
    db.remove_custom_feed(update.effective_user.id, feed_id)
    await update.message.reply_text(f"✅ Feed {feed_id} eliminado.")


# ============================================================
# /borrar_datos — GDPR Compliance
# ============================================================
async def borrar_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args or context.args[0].lower() != "confirmar":
        await update.message.reply_text(
            "⚠️ <b>ATENCIÓN: CUIDADO</b>\n\n"
            "Estás por borrar TODA tu información de nuestra base de datos:\n"
            "• Tu perfil y preferencias\n"
            "• Tu CV (archivo físico)\n"
            "• Tu historial de ofertas enviadas\n"
            "• Tus feeds RSS personalizados\n\n"
            "Esta acción no se puede deshacer.\n\n"
            "Para proceder, escribí <code>/borrar_datos confirmar</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    # 1. Obtener path del CV para borrar el archivo
    user_data = db.get_user(user_id)
    if user_data and user_data.get("cv_path"):
        try:
            cv_path = Path(user_data["cv_path"])
            if cv_path.exists():
                cv_path.unlink()
                logger.info("CV borrado: %s", cv_path)
        except Exception as e:
            logger.error("Error borrando archivo CV: %s", e)

    # 2. Borrar de la base de datos
    db.delete_user_data(user_id)

    await update.message.reply_text(
        "✅ <b>Tus datos han sido eliminados por completo.</b>\n\n"
        "Esperamos verte pronto. Si querés volver a empezar, usá /start.",
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /entrevista — Simulador de Entrevista con IA
# ============================================================
async def entrevista_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = _get_user_plan(user_id)
    if plan != "premium":
        await update.message.reply_text(
            "🔒 El simulador de entrevistas con IA es parte del plan Premium.\n"
            "Podés seguir usando el bot para buscar trabajos y analizar tu CV, "
            "y actualizarte a Premium para practicar entrevistas.",
        )
        return

    user_data = db.get_user(user_id)

    if not user_data or not user_data.get("cv_path"):
        await update.message.reply_text(
            "❌ No tenés un CV cargado.\n"
            "Usá /cargar_cv primero para que la IA pueda preguntarte sobre tu experiencia."
        )
        return ConversationHandler.END

    if not config.GROQ_API_KEY:
        await update.message.reply_text(
            "❌ La IA no está configurada por el administrador."
        )
        return ConversationHandler.END

    status_msg = await update.message.reply_text(
        "🧠 Generando preguntas de entrevista personalizadas..."
    )
    cv_text = parse_cv(user_data["cv_path"])

    questions_text = await generate_interview_questions(
        cv_text, user_data.get("role_type", "Developer")
    )
    if not questions_text:
        await status_msg.edit_text("❌ Error al contactar con la IA.")
        return ConversationHandler.END

    # Parsear las 5 preguntas
    import re

    questions = re.findall(r"\d[\.\)]\s*(.*)", questions_text)
    if not questions:
        # Fallback si el regex falla por formato
        questions = [q.strip() for q in questions_text.split("\n") if q.strip()][:5]

    if len(questions) < 3:
        await status_msg.edit_text(
            "❌ No pude generar suficientes preguntas. Intentá de nuevo."
        )
        return ConversationHandler.END

    context.user_data["interview_questions"] = questions
    context.user_data["interview_index"] = 0
    context.user_data["interview_cv_text"] = cv_text

    await status_msg.edit_text(
        "🎙 <b>¡Bienvenido al Simulador de Entrevistas JobBot!</b>\n\n"
        "Voy a hacerte 5 preguntas (tecnología y soft skills) basadas en tu perfil.\n"
        "Al final de cada una te daré feedback y una nota.\n\n"
        "¿Estás listo? Empezamos con la primera...\n\n"
        f"1️⃣ <b>{questions[0]}</b>",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_INTERVIEW_ANSWER


async def entrevista_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answer = update.message.text.strip()
    questions = context.user_data.get("interview_questions")
    idx = context.user_data.get("interview_index", 0)
    cv_text = context.user_data.get("interview_cv_text")

    if not questions or idx >= len(questions):
        return ConversationHandler.END

    current_q = questions[idx]

    status_msg = await update.message.reply_text("🧐 Evaluando tu respuesta...")

    evaluation = await evaluate_interview_answer(current_q, answer, cv_text)
    if not evaluation:
        evaluation = "⚠️ No pude evaluar esta respuesta, pero sigamos."

    await status_msg.edit_text(
        f"📝 <b>Feedback Pregunta {idx + 1}:</b>\n\n{evaluation}",
        parse_mode=ParseMode.HTML,
    )

    # Pasar a la siguiente o terminar
    next_idx = idx + 1
    if next_idx < len(questions):
        context.user_data["interview_index"] = next_idx
        await update.message.reply_text(
            f"Siguiente pregunta...\n\n{next_idx + 1}️⃣ <b>{questions[next_idx]}</b>",
            parse_mode=ParseMode.HTML,
        )
        return WAITING_INTERVIEW_ANSWER
    else:
        await update.message.reply_text(
            "🏁 <b>¡Entrevista terminada!</b>\n\n"
            "Espero que te haya servido para practicar. Podés volver a jugar cuando quieras con /entrevista.\n\n"
            "¡Muchos éxitos en tus búsquedas reales! 🚀",
            parse_mode=ParseMode.HTML,
        )
        context.user_data.clear()
        return ConversationHandler.END


# ============================================================
# /carta — Generador de Carta de Presentación
# ============================================================
async def carta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data.get("cv_path"):
        await update.message.reply_text(
            "❌ No tenés un CV cargado. Usá /cargar_cv primero."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "📝 <b>Generador de Carta de Presentación</b>\n\n"
            "Uso: <code>/carta [descripción del puesto o link]</code>\n\n"
            "Ejemplo: <code>/carta Desarrollador Python Senior en Mercado Libre</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    role_info = " ".join(context.args)
    status_msg = await update.message.reply_text(
        "✍️ Redactando tu carta de presentación personalizada..."
    )

    cv_text = parse_cv(user_data["cv_path"])
    letter = await generate_cover_letter(cv_text, role_info)

    if not letter:
        await status_msg.edit_text(
            "❌ No pude generar la carta. Verificá la configuración de la IA."
        )
        return

    await status_msg.edit_text(
        "📄 <b>Tu Carta de Presentación</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{letter}\n\n"
        "💡 <i>Podés copiar este texto y ajustarlo a tu gusto.</i>",
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /ayuda
# ============================================================
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 JobBot — Tu asistente de búsqueda laboral\n\n"
        "⚙️ Configuración:\n"
        "/preferencias — Perfil, nivel, tecnologías y zona\n"
        "/horarios — Frecuencia y franja horaria de alertas\n"
        "/cargar_cv — Subir tu CV (PDF o TXT)\n"
        "/borrar_datos — Eliminar toda tu información (GDPR)\n\n"
        "🔍 Búsqueda:\n"
        "/buscar — Búsqueda manual ahora\n"
        "/activar_alertas — Monitoreo automático personalizado\n"
        "/desactivar_alertas — Pausar monitoreo\n\n"
        "📄 Análisis de CV:\n"
        "/analizar_cv — Análisis general de tu CV\n"
        "/analizar_oferta [URL] — Comparar tu CV vs una oferta\n\n"
        "🏢 Empresa y detalle:\n"
        "/empresa [dominio|URL] — Ver info de una empresa\n"
        "/detalle_job [job_id] [country] — Ver detalle técnico de una oferta\n\n"
        "📡 Feeds RSS:\n"
        "/agregar_feed [URL] [Nombre] — Agregar fuente\n"
        "/mis_feeds — Ver tus feeds\n"
        "/eliminar_feed [ID] — Eliminar feed\n"
        "/entrevista — Practicar para una entrevista con IA\n"
        "/carta [text] — Generar carta de presentación\n\n"
        "📊 Info:\n"
        "/estado — Tu configuración completa\n"
        "/web — Landing page del bot\n"
        "/ayuda — Este mensaje\n\n"
        "🌐 Fuentes: LinkedIn AR, Remotive, Arbeitnow, Jobicy, Himalayas, "
        "Google Jobs, Twitter/X, RSS personalizados.",
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /web — Link a la landing page
# ============================================================
async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🌐 \u00a1Visitá nuestra web!\n\n"
        f"{config.LANDING_URL}\n\n"
        "Ahí podés ver todas las funcionalidades, fuentes de empleo "
        "y cómo funciona el bot."
    )


async def web_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un enlace temporal para entrar al dashboard web con identidad Telegram."""
    user = update.effective_user
    db.create_user_if_not_exists(user.id, user.first_name or "Usuario")
    code = secrets.token_hex(3).upper()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    db.create_web_login_code(user.id, code, expires_at)
    base_url = (config.LANDING_URL or "https://jobbot.ar").rstrip("/")
    login_url = f"{base_url}/login?code={code}"
    await update.message.reply_text(
        "🌐 <b>Entrá a tu panel web</b>\n\n"
        f"Acceso directo: {login_url}\n"
        f"Código de acceso: <code>{code}</code>\n\n"
        "El enlace vence en 10 minutos y te deja entrar con tu identidad real de Telegram.\n"
        "Si preferís, abrí la web y pegá el código manualmente en la opción Telegram.",
        parse_mode=ParseMode.HTML,
    )


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias de /web para enviar el link al dashboard/landing."""
    await web_login(update, context)


# ============================================================
# JOB TRACKER (PRO — /track y /postulaciones)
# ============================================================
async def track_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra una postulación manual: /track [empresa] [puesto] [url]"""
    tid = update.effective_user.id
    plan = _get_user_plan(tid)
    if plan == "free":
        await update.message.reply_text(
            "🔒 El Job Tracker es parte de JobBot Pro.\n"
            "Actualizá tu plan para habilitar el pipeline de postulaciones.",
        )
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Uso: `/track [Empresa] [Puesto] [URL_opcional]`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    company = args[0]
    title = args[1]
    url = args[2] if len(args) > 2 else ""

    db.add_application(tid, title, company, url)
    await update.message.reply_text(
        f"✅ ¡Anotado! Suerte en **{company}**. Podés ver tus aplicaciones con /postulaciones."
    )


async def postulaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista las postulaciones actuales."""
    tid = update.effective_user.id
    plan = _get_user_plan(tid)
    if plan == "free":
        await update.message.reply_text(
            "🔒 El pipeline de postulaciones es parte de JobBot Pro.\n"
            "Actualizá tu plan para ver y gestionar tus aplicaciones desde JobBot.",
        )
        return
    apps = db.get_user_applications(tid)

    if not apps:
        await update.message.reply_text(
            "Aún no registraste ninguna postulación. Usá `/track Empresa Puesto` para empezar."
        )
        return

    text = "📋 **Tus Postulaciones:**\n\n"
    for a in apps[:10]:  # Top 10
        status_icon = (
            "🔵"
            if a["status"] == "aplicado"
            else "🟡"
            if a["status"] == "entrevista"
            else "🔴"
            if a["status"] == "rechazado"
            else "🟢"
        )
        text += f"{status_icon} **{a['company']}** - {a['job_title']}\n"
        text += f"   └ Estado: {a['status'].capitalize()} | ID: `{a['id']}`\n\n"

    text += "\n*Cambiá el estado con:* `/estado_job [ID] [estado]`\n*(estados: aplicado, entrevista, rechazado, oferta)*"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def estado_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cambia el estado de una postulación."""
    tid = update.effective_user.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Uso: `/estado_job [ID] [nuevo_estado]`")
        return

    try:
        app_id = int(args[0])
        new_status = args[1].lower()
        if new_status not in ["aplicado", "entrevista", "rechazado", "oferta"]:
            raise ValueError

        db.update_application_status(app_id, tid, new_status)
        await update.message.reply_text(
            f"✅ Estado del job #{app_id} actualizado a **{new_status}**."
        )
    except:
        await update.message.reply_text("❌ ID inválido o estado no reconocido.")


# ============================================================
# MODO BÚSQUEDA (VOLUMEN vs CALIDAD)
# ============================================================
async def modo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configura el modo de búsqueda: /modo [volumen|calidad]"""
    tid = update.effective_user.id
    args = context.args

    if not args:
        # Mostrar modo actual
        user_data = db.get_user(tid)
        modo_actual = (
            user_data.get("search_mode", "calidad") if user_data else "calidad"
        )
        await update.message.reply_text(
            f"🎯 **Tu modo actual: {modo_actual.capitalize()}**\n\n"
            "**Modos disponibles:**\n"
            "• /modo volumen - Máxima cantidad de alertas (ideal para Juniors)\n"
            "• /modo calidad - Solo las mejores ofertas (match > 75%)\n\n"
            "Ejemplo: `/modo volumen`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    modo = args[0].lower()
    if modo not in ["volumen", "calidad"]:
        await update.message.reply_text(
            "❌ Modo inválido. Usá `/modo volumen` o `/modo calidad`."
        )
        return

    db.set_search_mode(tid, modo)

    if modo == "volumen":
        await update.message.reply_text(
            "✅ **Modo Volumen activado** 🚀\n\n"
            "📊 Recibirás alertas de TODOS los empleos que coincidan con tu perfil.\n"
            "• Más opciones pero menos filtrado\n"
            "• Ideal para aumentar tu volumen de aplicaciones\n"
            "• Checkeo cada 3 horas para máxima cobertura\n\n"
            "💡 *Este modo es ideal si estás starting y querés aplicar a muchos puestos.*"
        )
    else:
        await update.message.reply_text(
            "✅ **Modo Calidad activado** 🎯\n\n"
            "📊 Recibirás solo las mejores ofertas (match > 75%).\n"
            "• Menos alertas pero más relevantes\n"
            "• Ahorrás tiempo revisando\n"
            "• Checkeo cada 6 horas para no saturarte\n\n"
            "💡 *Este modo es ideal si ya tenés experiencia y buscás roles específicos.*"
        )


# ============================================================
# GITHUB ANALYSIS (PRO — /github)
# ============================================================
async def github_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza el perfil de GitHub del usuario: /github [username] [texto_oferta_opcional]"""
    tid = update.effective_user.id
    args = context.args

    # 1. Obtener username
    if args:
        username = args[0]
        db.set_github_url(tid, username)
    else:
        user_data = db.get_user(tid)
        username = user_data.get("github_url")
        if not username:
            await update.message.reply_text(
                "❌ Pasame tu usuario de GitHub: `/github tu_usuario`"
            )
            return

    msg = await update.message.reply_text(
        f"🔍 Analizando repositorios de `{username}`... Dame un segundo.",
        parse_mode=ParseMode.MARKDOWN,
    )

    repos = await fetch_github_repos(username)
    if not repos:
        await msg.edit_text("❌ No encontré repositorios públicos para ese usuario.")
        return

    # 2. Si hay texto de oferta (pegado después del username), hacemos match
    job_desc = " ".join(args[1:]) if len(args) > 1 else ""

    if job_desc:
        await msg.edit_text("🤖 Comparando tu código con la oferta...")
        analysis = await analyze_github_match(repos, job_desc)
    else:
        # Resumen general si no hay oferta
        summary = f"✅ Encontré {len(repos)} repositorios.\n\n"
        techs = {}
        for r in repos:
            lang = r["language"] or "Otros"
            techs[lang] = techs.get(lang, 0) + 1

        summary += "**Stack detectado:**\n"
        for lang, count in sorted(techs.items(), key=lambda x: x[1], reverse=True):
            summary += f"- {lang}: {count} proyectos\n"

        summary += "\n*Tip:* Pegá la descripción de un puesto después de tu usuario para ver si hacés match!"
        analysis = summary

    await update.message.reply_text(analysis, parse_mode=ParseMode.MARKDOWN)


# ============================================================
# SMART SUMMARY UX - Handlers de Callbacks
# ============================================================

async def handle_view_jobs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para cuando el usuario toca el botón "Ver todas las ofertas"
    en el mensaje resumen Smart Summary.
    """
    query = update.callback_query
    await query.answer()  # Cerrar el "loading"
    
    # Extraer batch_id del callback_data
    callback_data = query.data
    try:
        batch_id = int(callback_data.split(":")[1])
    except (IndexError, ValueError):
        await query.edit_message_text(
            "❌ Error: No se pudo procesar la solicitud.\n"
            "Probá con /buscar nuevamente."
        )
        return
    
    telegram_id = update.effective_user.id
    
    # Importar la función del scheduler
    try:
        from scheduler import send_jobs_from_batch
    except ImportError:
        from job_bot.scheduler import send_jobs_from_batch
    
    # Enviar los jobs del batch
    success = await send_jobs_from_batch(
        bot=context.bot,
        telegram_id=telegram_id,
        batch_id=batch_id,
        db=db
    )
    
    if success:
        # Reemplazar el mensaje resumen con confirmación
        await query.edit_message_text(
            "✅ ¡Ofertas enviadas! Revisá el chat."
        )


async def handle_company_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para cuando el usuario toca "Saber más de la empresa"
    en un mensaje de oferta.
    """
    query = update.callback_query
    await query.answer()  # Cerrar el "loading"
    
    # Extraer dominio del callback_data
    callback_data = query.data
    try:
        domain = callback_data.split(":", 1)[1]
    except IndexError:
        await query.edit_message_text(
            "❌ Error: No se pudo obtener información de la empresa."
        )
        return
    
    # Obtener datos de la empresa
    company_data = get_company_by_domain(domain, db=db)
    
    if not company_data:
        await query.edit_message_text(
            f"❌ No encontré información de <b>{domain}</b>.\n"
            f"La empresa puede ser privada o muy pequeña.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Intentar obtener datos financieros
    stock_data = None
    try:
        ticker = get_ticker_from_domain(domain)
        if ticker:
            stock_data = get_stock_data(ticker, db=db)
    except Exception as e:
        logger.info(f"No se pudieron obtener datos financieros para {domain}: {e}")
    
    # Formatear mensaje completo
    try:
        from financial_service import format_company_full_message
    except ImportError:
        from job_bot.financial_service import format_company_full_message
    
    formatted = format_company_full_message(company_data, stock_data)
    
    # Enviar como nuevo mensaje (para no perder el job original)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


# ============================================================
# MAIN
# ============================================================
def main():
    if not config.TELEGRAM_TOKEN:
        logger.error(
            "❌ TELEGRAM_TOKEN no configurado.\n"
            "   1. Creá el archivo .env\n"
            "   2. Copiá el contenido de .env.example\n"
            "   3. Completá TELEGRAM_TOKEN con el token de @BotFather"
        )
        return

    Path(config.CV_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    logger.info("🚀 Iniciando Job Monitor Bot para Buenos Aires...")
    logger.info(
        "📡 Fuentes activas: %s",
        ", ".join(k for k, v in config.SOURCES_ENABLED.items() if v),
    )

    # ---- Construir la app SIN job-queue ----
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # ---- Registrar handler global de errores ----
    app.add_error_handler(error_handler)

    # ---- ConversationHandler para /preferencias ----
    conv_preferencias = ConversationHandler(
        entry_points=[CommandHandler("preferencias", preferencias_start)],
        states={
            WAITING_LEVEL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, preferencias_recibe_level
                )
            ],
            WAITING_ROLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, preferencias_recibe_role
                )
            ],
            WAITING_TECHS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, preferencias_recibe_techs
                )
            ],
            WAITING_LOCATION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, preferencias_recibe_location
                )
            ],
            WAITING_MODALITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, preferencias_recibe_modality
                )
            ],
            WAITING_MAX_AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, preferencias_recibe_max_age
                )
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )

    # ---- ConversationHandler para /horarios ----
    conv_horarios = ConversationHandler(
        entry_points=[CommandHandler("horarios", horarios_start)],
        states={
            WAITING_INTERVAL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, horarios_recibe_interval
                )
            ],
            WAITING_START_HOUR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, horarios_recibe_start)
            ],
            WAITING_END_HOUR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, horarios_recibe_end)
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )

    # ---- ConversationHandler para /entrevista ----
    conv_entrevista = ConversationHandler(
        entry_points=[CommandHandler("entrevista", entrevista_start)],
        states={
            WAITING_INTERVIEW_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, entrevista_logic)
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )

    # ---- Registrar handlers ----
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("help", ayuda))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(conv_preferencias)
    app.add_handler(conv_horarios)
    app.add_handler(conv_entrevista)
    app.add_handler(CommandHandler("cargar_cv", cargar_cv_start))
    app.add_handler(CommandHandler("analizar_oferta", analizar_oferta))
    app.add_handler(CommandHandler("empresa", empresa))
    app.add_handler(CommandHandler("detalle_job", detalle_job))
    app.add_handler(CommandHandler("carta", carta))
    app.add_handler(CommandHandler("entrevista", entrevista_start))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("activar_alertas", activar_alertas))
    app.add_handler(CommandHandler("desactivar_alertas", desactivar_alertas))
    app.add_handler(CommandHandler("agregar_feed", agregar_feed))
    app.add_handler(CommandHandler("mis_feeds", mis_feeds))
    app.add_handler(CommandHandler("eliminar_feed", eliminar_feed))
    app.add_handler(CommandHandler("track", track_job))
    app.add_handler(CommandHandler("postulaciones", postulaciones))
    app.add_handler(CommandHandler("estado_job", estado_job))
    app.add_handler(CommandHandler("modo", modo))
    app.add_handler(CommandHandler("github", github_analysis))
    app.add_handler(CommandHandler("web", web_login))
    app.add_handler(CommandHandler("web_login", web_login))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("borrar_datos", borrar_datos))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # ---- Handlers de Callbacks para Smart Summary UX ----
    app.add_handler(CallbackQueryHandler(handle_view_jobs_callback, pattern="^view_jobs_batch:"))
    app.add_handler(CallbackQueryHandler(handle_company_info_callback, pattern="^company_info:"))

    # ---- Crear y setear el event loop ANTES de lanzar el thread (Python 3.14+) ----
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # ---- Scheduler en thread separado (compatible con Python 3.14) ----
    scheduler_thread = threading.Thread(
        target=run_scheduler,
        args=(app, loop),
        daemon=True,  # Se cierra automáticamente cuando el bot se detiene
        name="JobScheduler",
    )
    scheduler_thread.start()

    logger.info(
        "✅ Bot listo. Scheduler inteligente en background (polling cada %d min).",
        config.SCHEDULER_POLL_MINUTES,
    )
    logger.info("📡 Esperando mensajes... Presioná Ctrl+C para detener.")

    # ---- Iniciar polling (maneja su propio event loop internamente) ----
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
