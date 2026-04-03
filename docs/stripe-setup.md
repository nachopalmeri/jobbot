# Stripe Setup

Para que JobBot pueda vender con Stripe en producción hacen falta tres bloques:

## 1. Productos y precios

Creá estos `Price IDs` en Stripe:

- `STRIPE_STARTER_PRICE_ID`
- `STRIPE_PRO_PRICE_ID`
- `STRIPE_PREMIUM_PRICE_ID`
- `STRIPE_STARTER_YEARLY_PRICE_ID`
- `STRIPE_PRO_YEARLY_PRICE_ID`
- `STRIPE_PREMIUM_YEARLY_PRICE_ID`
- `STRIPE_UNLOCK_PRICE_ID`
- `STRIPE_25CREDITS_PRICE_ID`
- `STRIPE_60CREDITS_PRICE_ID`
- `STRIPE_150CREDITS_PRICE_ID`

Valores esperados hoy:

- `Starter monthly`: `USD 4`
- `Pro monthly`: `USD 8`
- `Premium monthly`: `USD 12`
- `Starter yearly`: `USD 40`
- `Pro yearly`: `USD 80`
- `Premium yearly`: `USD 120`
- `Unlock suite`: `USD 9`
- `25 credits`: `USD 7`
- `60 credits`: `USD 15`
- `150 credits`: `USD 29`

## 2. Variables de entorno

Cargá en Azure y donde corresponda:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_CREDITS_WEBHOOK_SECRET`
- todos los `STRIPE_*_PRICE_ID`

## 3. Webhooks

Suscripciones:

- endpoint: `https://tu-api/subscriptions/webhook/stripe`
- eventos:
  - `checkout.session.completed`
  - `customer.subscription.deleted`

Créditos:

- endpoint: `https://tu-api/credits/webhook`
- eventos:
  - `checkout.session.completed`

## 4. Billing portal

El dashboard ya expone `Gestionar facturación` para Stripe si el usuario tiene:

- `subscription_provider = stripe`
- `subscription_id` guardado

## 5. Check de readiness

`GET /health` devuelve `stripe=configured` solo si están:

- secret key
- webhook secret
- price IDs mensuales
- price IDs anuales
- price IDs de créditos
- webhook secret de créditos
