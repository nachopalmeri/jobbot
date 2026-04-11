#!/bin/bash
#
# Ejecutar tests E2E usando Docker con Chrome completo
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "   🐳 JobBot E2E - Ejecutando con Docker"
echo "═══════════════════════════════════════════════════════════════"

# Verificar Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker no está instalado"
  echo "   Instalalo desde: https://docs.docker.com/get-docker/"
  exit 1
fi

# Crear Dockerfile temporal
cat > /tmp/agent-browser-dockerfile << 'DOCKERFILE'
FROM mcr.microsoft.com/playwright:v1.42.0-jammy

# Instalar agent-browser
RUN npm install -g agent-browser && \
    agent-browser install

# Crear directorio de trabajo
WORKDIR /e2e

# Copiar tests
COPY . .

# Exponer puerto para dashboard
EXPOSE 3000

CMD ["bash"]
DOCKERFILE

echo "🔨 Construyendo imagen Docker..."
docker build -t jobbot-e2e -f /tmp/agent-browser-dockerfile . 2>&1 || {
  echo "❌ Error construyendo imagen"
  exit 1
}

echo ""
echo "🚀 Ejecutando tests en Docker..."
docker run --rm -it \
  --network host \
  -v "$(pwd)/reports:/e2e/reports" \
  -v "$(pwd)/screenshots:/e2e/screenshots" \
  jobbot-e2e \
  bash -c "./suite.sh all"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   ✅ Tests completados"
echo "   Reportes: ./reports/"
echo "   Screenshots: ./screenshots/"
echo "═══════════════════════════════════════════════════════════════"
