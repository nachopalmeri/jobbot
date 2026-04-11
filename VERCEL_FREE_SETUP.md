# Vercel Free Setup

Estado operativo actual para JobBot mientras no se usen dominios custom.

## Dos superficies públicas

- **Landing pública marketinera**
  - código: `job_bot/landing/`
  - URL operativa: `https://jobbot-lime.vercel.app`
  - proyecto Vercel actual: `jobbot`

- **App real / dashboard**
  - código: `dashboard/`
  - URL operativa: `https://app-jobbot.vercel.app`
  - proyecto Vercel actual: `dashboard`

## Regla de enlace

Todos los CTAs públicos de la landing deben apuntar a `https://app-jobbot.vercel.app`:

- `/register`
- `/login`
- `/dashboard`
- `/dashboard/suscripcion`
- `/dashboard/creditos`

## Naming objetivo

Cuando más adelante se ordene Vercel por nombre, los canónicos deseados son:

- `jobbot-landing`
- `jobbot-app`

Mientras tanto, los canónicos operativos reales son:

- `jobbot` para la landing
- `dashboard` para la app

## Proyectos redundantes detectados

Estos no deben usarse para links públicos, metadata o material comercial:

- `jobbot-s2og`
- `job-bot`
- `jobbotasdas`
- `landing`
- `jobbot_landing_clean`
- `jobbot_landing_deploy`
- `jobbot-landing`
- `jobbot-landing-as7e`

## Regla editorial

- La landing pública vive en `job_bot/landing/`.
- La app real vive en `dashboard/`.
- No volver a mezclar la home interna del dashboard con la landing pública en docs o deploy notes.
