# Tests E2E - Índice Completo

## 📊 Resumen

**Total de tests:** 30 tests automatizados  
**Cobertura:** Todos los flujos críticos de JobBot Dashboard  
**Herramienta:** agent-browser (Vercel Labs)  

---

## 🗂️ Categorías

### 1. Páginas Públicas (4 tests)
| # | Test | Descripción |
|---|------|-------------|
| 01 | `landing` | Hero, features, scroll completo |
| 02 | `contacto` | Formulario de contacto |
| 03 | `legal` | Términos, privacidad, reembolsos |
| 24 | `links-navigation` | Links entre auth pages |

### 2. Autenticación (3 tests)
| # | Test | Descripción |
|---|------|-------------|
| 04 | `login` | Login exitoso con credenciales |
| 05 | `register` | Formulario de registro |
| 06 | `password-reset` | Forgot + reset password |

### 3. Dashboard Core (4 tests)
| # | Test | Descripción |
|---|------|-------------|
| 07 | `dashboard` | Dashboard home y widgets |
| 08 | `buscar` | Búsqueda de empleos |
| 17 | `navegacion` | Navegación entre páginas |
| 25 | `search-filters` | Búsquedas con diferentes filtros |

### 4. CV Suite (4 tests)
| # | Test | Descripción |
|---|------|-------------|
| 09 | `cv` | Página principal de CV |
| 10 | `cv-cover-letter` | Generador de cartas |
| 11 | `cv-mock-interview` | Simulación de entrevistas |
| 22 | `cv-historial-detail` | Detalle de análisis histórico |

### 5. Management (6 tests)
| # | Test | Descripción |
|---|------|-------------|
| 12 | `postulaciones` | Kanban board |
| 13 | `configuracion` | Tabs de configuración |
| 14 | `creditos` | Página de créditos |
| 15 | `suscripcion` | Planes y pricing |
| 16 | `admin` | Panel de admin |
| 23 | `kanban-workflow` | Crear y mover postulaciones |

### 6. Responsive (2 tests)
| # | Test | Descripción |
|---|------|-------------|
| 18 | `mobile-responsive` | iPhone viewport (390x844) |
| 21 | `tablet-responsive` | iPad viewport (768x1024) |

### 7. Errores y Validaciones (1 test)
| # | Test | Descripción |
|---|------|-------------|
| 19 | `error-states` | Form errors, validation |

### 8. Flujos E2E (2 tests)
| # | Test | Descripción |
|---|------|-------------|
| 20 | `flujo-completo` | Todo el flujo: login → search → cv → postulaciones → config → suscripción |
| 26 | `accessibility-check` | Verificación de roles ARIA |

---

## 🚀 Uso con suite.sh

```bash
./suite.sh all              # Todos los tests (30)
./suite.sh public           # Solo públicas (4)
./suite.sh auth             # Solo auth (3)
./suite.sh dashboard        # Solo dashboard (4)
./suite.sh cv               # Solo CV (4)
./suite.sh management       # Solo management (6)
./suite.sh responsive       # Solo responsive (2)
./suite.sh errors           # Solo errores (1)
./suite.sh e2e              # Solo E2E (2)
./suite.sh list             # Listar todos
./suite.sh help             # Ayuda
```

---

## 🔧 Uso individual

```bash
./run.sh 01-landing         # Test específico
./run.sh 04-login           # Login
./run.sh 20-flujo-completo  # Flujo E2E
```

---

## 📱 Viewports usados

| Dispositivo | Viewport | Tests |
|-------------|----------|-------|
| Desktop | 1280x720 default | Todos |
| Mobile (iPhone) | 390x844 @3x | 18-mobile-responsive |
| Tablet (iPad) | 768x1024 @2x | 21-tablet-responsive |

---

## 🖼️ Screenshots generados

Cada test genera screenshots en `./screenshots/`:

- `landing-hero.png`, `landing-features.png`
- `auth-*.png`
- `dashboard-*.png`
- `cv-*.png`
- `mobile-*.png`, `tablet-*.png`
- etc.

---

## 📋 Reportes

Los reportes se guardan en `./reports/`:
- `summary.json` - Resumen JSON con todos los resultados
- `*.log` - Logs individuales de cada test

---

## 🔍 Inspección y debugging

```bash
./inspect.sh /login         # Ver refs de login
./inspect.sh /cv            # Ver refs de CV
./record.sh mi-test         # Crear nuevo test
./check.sh                  # Verificar setup
```

---

## 🧪 Test de ejemplo: Flujo completo

```bash
./run.sh 20-flujo-completo
```

Pasos:
1. Login con credenciales
2. Screenshot del dashboard
3. Buscar "frontend developer"
4. Screenshot de resultados
5. Ir a /cv
6. Ir a /cv/historial
7. Crear postulación en Kanban
8. Ir a configuración
9. Ir a suscripción

---

## 📝 Crear nuevo test

1. Inspeccionar la página:
   ```bash
   ./inspect.sh /nueva-ruta
   ```

2. Crear archivo `tests/XX-nombre.json`:
   ```json
   [
     ["open", "http://localhost:3000/nueva-ruta"],
     ["wait", "--load", "networkidle"],
     ["snapshot", "-i"],
     ["click", "@e1"],
     ["screenshot", "./screenshots/nueva-ruta.png"]
   ]
   ```

3. Agregar a `suite.sh` en la categoría correspondiente.

---

## 🚨 Troubleshooting

### Chrome no disponible
```bash
agent-browser install
# En Linux:
agent-browser install --with-deps
```

### Servidor no responde
```bash
cd ../dashboard && npm run dev
# Esperar a que inicie, luego:
cd e2e && ./suite.sh all
```

### Refs cambiaron
```bash
./inspect.sh /ruta         # Ver nuevos refs
# Actualizar el test JSON
```

---

## 📚 Recursos

- [agent-browser docs](https://github.com/vercel-labs/agent-browser)
- [Comandos CLI](https://github.com/vercel-labs/agent-browser#commands)
- [Workflow óptimo](https://github.com/vercel-labs/agent-browser#optimal-ai-workflow)
