#!/bin/bash
#
# Generar nuevos tests desde interacciones manuales
# Uso: ./record.sh <nombre-del-test>
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TEST_NAME="${1:-new-test}"
TEST_FILE="./tests/$TEST_NAME.json"
BASE_URL="${BASE_URL:-http://localhost:3000}"
SESSION="record-$(date +%s)"

echo "═══════════════════════════════════════════════════════════════"
echo "   🎬 Grabación de test: $TEST_NAME"
echo "═══════════════════════════════════════════════════════════════"

if [[ -f "$TEST_FILE" ]]; then
  echo "⚠️  El archivo $TEST_FILE ya existe"
  read -p "¿Sobrescribir? (y/N): " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Cancelado"
    exit 1
  fi
fi

# Template inicial
cat > "$TEST_FILE" << 'EOF'
[
  ["open", "{{BASE_URL}}/login"],
  ["wait", "--load", "networkidle"],
  ["snapshot", "-i"],
  ["fill", "@e1", "test@example.com"],
  ["fill", "@e2", "password123"],
  ["click", "@e3"],
  ["wait", "--load", "networkidle"],
  ["wait", "2000"],
  ["get", "url"],
  ["snapshot", "-i"]
]
EOF

# Reemplazar BASE_URL
sed -i "s|{{BASE_URL}}|$BASE_URL|g" "$TEST_FILE"

echo ""
echo "✅ Test creado: $TEST_FILE"
echo ""
echo "📋 Pasos para completar:"
echo "   1. Revisá los refs con: ./inspect.sh <ruta>"
echo "   2. Editá el archivo: $TEST_FILE"
echo "   3. Probá el test: ./run.sh $TEST_NAME"
echo ""
echo "📝 Estructura del test:"
cat "$TEST_FILE"
