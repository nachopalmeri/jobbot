# 🚀 DEPLOY CHECKLIST - JobBot MVP

## ✅ Estado Actual: LISTO PARA PRODUCCIÓN

**Última verificación:** 31/03/2026  
**Tests:** 14 passed ✅  
**Build:** OK ✅  
**Logo:** Integrado ✅  
**Smart Summary UX:** Implementado ✅

---

## 📋 Checklist Pre-Deploy

### 1. Variables de Entorno (.env)

```bash
□ APP_ENV=production
□ JWT_SECRET_KEY=<minimo-32-caracteres-seguros>
□ TELEGRAM_TOKEN=<token-de-botfather>
□ LANDING_URL=https://jobbot.ar
□ DATABASE_TYPE=sqlite (o postgresql para produccion)
□ STRIPE_SECRET_KEY=sk_live_...
□ STRIPE_WEBHOOK_SECRET=whsec_...
□ STRIPE_PRO_PRICE_ID=price_...
□ STRIPE_PREMIUM_PRICE_ID=price_...
□ MP_ACCESS_TOKEN=TEST-...
□ MP_WEBHOOK_SECRET=...
□ RAPIDAPI_KEY=<tu-api-key>
□ GROQ_API_KEY=<opcional-para-IA>
```

### 2. Archivos de Logo (frontend/public/)

```bash
□ jobbot-logo.svg ✓ (creado)
□ icon.svg ✓ (creado)
□ manifest.json ✓ (creado)
□ (Opcional) Reemplazar con tus PNGs siguiendo LOGO_INSTRUCTIONS.md
```

### 3. Base de Datos

```bash
□ SQLite: job_bot.db inicializada
□ Tablas creadas: users, web_users, payments, pending_job_batches, etc.
□ Migración ejecutada sin errores
```

---

## 🚀 Pasos de Deploy

### PASO 1: Backend API (Railway/Render/VPS)

**Opción A: Railway (Recomendado para MVP)**

```bash
# 1. Instalar CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Inicializar proyecto
cd jobbot
railway init

# 4. Configurar variables (una por una o desde archivo)
railway variables set APP_ENV=production
railway variables set JWT_SECRET_KEY=tu-secreto-jwt
# ... (todas las variables del .env)

# 5. Deploy
railway up

# 6. Obtener URL
railway domain
```

**Opción B: Render**

1. Crear cuenta en render.com
2. New Web Service
3. Connect GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements_api.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port 8000`
5. Environment Variables: Copiar todo el .env
6. Deploy

**Opción C: VPS (DigitalOcean, AWS, etc.)**

```bash
# En el servidor
sudo apt update && sudo apt install python3-pip nginx

# Clonar repo
git clone <tu-repo> /var/www/jobbot
cd /var/www/jobbot

# Virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_api.txt

# Crear service systemd
sudo nano /etc/systemd/system/jobbot-api.service
```

**Contenido de /etc/systemd/system/jobbot-api.service:**
```ini
[Unit]
Description=JobBot API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/jobbot
EnvironmentFile=/var/www/jobbot/.env
ExecStart=/var/www/jobbot/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Activar service
sudo systemctl enable jobbot-api
sudo systemctl start jobbot-api
sudo systemctl status jobbot-api
```

### PASO 2: Frontend (Vercel)

```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Ir al frontend
cd jobbot/frontend

# 3. Deploy
vercel --prod

# 4. Configurar en dashboard de Vercel:
#    - Framework: Next.js
#    - Root: frontend/
#    - Build: npm run build
```

**Variables de entorno en Vercel:**
```
NEXT_PUBLIC_API_BASE_URL=https://tu-api.railway.app
```

### PASO 3: Configurar Dominio

```bash
# En Vercel Dashboard:
# Settings → Domains → Add Domain → jobbot.ar

# Configurar DNS en tu registrador:
# CNAME → cname.vercel-dns.com
# o
# A → 76.76.21.21 (IP de Vercel)
```

### PASO 4: Webhooks de Pagos

**Stripe Dashboard:**
1. Developers → Webhooks
2. Add endpoint: `https://tu-api.railway.app/subscriptions/webhook/stripe`
3. Select events: `checkout.session.completed`
4. Copy signing secret → `STRIPE_WEBHOOK_SECRET`

**MercadoPago Dashboard:**
1. Tu aplicación → Webhooks
2. URL: `https://tu-api.railway.app/subscriptions/webhook/mercadopago`
3. Events: `payment`
4. Secret: `MP_WEBHOOK_SECRET`

### PASO 5: Sanity Check

```bash
# Test 1: Health endpoint
curl https://tu-api.railway.app/health
# Expected: {"status":"ok"}

# Test 2: Stats endpoint
curl https://tu-api.railway.app/stats
# Expected: {"jobs_count":..., "active_users":...}

# Test 3: Landing page
curl -I https://jobbot.ar
# Expected: HTTP 200

# Test 4: Telegram Bot
# Enviar /start a @TuBot
# Expected: "¡Hola! Soy JobBot..."
```

---

## 🔧 Configuración Post-Deploy

### 1. Stripe (Productos y Precios)

```bash
# Crear productos:
# 1. Starter - USD 3/mes
# 2. Pro - USD 7/mes  
# 3. Premium - USD 15/mes

# Copiar los Price IDs:
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_PREMIUM_PRICE_ID=price_...
```

### 2. MercadoPago (Productos)

```bash
# Crear plan de suscripción por cada producto
# Copiar External Reference IDs a:
MP_STARTER_PRICE_ID=...
MP_PRO_PRICE_ID=...
MP_PREMIUM_PRICE_ID=...
```

### 3. Telegram BotFather

```
/start
/setdomain
# Elegir tu bot
# Ingresar: https://jobbot.ar
```

### 4. Google Search Console

1. Ir a https://search.google.com/search-console
2. Add property → jobbot.ar
3. Verificar dominio (DNS o HTML)
4. Copiar código de verificación a `layout.tsx`
5. Submit sitemap: `https://jobbot.ar/sitemap.xml`

---

## 📊 Costos Estimados (Mensual)

| Servicio | Tier | Costo |
|----------|------|-------|
| **Vercel** (Frontend) | Hobby | $0 |
| **Railway** (API) | Starter | $5 |
| **RapidAPI** (LinkedIn/Yahoo) | Free | $0 |
| **Stripe** | Transacciones | $0 + 2.9% + 30¢ por pago |
| **MercadoPago** | Transacciones | $0 + fees locales |
| **Dominio** | .com.ar | ~$3-5/año |
| **Total** | | **~$5/mes** |

---

## 🆘 Troubleshooting

### Problema: API no responde
```bash
# Ver logs
railway logs
# o
sudo journalctl -u jobbot-api -f
```

### Problema: Webhooks no funcionan
1. Verificar que la URL es HTTPS
2. Check secret keys en dashboard
3. Ver logs: `grep "webhook" bot.log`

### Problema: Frontend no conecta a API
1. Verificar `NEXT_PUBLIC_API_BASE_URL` en Vercel
2. Check CORS en `api/main.py`
3. Probar directo: `curl $API_URL/health`

### Problema: Bot no responde
1. Verificar `TELEGRAM_TOKEN`
2. Check webhook de Telegram
3. Revisar logs: `tail -f bot.log`

---

## 📞 Checklist Final

```bash
□ Backend API desplegado y responde /health
□ Frontend en Vercel con dominio configurado
□ Webhooks de Stripe configurados
□ Webhooks de MercadoPago configurados
□ Bot de Telegram responde a /start
□ Checkout de pagos funciona en test
□ Logo visible en pestaña del navegador
□ OG Image aparece al compartir en redes
□ Alertas automáticas funcionan
□ Smart Summary UX funciona (/buscar)
□ Fallback de alertas configurado
```

---

## 🎉 Post-Deploy

### Lanzamiento:

1. **Beta cerrada** (1 semana)
   - Invitar 10 usuarios a probar
   - Recoger feedback
   - Fix urgentes

2. **Lanzamiento público**
   - Post en redes sociales
   - Comunidades de IT (Argentina)
   - Email a lista de espera

3. **Monitoreo**
   - Railway dashboard
   - Vercel analytics
   - Stripe dashboard
   - Bot logs

---

## 📚 Documentación Adicional

- `DEPLOY.md` - Guía completa de deploy
- `LAUNCH_CHECKLIST_AR.md` - Checklist específico Argentina
- `SMART_SUMMARY_UX.md` - Documentación de la UX nueva
- `LOGO_INSTRUCTIONS.md` - Cómo reemplazar el logo
- `frontend/public/manifest.json` - Config PWA

---

**🚀 ¿Estás listo? Empezá con el PASO 1 y seguí el checklist.**

**Tiempo estimado:** 30-45 minutos  
**Complejidad:** Media (con guía paso a paso)  
**Soporte:** Revisar logs en cada paso

¡Éxitos con el deploy! 🎯
