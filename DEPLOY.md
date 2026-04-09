# Deploy JobBot

## Stack canonico

- Frontend publico: `frontend/`
- Backend API: `api/`
- Bot de Telegram: `job_bot/`

Importante:

- La landing canónica para salir a mercado es `frontend/src/app/page.tsx`.
- `job_bot/landing/index.html` queda solo como landing legacy de respaldo.
- Si hoy tenes Vercel apuntando al `index.html` viejo, no hagas un redeploy ciego sobre ese proyecto. Crea o migra un proyecto nuevo con root en `jobbot/frontend`.

## Requisitos

- Python 3.11+
- Node.js 18+
- SQLite para MVP o PostgreSQL para produccion
- Cuenta/configuracion de Stripe y MercadoPago
- HTTPS terminado delante de FastAPI y Next.js

## Variables de entorno

Completa `.env` usando [.env.example](C:/Users/nacho/Downloads/jobobt/jobbot/.env.example).

Obligatorias para produccion:

- `APP_ENV=production`
- `JWT_SECRET_KEY`
- `TELEGRAM_TOKEN`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `MP_ACCESS_TOKEN`
- `MP_WEBHOOK_SECRET`
- `STRIPE_STARTER_PRICE_ID`
- `STRIPE_PRO_PRICE_ID`
- `STRIPE_PREMIUM_PRICE_ID`
- `MP_STARTER_PRICE_ID`
- `MP_PRO_PRICE_ID`
- `MP_PREMIUM_PRICE_ID`
- `LANDING_URL`

## Backend

```bash
cd jobbot
python -m venv .venv
. .venv/bin/activate
pip install -r requirements_api.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Frontend

```bash
cd jobbot/frontend
npm install
npm run build
npm run start
```

En Vercel:

1. Crear proyecto nuevo.
2. Setear `Root Directory` en `jobbot/frontend`.
3. Agregar variables `NEXT_PUBLIC_API_BASE_URL` y las que use el frontend.
4. Verificar que el dominio principal apunte a este proyecto, no al HTML legacy.

## Webhooks

### Stripe

- Endpoint: `https://YOUR_API_DOMAIN/subscriptions/webhook/stripe`
- Evento minimo: `checkout.session.completed`
- Firma: usar `STRIPE_WEBHOOK_SECRET`

### MercadoPago

- Endpoint: `https://YOUR_API_DOMAIN/subscriptions/webhook/mercadopago`
- Configurar `MP_WEBHOOK_SECRET`
- Opcional pero recomendado: definir `MP_WEBHOOK_IPS`

### Coinbase Commerce

- Endpoint: `https://YOUR_API_DOMAIN/subscriptions/webhook/crypto`
- Configurar `COINBASE_WEBHOOK_SECRET`

## Sanity checks post deploy

1. `GET /health` devuelve `status=ok` o `degraded` con detalle.
2. `GET /stats` responde sin exponer datos de usuario.
3. Login web responde con token real.
4. Dashboard carga con Bearer token.
5. Checkout genera URL real de proveedor.
6. Webhook de prueba actualiza plan en DB.

## SSL, backup y rollback

- Sirve frontend y backend solo por HTTPS.
- Backups de SQLite/PostgreSQL al menos diarios.
- Mantener la release previa para rollback rapido.
- Si falla deploy:
  - restaurar `.env` previo
  - volver a la imagen/build anterior
  - correr `scripts/sanity-check.sh`

## Troubleshooting

- `401 en dashboard`: revisar `JWT_SECRET_KEY` y expiracion del token.
- `503 en IA`: revisar `GROQ_API_KEY`.
- `checkout falla`: revisar `STRIPE_SECRET_KEY` o `MP_ACCESS_TOKEN`.
- `plan no sube`: revisar logs del webhook y secreto correspondiente.
- `Vercel sigue mostrando la landing vieja`: revisar el `Root Directory` del proyecto y que el dominio este conectado al deploy de `jobbot/frontend`.
