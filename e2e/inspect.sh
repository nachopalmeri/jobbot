#!/bin/bash
#
# Inspector de refs para crear/actualizar tests E2E
# Uso: ./inspect.sh <path>
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "./utils/agent.sh"

URL_PATH="${1:-/login}"
BASE_URL="${BASE_URL:-http://localhost:3000}"
FULL_URL="$BASE_URL$URL_PATH"
SESSION="inspect-$(date +%s)"

echo "═══════════════════════════════════════════════════════════════"
echo "   🔍 Inspector de refs - JobBot Dashboard"
echo "═══════════════════════════════════════════════════════════════"
echo "   URL: $FULL_URL"
echo "═══════════════════════════════════════════════════════════════"

# Verificar agent-browser
check_agent_browser

# Cerrar sesión previa
agent-browser --session "$SESSION" close --all 2>/dev/null || true

echo ""
echo "🌐 Abriendo página..."
agent-browser --session "$SESSION" open "$FULL_URL"

echo ""
echo "⏳ Esperando carga..."
sleep 2

echo ""
echo "📸 Screenshot anotado (con refs visuales)..."
agent-browser --session "$SESSION" screenshot --annotate ./screenshots/inspect-$(basename "$URL_PATH")-$(date +%Y%m%d-%H%M%S).png

echo ""
echo "📋 Snapshot interactivo (refs para usar en tests):"
echo "───────────────────────────────────────────────────────────────"
agent-browser --session "$SESSION" snapshot -i
echo "───────────────────────────────────────────────────────────────"

echo ""
echo "🎯 Comandos útiles para tu test:"
echo ""
echo "# Abrir página"
echo "[\"open\", \"$FULL_URL\"],"
echo "[\"wait\", \"--load\", \"networkidle\"],"
echo "[\"snapshot\", \"-i\"],"
echo ""
echo "# Ejemplo de interacciones (reemplazar @eX con los refs de arriba):"
echo "[\"fill\", \"@e1\", \"test@example.com\"],"
echo "[\"fill\", \"@e2\", \"password123\"],"
echo "[\"click\", \"@e3\"],"
echo "[\"wait\", \"2000\"],"
echo "[\"screenshot\", \"./screenshots/result.png\"]"
echo ""

# Mantener sesión abierta para inspección manual
echo ""
echo "───────────────────────────────────────────────────────────────"
echo "   Sesión activa: $SESSION"
echo "   Para interactuar manualmente:"
echo "   agent-browser --session $SESSION <comando>"
echo ""
echo "   Ejemplos:"
echo "   agent-browser --session $SESSION click @e1"
echo "   agent-browser --session $SESSION get url"
echo "   agent-browser --session $SESSION screenshot"
echo ""
echo "   Para cerrar: agent-browser --session $SESSION close"
echo "───────────────────────────────────────────────────────────────"
