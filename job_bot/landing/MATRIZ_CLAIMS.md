# Matriz de Claims - Landing Legacy HTML

> **Fecha de corrección:** 2026-04-09  
> **Estado:** Alineado con fuente de verdad API/dashboard/bot  
> **Fuente de verdad:** `api/routes/subscriptions.py`, `dashboard/src/app/(dashboard)/suscripcion/page.tsx`, `job_bot/bot.py`

---

## Claims Corregidos ✅

| Claim Anterior | Claim Corregido | Ubicación | Estado | Notas |
|----------------|-----------------|-----------|--------|-------|
| 1,200+ usuarios activos | **Beta** - Controlled launch | Hero stats | ✅ Real | Honestidad sobre estado actual |
| 247 empleos esta semana | **24/7** búsqueda continua | Hero stats | ✅ Ilustrativo | Cambiado a cualitativo |
| 15 portales monitoreados | **6+** fuentes activas | Hero stats | ✅ Real | LinkedIn, Remotive, Arbeitnow, Jobicy, Himalayas, RSS |
| 30-50 empleos/semana | Alertas personalizadas según perfil | Numbers game | ✅ Real | Sin承诺 específico de volumen |
| 1,200+ búsquedas reales | Búsquedas reales analizadas por IA | Tips section | ✅ Cualitativo | Removido número no verificable |
| 10x más empleos | Más oportunidades relevantes, menos ruido | Chatbot | ✅ Real | Quitado multiplicador sin base |

---

## Pricing Alineado ✅

| Plan | Landing | API | Dashboard | Bot | Estado |
|------|---------|-----|-----------|-----|--------|
| Free | ✅ $0/mes | ✅ $0 | ✅ $0 | ✅ $0 | Consistente |
| Starter | ✅ **$4/mes** o $40/año | ✅ $4 | ✅ $4 | ✅ $4 | **Agregado** |
| Pro | ✅ $8/mes o $80/año | ✅ $8 | ✅ $8 | ✅ $8 | Consistente |
| Premium | ✅ $12/mes o $120/año | ✅ $12 | ✅ $12 | ✅ $12 | Consistente |
| Créditos | ✅ $9 unlock + packs | ✅ Implementado | ✅ UI lista | ✅ /creditos | Consistente |

---

## Features Alineadas ✅

### Free (0$/mes)
- ✅ 3 búsquedas guiadas/día
- ✅ Hasta 3 resultados visibles
- ✅ Dashboard liviano
- ✅ Score ATS inicial de CV
- ❌ Match avanzado (requiere Starter+)
- ❌ Pipeline (requiere Starter+)
- ❌ Mock interviews (requiere Premium)

### Starter ($4/mes) - **NUEVO**
- ✅ 12 búsquedas por día
- ✅ Resultados completos
- ✅ Pipeline de postulaciones
- ✅ Alertas automáticas por Telegram
- ✅ CV score y quick wins
- ❌ Análisis IA (requiere Pro+)
- ❌ Match score avanzado (requiere Pro+)
- ❌ Cover letters (requiere Premium)

### Pro ($8/mes)
- ✅ 40 búsquedas por día
- ✅ 4 análisis IA de CV por mes
- ✅ Match score + keywords faltantes
- ✅ Alertas automáticas por Telegram
- ✅ Pipeline completo
- ❌ Cover letters premium (requiere Premium)
- ❌ Mock interviews (requiere Premium)

### Premium ($12/mes)
- ✅ Todo lo de Pro
- ✅ 20 análisis IA de CV por mes
- ✅ 10 mock interviews por mes
- ✅ Cover letters personalizadas
- ✅ 120 búsquedas por día
- ✅ Historial completo y workflow de CV

---

## Dominios Canonical ✅

| Elemento | Anterior | Corregido | Estado |
|----------|----------|-----------|--------|
| Canonical | jobbot.ar | ✅ jobbot.ar | Consistente |
| OG URL | jobbotlandingclean.vercel.app | ✅ app-jobbot.vercel.app | Unificado |
| OG Image | jobbotlandingclean.vercel.app | ✅ app-jobbot.vercel.app | Unificado |
| Twitter Image | jobbotlandingclean.vercel.app | ✅ app-jobbot.vercel.app | Unificado |
| CTAs Register | app-jobbot.vercel.app | ✅ app-jobbot.vercel.app | Consistente |
| CTAs Suscripción | app-jobbot.vercel.app | ✅ app-jobbot.vercel.app | Consistente |

---

## Chatbot Responses Actualizadas ✅

| Pregunta | Response Anterior | Response Corregido |
|----------|-------------------|-------------------|
| precio/plan/pro | Solo Pro $8 | ✅ Starter $4, Pro $8, Premium $12 + créditos |
| match/funciona | "10x más empleos" | ✅ "Más oportunidades relevantes, menos ruido" |
| General | "30-50 puestos/semana" | ✅ "Alertas automáticas sobre oportunidades que matchean" |

---

## Claims Ilustrativos (Demo) Marcados

Elementos visuales que representan funcionalidad pero NO son datos reales:
- Dashboard mock en hero visual: Labels "MN" usuario, "Frontend Developer" - **Ilustrativo**
- Stats "24 Nuevos empleos", "8 Postulados", "3 Entrevistas" - **Demo visual**
- Job cards con "92% match", "TechFlow", "$2,400 USD" - **Ejemplos ilustrativos**
- Sección "Así se ve JobBot Pro" - **Demo interactiva, no datos reales**

---

## Notas de Mantenimiento

1. **NO editar pricing** sin actualizar primero:
   - `api/routes/subscriptions.py` (PLANS dict)
   - `dashboard/src/app/(dashboard)/suscripcion/page.tsx` (planOverrides)
   - `job_bot/bot.py` (/precios command)

2. **NO agregar claims numéricos** sin:
   - Instrumentación PostHog/Amplitude
   - Base de datos real con queries
   - Nota de "datos reales de [fecha]"

3. **NO cambiar features por plan** sin verificar:
   - Límites técnicos en `api/core/limits.py` o `config.py`
   - Gating en dashboard (`page.tsx` con plan checks)
   - Comandos bot con `@require_plan` o similares

4. **Dominios:** Mantener `app-jobbot.vercel.app` como único en OG/CTAs hasta migración definitiva a dominio propio.

---

## Validación Checklist

- [x] Pricing parity: landing = API = dashboard = bot
- [x] Feature parity: límites por plan consistentes
- [x] Claims numéricos removidos o verificables
- [x] Dominios OG/CTAs unificados
- [x] Plan Starter agregado
- [x] Chatbot responses actualizadas
- [x] Matriz de claims documentada

**Estado:** ✅ Landing legacy corregida y alineada con fuente de verdad (2026-04-09)
