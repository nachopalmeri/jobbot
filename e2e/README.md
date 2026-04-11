# E2E Tests para JobBot Dashboard

**30 tests automatizados** usando [agent-browser](https://github.com/vercel-labs/agent-browser) - CLI nativa en Rust para automatización de browser.

---

## ⚡ Quick Start (2 minutos)

```bash
cd e2e/

# Verificar todo está listo
./check.sh

# Smoke tests rápidos (4 tests críticos)
./smoke.sh

# Ejecutar categoría específica
./suite.sh auth        # Login, register, forgot
./suite.sh cv          # Todo el flujo de CV
./suite.sh responsive  # Mobile + tablet

# Ejecutar TODO (30 tests)
./suite.sh all
```

---

## 📊 Cobertura de Tests (30 tests)

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| **Public** | 4 | Landing, contacto, legal pages |
| **Auth** | 3 | Login, register, password reset |
| **Dashboard** | 4 | Home, búsqueda, navegación |
| **CV Suite** | 4 | Upload, historial, cover letter, mock interview |
| **Management** | 6 | Postulaciones, config, créditos, suscripción, admin |
| **Responsive** | 2 | Mobile (iPhone) + Tablet (iPad) |
| **Errors** | 1 | Validaciones y estados de error |
| **E2E Flows** | 2 | Flujo completo + accessibility |

---

## 🗂️ Estructura

```
e2e/
├── run.sh              # Ejecutar 1 test
├── suite.sh            # Ejecutar categorías (all, auth, cv, etc.)
├── smoke.sh            # 4 tests rápidos
├── inspect.sh            # Inspeccionar refs
├── record.sh           # Crear nuevo test
├── check.sh            # Verificar setup
├── tests/              # 30 tests JSON
│   ├── 01-landing.json
│   ├── 04-login.json
│   ├── 09-cv.json
│   ├── 12-postulaciones.json
│   ├── 18-mobile-responsive.json
│   ├── 20-flujo-completo.json
│   └── ... 24 más
├── utils/              # Helpers y wrappers
├── fixtures/           # Datos de prueba
├── screenshots/        # Screenshots generados
└── reports/            # Logs y reportes JSON
```

---

## 🚀 Comandos Principales

### suite.sh - Ejecutar por categorías

```bash
./suite.sh all              # Todos los tests (30)
./suite.sh public           # 01-landing, 02-contacto, 03-legal, 24-links
./suite.sh auth             # 04-login, 05-register, 06-password-reset
./suite.sh dashboard        # 07-dashboard, 08-buscar, 17-navegacion, 25-filters
./suite.sh cv               # 09-cv, 10-cover-letter, 11-mock, 22-historial
./suite.sh management       # 12-postulaciones, 13-config, 14-creditos, 15-suscripcion, 16-admin, 23-kanban
./suite.sh responsive       # 18-mobile, 21-tablet
./suite.sh errors           # 19-error-states
./suite.sh e2e              # 20-flujo-completo, 26-accessibility
./suite.sh list             # Listar todos los tests
./suite.sh help             # Ayuda
```

### run.sh - Ejecutar 1 test

```bash
./run.sh 01-landing         # Landing page
./run.sh 04-login           # Flujo de login
./run.sh 20-flujo-completo  # Flujo E2E completo
```

### Scripts de utilidad

```bash
./smoke.sh                  # 4 tests rápidos (landing, login, dashboard, buscar)
./inspect.sh /login         # Ver refs @e1, @e2, etc.
./inspect.sh /cv            # Inspeccionar CV page
./record.sh mi-test         # Crear test nuevo
./check.sh                  # Verificar configuración
```

---

## 📝 Tests Destacados

### 20-flujo-completo.json
Test E2E que recorre todo:
- Login → Dashboard → Buscar empleos → CV → Historial → Postulaciones (crear) → Configuración → Suscripción

### 18-mobile-responsive.json
Tests en iPhone viewport (390x844 @3x):
- Landing, Login, Dashboard, Buscar, CV, Postulaciones

### 12-postulaciones + 23-kanban-workflow
Tests del Kanban board:
- Board view, crear postulación, modal, flujo completo

---

## 🖼️ Screenshots

Todos los tests generan screenshots en `./screenshots/`:

```
screenshots/
├── landing-hero.png
├── landing-features.png
├── auth-login.png
├── auth-login-success.png
├── dashboard-home.png
├── cv-main.png
├── cv-cover-letter-generated.png
├── postulaciones-kanban.png
├── mobile-landing.png
├── tablet-dashboard.png
└── ...
```

---

## 📋 Reportes

Después de ejecutar:

```bash
cat reports/summary.json
```

```json
{
  "timestamp": "2025-04-03T14:30:00Z",
  "baseUrl": "http://localhost:3000",
  "total": 30,
  "passed": 28,
  "failed": 2,
  "results": {
    "01-landing": { "status": "✅ PASSED", "duration": 8 },
    "04-login": { "status": "✅ PASSED", "duration": 12 },
    ...
  }
}
```

---

## 🔧 Configuración

Variables de entorno:

```bash
export BASE_URL=http://localhost:3000      # URL del dashboard
export SESSION_NAME=jobbot-test            # Nombre de sesión
export SCREENSHOT_DIR=./screenshots        # Directorio screenshots
export TIMEOUT=10000                       # Timeout en ms
```

---

## 🐛 Debugging

### Ver refs de una página
```bash
./inspect.sh /login
# Output:
# - textbox "Email" [ref=e1]
# - textbox "Password" [ref=e2]
# - button "Sign In" [ref=e3]
```

### Modo headed (ver browser)
```bash
agent-browser --headed open http://localhost:3000/login
agent-browser --headed snapshot -i
```

### DevTools
```bash
agent-browser open http://localhost:3000/login
agent-browser inspect              # Abrir Chrome DevTools
```

---

## 🧪 Crear nuevo test

```bash
# 1. Inspeccionar la página
./inspect.sh /nueva-ruta

# 2. Crear test
./record.sh 27-nueva-ruta

# 3. Editar tests/27-nueva-ruta.json
# 4. Ejecutar
./run.sh 27-nueva-ruta

# 5. Agregar a suite.sh en la categoría correspondiente
```

---

## 🔄 CI/CD

GitHub Actions configurado en `.github/workflows/e2e-tests.yml`:

```yaml
- name: 🧪 Run E2E Tests
  working-directory: ./e2e
  run: ./suite.sh all
```

Se ejecuta en:
- Push a `main` o `develop`
- PRs que modifican `dashboard/**` o `e2e/**`
- Manual (workflow_dispatch)

Artefactos:
- Screenshots de todos los tests
- Reporte JSON (`summary.json`)
- Logs individuales

---

## 📚 Documentación

- `README.md` - Este archivo (guía rápida)
- `TESTS.md` - Índice completo de los 30 tests
- [agent-browser docs](https://github.com/vercel-labs/agent-browser)

---

## 🎯 Próximos pasos

1. **Personalizar credenciales:** Editar `fixtures/test-data.sh`
2. **Ajustar refs:** Ejecutar `./inspect.sh` en cada ruta
3. **Agregar tests:** Usar `./record.sh` para nuevos flujos
4. **Screenshots baselines:** Para visual diff testing

---

## 📊 Estado actual

```
✅ 30 tests implementados
✅ 8 categorías de cobertura
✅ Scripts de ejecución listos
✅ CI/CD configurado
✅ Documentación completa
```

¿Listo para ejecutar? `cd e2e && ./smoke.sh`
