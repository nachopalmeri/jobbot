#!/bin/bash
#
# JobBot E2E Test Suite - Ejecutor de todas las categorías
# Uso: ./suite.sh [categoria|all]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CATEGORY="${1:-all}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Categorías de tests
declare -A TEST_CATEGORIES
TEST_CATEGORIES=(
  ["public"]="01-landing 02-contacto 03-legal 24-links-navigation"
  ["auth"]="04-login 05-register 06-password-reset"
  ["dashboard"]="07-dashboard 08-buscar 17-navegacion 25-search-filters"
  ["cv"]="09-cv 10-cv-cover-letter 11-cv-mock-interview 22-cv-historial-detail"
  ["management"]="12-postulaciones 13-configuracion 14-creditos 15-suscripcion 16-admin 23-kanban-workflow"
  ["responsive"]="18-mobile-responsive 21-tablet-responsive"
  ["errors"]="19-error-states"
  ["e2e"]="20-flujo-completo 26-accessibility-check"
  ["security"]="27-security-routes 28-security-xss 29-security-headers 30-security-brute-force 31-security-session"
)

# Encabezado
print_header() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "   🧪 JobBot Dashboard - E2E Test Suite"
  echo "═══════════════════════════════════════════════════════════════"
  echo "   Categoría: $CATEGORY"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
}

# Mostrar ayuda
show_help() {
  echo ""
  echo "Uso: ./suite.sh [categoria|all|list|help]"
  echo ""
  echo "Categorías disponibles:"
  echo "  all          - Ejecutar todos los tests (35 tests)"
  echo "  public       - Páginas públicas (landing, contacto, legal)"
  echo "  auth         - Autenticación (login, register, forgot)"
  echo "  dashboard    - Dashboard y búsqueda"
  echo "  cv           - Suite completa de CV"
  echo "  management   - Postulaciones, config, créditos, admin"
  echo "  responsive   - Tests mobile y tablet"
  echo "  errors       - Estados de error y validaciones"
  echo "  e2e          - Flujos completos end-to-end"
  echo "  security     - Tests de seguridad (XSS, headers, brute force)"
  echo ""
  echo "Ejemplos:"
  echo "  ./suite.sh all           # Todo"
  echo "  ./suite.sh public        # Solo públicas"
  echo "  ./suite.sh auth          # Solo auth"
  echo "  ./suite.sh cv            # Solo CV"
  echo "  ./suite.sh responsive    # Solo responsive"
  echo ""
}

# Listar tests
list_tests() {
  echo ""
  echo "📋 Tests disponibles:"
  echo ""
  
  for cat in public auth dashboard cv management responsive errors e2e security; do
    echo -e "${BLUE}[$cat]${NC}"
    for test in ${TEST_CATEGORIES[$cat]}; do
      local file="./tests/$test.json"
      if [[ -f "$file" ]]; then
        echo "  ✅ $test"
      else
        echo "  ❌ $test (no encontrado)"
      fi
    done
    echo ""
  done
  
  local total=$(find ./tests -name "*.json" | wc -l)
  echo "Total: $total tests"
  echo ""
}

# Ejecutar categoría
run_category() {
  local cat="$1"
  local tests="${TEST_CATEGORIES[$cat]}"
  local passed=0
  local failed=0
  
  echo -e "${YELLOW}▶️  Ejecutando categoría: $cat${NC}"
  echo ""
  
  for test in $tests; do
    if ./run.sh "$test"; then
      passed=$((passed + 1))
    else
      failed=$((failed + 1))
    fi
    echo ""
  done
  
  echo -e "${GREEN}✅ Pasaron: $passed${NC}"
  if [[ $failed -gt 0 ]]; then
    echo -e "${RED}❌ Fallaron: $failed${NC}"
  fi
  
  return $failed
}

# Ejecutar todas
run_all() {
  local total_passed=0
  local total_failed=0
  
  for cat in public auth dashboard cv management responsive errors e2e; do
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    run_category "$cat"
    if [[ $? -eq 0 ]]; then
      total_passed=$((total_passed + 1))
    else
      total_failed=$((total_failed + 1))
    fi
  done
  
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "   📊 RESUMEN FINAL"
  echo "═══════════════════════════════════════════════════════════════"
  echo -e "   Categorías exitosas: ${GREEN}$total_passed${NC}"
  if [[ $total_failed -gt 0 ]]; then
    echo -e "   Categorías con fallos: ${RED}$total_failed${NC}"
  fi
  echo "═══════════════════════════════════════════════════════════════"
  
  return $total_failed
}

# Main
print_header

case "$CATEGORY" in
  help|--help|-h)
    show_help
    exit 0
    ;;
  list|--list|-l)
    list_tests
    exit 0
    ;;
  all)
    run_all
    exit $?
    ;;
  public|auth|dashboard|cv|management|responsive|errors|e2e|security)
    run_category "$CATEGORY"
    exit $?
    ;;
  *)
    echo -e "${RED}❌ Categoría desconocida: $CATEGORY${NC}"
    show_help
    exit 1
    ;;
esac
