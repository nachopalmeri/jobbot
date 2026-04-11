#!/bin/bash
#
# E2E Test Runner para JobBot Dashboard
# Uso: ./run.sh [test-name|all]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "./utils/agent.sh"
source "./utils/helpers.sh"

# Configuración
TEST_NAME="${1:-all}"
REPORT_DIR="./reports"
SCREENSHOT_DIR="./screenshots"
BASE_URL="${BASE_URL:-http://localhost:3000}"

mkdir -p "$REPORT_DIR" "$SCREENSHOT_DIR"

# Banner
echo "═══════════════════════════════════════════════════════════════"
echo "   🧪 JobBot Dashboard - E2E Tests con agent-browser"
echo "═══════════════════════════════════════════════════════════════"
echo "   Base URL: $BASE_URL"
echo "   Test: $TEST_NAME"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Verificaciones
check_agent_browser

# Verificar/levantar servidor
if ! curl -s "$BASE_URL" > /dev/null 2>&1; then
  echo "⚠️  Servidor no detectado en $BASE_URL"
  echo "   Por favor iniciá el dashboard primero:"
  echo "   cd ../dashboard && npm run dev"
  exit 1
fi

# Resultados
declare -A RESULTS
declare -A DURATIONS

# Ejecutar un test
run_test() {
  local name="$1"
  local file="./tests/$name.json"
  
  if [[ ! -f "$file" ]]; then
    echo "❌ Test no encontrado: $file"
    return 1
  fi
  
  echo "═══════════════════════════════════════════════════════════════"
  echo "▶️  Ejecutando: $name"
  echo "═══════════════════════════════════════════════════════════════"
  
  local start_time=$(date +%s)
  
  # Cerrar sesión previa
  agent-browser --session "jobbot-$name" close --all 2>/dev/null || true
  
  # Ejecutar batch
  if agent-browser --session "jobbot-$name" batch --json --bail < "$file" 2>&1 | tee "$REPORT_DIR/${name}.log"; then
    local end_time=$(date +%s)
    DURATIONS[$name]=$((end_time - start_time))
    RESULTS[$name]="✅ PASSED"
    echo "✅ $name: PASÓ en ${DURATIONS[$name]}s"
    
    # Screenshot final
    agent-browser --session "jobbot-$name" screenshot "$SCREENSHOT_DIR/${name}-final.png" 2>/dev/null || true
    agent-browser --session "jobbot-$name" close --all 2>/dev/null || true
    return 0
  else
    local end_time=$(date +%s)
    DURATIONS[$name]=$((end_time - start_time))
    RESULTS[$name]="❌ FAILED"
    echo "❌ $name: FALLÓ en ${DURATIONS[$name]}s"
    
    # Screenshot del error
    agent-browser --session "jobbot-$name" screenshot "$SCREENSHOT_DIR/${name}-error.png" 2>/dev/null || true
    agent-browser --session "jobbot-$name" close --all 2>/dev/null || true
    return 1
  fi
}

# Ejecutar todos los tests
run_all_tests() {
  local failed=0
  
  for test_file in ./tests/*.json; do
    local name=$(basename "$test_file" .json)
    if ! run_test "$name"; then
      failed=$((failed + 1))
    fi
    echo ""
  done
  
  return $failed
}

# Reporte final
print_report() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "   📊 REPORTE FINAL"
  echo "═══════════════════════════════════════════════════════════════"
  
  local total=0
  local passed=0
  local failed=0
  
  for name in "${!RESULTS[@]}"; do
    total=$((total + 1))
    if [[ "${RESULTS[$name]}" == "✅ PASSED" ]]; then
      passed=$((passed + 1))
    else
      failed=$((failed + 1))
    fi
    printf "   %-20s %s (%ss)\n" "$name:" "${RESULTS[$name]}" "${DURATIONS[$name]:-0}"
  done
  
  echo "───────────────────────────────────────────────────────────────"
  echo "   Total: $total | ✅ Pasaron: $passed | ❌ Fallaron: $failed"
  echo "═══════════════════════════════════════════════════════════════"
  
  # Guardar reporte JSON
  cat > "$REPORT_DIR/summary.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "baseUrl": "$BASE_URL",
  "total": $total,
  "passed": $passed,
  "failed": $failed,
  "results": {
$(for name in "${!RESULTS[@]}"; do
  echo "    \"$name\": { \"status\": \"${RESULTS[$name]}\", \"duration\": ${DURATIONS[$name]:-0} },"
done | sed '$ s/,$//')
  }
}
EOF

  return $failed
}

# Main
trap cleanup EXIT

if [[ "$TEST_NAME" == "all" ]]; then
  run_all_tests
  exit_code=$?
else
  if run_test "$TEST_NAME"; then
    exit_code=0
  else
    exit_code=1
  fi
fi

print_report
exit $exit_code
