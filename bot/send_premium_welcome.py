#!/usr/bin/env python3
"""
Envia mensaje de bienvenida Premium al usuario manualmente.
"""

import sys
import os
from pathlib import Path

# Asegurar que podemos importar job_bot
sys.path.insert(0, str(Path(__file__).parent))

# Configurar variables de entorno si no existen
if not os.getenv('TELEGRAM_TOKEN'):
    # Leer del archivo .env si existe
    from dotenv import load_dotenv
    load_dotenv()

from telegram import Bot
from telegram.constants import ParseMode

# Datos del usuario
TELEGRAM_ID = 6722199376
FIRST_NAME = "Pisculichi"
EXPIRES_DATE = "2026-04-30"

async def send_premium_welcome():
    """Envia mensaje de bienvenida Premium al usuario."""
    
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("Error: No se encontro TELEGRAM_TOKEN")
        print("Asegurate de tener el token configurado en .env")
        return False
    
    bot = Bot(token=token)
    
    message = (
        f"👋 ¡Hola {FIRST_NAME}!\n\n"
        f"💎 <b>BIENVENIDO A TU PLAN PREMIUM</b> 💎\n\n"
        f"Tu suscripcion esta activa hasta el {EXPIRES_DATE}.\n\n"
        f"🎯 <b>Beneficios incluidos:</b>\n"
        f"• 150 busquedas por dia\n"
        f"• 30 analisis IA de CV y ofertas por mes\n"
        f"• Simulador de entrevistas con IA (20/mes)\n"
        f"• Generador de cover letters (20/mes)\n"
        f"• Job tracker completo sin limites\n\n"
        f"📋 <b>Comandos Premium disponibles:</b>\n"
        f"/entrevista — Simular entrevista tecnica\n"
        f"/carta [URL] — Generar cover letter personalizado\n"
        f"/analizar_oferta [URL] — Analisis match con IA\n\n"
        f"📊 <b>Configuracion:</b>\n"
        f"/preferencias — Configurar tu perfil\n"
        f"/horarios — Elegir frecuencia de alertas\n"
        f"/estado — Ver tu configuracion y uso\n\n"
        f"🚀 Empeza con /preferencias"
    )
    
    try:
        await bot.send_message(
            chat_id=TELEGRAM_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
        print(f"[OK] Mensaje de bienvenida Premium enviado a {FIRST_NAME}")
        return True
    except Exception as e:
        print(f"[X] Error enviando mensaje: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    try:
        result = asyncio.run(send_premium_welcome())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
