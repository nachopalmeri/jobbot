# JobBot Dashboard

Aplicación web principal de JobBot construida con Next.js App Router.

## Qué hace

- Landing pública del producto
- Registro, login y recuperación de password
- Dashboard autenticado
- CV Suite, búsquedas, postulaciones, suscripciones y panel admin

## Contrato operativo

- El frontend consume `/api/backend/*`.
- Ese path es un proxy seguro hacia la API real de JobBot.
- La sesión se guarda en cookie `httpOnly`; no se usa `localStorage` para auth.

## Variables relevantes

- `JOBBOT_API_ORIGIN`: origen de la API real, por ejemplo `http://127.0.0.1:8000`
- `NEXT_PUBLIC_APP_URL`: URL pública de la app
- `NEXT_PUBLIC_LANDING_URL`: URL pública de marketing si difiere

## Desarrollo

```bash
npm install
npm run dev
```

## Verificación

```bash
npm test
npm run build
```
