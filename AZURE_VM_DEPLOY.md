# Deploy en Azure VM

Esta receta deja `api + bot + postgres` corriendo dentro de una sola VM Ubuntu usando Docker Compose.

## 1. Entrar por SSH

```bash
chmod 600 ~/Downloads/jobbot-api_key
ssh -i ~/Downloads/jobbot-api_key azureuser@TU_IP_PUBLICA
```

## 2. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 3. Instalar Git y clonar el repo

```bash
sudo apt-get update
sudo apt-get install -y git
git clone TU_REPO_GIT jobbot
cd jobbot
```

## 4. Preparar variables de entorno

```bash
cp .env.azure.example .env
nano .env
```

Campos minimos que tenes que completar:

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `TELEGRAM_TOKEN`
- `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` si queres pagos ya activos
- `GROQ_API_KEY` si queres IA

## 5. Levantar servicios

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```

## 6. Verificar

Desde la VM:

```bash
curl http://localhost:8000/health
docker compose -f docker-compose.prod.yml logs --tail=100 bot
```

## 7. Abrir HTTP/HTTPS en Azure

Cuando todo responda bien, agregá inbound rules para:

- `80/tcp`
- `443/tcp`

Mantene cerrados:

- `5432`
- `8000`

## 8. Reverse proxy

El siguiente paso recomendado es poner `Caddy` o `Nginx` delante de la API para publicar:

- `https://api.tudominio.com` -> `http://127.0.0.1:8000`

## 9. Conectar Vercel

Cuando la API ya esté pública:

1. En el proyecto `dashboard` de Vercel configurá `NEXT_PUBLIC_API_URL=https://api.tudominio.com`
2. Redeploy del dashboard
3. Probar:
   - login web
   - registro web
   - login por código desde Telegram
   - búsqueda
   - suscripción
