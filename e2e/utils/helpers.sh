#!/bin/bash
#
# Helpers para tests E2E de JobBot Dashboard
#

set -euo pipefail

# Get the directory where this script is located (works when sourced)
UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$UTILS_DIR/agent.sh"

# Esperar a que el servidor esté disponible
wait_for_server() {
  local url="${1:-$BASE_URL}"
  local max_attempts="${2:-30}"
  local wait_time="${3:-2}"

  echo "⏳ Esperando servidor en $url..."
  
  for i in $(seq 1 $max_attempts); do
    if curl -s "$url" > /dev/null 2>&1; then
      echo "✅ Servidor disponible"
      return 0
    fi
    echo "   Intento $i/$max_attempts..."
    sleep $wait_time
  done

  echo "❌ Servidor no disponible después de $max_attempts intentos"
  return 1
}

# Iniciar servidor Next.js en background
start_dev_server() {
  local port="${1:-3000}"
  echo "🔧 Iniciando Next.js en puerto $port..."
  
  cd ../dashboard
  npm run dev -- --port $port > /tmp/next-dev.log 2>&1 &
  local pid=$!
  
  echo "$pid" > /tmp/next-dev.pid
  echo "   PID: $pid"
  
  # Esperar a que esté listo
  sleep 3
  wait_for_server "http://localhost:$port"
}

# Detener servidor
dev_server_stop() {
  if [[ -f /tmp/next-dev.pid ]]; then
    local pid=$(cat /tmp/next-dev.pid)
    echo "🛑 Deteniendo servidor (PID: $pid)..."
    kill $pid 2>/dev/null || true
    rm -f /tmp/next-dev.pid
  fi
}

# Crear reporte de test
generate_report() {
  local test_name="$1"
  local result="${2:-PASSED}"
  local duration="${3:-0}"
  local output_dir="${4:-./reports}"
  
  mkdir -p "$output_dir"
  
  local report_file="$output_dir/$(date +%Y%m%d-%H%M%S)-$test_name.txt"
  
  cat > "$report_file" << EOF
Test: $test_name
Resultado: $result
Duración: ${duration}s
Fecha: $(date -Iseconds)
URL Base: $BASE_URL
Session: $SESSION_NAME
EOF

  echo "📝 Reporte: $report_file"
}

# Helper: Encontrar ref por texto
find_ref_by_text() {
  local text="$1"
  local snapshot_file="${2:-/tmp/snapshot.txt}"
  
  # Buscar ref que contiene el texto
  grep -i "$text" "$snapshot_file" | grep -o '\[ref=[^]]*\]' | head -1 | sed 's/\[ref=//;s/\]//' || echo ""
}

# Helper: Esperar y reintentar
retry() {
  local max_attempts="${1:-3}"
  shift
  local delay="${1:-2}"
  shift
  
  for i in $(seq 1 $max_attempts); do
    if "$@"; then
      return 0
    fi
    echo "   Reintento $i/$max_attempts..."
    sleep $delay
  done
  
  return 1
}

# Exportar
export -f wait_for_server start_dev_server dev_server_stop generate_report find_ref_by_text retry
