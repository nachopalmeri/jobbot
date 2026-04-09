#!/usr/bin/env python3
"""
Activa plan Premium para @Pisculichiii usando el flujo real del sistema.
Simula un pago exitoso procesado por webhook.
"""

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Asegurar que podemos importar job_bot
sys.path.insert(0, str(Path(__file__).parent))

try:
    from database import Database
except ImportError:
    from job_bot.database import Database

# Datos del usuario (proporcionados por el usuario real)
TELEGRAM_ID = 6722199376
USERNAME = "@Pisculichiii"
FIRST_NAME = "Pisculichi"
TEST_EMAIL = "pisculichi.test@jobbot.local"  # Email temporal para testing

# Datos del "pago" simulado (generados dinamicamente, no hardcodeados)
PAYMENT_ID = f"test_{uuid.uuid4().hex[:12]}"
WEBHOOK_EVENT_ID = f"evt_{uuid.uuid4().hex[:16]}"
PROVIDER = "stripe_test"  # Simulando Stripe
PLAN = "premium"
AMOUNT = 15.00
CURRENCY = "USD"

def activate_premium_realistic():
    """Activa Premium usando los metodos reales de la base de datos."""
    
    print(">>> Activando plan Premium via flujo real del sistema...")
    print(f"   Usuario: {USERNAME}")
    print(f"   Telegram ID: {TELEGRAM_ID}")
    print(f"   Plan: {PLAN.capitalize()}")
    print(f"   Monto: ${AMOUNT} {CURRENCY}")
    print(f"   Payment ID: {PAYMENT_ID}")
    print(f"   Webhook Event: {WEBHOOK_EVENT_ID}\n")
    
    db = Database()
    
    # 1. Verificar si ya existe un pago registrado para este usuario
    existing_payments = db.get_user_payments(TELEGRAM_ID)
    if existing_payments:
        print(f"[!] El usuario ya tiene {len(existing_payments)} pago(s) registrado(s)")
        for p in existing_payments[:3]:  # Mostrar ultimos 3
            print(f"   - {p['provider']}: ${p['amount']} ({p['status']})")
        print()
    
    # 2. Verificar si el webhook ya fue procesado (idempotencia)
    if db.is_webhook_processed(WEBHOOK_EVENT_ID):
        print(f"[!] Webhook {WEBHOOK_EVENT_ID[:20]}... ya fue procesado anteriormente")
        print("   Usando flujo de recuperacion...\n")
    else:
        # 3. Registrar el pago usando el metodo REAL del sistema
        print("[+] Registrando pago en tabla 'payments'...")
        db.record_payment(
            telegram_id=TELEGRAM_ID,
            provider=PROVIDER,
            amount=AMOUNT,
            currency=CURRENCY,
            status="completed",
            provider_payment_id=PAYMENT_ID
        )
        print(f"   [OK] Pago registrado: ${AMOUNT} {CURRENCY}")
        
        # 4. Marcar webhook como procesado (idempotencia real)
        print(f"[+] Marcando webhook como procesado...")
        db.mark_webhook_processed(
            event_id=WEBHOOK_EVENT_ID,
            provider=PROVIDER,
            event_type="checkout.session.completed"
        )
        print(f"   [OK] Webhook {WEBHOOK_EVENT_ID[:20]}... procesado")
    
    # 5. Crear/verificar usuario en tabla users (legacy) si no existe
    print(f"\n[+] Verificando usuario en sistema...")
    existing_user = db.get_user(TELEGRAM_ID)
    if existing_user:
        print(f"   [OK] Usuario existe: {existing_user.get('name', 'N/A')}")
        print(f"   [i] Plan actual: {existing_user.get('plan', 'free')}")
    else:
        print(f"   [+] Creando usuario nuevo...")
        db.create_user_if_not_exists(TELEGRAM_ID, FIRST_NAME)
        print(f"   [OK] Usuario creado: {FIRST_NAME}")
    
    # 6. Nota: La tabla 'users' (legacy) NO tiene columna 'plan'
    # El plan se maneja exclusivamente en 'web_users' (SaaS)
    # El bot consulta get_user_plan() que lee de web_users
    print(f"\n[i] Nota: El plan se maneja en tabla 'web_users' (SaaS)")
    print(f"   La tabla 'users' (legacy) no tiene columna 'plan'")
    print(f"   El bot usa get_user_plan() que lee desde web_users")
    
    # 7. Crear/actualizar en tabla web_users (SaaS) con metodo REAL
    print(f"\n[+] Verificando cuenta web (SaaS)...")
    web_user = db.get_web_user(TELEGRAM_ID)
    
    if not web_user:
        print(f"   [+] Creando cuenta web...")
        # Crear password hash temporal
        import hashlib
        password_hash = hashlib.sha256(f"temp_pass_{TELEGRAM_ID}".encode()).hexdigest()
        db.create_web_user(TELEGRAM_ID, TEST_EMAIL, password_hash)
        print(f"   [OK] Cuenta web creada: {TEST_EMAIL}")
    else:
        print(f"   [OK] Cuenta web existe: {web_user.get('email', 'N/A')}")
        print(f"   [i] Plan actual web: {web_user.get('plan', 'free')}")
    
    # 8. Actualizar a Premium usando el metodo REAL del sistema
    print(f"\n[>] Activando plan Premium con limites...")
    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    db.update_user_plan(TELEGRAM_ID, PLAN, expires_at)
    print(f"   [OK] Plan activado: {PLAN.capitalize()}")
    print(f"   [OK] Expira: {expires_at[:10]}")
    
    # 8.5 Ajustar searches_limit a 150 (realista, no ilimitado)
    # y asegurar que interviews_limit esté configurado
    print(f"\n[>] Ajustando limites realistas...")
    db._execute(
        "UPDATE web_users SET searches_limit = 150, interviews_limit = 20 WHERE telegram_id = ?",
        (TELEGRAM_ID,)
    )
    print(f"   [OK] Limite ajustado: 150 busquedas/dia")
    print(f"   [OK] Entrevistas incluidas: 20/mes")
    
    # 9. Verificacion final
    print(f"\n{'='*60}")
    print(f"[+] PREMIUM ACTIVADO - FLUJO REAL COMPLETADO")
    print(f"{'='*60}")
    
    # Verificar tabla users
    user_final = db.get_user(TELEGRAM_ID)
    actual_plan = db.get_user_plan(TELEGRAM_ID)
    print(f"\n[i] Tabla 'users' (Bot Telegram):")
    print(f"   ID: {user_final['telegram_id']}")
    print(f"   Nombre: {user_final['name']}")
    print(f"   Alertas: {'Activas' if user_final.get('active_alerts') else 'Inactivas'}")
    print(f"   [OK] Plan actual (via get_user_plan): {actual_plan}")
    
    # Verificar tabla web_users
    web_final = db.get_web_user(TELEGRAM_ID)
    print(f"\n[i] Tabla 'web_users' (Dashboard):")
    print(f"   Email: {web_final['email']}")
    print(f"   Plan: {web_final['plan']}")
    print(f"   Estado: {web_final['subscription_status']}")
    print(f"   AI Analisis: {web_final['ai_analyses_used']}/{web_final['ai_analyses_limit']}")
    print(f"   Busquedas: {web_final['searches_used']}/{web_final['searches_limit']}")
    print(f"   Entrevistas: {web_final.get('interviews_used', 0)}/{web_final.get('interviews_limit', 20)}")
    print(f"   Job Tracker: {'SI' if web_final['job_tracker_enabled'] else 'NO'}")
    print(f"   Expira: {web_final['subscription_expires_at'][:10] if web_final['subscription_expires_at'] else 'Nunca'}")
    
    # Verificar pagos
    payments_final = db.get_user_payments(TELEGRAM_ID)
    print(f"\n[$] Pagos registrados: {len(payments_final)}")
    for p in payments_final[:1]:
        print(f"   Ultimo: {p['provider']} - ${p['amount']} {p['currency']} ({p['status']})")
    
    print(f"\n{'='*60}")
    print(f"[+] LISTO PARA TESTEAR!")
    print(f"{'='*60}")
    print(f"\n[>] Flujo a probar desde cero:")
    print(f"   1. /start - Iniciar bot")
    print(f"   2. /preferencias - Configurar perfil (vacio)")
    print(f"   3. /cargar_cv - Subir tu CV real")
    print(f"   4. /analizar_cv - IA analiza tu CV")
    print(f"   5. /horarios - Configurar alertas")
    print(f"   6. /activar_alertas - Recibir ofertas")
    print(f"   7. /buscar - Buscar trabajos")
    print(f"   8. /entrevista - Simular entrevistas (Premium)")
    print(f"   9. /carta - Generar cover letters (Premium)")
    print(f"\n[i] Todos los limites Premium activados:")
    print(f"   - 150 busquedas/dia")
    print(f"   - 50 analisis IA/mes")
    print(f"   - 20 entrevistas/mes")
    print(f"   - 20 cover letters/mes")
    print(f"   - Job tracker completo")
    
    return True

if __name__ == "__main__":
    try:
        success = activate_premium_realistic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
