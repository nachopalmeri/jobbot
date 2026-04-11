# Smart Summary UX - Implementation Summary

## Resumen de Cambios

Se implementó el **Smart Summary UX**, un nuevo flujo de notificaciones que mejora drásticamente la experiencia del usuario y optimiza el consumo de recursos.

---

## 🎯 Características Principales

### 1. Flujo Resumen → Confirmación → Detalle

**Antes:**
- Bot enviaba hasta 15 mensajes seguidos (1 por oferta)
- Usuario se sentía saturado de información

**Ahora:**
```
[Paso 1] Usuario: /buscar
         ↓
[Paso 2] Bot: "🎯 Encontramos 12 propuestas
              
              📊 Análisis:
              🟢 3 Super match (80%+)
              🟡 5 Buen match (60-80%)
              ⚪ 4 Match regular
              
              [📋 Ver todas las ofertas] ← Botón
              
              ⏳ Disponible 30 min"
         ↓
[Paso 3] [Usuario toca botón]
         ↓
[Paso 4] Bot: Muestra ofertas una por una
            (cada una con botón [🏢 Empresa])
```

### 2. Botón "Saber más de la empresa"

En cada oferta, ahora hay un botón inline que permite al usuario ver:
- Datos de LinkedIn (nombre, industria, tamaño)
- Datos financieros de Yahoo Finance (precio, market cap, rendimiento)
- Todo en formato UX premium con secciones visuales

### 3. Fallback Inteligente para Alertas

**Para alertas automáticas:**
- Se envía resumen con botón
- Si el usuario no responde en 35 minutos, se envían las ofertas directo
- El usuario nunca pierde una alerta importante

---

## 📊 Configuración por Plan

```python
MAX_JOBS_PER_BATCH = {
    "free": 5,
    "starter": 8,
    "pro": 15,
    "premium": 20
}
```

**TTL (Time To Live):**
- Batch disponible: 30 minutos
- Fallback para alertas: 35 minutos
- Limpieza de batches antiguos: 24 horas

---

## 🗄️ Nuevas Tablas en Base de Datos

### 1. `pending_job_batches`
```sql
CREATE TABLE pending_job_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    jobs_json TEXT NOT NULL,           -- JSON array de jobs
    total_count INTEGER DEFAULT 0,
    high_match_count INTEGER DEFAULT 0,    -- >80%
    medium_match_count INTEGER DEFAULT 0,  -- 60-80%
    regular_match_count INTEGER DEFAULT 0, -- <60%
    source TEXT DEFAULT 'manual',          -- 'manual' o 'alert'
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    viewed INTEGER DEFAULT 0,            -- 0=pending, 1=viewed, 2=expired
    fallback_sent INTEGER DEFAULT 0
);
```

### 2. `batch_interactions` (analytics)
```sql
CREATE TABLE batch_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'viewed', 'expired', 'fallback_sent', 'dismissed'
    timestamp INTEGER NOT NULL
);
```

---

## 📁 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `job_bot/scheduler.py` | +316 líneas: Smart Summary functions, batch management, fallback logic |
| `job_bot/bot.py` | +85 líneas: Callback handlers para botones inline |
| `job_bot/database.py` | +200 líneas: Métodos CRUD para batches |
| `job_bot/config.py` | Nuevas constantes de configuración |

---

## 🚀 Flujo Técnico

### Búsqueda Manual (/buscar)

```python
1. check_jobs_for_user() encuentra N jobs
2. create_and_send_batch_summary():
   a. Crea batch en DB con TTL 30 min
   b. Calcula conteos por match score
   c. Envía mensaje resumen con botón inline
3. Usuario toca botón → handle_view_jobs_callback()
4. send_jobs_from_batch():
   a. Marca batch como 'viewed'
   b. Envía jobs uno por uno con botón de empresa
   c. Respeta límite según plan del usuario
```

### Alerta Automática (Scheduler)

```python
1. scheduled_job_check() procesa usuarios activos
2. Para cada usuario con jobs nuevos:
   a. Crea batch con source='alert'
   b. Envía resumen con botón
3. Al finalizar:
   a. process_expired_alert_batches():
      - Busca alertas expiradas (>35 min)
      - Envía fallback directo
   b. expire_old_batches():
      - Limpia batches >24h
```

### Botón "Saber más de la empresa"

```python
1. Usuario toca botón en oferta
2. handle_company_info_callback():
   a. Extrae dominio del callback_data
   b. Llama get_company_by_domain() (LinkedIn Data API)
   c. Llama get_stock_data() (Yahoo Finance API)
   d. Formatea mensaje combinado
3. Envía ficha completa de empresa
```

---

## 💰 Optimización de Costos

| API | Límite | Uso con Smart Summary |
|-----|--------|----------------------|
| **Yahoo Finance** | 500 req/mes | Solo cuando tocan botón "Empresa" |
| **LinkedIn Data** | 500 req/mes | Cache 7 días, solo dominios nuevos |
| **JSearch** | Variable | Solo búsquedas manuales |

**Resultado:**
- Antes: 15 llamadas por usuario/búsqueda (envío directo)
- Ahora: 1 llamada por empresa que realmente interesa
- Ahorro estimado: **~80-90%** en consumo de APIs

---

## ✅ Testing

```bash
python -m pytest job_bot/tests/ -q
```

**Resultado:** `14 passed` ✅

---

## 📱 Ejemplo de UX

### Mensaje Resumen (Smart Summary)
```
🎯 Encontramos 12 propuestas para vos

📊 Análisis por match:
🟢 3 Super match (80%+)
🟡 5 Buen match (60-80%)
⚪ 4 Match regular

💼 Filtros aplicados:
📍 Buenos Aires
👤 Junior
💻 Python, React

[📋 Ver todas las ofertas]

⏳ Disponible 30 min
```

### Mensaje de Oferta (con botón)
```
<b>1/12</b> 💼 <b>Senior Python Developer</b>
🏢 Google
📍 Buenos Aires (Remoto)
🌐 Fuente: LinkedIn

📝 Desarrollo backend con Python y microservicios...

🔗 Ver oferta completa

[🏢 Saber más de la empresa]
```

### Ficha de Empresa (al tocar botón)
```
🏢 Google Inc.
🌐 google.com

📊 FINANCIERO ─────────────────────────
📈 GOOGL (NASDAQ)
💰 $1,847.50
🟢 +2.3% hoy
📈 +8.7% semana
💹 Volumen: 452K

💼 EMPRESA ──────────────────────────
👥 10,000+
📍 Mountain View, CA
✨ Search, Cloud, AI, Ads

🔗 Sitio web • 💼 LinkedIn • 📈 Yahoo Finance
```

---

## 🔧 Configuración en .env

```bash
# Smart Summary UX
JOB_BATCH_TTL_MINUTES=30
JOB_BATCH_FALLBACK_MINUTES=35
MAX_JOBS_FREE=5
MAX_JOBS_STARTER=8
MAX_JOBS_PRO=15
MAX_JOBS_PREMIUM=20
SEARCH_COOLDOWN_MINUTES=5

# APIs (ya existentes)
RAPIDAPI_KEY=tu_api_key
RAPIDAPI_LINKEDIN_DATA_HOST=linkedin-data-api.p.rapidapi.com
```

---

## 📊 Métricas Analytics

La tabla `batch_interactions` permite trackear:
- Cuántos usuarios tocan "Ver ofertas" vs dejan expirar
- Tiempo promedio de respuesta
- Cuántos usan el botón "Saber más de empresa"
- Tasa de conversión de alertas (fallback vs interacción)

---

## 🎯 Estado: Listo para Producción

✅ Código implementado y testeado (14 tests passed)
✅ Base de datos migrada con nuevas tablas
✅ UX premium con secciones visuales
✅ Fallback inteligente para alertas
✅ Optimización de costos (80-90% ahorro APIs)
✅ Límites por plan configurables

**El sistema está listo para deploy.**
