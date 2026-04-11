#!/bin/bash
#
# Sanity check - Verifica que todo esté configurado correctamente
#

set -euo pipefail

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════════"
echo "   ✅ Sanity Check - JobBot E2E Tests"
echo "═══════════════════════════════════════════════════════════════"

ERRORS=0

# 1. Verificar agent-browser
echo ""
echo "1. Verificando agent-browser..."
if command -v agent-browser &> /dev/null; then
  echo "   ✅ agent-browser instalado"
  agent-browser --version 2>/dev/null || echo "   ⚠️  No se pudo obtener versión"
else
  echo "   ❌ agent-browser no encontrado"
  echo "      Instalalo: npm install -g agent-browser"
  ERRORS=$((ERRORS + 1))
fi

# 2. Verificar Chrome
echo ""
echo "2. Verificando Chrome..."
if agent-browser eval "1+1" &> /dev/null; then
  echo "   ✅ Chrome disponible"
else
  echo "   ❌ Chrome no disponible"
  echo "      Ejecutá: agent-browser install"
  ERRORS=$((ERRORS + 1))
fi

# 3. Verificar estructura
echo ""
echo "3. Verificando estructura de directorios..."
for dir in tests utils fixtures screenshots reports; do
  if [[ -d "$dir" ]]; then
    echo "   ✅ $dir/"
  else
    echo "   ❌ $dir/ no existe"
    ERRORS=$((ERRORS + 1))
  fi
done

# 4. Verificar archivos de test
echo ""
echo "4. Verificando archivos de test..."
for file in tests/*.json; do
  if [[ -f "$file" ]]; then
    echo "   ✅ $(basename "$file")"
  fi
done

# 5. Verificar permisos
echo ""
echo "5. Verificando permisos de scripts..."
for script in run.sh inspect.sh record.sh; do
  if [[ -x "$script" ]]; then
    echo "   ✅ $script es ejecutable"
  else
    echo "   ❌ $script no es ejecutable"
    echo "      Ejecutá: chmod +x $script"
    ERRORS=$((ERRORS + 1))
  fi
done

# 6. Verificar servidor
echo ""
echo "6. Verificando servidor de dashboard..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "   ✅ Dashboard disponible en http://localhost:3000"
else
  echo "   ⚠️  Dashboard no disponible en http://localhost:3000"
  echo "      Para ejecutar tests localmente, iniciá el dashboard:"
  echo "      cd ../dashboard && npm run dev"
fi

# 7. Verificar CI/CD
echo ""
echo "7. Verificando configuración de CI/CD..."
if [[ -f ../.github/workflows/e2e-tests.yml ]]; then
  echo "   ✅ GitHub Actions workflow configurado"
else
  echo "   ⚠️  GitHub Actions workflow no encontrado"
fi

# Resumen
echo ""
echo "═══════════════════════════════════════════════════════════════"
if [[ $ERRORS -eq 0 ]]; then
  echo "   🎉 Todo listo para ejecutar tests!"
  echo ""
  echo "   Comandos disponibles:"
  echo "   ./run.sh all          # Ejecutar todos los tests"
  echo "   ./run.sh login        # Ejecutar test específico"
  echo "   ./inspect.sh /login   # Inspeccionar refs"
  echo "   ./record.sh mi-test   # Crear nuevo test"
  echo "═══════════════════════════════════════════════════════════════"
  exit 0
else
  echo "   ⚠️  Se encontraron $ERRORS problema(s)"
  echo "   Corregí los errores marcados con ❌"
  echo "═══════════════════════════════════════════════════════════════"
  exit 1
fi
