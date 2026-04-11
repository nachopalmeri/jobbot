# Fixtures para tests E2E de JobBot Dashboard
# 
# Estos son datos de prueba para usar en los tests.
# En un entorno real, estos vendrían de variables de entorno
# o de un servicio de test data management.

# Usuario de prueba
TEST_USER_EMAIL="test@example.com"
TEST_USER_PASSWORD="password123"
TEST_USER_NAME="Usuario de Prueba"

# URLs
BASE_URL="${BASE_URL:-http://localhost:3000}"
API_URL="${API_URL:-http://localhost:8000}"

# Rutas de la app
ROUTES=(
  "/"
  "/login"
  "/register"
  "/buscar"
  "/cv"
  "/cv/historial"
  "/cv/cover-letter"
  "/postulaciones"
  "/configuracion"
  "/creditos"
  "/suscripcion"
)

# Búsquedas de prueba
SEARCH_QUERIES=(
  "desarrollador frontend"
  "backend engineer"
  "product manager"
  "ux designer"
)

# Tiempos de espera (ms)
TIMEOUT_SHORT=1000
TIMEOUT_MEDIUM=3000
TIMEOUT_LONG=5000
TIMEOUT_NETWORK=10000

# Selectores comunes (CSS fallback)
CSS_SELECTORS=(
  "button[type='submit']"
  "input[type='email']"
  "input[type='password']"
  "[data-testid='search-input']"
  "[data-testid='upload-cv']"
)
