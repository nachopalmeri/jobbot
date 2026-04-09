#!/usr/bin/env python3
"""
Script para crear usuario web vinculado a Telegram.
Uso: python3 add_web_user.py
"""
import os
import sys

# Agregar job_bot al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from job_bot.database import Database
from werkzeug.security import generate_password_hash

def add_web_user():
    # Configuración del usuario
    TELEGRAM_ID = 6722199376
    EMAIL = "paradonista@gmail.com"
    PASSWORD = "lulita"
    PLAN = "free"  # free, starter, pro, premium
    
    print(f"Creando usuario web...")
    print(f"  Email: {EMAIL}")
    print(f"  Telegram ID: {TELEGRAM_ID}")
    print(f"  Plan: {PLAN}")
    
    # Inicializar DB
    db = Database()
    
    # Verificar si ya existe usuario Telegram
    telegram_user = db.get_user(TELEGRAM_ID)
    if not telegram_user:
        print(f"\n⚠️  No existe usuario Telegram con ID {TELEGRAM_ID}")
        print("Creando usuario Telegram primero...")
        db.create_user_if_not_exists(TELEGRAM_ID, "Pisculichi")
        print("✅ Usuario Telegram creado")
    else:
        print(f"✅ Usuario Telegram encontrado: {telegram_user.get('name', 'N/A')}")
    
    # Verificar si ya existe web_user
    existing = db.get_web_user(TELEGRAM_ID)
    if existing:
        print(f"\n⚠️  Ya existe web_user para este telegram_id")
        print(f"   Email actual: {existing.get('email')}")
        print(f"   Plan actual: {existing.get('plan')}")
        
        respuesta = input("\n¿Querés actualizar la contraseña? (s/n): ").lower()
        if respuesta == 's':
            # Actualizar contraseña
            password_hash = generate_password_hash(PASSWORD)
            if db.db_type == "supabase":
                db._execute(
                    "UPDATE web_users SET password_hash = %s WHERE telegram_id = %s",
                    (password_hash, TELEGRAM_ID)
                )
            else:
                db._execute(
                    "UPDATE web_users SET password_hash = ? WHERE telegram_id = ?",
                    (password_hash, TELEGRAM_ID)
                )
            print("✅ Contraseña actualizada")
        return
    
    # Crear web_user
    password_hash = generate_password_hash(PASSWORD)
    
    if db.db_type == "supabase":
        query = """
            INSERT INTO web_users 
            (telegram_id, email, password_hash, plan, job_tracker_enabled, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
    else:
        query = """
            INSERT INTO web_users 
            (telegram_id, email, password_hash, plan, job_tracker_enabled, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """
    
    try:
        db._execute(query, (
            TELEGRAM_ID, 
            EMAIL, 
            password_hash, 
            PLAN,
            1 if PLAN in ['starter', 'pro', 'premium'] else 0,  # job_tracker_enabled
            1  # is_admin = 1 (como ya lo tenía antes)
        ))
        print("\n✅ Usuario web creado exitosamente!")
        print(f"\n📧 Email: {EMAIL}")
        print(f"🔑 Contraseña: {PASSWORD}")
        print(f"👤 Usuario: Pisculichi")
        print(f"🆔 Telegram ID: {TELEGRAM_ID}")
        print(f"⭐ Plan: {PLAN}")
        print(f"🛡️ Admin: Sí")
        print(f"\n🔗 Login en: https://app-jobbot.vercel.app/login")
        
    except Exception as e:
        print(f"\n❌ Error creando usuario: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_web_user()
