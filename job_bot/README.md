# 🤖 Job Monitor Bot — Buenos Aires IT

Bot de Telegram para monitorear ofertas laborales de Python/Backend/Junior en Buenos Aires con integración de **IA (Groq/Llama 3)** para analizar tu CV.

Hecho por y para **Nacho (PISCU)** — Gestión de TI.

---

## 📁 Estructura de archivos

```
job_bot/
├── bot.py            ← Punto de entrada. Ejecutá esto.
├── config.py         ← Variables de entorno y settings globales
├── database.py       ← Capa de base de datos (SQLite)
├── job_scraper.py    ← Scrapers de todas las fuentes de empleo
├── scheduler.py      ← Lógica del monitoreo automático + perfilado
├── cv_analyzer.py    ← Inteligencia Artificial (Groq) para analizar CVs
├── stats_api.py      ← API para enviar estadísticas a la landing page
├── requirements.txt  ← Dependencias
├── .env.example      ← Template de configuración
├── tests/            ← Unit tests para asegurar que todo funcione
└── cvs/              ← Carpeta de CVs subidos (local)
```

---

## ⚡ Instalación paso a paso

### Paso 1 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 2 — Configurar el archivo .env

```bash
cp .env.example .env
# Completá TELEGRAM_TOKEN y GROQ_API_KEY
```

### Paso 3 — Ejecutar el bot

```bash
python bot.py
```

---

## 📋 Comandos del bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Bienvenida e inicialización |
| `/preferencias` | **Wizard de configuración**: perfil, nivel, techs, **modalidad** y zona |
| `/horarios` | Configurar frecuencia de alertas y franja horaria (ej: 09:00 a 20:00) |
| `/cargar_cv` | Subir tu CV (PDF/TXT) para que la IA lo analice |
| `/analizar_cv` | La IA (Llama 3) analiza tu perfil y te da sugerencias de mejora |
| `/analizar_oferta [URL]`| Compara tu CV contra una oferta específica y te da un puntaje de "match" |
| `/buscar` | Búsqueda manual inmediata |
| `/activar_alertas` | Activar el monitoreo automático inteligente |
| `/desactivar_alertas`| Pausar el monitoreo |
| `/estado` | Ver tu perfil completo y configuración actual |
| `/borrar_datos` | Eliminar TODA tu info (GDPR Compliance) |
| `/web` | Abrir la landing page del proyecto |

---

## 🌐 Fuentes de empleo inteligentes

El bot busca automáticamente en:
- **LinkedIn AR** (vía Google News RSS local) ✅
- **Remotive** (API de trabajos remotos) ✅
- **Arbeitnow** (API global tech) ✅
- **Jobicy** (Startup & remote tech jobs) ✅
- **Himalayas** (Remote jobs for startups & tech) ✅
- **Google Jobs** (vía SerpAPI - opcional) 🔑
- **Twitter/X** (vía API v2 - opcional) 🔑
- **Custom RSS** (feeds que vos mismo agregues) ✅

---

## 🏠 Filtro por Modalidad (Nuevo Hito 4)

Ahora podés elegir qué tipo de trabajo buscás en el wizard de `/preferencias`:
- 🌐 **Remoto**: Solo ofertas 100% remote.
- 🏢 **Híbrido**: Combina oficina y casa.
- 📍 **Presencial**: Trabajo tradicional en oficina.
- ♾️ **Cualquiera**: No filtra por modalidad.

---

## 🧠 IA & Análisis de CV (Nuevo Hito 3)

Integración con **Groq API (Llama 3.3 70B)** permitiendo:
1. **Match Scoring**: Cada oferta que te llega tiene un puntaje (🟢, 🟡, 🟠, 🔴) comparándola con tu CV.
2. **Keywords sugeridas**: Te dice qué palabras clave te faltan para aplicar a esa oferta.
3. **Análisis de perfil**: Te ayuda a redactar mejor tu experiencia.

---

## 🔧 Configuración para Nacho (Admin)

Para que el bot corra solo:
- **Windows**: Usar `python bot.py` en una ventana de terminal o configurar una Tarea Programada.
- **Producción**: El bot está diseñado para ser escalable y manejar múltiples usuarios con sus propios horarios y perfiles.

---

*Creado para Nacho (PISCU) — Optimizando la búsqueda laboral con tecnología y IA.*
