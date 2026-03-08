#!/usr/bin/env python3
"""
bot.py — Punto de entrada del Job Monitor Bot
Nacho (PISCU) — Bot de búsqueda laboral IT para Buenos Aires

Ejecutar: python bot.py
"""

import asyncio
import logging
import os
import threading
import time
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
from database import Database
from job_scraper import JobScraper
from scheduler import check_jobs_for_user
from stats_api import run_stats_api

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
db = Database(config.DATABASE_PATH)
scraper = JobScraper()

WAITING_LEVEL, WAITING_ROLE, WAITING_TECHS, WAITING_LOCATION, WAITING_MAX_AGE = range(5)

# ============================================================
# SCHEDULER EN THREAD SEPARADO (reemplaza JobQueue)
# Funciona con cualquier versión de Python incluyendo 3.14
# ============================================================

def run_scheduler(app: Application, loop: asyncio.AbstractEventLoop):
    """
    Corre en un thread separado. Cada CHECK_INTERVAL_HOURS horas
    chequea ofertas para todos los usuarios con alertas activas.
    """
    # Esperar 5 minutos antes del primer chequeo
    logger.info("⏰ Scheduler iniciado. Primer chequeo en 5 minutos.")
    time.sleep(5 * 60)

    while True:
        try:
            logger.info("⏰ Iniciando ciclo automático del scheduler...")
            active_users = db.get_all_active_users()
            logger.info("👥 %d usuario(s) con alertas activas", len(active_users))

            for user in active_users:
                tid = user["telegram_id"]
                try:
                    # Ejecutar la corutina async desde el thread sincrónico usando el loop principal
                    future = asyncio.run_coroutine_threadsafe(
                        check_jobs_for_user(app.bot, tid, db, scraper, notify_if_empty=False),
                        loop,
                    )
                    future.result(timeout=120)
                except Exception as e:
                    logger.error("Error en scheduler para usuario %s: %s", tid, e)
                time.sleep(2)

            logger.info("✅ Ciclo automático completado. Próximo en %dh.", config.CHECK_INTERVAL_HOURS)
        except Exception as e:
            logger.error("Error en ciclo del scheduler: %s", e)

        # Dormir hasta el próximo ciclo
        time.sleep(config.CHECK_INTERVAL_HOURS * 3600)


# ============================================================
# /start
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user_if_not_exists(user.id, user.first_name or "Usuario")
    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name}! Soy tu asistente de búsqueda laboral IT.\n\n"
        "🎯 Qué puedo hacer:\n"
        "• Monitorear ofertas cada 2 horas automáticamente\n"
        "• Buscar en LinkedIn AR, Remotive, Arbeitnow, Jobicy y más\n"
        "• Notificarte SOLO cuando hay algo nuevo\n"
        "• Guardar tu CV para tenerlo a mano\n\n"
        "📋 Comandos:\n"
        "/preferencias — Configurar tu perfil y zona\n"
        "/cargar_cv — Subir tu CV (PDF o TXT)\n"
        "/buscar — Búsqueda inmediata\n"
        "/activar_alertas — Monitoreo automático cada 2h\n"
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
    user_data    = db.get_user(user.id)
    keywords     = db.get_user_keywords(user.id)
    custom_feeds = db.get_custom_feeds(user.id)

    profile = db.get_user_profile(user.id)
    level_names = {
        "sin_experiencia": "Sin experiencia",
        "junior": "Junior",
        "semi_senior": "Semi-Senior",
        "senior": "Senior",
    }
    exp = level_names.get(profile.get("experience_level", "junior"), "Junior")
    rol = profile.get("role_type") or "No definido"
    tec = profile.get("technologies") or "No definido"

    alertas  = "✅ Activas"  if user_data.get("active_alerts") else "❌ Inactivas"
    cv       = f"✅ {Path(user_data['cv_path']).name}" if user_data.get("cv_path") else "❌ No cargado"
    last     = user_data.get("last_check") or "Nunca"
    location = user_data.get("location") or config.DEFAULT_LOCATION
    kw_lines = "\n".join(f"  • {kw}" for kw in keywords) if keywords else "  Sin keywords"

    feeds_section = ""
    if custom_feeds:
        feeds_section = "\n\nFeeds RSS personalizados:\n"
        feeds_section += "\n".join(f"  • {f['feed_name']} (ID: {f['id']})" for f in custom_feeds)

    msg = (
        f"📊 Tu configuración\n\n"
        f"👤 Nombre: {user_data['name']}\n"
        f"📍 Ubicación: {location}\n"
        f"🏅 Nivel: {exp}\n"
        f"💼 Rol: {rol}\n"
        f"🛠 Tecnología: {tec}\n"
        f"⏳ Antigüedad máx: {profile.get('max_job_age_days', 30)} días\n\n"
        f"🔔 Alertas: {alertas}\n"
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
        "<b>Paso 1/5 — ¿Cuál es tu nivel de experiencia?</b>\n\n"
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
        "1": "sin_experiencia", "sin experiencia": "sin_experiencia",
        "2": "junior", "junior": "junior",
        "3": "semi_senior", "semi senior": "semi_senior", "ssr": "semi_senior",
        "4": "senior", "senior": "senior",
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
        "💼 <b>Paso 2/5 — ¿Qué tipo de rol buscás?</b>\n\n"
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
        "🛠 <b>Paso 3/5 — ¿Qué tecnologías sabés o estás aprendiendo?</b>\n\n"
        "Escribí separadas por coma:\n"
        "Ejemplo: Python, JavaScript, SQL, React, Java\n\n"
        "Si no sabés todavía, escribí: general",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_TECHS


async def preferencias_recibe_techs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text or len(text) < 2:
        await update.message.reply_text("❌ Escribí al menos una tecnología o 'general'.")
        return WAITING_TECHS

    if text.lower() == "general":
        text = "programación, IT, desarrollo, software"

    context.user_data["technologies"] = text

    user_data = db.get_user(update.effective_user.id)
    curr_location = user_data.get("location", config.DEFAULT_LOCATION) if user_data else config.DEFAULT_LOCATION

    await update.message.reply_text(
        f"✅ Tecnologías: <b>{text}</b>\n\n"
        "📍 <b>Paso 4/5 — ¿En qué zona buscás trabajo?</b>\n\n"
        f"Ubicación actual: {curr_location}\n\n"
        "Escribí la nueva ubicación o escribí 'misma' para mantener la actual.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_LOCATION


async def preferencias_recibe_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.lower() not in ["/misma", "misma"]:
        db.set_user_location(user_id, text)
        location = text
    else:
        user_data = db.get_user(user_id)
        location = user_data.get("location", config.DEFAULT_LOCATION) if user_data else config.DEFAULT_LOCATION

    context.user_data["location"] = location

    await update.message.reply_text(
        f"✅ Ubicación: <b>{location}</b>\n\n"
        "⏳ <b>Paso 5/5 — ¿Qué antigüedad máxima pueden tener las ofertas?</b>\n\n"
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


async def preferencias_recibe_max_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    age_map = {
        "1": 1, "24 horas": 1, "24hs": 1, "1 dia": 1, "1 día": 1,
        "2": 3, "3 dias": 3, "3 días": 3,
        "3": 7, "1 semana": 7, "7 dias": 7, "7 días": 7,
        "4": 30, "1 mes": 30, "30 dias": 30, "30 días": 30,
        "5": 90, "3 meses": 90, "90 dias": 90, "90 días": 90,
        "6": 3650, "cualquiera": 3650, "mas": 3650, "más": 3650,
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
    
    db.set_user_profile(user_id, exp_level, role_type, technologies, "cualquiera", max_job_age_days=max_age)

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
        1: "24 horas", 3: "3 días", 7: "1 semana", 
        30: "1 mes", 90: "3 meses", 3650: "Sin límite"
    }

    kw_text = "\n".join(f"  • {kw}" for kw in smart_keywords)
    await update.message.reply_text(
        "✅ <b>¡Perfil configurado!</b>\n\n"
        f"📊 Nivel: {level_names.get(exp_level, exp_level)}\n"
        f"💼 Rol: {role_type}\n"
        f"🛠 Tecnologías: {technologies}\n"
        f"📍 Ubicación: {location}\n"
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

    doc     = update.message.document
    user_id = update.effective_user.id

    allowed_types = {"application/pdf", "text/plain"}
    if doc.mime_type not in allowed_types:
        await update.message.reply_text("❌ Solo acepto PDF o TXT.")
        return
    if doc.file_size > 5 * 1024 * 1024:
        await update.message.reply_text("❌ Archivo muy grande. Máximo 5 MB.")
        return

    cv_dir    = Path(config.CV_STORAGE_PATH)
    cv_dir.mkdir(parents=True, exist_ok=True)
    ext       = ".pdf" if doc.mime_type == "application/pdf" else ".txt"
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
        await update.message.reply_text(f"❌ Error al guardar. Intentá de nuevo.\nDetalle: {str(e)[:100]}")


# ============================================================
# /buscar
# ============================================================
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user_if_not_exists(user_id, update.effective_user.first_name or "Usuario")
    keywords = db.get_user_keywords(user_id)
    if not keywords:
        await update.message.reply_text("⚠️ No tenés keywords. Usá /preferencias primero.")
        return

    status_msg = await update.message.reply_text(
        f"🔍 Buscando trabajos...\n"
        f"({len(keywords)} keywords — puede tardar 15-30 segundos)"
    )
    try:
        await check_jobs_for_user(context.bot, user_id, db, scraper, notify_if_empty=True)
        await status_msg.delete()
    except Exception as e:
        logger.error("Error en búsqueda manual: %s", e)
        await status_msg.edit_text(f"❌ Error durante la búsqueda.\nDetalle: {str(e)[:100]}")


# ============================================================
# /activar_alertas y /desactivar_alertas
# ============================================================
async def activar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user_if_not_exists(user_id, update.effective_user.first_name or "Usuario")
    keywords = db.get_user_keywords(user_id)
    if not keywords:
        await update.message.reply_text("⚠️ Configurá tus keywords primero con /preferencias")
        return
    db.set_alerts_active(user_id, True)
    await update.message.reply_text(
        f"✅ Alertas activadas!\n\n"
        f"Te notifico cada {config.CHECK_INTERVAL_HOURS} horas si hay nuevas ofertas.\n"
        f"Monitoreando {len(keywords)} keywords.\n\n"
        "Primer chequeo automático: en ~5 min desde que arranqué.\n"
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

    url  = context.args[0].strip()
    name = " ".join(context.args[1:]).strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ La URL debe empezar con http:// o https://")
        return

    await update.message.reply_text("⏳ Verificando el feed...")
    import feedparser
    try:
        test           = feedparser.parse(url)
        entries_count  = len(test.entries)
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
        await update.message.reply_text("No tenés feeds. Usá /agregar_feed para agregar uno.")
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
# /ayuda
# ============================================================
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Job Monitor Bot — Comandos\n\n"
        "/start — Iniciar\n"
        "/preferencias — Configurar tu perfil y zona\n"
        "/cargar_cv — Subir CV (PDF o TXT)\n"
        "/buscar — Búsqueda manual ahora\n"
        "/activar_alertas — Monitoreo automático cada 2h\n"
        "/desactivar_alertas — Pausar monitoreo\n"
        "/estado — Ver tu configuración\n"
        "/agregar_feed [URL] [Nombre] — Agregar RSS\n"
        "/mis_feeds — Ver feeds agregados\n"
        "/eliminar_feed [ID] — Eliminar feed\n"
        "/web — Ver la landing page del bot\n"
        "/ayuda — Este mensaje\n\n"
        "Fuentes: LinkedIn AR (Google News RSS), Remotive, Arbeitnow, Jobicy (remotos IT), "
        "Google Jobs (con SerpAPI key), Twitter/X (con Bearer Token), "
        "Feeds RSS personalizados."
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
    logger.info("📡 Fuentes activas: %s",
        ", ".join(k for k, v in config.SOURCES_ENABLED.items() if v))

    # ---- Construir la app SIN job-queue ----
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # ---- ConversationHandler para /preferencias ----
    conv_preferencias = ConversationHandler(
        entry_points=[CommandHandler("preferencias", preferencias_start)],
        states={
            WAITING_LEVEL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, preferencias_recibe_level)],
            WAITING_ROLE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, preferencias_recibe_role)],
            WAITING_TECHS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, preferencias_recibe_techs)],
            WAITING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, preferencias_recibe_location)],
            WAITING_MAX_AGE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, preferencias_recibe_max_age)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )

    # ---- Registrar handlers ----
    app.add_handler(CommandHandler("start",              start))
    app.add_handler(CommandHandler("ayuda",              ayuda))
    app.add_handler(CommandHandler("help",               ayuda))
    app.add_handler(CommandHandler("estado",             estado))
    app.add_handler(conv_preferencias)
    app.add_handler(CommandHandler("cargar_cv",          cargar_cv_start))
    app.add_handler(CommandHandler("buscar",             buscar))
    app.add_handler(CommandHandler("activar_alertas",    activar_alertas))
    app.add_handler(CommandHandler("desactivar_alertas", desactivar_alertas))
    app.add_handler(CommandHandler("agregar_feed",       agregar_feed))
    app.add_handler(CommandHandler("mis_feeds",          mis_feeds))
    app.add_handler(CommandHandler("eliminar_feed",      eliminar_feed))
    app.add_handler(CommandHandler("web",                 web))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # ---- Crear y setear el event loop ANTES de lanzar el thread (Python 3.14+) ----
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # ---- Scheduler en thread separado (compatible con Python 3.14) ----
    scheduler_thread = threading.Thread(
        target=run_scheduler,
        args=(app, loop),
        daemon=True,   # Se cierra automáticamente cuando el bot se detiene
        name="JobScheduler",
    )
    scheduler_thread.start()

    # ---- Stats API (para la landing page) ----
    if config.STATS_API_ENABLED:
        run_stats_api(db, port=config.STATS_API_PORT)

    logger.info("✅ Bot listo. Scheduler en background (primer chequeo en 5 min).")
    logger.info("📡 Esperando mensajes... Presioná Ctrl+C para detener.")

    # ---- Iniciar polling (maneja su propio event loop internamente) ----
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
