@echo off
echo.
echo ========================================
echo 🎯 JOBBOT - EJECUTAR BOT
echo ========================================
echo.

REM Matar cualquier proceso anterior de python
echo 🧹 Cerrando procesos anteriores...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Ir al directorio correcto
cd /d "%~dp0"

REM Verificar que existe bot.py
if not exist bot.py (
    echo ❌ Error: No se encuentra bot.py
    echo 💡 Asegurate de estar en la carpeta job_bot
    pause
    exit /b 1
)

echo.
echo ✅ Todo listo!
echo.
echo ▶️  Iniciando JobBot...
echo 📡 Esperando mensajes de Telegram...
echo.
echo Presiona Ctrl+C para detener
echo.

python bot.py
