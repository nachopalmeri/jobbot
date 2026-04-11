#!/bin/bash
#
# Quick smoke tests - Verifica que todo funcione en 2 minutos
#

set -euo pipefail

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════════"
echo "   ⚡ Smoke Tests - JobBot Dashboard"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Tests rápidos para verificar que el sistema funciona:"
echo ""

PASSED=0
FAILED=0

run_smoke() {
  local name="$1"
  local test_file="$2"
  
  echo -n "→ $name... "
  
  if ./run.sh "$test_file" > /tmp/smoke-$name.log 2>&1; then
    echo "✅"
    PASSED=$((PASSED + 1))
  else
    echo "❌"
    FAILED=$((FAILED + 1))
    echo "   Ver log: /tmp/smoke-$name.log"
  fi
}

# 1. Landing (pública)
run_smoke "Landing" "01-landing"

# 2. Login (auth)
run_smoke "Login" "04-login"

# 3. Dashboard (protegido)
run_smoke "Dashboard" "07-dashboard"

# 4. Buscar (protegido)
run_smoke "Buscar" "08-buscar"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   Resultado: $PASSED pasaron, $FAILED fallaron"
echo "═══════════════════════════════════════════════════════════════"

if [[ $FAILED -eq 0 ]]; then
  echo "✅ Smoke tests exitosos - El sistema está funcionando"
  exit 0
else
  echo "❌ Algunos tests fallaron - Revisar logs"
  exit 1
fi
