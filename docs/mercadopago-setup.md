# Mercado Pago Setup

Para lanzar JobBot con Mercado Pago en produccion hacen falta tres bloques:

## 1. Credenciales de produccion

En Mercado Pago, dentro de tu aplicacion `jobbot`, anda a:

- `Produccion`
- `Credenciales de produccion`

Y copia estos valores:

- `MP_ACCESS_TOKEN`
- `MP_PUBLIC_KEY`

## 2. Webhook de produccion

En Mercado Pago, dentro de:

- `Notificaciones`
- `Webhooks`

configura el endpoint publico del backend:

- `http://128.203.100.186/subscriptions/webhook/mercadopago`

Si luego movemos la API a un dominio propio, reemplazalo por:

- `https://api.jobbot.ar/subscriptions/webhook/mercadopago`

Despues guarda el secreto de firma en:

- `MP_WEBHOOK_SECRET`

Opcionalmente, si queres endurecer mas la validacion por origen, carga tambien:

- `MP_WEBHOOK_IPS`

como una lista separada por comas.

## 3. Variables de entorno en Azure

Carga en la VM del backend:

- `MP_ACCESS_TOKEN`
- `MP_PUBLIC_KEY`
- `MP_WEBHOOK_SECRET`
- `MP_WEBHOOK_IPS` (opcional)

Con la integracion actual, Mercado Pago no necesita `price IDs` para funcionar.
El backend crea la suscripcion recurrente con:

- plan
- monto
- ciclo (`monthly` o `yearly`)

directamente en el `preapproval` de Mercado Pago.

## 4. Que hace hoy la integracion

JobBot ya soporta en produccion:

- checkout recurrente mensual
- checkout recurrente anual
- webhook firmado
- activacion automatica del plan
- cancelacion real del `preapproval`
- idempotencia de eventos

Rutas involucradas:

- `POST /subscriptions/create-checkout`
- `POST /subscriptions/webhook/mercadopago`
- `POST /subscriptions/cancel`

## 5. Check de readiness

`GET /health` devuelve `mercadopago=configured` si estan cargados:

- `MP_ACCESS_TOKEN`
- `MP_WEBHOOK_SECRET`

## 6. Smoke test recomendado

Antes de abrir ventas:

1. Inicia checkout de un plan desde `https://app-jobbot.vercel.app/dashboard/suscripcion`
2. Completa un pago productivo de prueba en Mercado Pago
3. Verifica que el webhook active el plan
4. Revisa `GET /subscriptions/status`
5. Prueba `POST /subscriptions/cancel`
6. Verifica que la recurrencia quede cancelada en Mercado Pago

## 7. Nota practica

Para el launch en Argentina, Mercado Pago es hoy la via mas natural para:

- cobrar en moneda local
- evitar el onboarding mas pesado de Stripe live
- validar rapido un primer flujo productivo real
