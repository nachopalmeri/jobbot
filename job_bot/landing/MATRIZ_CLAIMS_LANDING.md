# Matriz de Claims - Landing Legacy JobBot AR

> Fuente de verdad: `api/routes/subscriptions.py`, `api/routes/credits.py`, `dashboard/src/app/(dashboard)/suscripcion/page.tsx`

## Claims de Pricing

| Claim | Fuente de verdad | Status | Ubicación landing |
|-------|-------------------|--------|-------------------|
| Free: $0/mes | API `subscriptions.py` L33 | ✅ Real | L5400 |
| Starter: $4/mes o $40/año | API L34-35 | ✅ Real | L5417-5422 |
| Pro: $8/mes o $80/año | API L43-44 | ✅ Real | L5438-5443 |
| Premium: $12/mes o $120/año | API L51-53 | ✅ Real | L5460-5464 |
| CV Suite Unlock: $9 + 50 créditos | API `credits.py` L25-31 | ✅ Real | Nueva sección |
| 25 créditos: $7 | API L33-40 | ✅ Real | Nueva sección |
| 60 créditos: $15 | API L41-49 | ✅ Real | Nueva sección |
| 150 créditos: $29 | API L50-57 | ✅ Real | Nueva sección |
| 1 crédito = 1 análisis IA o 1 cover letter | API L91 | ✅ Real | Nueva sección |
| Créditos nunca expiran | API L91 | ✅ Real | Nueva sección |

## Claims de Features por Plan

| Claim | Fuente de verdad | Status | Ubicación landing |
|-------|-------------------|--------|-------------------|
| Free: 3 búsquedas/día | Dashboard L56 | ✅ Real | L5407 |
| Free: Hasta 3 resultados | Dashboard L57 | ✅ Real | L5408 |
| Starter: 12 búsquedas/día | Dashboard L66 | ✅ Real | L5425 |
| Starter: Pipeline de postulaciones | Dashboard L68 | ✅ Real | L5427 |
| Starter: Alertas Telegram | Dashboard L69 | ✅ Real | L5428 |
| Pro: 40 búsquedas/día | Dashboard L76 | ✅ Real | L5446 |
| Pro: 4 análisis IA/mes | Dashboard L77 | ✅ Real | L5447 |
| Pro: Match score + keywords | Dashboard L78 | ✅ Real | L5448 |
| Premium: 20 análisis IA/mes | Dashboard L88 | ✅ Real | L5468 |
| Premium: 10 mock interviews/mes | Dashboard L88 | ✅ Real | L5469 |
| Premium: Cover letters | Dashboard L89 | ✅ Real | L5470 |
| Premium: 120 búsquedas/día | Dashboard L91 | ✅ Real | L5472 |

## Claims Numéricos / Operativos

| Claim | Fuente de verdad | Status | Ubicación landing |
|-------|-------------------|--------|-------------------|
| "6+ fuentes activas" | MATRIZ_CLAIMS.md principal | ✅ Real | L5146, L5552 |
| "Beta - Controlled launch" | Status real del producto | ✅ Real | L5141 |
| "24/7 búsqueda continua" | Funcionamiento del bot | ⚠️ Ilustrativo (el bot no escanea literalmente 24/7) | L5136, L5548 |
| "15+ portales" | ❌ NO VERIFICADO (real: 6+) | 🚫 Corregido a "múltiples fuentes" | L5539 |
| "42 empleos esta semana" | ❌ Dato ficticio demo | 🚫 Corregido a "varios empleos" | L6108 |
| "Top 10% de usuarios" | ❌ No instrumentado | 🚫 Eliminado | L6108 |
| "1,200+ usuarios" | ❌ No instrumentado | 🚫 No encontrado en landing actual |
| "247 empleos esta semana" | ❌ No instrumentado | 🚫 No encontrado en landing actual |
| "30-50 empleos/semana" | ❌ No instrumentado | 🚫 No encontrado en landing actual |
| "10x más empleos" | ❌ No instrumentado | 🚫 No encontrado en landing actual |

## Claims del Chatbot Embebido

| Claim | Status | Notas |
|-------|--------|-------|
| "Starter: $4/mes o $40/año - 12 búsquedas/día" | ✅ Alineado | L7615 |
| "Pro: $8/mes o $80/año - 40 búsquedas/día, 4 análisis IA" | ✅ Alineado | L7615 |
| "Premium: $12/mes o $120/año - Todo + cover letters, 20 análisis, 10 interviews" | ✅ Alineado | L7615 |

## Metadatos SEO/Social

| Elemento | Valor actual | Status |
|----------|--------------|--------|
| `canonical` | `https://jobbot.ar/` | ✅ Consistente |
| `og:url` | `https://jobbot.ar/` | ✅ Consistente |
| `og:image` | `https://jobbot.ar/og-jobbot-dashboard.png` | ✅ Consistente |
| `twitter:image` | `https://jobbot.ar/og-jobbot-dashboard.png` | ✅ Consistente |

## CTAs y Links

| Link | Destino | Status |
|------|---------|--------|
| Register | `https://app-jobbot.vercel.app/register` | ⚠️ Dominio mezclado (ideal: `app.jobbot.ar`) |
| Dashboard/Suscripcion | `https://app-jobbot.vercel.app/dashboard/suscripcion` | ⚠️ Dominio mezclado |
| Dashboard/Créditos | `https://app-jobbot.vercel.app/dashboard/creditos` | ⚠️ Dominio mezclado |
| FAQ (footer) | `#como-funciona` | ✅ Corregido a "Cómo funciona" |

## Reglas para futuras ediciones

1. **Nunca** cambiar pricing en landing sin actualizar `api/routes/subscriptions.py`
2. **Nunca** agregar features que no estén en `dashboard/src/app/(dashboard)/suscripcion/page.tsx`
3. **Nunca** usar números redondos sin verificar instrumentación real
4. **Siempre** marcar datos demo con badge "Demo ilustrativa"
5. **Siempre** preferir claims cualitativos sobre numéricos no verificables

## Diccionario de términos permitidos

| En vez de... | Usar... |
|--------------|---------|
| "15+ portales" | "múltiples fuentes" o "6+ fuentes activas" |
| "42 empleos" | "varios empleos" (o eliminar número) |
| "1,200+ usuarios" | "Beta - Controlled launch" |
| "10x más" | "más" (sin multiplicador) |
| "247 empleos" | "oportunidades filtradas" (sin número) |
| "30-50 por semana" | "oportunidades relevantes" (sin rango) |

---

**Última actualización:** 2026-04-10  
**Responsable:** Landing legacy maintenance
