# Launch Checklist Argentina

## 1. Definir el stack publico

- Vercel: `jobbot/frontend`
- Railway, Render o VPS para FastAPI: `jobbot/api`
- Railway o VPS para el bot: `jobbot/job_bot`
- Base de datos recomendada para produccion: PostgreSQL

## 2. Orden correcto de migracion

1. Dejar Vercel actual quieto si hoy sirve la landing legacy.
2. Crear un proyecto nuevo de Vercel con root en `jobbot/frontend`.
3. Validar ese deploy en URL preview.
4. Recién cuando todo este bien, mover el dominio principal al nuevo proyecto.

## 3. Variables minimas

- `APP_ENV=production`
- `JWT_SECRET_KEY`
- `NEXT_PUBLIC_API_BASE_URL`
- `TELEGRAM_TOKEN`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_STARTER_PRICE_ID`
- `STRIPE_PRO_PRICE_ID`
- `STRIPE_PREMIUM_PRICE_ID`
- `MP_ACCESS_TOKEN`
- `MP_WEBHOOK_SECRET`
- `MP_STARTER_PRICE_ID`
- `MP_PRO_PRICE_ID`
- `MP_PREMIUM_PRICE_ID`
- `LANDING_URL`
- `GROQ_API_KEY` si queres IA real

## 4. Pricing recomendado para Argentina

- `Free`: prueba real sin pagar
- `Starter`: USD 3
- `Pro`: USD 5
- `Premium`: USD 15

Lectura comercial:

- `Starter` sirve para destrabar compra impulsiva en Argentina y LATAM.
- `Pro` es el plan con mejor relacion precio-valor para un usuario activo.
- `Premium` queda para usuarios con urgencia, mejor poder adquisitivo o uso intensivo de IA.

## 5. Qué tiene que cumplir cada plan

- `Free`: busquedas limitadas, dashboard basico, sin IA paga
- `Starter`: mas busquedas, alertas y pipeline operativo
- `Pro`: filtros avanzados y analisis de CV con IA
- `Premium`: mayor cuota de IA, tailoring y mock interviews

No prometas calendario como feature actual. Hoy debe mostrarse como `Coming Soon`.

## 6. Configuracion de pagos

Stripe o MercadoPago:

1. Crear producto `Starter` con precio `USD 3`.
2. Crear producto `Pro` con precio `USD 5`.
3. Crear producto `Premium` con precio `USD 15`.
4. Copiar los price IDs al `.env`.
5. Configurar webhooks hacia el backend real.
6. Probar un pago de punta a punta en modo test antes de publicar.

## 7. Pruebas antes de abrir el dominio

Desde `jobbot/`:

```bash
python -m pytest
```

Desde `jobbot/dashboard/`:

```bash
npm run build
npm run test:e2e
```

## 8. Smoke test manual

1. Registro
2. Login
3. Busqueda de jobs
4. Guardar preferencias
5. Checkout Starter
6. Recepcion del webhook
7. Upgrade de plan visible en dashboard
8. Uso real de feature Pro o Premium
9. Logout
10. Reingreso con sesion valida

## 9. Telegram y dominio

- Configurar `LANDING_URL` con el dominio publico nuevo.
- Verificar que `/web` en el bot abra la landing correcta.
- Si vas a usar un dominio `.com.ar`, conectarlo primero a Vercel y despues actualizar el bot.

## 10. Corte final

Cuando el dominio principal ya apunte a `jobbot/frontend` y el checkout funcione:

- dejar `job_bot/landing/index.html` solo como backup
- no volver a deployar el proyecto viejo de Vercel
- limpiar el HTML legacy en una segunda pasada
