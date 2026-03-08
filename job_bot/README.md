# 🤖 Job Monitor Bot — Buenos Aires IT

Bot de Telegram para monitorear ofertas laborales de Python/Backend/Junior en Buenos Aires.
Hecho por y para **Nacho (PISCU)** — Gestión de TI.

---

## 📁 Estructura de archivos

```
job_bot/
├── bot.py            ← Punto de entrada. Ejecutá esto.
├── config.py         ← Variables de entorno y settings globales
├── database.py       ← Capa de base de datos (SQLite)
├── job_scraper.py    ← Scrapers de todas las fuentes de empleo
├── scheduler.py      ← Lógica del monitoreo automático + formato de mensajes
├── requirements.txt  ← Dependencias
├── .env.example      ← Template de configuración
├── .env              ← Tu config real (NO subir a git)
├── bot.log           ← Logs del bot (se crea al ejecutar)
├── job_bot.db        ← Base de datos SQLite (se crea al ejecutar)
└── cvs/              ← Carpeta de CVs subidos (se crea al ejecutar)
```

---

## ⚡ Instalación paso a paso

### Paso 1 — Verificar Python

```bash
python --version
# Necesitás Python 3.8 o superior
```

### Paso 2 — Clonar / descargar el proyecto

```bash
# Si lo bajaste como ZIP, descomprimilo en una carpeta
cd job_bot
```

### Paso 3 — (Recomendado) Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Paso 4 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 5 — Crear tu bot en Telegram

1. Abrí Telegram y buscá **@BotFather**
2. Enviá `/newbot`
3. Elegí un nombre: `NachoJobMonitor`
4. Elegí un username (debe terminar en "bot"): `nacho_job_monitor_bot`
5. BotFather te responde con un **token** así:
   ```
   1234567890:ABCDefGhIjKlMnOpQrStUvWxYz-abcdefghi
   ```
6. Copiá ese token — lo necesitás en el próximo paso

### Paso 6 — Configurar el archivo .env

```bash
# Copiá el template
cp .env.example .env

# Abrilo con cualquier editor y completá TELEGRAM_TOKEN
```

Ejemplo de `.env` mínimo funcional:
```
TELEGRAM_TOKEN=1234567890:ABCDefGhIjKlMnOpQrStUvWxYz-abcdefghi
CHECK_INTERVAL_HOURS=2
```

### Paso 7 — Ejecutar el bot

```bash
python bot.py
```

Deberías ver algo así:
```
2024-01-15 10:30:00 | INFO     | __main__ | 🚀 Iniciando Job Monitor Bot para Buenos Aires...
2024-01-15 10:30:00 | INFO     | __main__ | 📡 Fuentes activas: indeed_ar, computrabajo, bumeran, tecnoempleo, custom_rss
2024-01-15 10:30:01 | INFO     | __main__ | ✅ Bot listo. Scheduler configurado cada 2h (primer chequeo en 5 min).
2024-01-15 10:30:01 | INFO     | __main__ | 📡 Esperando mensajes... Presioná Ctrl+C para detener.
```

Abrí Telegram, buscá tu bot por su username y enviá `/start`. ✅

---

## 🔑 APIs opcionales

### SerpAPI — Google Jobs (100 req gratis/mes)

1. Registrate en [serpapi.com](https://serpapi.com)
2. Copiá tu API key del dashboard
3. Agregala al `.env`:
   ```
   SERPAPI_KEY=tu_key_acá
   ```

### Twitter/X (⚠️ requiere plan pago)

El plan **Free** de Twitter **no permite buscar tweets** desde 2023.
Necesitás el plan **Basic** ($100/mes) para usar esta fuente.
Si no lo tenés, dejá `TWITTER_BEARER_TOKEN` vacío → se saltea sin errores.

---

## 📋 Comandos del bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicializar el bot y ver bienvenida |
| `/preferencias` | Configurar keywords y ubicación de búsqueda |
| `/cargar_cv` | Subir tu CV en PDF o TXT |
| `/buscar` | Búsqueda manual inmediata en todas las fuentes |
| `/activar_alertas` | Activar monitoreo automático cada 2 horas |
| `/desactivar_alertas` | Pausar el monitoreo automático |
| `/estado` | Ver toda tu configuración actual |
| `/agregar_feed [URL] [Nombre]` | Agregar un RSS feed personalizado |
| `/mis_feeds` | Ver todos tus feeds agregados |
| `/eliminar_feed [ID]` | Eliminar un feed personalizado |
| `/ayuda` | Ver todos los comandos |

---

## 🌐 Fuentes de empleo

| Fuente | Tipo | Requiere key | Foco |
|--------|------|-------------|------|
| Indeed AR | RSS oficial | No | Buenos Aires |
| Computrabajo | Scraping | No | Buenos Aires |
| Bumeran | Scraping | No | Buenos Aires |
| Tecnoempleo | RSS oficial | No | España + remoto |
| Google Jobs | API (SerpAPI) | Sí (gratis 100/mes) | Global |
| Twitter/X | API v2 | Sí (Basic $100/mes) | Global |
| Custom RSS | RSS | No | Lo que vos definas |

### Feeds RSS útiles para agregar manualmente

```
# Mercado Libre (buscar su página de careers para RSS)
/agregar_feed https://careers.mercadolibre.com/rss MercadoLibre

# Globant
/agregar_feed https://www.globant.com/es/jobs/rss Globant

# GetManfred (portal hispanoparlante)
/agregar_feed https://www.getmanfred.com/es/rss ManFred

# LinkedIn: no tiene RSS público.
# Alternativa: guardá una búsqueda en LinkedIn y copiá su URL de alerta como RSS si te lo ofrece.
```

---

## 🔄 Dejar el bot corriendo 24/7 en tu PC

### Windows — usando pythonw (sin ventana de terminal)

Creá un archivo `run_bot.bat`:
```batch
@echo off
cd /d "C:\ruta\a\tu\job_bot"
call venv\Scripts\activate
python bot.py
```

Para que corra al iniciar Windows, agregá este `.bat` al Startup folder:
`Win+R` → `shell:startup` → pegá ahí un acceso directo al `.bat`

### Windows — usando el Administrador de Tareas

1. Abrí "Programador de tareas"
2. Crear tarea básica
3. Desencadenador: "Al iniciar sesión"
4. Acción: ejecutar `python.exe` con argumento `bot.py` en tu directorio

### Mac/Linux — usando nohup

```bash
nohup python bot.py > bot.log 2>&1 &
echo $! > bot.pid    # guarda el PID para poder matarlo después

# Para detenerlo:
kill $(cat bot.pid)
```

### Linux — usando screen (recomendado)

```bash
# Instalar screen si no lo tenés
sudo apt install screen

# Crear sesión
screen -S jobbot

# Dentro de la sesión:
python bot.py

# Salir sin matar el proceso: Ctrl+A, luego D
# Volver a la sesión: screen -r jobbot
```

---

## 🔧 Configuración avanzada de keywords

### Keywords recomendadas para tu perfil (Nacho)

```
Python junior, Python trainee, backend Python, Django junior, 
FastAPI junior, SQL developer junior, PostgreSQL junior, Supabase, 
desarrollador junior Buenos Aires, pasantía IT, pasantia programacion, 
fullstack junior, Web3 developer, Solidity junior, blockchain developer junior,
junior developer remoto Argentina
```

Usá `/preferencias` para configurarlas.

### Tips para mejores resultados

- **Sé específico**: `Python junior Buenos Aires` > `programador`
- **Variantes en español e inglés**: `pasantía IT` y `IT internship`
- **Evitá muy genérico**: `developer` trae demasiado ruido
- **Máximo 10-15 keywords** para no ralentizar las búsquedas

---

## 🐛 Troubleshooting

### El bot no responde
- Verificá que `TELEGRAM_TOKEN` está correcto en `.env`
- Revisá `bot.log` para errores
- Asegurate de haber enviado `/start` al bot primero

### "No hay nada nuevo" cuando debería haber
- Las keywords quizás son muy específicas → probá más genéricas con `/preferencias`
- Los sitios pueden haber cambiado su HTML → revisá `bot.log` para ver si hay errores de scraping
- Usá `/buscar` para forzar una búsqueda manual y ver los logs en tiempo real

### Error de importación al arrancar
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Computrabajo / Bumeran no devuelven resultados
Estos sitios pueden actualizar su HTML y romper el scraper. Revisá los logs:
```bash
tail -f bot.log | grep -E "Computrabajo|Bumeran"
```
Si el scraper falla, el bot sigue funcionando con las otras fuentes.

### El scheduler no está corriendo
- El JobQueue necesita que el bot esté corriendo continuamente
- En Windows, asegurate de que la terminal/proceso no se cierra
- Verificá con `/estado` → muestra el "Último chequeo"

---

## 📊 Arquitectura del sistema

```
bot.py (entry point)
  │
  ├── Application (python-telegram-bot)
  │     ├── CommandHandlers (/start, /buscar, etc.)
  │     ├── ConversationHandler (/preferencias)
  │     └── JobQueue (scheduler automático cada 2h)
  │           └── scheduled_job_check() → scheduler.py
  │
  ├── scheduler.py
  │     └── check_jobs_for_user()
  │           ├── job_scraper.py (busca en todas las fuentes)
  │           ├── database.py (filtra duplicados)
  │           └── bot.send_message() (notifica)
  │
  ├── job_scraper.py
  │     ├── search_indeed_ar()     → feedparser (RSS)
  │     ├── search_computrabajo()  → requests + BeautifulSoup
  │     ├── search_bumeran()       → requests + BeautifulSoup
  │     ├── search_google_jobs()   → SerpAPI REST
  │     ├── search_twitter()       → Twitter API v2
  │     ├── search_tecnoempleo()   → feedparser (RSS)
  │     └── search_custom_rss()    → feedparser (RSS)
  │
  └── database.py (SQLite)
        ├── users
        ├── keywords
        ├── jobs_seen (deduplicación)
        └── custom_feeds
```

---

## 📝 Notas sobre LinkedIn

LinkedIn **no tiene un RSS público** para ofertas de trabajo. Opciones:
1. **Manualmente**: Hacé una búsqueda en LinkedIn Jobs → guardala como alerta → si LinkedIn te ofrece la opción de RSS, copiá esa URL y usala con `/agregar_feed`
2. **LinkedIn Jobs API**: Requiere aprobación de LinkedIn (proceso lento)
3. **Recomendación**: Usá el bot para las demás fuentes y revisá LinkedIn manualmente 1-2 veces por semana

---

*Creado para Nacho (PISCU) — Estudiante de Lic. en Gestión de TI buscando pasantías en Buenos Aires.*
