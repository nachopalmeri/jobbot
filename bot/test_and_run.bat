@echo off
REM ============================================
REM JobBot - Script de Setup y Prueba
REM ============================================

echo.
echo ========================================
echo 🎯 JOBBOT - SETUP DE PRUEBA
echo ========================================
echo.

REM 1. Instalar dependencias
echo 📦 Paso 1: Instalando dependencias...
pip install python-telegram-bot python-dotenv requests feedparser beautifulsoup4 pdfplumber groq
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)
echo ✅ Dependencias instaladas
echo.

REM 2. Configurar usuario premium
echo 🗄️  Paso 2: Configurando usuario premium...
python setup_test_user.py
echo.

REM 3. Iniciar el bot
echo.
echo ========================================
echo 🎉 SETUP COMPLETO!
echo ========================================
echo.
echo 📋 PRÓXIMOS PASOS:
echo.
echo 1. Ejecuta: python bot.py
echo 2. Ve a Telegram y enviale estos comandos:
echo    /start
echo    /estado
echo    /buscar
echo    /modo volumen
echo    /track MercadoLibre Python
echo    /postulaciones
echo.
echo 3. Para probar el dashboard:
echo    - Abrir index.html en browser
echo    - Ir a "Demo Pro"
echo    - Ingresar ID: 6722199376
echo.
echo ========================================
echo.
echo Presiona cualquier tecla para iniciar el bot...
pause >nul

echo.
echo ▶️  Iniciando JobBot...
python bot.py
