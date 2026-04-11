#!/bin/bash
#
# Agent-Browser Test Runner para JobBot Dashboard
# Wrapper para ejecutar agent-browser con configuración consistente
#

set -euo pipefail

# Configuración
BASE_URL="${BASE_URL:-http://localhost:3000}"
SESSION_NAME="${SESSION_NAME:-jobbot-test}"
SCREENSHOT_DIR="${SCREENSHOT_DIR:-./screenshots}"
TIMEOUT="${TIMEOUT:-10000}"

# Verificar que agent-browser está instalado
check_agent_browser() {
  if ! command -v agent-browser &> /dev/null; then
    echo "❌ agent-browser no está instalado"
    echo "   Instalalo con: npm install -g agent-browser"
    echo "   O: brew install agent-browser"
    exit 1
  fi
  echo "✅ agent-browser $(agent-browser --version 2>/dev/null || echo 'detectado')"
}

# Iniciar sesión limpia
start_session() {
  echo "🚀 Iniciando sesión de test: $SESSION_NAME"
  # Cerrar sesión previa si existe
  agent-browser --session "$SESSION_NAME" close --all 2>/dev/null || true
}

# Navegar a URL
open_url() {
  local path="${1:-/}"
  local full_url="$BASE_URL$path"
  echo "🌐 Abriendo: $full_url"
  agent-browser --session "$SESSION_NAME" open "$full_url"
  sleep 1
}

# Obtener snapshot y guardar refs
get_snapshot() {
  local output_file="${1:-}"
  echo "📸 Obteniendo snapshot interactivo..."
  
  if [[ -n "$output_file" ]]; then
    agent-browser --session "$SESSION_NAME" snapshot -i > "$output_file"
    echo "   Guardado en: $output_file"
  else
    agent-browser --session "$SESSION_NAME" snapshot -i
  fi
}

# Click por ref
click_ref() {
  local ref="$1"
  echo "🖱️  Click en $ref"
  agent-browser --session "$SESSION_NAME" click "$ref"
}

# Fill por ref
fill_ref() {
  local ref="$1"
  local value="$2"
  echo "✏️  Fill $ref con: $value"
  agent-browser --session "$SESSION_NAME" fill "$ref" "$value"
}

# Screenshot
screenshot() {
  local name="${1:-screenshot}"
  local path="$SCREENSHOT_DIR/${name}-$(date +%Y%m%d-%H%M%S).png"
  echo "📷 Screenshot: $path"
  agent-browser --session "$SESSION_NAME" screenshot "$path"
}

# Esperar elemento
wait_for() {
  local ref="$1"
  local timeout="${2:-5000}"
  echo "⏳ Esperando $ref (timeout: ${timeout}ms)..."
  agent-browser --session "$SESSION_NAME" wait --fn "document.querySelector('[ref=\"$ref\"]') !== null" || true
}

# Verificar texto en página
check_text() {
  local text="$1"
  echo "🔍 Verificando texto: '$text'"
  if agent-browser --session "$SESSION_NAME" eval "document.body.innerText.includes('$text')" | grep -q "true"; then
    echo "   ✅ Texto encontrado"
    return 0
  else
    echo "   ❌ Texto NO encontrado"
    return 1
  fi
}

# Cerrar sesión
cleanup() {
  echo "🧹 Cerrando sesión..."
  agent-browser --session "$SESSION_NAME" close --all 2>/dev/null || true
}

# Ejecutar batch de comandos JSON
run_batch() {
  local batch_file="$1"
  echo "▶️  Ejecutando batch: $batch_file"
  agent-browser --session "$SESSION_NAME" batch --json < "$batch_file"
}

# Exportar funciones
export -f check_agent_browser start_session open_url get_snapshot click_ref fill_ref screenshot wait_for check_text cleanup run_batch
export BASE_URL SESSION_NAME SCREENSHOT_DIR TIMEOUT
