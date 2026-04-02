import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DASHBOARD_URL = os.getenv(
    "DASHBOARD_URL", "https://app-jobbot.vercel.app"
).rstrip("/")


class AuthHandler:
    def __init__(self, db, api_base_url: str = DASHBOARD_URL):
        self.db = db
        self.api_url = api_base_url

    async def start_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el proceso de autenticación web."""
        user = update.effective_user
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔗 Vincular cuenta web",
                    url=f"{self.api_url}/login",
                )
            ]
        ]
        await update.message.reply_text(
            "💎 *Vincular tu cuenta*\n\n"
            "Conecta tu cuenta de Telegram con la web para acceder al dashboard "
            "y gestionar tu suscripción premium.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def check_premium(self, telegram_id: int) -> dict:
        """Verifica el estado premium del usuario."""
        user = self.db.get_web_user(telegram_id)
        if not user:
            return {"premium": False, "reason": "not_linked"}

        if (
            user.get("plan") == "premium"
            and user.get("subscription_status") == "active"
        ):
            return {"premium": True}

        return {"premium": False, "reason": "free_user"}

    async def require_premium(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Decorador para comandos premium. Retorna False si no es premium."""
        user_id = update.effective_user.id
        status = await self.check_premium(user_id)

        if not status["premium"]:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "⭐ Actualizar a Premium",
                        url=f"{self.api_url}/dashboard/suscripcion",
                    )
                ]
            ]
            await update.message.reply_text(
                "⚠️ *Función Premium*\n\n"
                "Esta función está disponible para usuarios Premium.\n"
                "¡Actualiza y disfruta de beneficios ilimitados!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return False
        return True

    async def send_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Envía el panel del usuario con su estado."""
        user_id = update.effective_user.id
        web_user = self.db.get_web_user(user_id)

        if not web_user:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔗 Vincular cuenta", url=f"{self.api_url}/login"
                    )
                ]
            ]
            await update.message.reply_text(
                "📱 *Tu Panel*\n\n"
                "¡Vincular tu cuenta para acceder al dashboard!\n\n"
                "Con Premium: análisis ilimitados, alertas sin límites y más.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return

        plan = web_user.get("plan", "free").upper()
        ai_used = web_user.get("ai_analyses_used", 0)
        ai_limit = web_user.get("ai_analyses_limit", 0)
        search_used = web_user.get("searches_used", 0)
        search_limit = web_user.get("searches_limit", 0)

        emoji = "🟣" if plan == "PREMIUM" else "⚪"
        ai_limit_label = "Ilimitado" if not ai_limit else str(ai_limit)
        search_limit_label = "Ilimitadas" if not search_limit else str(search_limit)

        usage = f"""
📊 *Tu Estado*

{emoji} Plan: *{plan}*
📈 Análisis CV: {ai_used}/{ai_limit_label}
🔍 Búsquedas: {search_used}/{search_limit_label}

/buscar - Buscar empleos
/cargar_cv - Subir CV
/vincular - Cuenta web
/suscripcion - Actualizar plan
"""
        await update.message.reply_text(usage, parse_mode="Markdown")

    async def check_and_increment_usage(
        self, telegram_id: int, usage_type: str
    ) -> tuple[bool, str]:
        """
        Verifica límites de uso y los incrementa.
        Retorna (puede_usar, mensaje)
        """
        web_user = self.db.get_web_user(telegram_id)

        if not web_user:
            return (True, "")  # Sin cuenta web = límites por defecto

        if not self.db.check_usage_limit(telegram_id, usage_type):
            return (
                False,
                f"Has alcanzado el límite de {usage_type}. ¡Actualiza a Premium!",
            )

        self.db.increment_usage(telegram_id, usage_type)
        return (True, "")
