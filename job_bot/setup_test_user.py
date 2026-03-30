"""
Script para configurar usuario de prueba premium
Ejecutar: python setup_test_user.py
"""

import sqlite3

DB_PATH = "job_bot.db"
TEST_TELEGRAM_ID = 6722199376
TEST_NAME = "@Pisculichiii"


def setup_user():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si existe el usuario
    cursor.execute(
        "SELECT telegram_id, name, plan FROM users WHERE telegram_id = ?",
        (TEST_TELEGRAM_ID,),
    )
    existing = cursor.fetchone()

    if existing:
        print(f"✅ Usuario {TEST_TELEGRAM_ID} ya existe: {existing}")
        print("Actualizando a premium...")
    else:
        print(f"❌ Usuario {TEST_TELEGRAM_ID} no existe. Creando...")
        cursor.execute(
            """
            INSERT INTO users (telegram_id, name, active_alerts, weekly_goal_apps, search_mode, job_modality, experience_level, role_type, technologies, plan)
            VALUES (?, ?, 1, 30, 'volumen', 'remoto', 'junior', 'Python Developer', 'python,django,postgresql', 'premium')
        """,
            (TEST_TELEGRAM_ID, TEST_NAME),
        )

    # Actualizar a premium
    cursor.execute(
        """
        UPDATE users SET 
            plan = 'premium',
            active_alerts = 1,
            weekly_goal_apps = 30,
            search_mode = 'volumen',
            job_modality = 'remoto',
            experience_level = 'junior',
            role_type = 'Python Developer',
            technologies = 'python,django,postgresql'
        WHERE telegram_id = ?
    """,
        (TEST_TELEGRAM_ID,),
    )

    conn.commit()

    # Verificar
    cursor.execute(
        "SELECT telegram_id, name, plan, active_alerts, weekly_goal_apps, search_mode, job_modality FROM users WHERE telegram_id = ?",
        (TEST_TELEGRAM_ID,),
    )
    user = cursor.fetchone()

    print("\n" + "=" * 50)
    print("✅ USUARIO CONFIGURADO:")
    print("=" * 50)
    print(f"ID: {user[0]}")
    print(f"Nombre: {user[1]}")
    print(f"Plan: {user[2]}")
    print(f"Alertas activas: {user[3]}")
    print(f"Goal semanal: {user[4]}")
    print(f"Modo búsqueda: {user[5]}")
    print(f"Modalidad: {user[6]}")
    print("=" * 50)

    conn.close()


if __name__ == "__main__":
    setup_user()
