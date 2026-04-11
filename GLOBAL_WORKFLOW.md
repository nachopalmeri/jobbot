# 🔄 Jobbot — Global Workflow Perfecto

> Integración de Skills, Agentes y MCPs para desarrollo óptimo
> Versión: 1.0 | Fecha: 2026-04-10

---

## 📋 Arquitectura de Recursos

### Skills Disponibles (18)
| Skill | Uso | Trigger |
|-------|-----|---------|
| `api-design` | REST endpoints, status codes, pagination | Nuevos endpoints |
| `arca-facturacion` | Facturación electrónica ARCA | Facturación AR |
| `backend-patterns` | FastAPI, arquitectura server | API logic |
| `bcra-dolar` | Cotizaciones BCRA | Finanzas AR |
| `core-web-vitals` | Performance frontend | LCP/INP/CLS issues |
| `deployment-patterns` | Docker, CI/CD, health checks | Deploy/infra |
| `frontend-patterns` | React, Next.js, state | Dashboard UI |
| `gws-*` (12 skills) | Google Workspace integrations | Gmail, Drive, Sheets, Calendar |
| `loop` | Tareas recurrentes | Monitoreo |
| `persona-*` (7 roles) | Flujos por rol | Eventos, HR, IT |
| `postgres-patterns` | Query optimization, RLS | DB changes |
| `python-patterns` | PEP 8, type hints, best practices | Python code |
| `qc-helper` | Help Qwen Code | `/qc-helper` |
| `recipe-*` (24 recetas) | Automatizaciones Workspace | Gmail/Drive/Sheets tasks |
| `review` | Code review de PRs/files | `/review` |
| `ripio-api` | Ripio crypto wallet | Crypto ops |
| `security-review` | Auth, inputs, secrets, APIs | Security-sensitive code |
| `ui-ux-pro-max` | UI/UX design intelligence | Frontend/design |
| `verification-before-completion` | Pre-commit verification | Antes de completar |
| `web-design-guidelines` | Review UI code compliance | Audit UI |

### Agentes Especializados
| Agente | Tipo | Cuándo Usar |
|--------|------|-------------|
| `general-purpose` | Tareas complejas multi-step | Investigación, búsqueda, ejecución |
| `Explore` | Exploración rápida de codebase | Find files, search code, architecture questions |
| `statusline-setup` | Configurar status line | Setup only |

### MCPs (Model Context Protocols)
| MCP | Función | Integración |
|-----|---------|-------------|
| `gws-docs` | Google Docs read/write | Documentation sync |
| `gws-sheets` | Google Sheets read/write | Data export/import |
| `gws-gmail` | Email management | Notifications, alerts |
| `gws-calendar` | Calendar management | Scheduling events |
| `gws-drive` | File management | Backup, sharing |
| `gws-chat` | Google Chat | Team notifications |
| `gws-tasks` | Task management | Sync with todo.md |

---

## 🎯 Workflow Global — 7 Fases

### Fase 1: Session Start (Inicio)
**Trigger**: Al abrir Qwen Code en el proyecto

```
1. Indexar recursos globales
   ├── Skills disponibles
   ├── Agentes especializados
   └── MCPs configurados

2. Leer estado del proyecto
   ├── tasks/todo.md → ¿Qué está pendiente?
   ├── tasks/lessons.md → ¿Qué aprendimos?
   └── tasks/architecture_log.md → ¿Qué decidimos?

3. Verificar repositorio
   ├── git status
   ├── git log --oneline -5
   └── Verificar rama actual

4. Planificar sesión
   ├── Objetivo claro
   ├── Skill/workflow a usar
   └── Actualizar tasks/todo.md
```

**Herramientas**:
- `read_file` → Estado del proyecto
- `glob` → Encontrar archivos relevantes
- `run_shell_command` → Git status

---

### Fase 2: Planificación (Antes de Código)
**Trigger**: Nueva feature o cambio significativo

```
1. Cargar skill: writing-plans
   ├── Definir objetivo
   ├── Impacto en archivos
   ├── Lógica paso a paso
   └── Riesgos potenciales

2. Para features complejas:
   └── Usar agente Explore para investigar codebase
       └── Prompt: "Find all files related to [feature]"

3. Crear plan en tasks/todo.md
   ├── Items verificables
   ├── Criterios de aceptación
   └── Dependencias entre tareas

4. Aprobar plan con usuario
   └── NO escribir código hasta aprobación
```

**Skills Usadas**:
- `writing-plans` → Planificación estructurada
- `api-design` → Si involucra nuevos endpoints
- `postgres-patterns` → Si involucra DB changes

**Agentes**:
- `Explore` → Exploración de codebase

---

### Fase 3: Implementación (Código)
**Trigger**: Plan aprobado por usuario

```
1. Seleccionar skills según contexto:
   ├── Python code → python-patterns
   ├── FastAPI routes → backend-patterns
   ├── React/Next.js → frontend-patterns
   ├── Database queries → postgres-patterns
   ├── Security-sensitive → security-review
   └── UI/UX → ui-ux-pro-max

2. Para tareas complejas (multi-step):
   └── Usar agente general-purpose
       ├── Delegar investigación paralela
       ├── Ejecutar tareas independientes
       └── Mantener contexto limpio

3. Implementar con verificación continua:
   ├── Commits pequeños y temáticos
   ├── Tests primero (TDD cuando aplique)
   └── Verificar con cada cambio

4. Para code reviews:
   └── Usar skill: review
       ├── /review <file>
       ├── /review <pr-number>
       └── /review <pr-number> --comment
```

**Skills por Contexto**:
| Contexto | Skill Primario | Skill Secundario |
|----------|---------------|-----------------|
| New API endpoint | `backend-patterns` | `api-design` |
| DB migration | `postgres-patterns` | `security-review` |
| UI component | `frontend-patterns` | `ui-ux-pro-max` |
| Auth flow | `security-review` | `backend-patterns` |
| Bug fix | `python-patterns` | `verification-before-completion` |

**Agentes**:
- `general-purpose` → Tareas complejas de implementación
- `Explore` → Búsqueda rápida de código/patrones

---

### Fase 4: Verificación (Pre-Commit)
**Trigger**: Antes de marcar tarea como completada

```
1. Cargar skill: verification-before-completion
   ├── Ejecutar comandos de verificación
   ├── Confirmar output antes de hacer claims
   └── Evidencia antes que afirmaciones

2. Verificaciones por capa:
   ├── Backend: pytest tests
   ├── Frontend: npm test / npm run lint
   ├── Security: grep para secrets/passwords
   └── Integration: curl health endpoints

3. Comandos de verificación Jobbot:
   ├── Backend: cd api && python -m pytest tests/ -v
   ├── Frontend: cd dashboard && npm run lint && npm test
   ├── Security: grep -r "password|secret|token" --include="*.py" api/
   └── Health: curl http://localhost:8000/health/ready

4. Si algo falla:
   └── NO cometer → arreglar primero
       └── Re-loop hasta que todo pase
```

**Skills**:
- `verification-before-completion` → Obligatorio
- `review` → Para revisión final de código

**Comandos**:
```bash
# Backend
cd api && python -m pytest tests/ -v --tb=short

# Frontend
cd dashboard && npm run lint && npm run build

# Security
grep -rn "password\|secret\|token" --include="*.py" api/ | grep -v ".pyc"

# Health check
curl -s http://localhost:8000/health/ready | jq .
```

---

### Fase 5: Integración Workspace (MCPs)
**Trigger**: Tareas que requieren Google Workspace

```
1. Google Sheets (gws-sheets):
   ├── Exportar datos de Jobbot → Sheets
   ├── Sync user lists desde Sheets
   └── Recipe: collect-form-responses

2. Google Docs (gws-docs):
   ├── Generar reportes automáticos
   ├── Documentación técnica
   └── Recipe: create-doc-from-template

3. Google Calendar (gws-calendar):
   ├── Agendar entrevistas
   ├── Recordatorios de scraping
   └── Recipe: schedule-recurring-event

4. Gmail (gws-gmail):
   ├── Notificaciones de jobs
   ├── Alertas de sistema
   └── Recipe: email-drive-link

5. Google Drive (gws-drive):
   ├── Backup de CVs generados
   ├── Exportar datos de usuarios
   └── Recipe: bulk-download-folder

6. Google Tasks (gws-tasks):
   ├── Sync con tasks/todo.md
   ├── Task lists por feature
   └── Recipe: create-task-list
```

**MCPs más usados en Jobbot**:
| MCP | Caso de Uso | Frecuencia |
|-----|-------------|------------|
| `gws-sheets` | Exportar métricas | Alta |
| `gws-gmail` | Notificaciones | Alta |
| `gws-calendar` | Agendar entrevistas | Media |
| `gws-docs` | Reportes semanales | Media |
| `gws-drive` | Backup de datos | Baja |
| `gws-tasks` | Sync tareas | Baja |

---

### Fase 6: Documentación (Post-Implementación)
**Trigger**: Después de cambio significativo

```
1. Actualizar tasks/lessons.md:
   ├── Problema
   ├── Concepto clave
   ├── Solución
   ├── Trade-offs
   ├── Verificación
   └── Lección aprendida

2. Actualizar tasks/architecture_log.md:
   ├── Skills/workflows usados
   ├── Decisiones de diseño
   └── Resultado obtenido

3. Para cambios de infraestructura:
   └── Actualizar README.md
       ├── Nuevos comandos
       ├── Variables de entorno
       └── Estructura de archivos

4. Para UI changes:
   └── Capturar screenshots
       └── Actualizar documentación visual
```

**Skills**:
- Ninguna requerida (manual)

---

### Fase 7: Deploy (CI/CD)
**Trigger**: Merge a develop/main

```
1. GitHub Actions ejecuta automáticamente:
   ├── test-backend (pytest + coverage)
   ├── test-frontend (lint + test + build)
   ├── security-scan (bandit + pip-audit)
   ├── integration-tests (health checks)
   └── deploy-staging/production

2. Verificar deployment patterns:
   ├── Health endpoints responden
   ├── Cache funciona (Redis)
   ├── Workers Celery activos
   └── Webhooks de pagos operativos

3. Post-deploy verification:
   ├── curl https://api.jobbot.ar/health/ready
   ├── Verificar logs de errores
   ├── Monitoring de métricas
   └── Alertas si algo falla
```

**Skills**:
- `deployment-patterns` → Para configurar CI/CD
- `security-review` → Pre-deploy audit

---

## 🔀 Workflows por Tipo de Tarea

### Nueva Feature
```
session_start → writing-plans → [backend-patterns|frontend-patterns]
→ verification-before-completion → review → lessons.md → deploy
```

### Bug Fix
```
session_start → Explore (find bug) → python-patterns → systematic-debugging
→ verification-before-completion → review → lessons.md → deploy
```

### Code Review
```
session_start → review (/review <pr>) → security-review (si aplica)
→ feedback → iterate → verification → merge
```

### Database Changes
```
session_start → postgres-patterns → writing-plans → implementation
→ verification (tests + migration check) → lessons.md → deploy
```

### UI/UX Changes
```
session_start → ui-ux-pro-max → frontend-patterns → implementation
→ core-web-vitals (si performance) → verification → review → deploy
```

### Security Changes
```
session_start → security-review → implementation → verification
→ security-scan (CI) → review → deploy
```

### Google Workspace Integration
```
session_start → [gws-sheets|gws-gmail|gws-calendar] → implementation
→ verification → testing → deploy
```

---

## 🧩 Matriz de Decisiones Rápidas

| Si necesito... | Entonces uso... |
|----------------|----------------|
| Planificar feature | `writing-plans` |
| Buscar en codebase | Agente `Explore` |
| Escribir Python | `python-patterns` |
| Escribir FastAPI | `backend-patterns` |
| Escribir React | `frontend-patterns` |
| Cambiar DB | `postgres-patterns` |
| Revisar código | `review` |
| Verificar antes de commit | `verification-before-completion` |
| Revisar seguridad | `security-review` |
| Diseñar UI/UX | `ui-ux-pro-max` |
| Optimizar performance | `core-web-vitals` |
| Deploy/CI-CD | `deployment-patterns` |
| Debugear algo | Agente `general-purpose` |
| Automatizar Workspace | MCPs `gws-*` |
| Tarea recurrente | `loop` |

---

## ⚡ Atajos de Comandos

### Comandos Slash
```
/review <pr>          → Revisar PR
/qc-helper <question> → Ayuda Qwen Code
/plan <requirement>   → Modo planificación (PROHIBIDO código)
/loop <schedule>      → Tarea recurrente
```

### Comandos Shell (Jobbot)
```bash
# Backend
cd api && python -m pytest tests/ -v
cd api && python -m pytest tests/ --cov=. --cov-report=xml

# Frontend
cd dashboard && npm run dev
cd dashboard && npm run lint && npm test && npm run build

# Bot
cd job_bot && python bot.py

# Workers
python workers/run_worker.py worker -q scraping

# Docker
docker-compose up -d
docker-compose -f docker-compose.prod.yml up -d

# Health
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/metrics

# Security
grep -rn "password\|secret\|token" --include="*.py" api/
bandit -r api/ -ll
```

---

## 🎓 Ejemplo de Flujo Completo

### Escenario: Agregar endpoint de estadísticas de usuario

**1. Session Start**
```
- Leer tasks/todo.md → "Agregar stats endpoint"
- Leer tasks/lessons.md → Lecciones previas de endpoints
- git status → En rama main
- git checkout -b feat/user-stats-endpoint
```

**2. Planificación**
```
Skill: api-design + backend-patterns
Plan:
  1. Crear ruta GET /users/stats
  2. Query: count jobs aplicados, avg match score, etc.
  3. Response: JSON con métricas
  4. Tests: unit + integration
Actualizar tasks/todo.md
```

**3. Implementación**
```
Skill: backend-patterns + postgres-patterns
Agente: Explore para encontrar patterns similares
Código:
  - api/routes/users.py → Agregar @router.get("/stats")
  - Tests: api/tests/test_user_stats.py
```

**4. Verificación**
```
Skill: verification-before-completion
Comandos:
  cd api && python -m pytest tests/test_user_stats.py -v
  curl http://localhost:8000/users/stats
  grep -n "password\|secret" api/routes/users.py
```

**5. Review**
```
Skill: review
/review api/routes/users.py
```

**6. Documentación**
```
Actualizar tasks/lessons.md con:
  - Problema: Necesidad de métricas de usuario
  - Solución: Endpoint GET /users/stats
  - Trade-off: Query complexity vs performance
  - Lección: Usar índices en DB para stats
```

**7. Deploy**
```
git add .
git commit -m "feat(users): add user statistics endpoint"
git push origin feat/user-stats-endpoint
# Crear PR → GitHub Actions ejecuta CI/CD
```

---

## 📊 Métricas del Workflow

| Métrica | Target | Cómo Medir |
|---------|--------|------------|
| Planificación antes de código | 100% | Verificar tasks/todo.md |
| Tests pasan pre-commit | 100% | `verification-before-completion` |
| Lecciones documentadas | 100% post-cambio | tasks/lessons.md |
| Security review en auth | 100% | `security-review` |
| Code review en PRs | 100% | `/review` |
| CI/CD verde | 100% | GitHub Actions status |

---

## 🚨 Anti-Patrones (Qué EVITAR)

| Anti-Patrón | Consecuencia | Solución |
|------------|--------------|----------|
| Escribir código sin plan | Retrabajo, bugs | Usar `writing-plans` |
| No verificar antes de commit | Breaks prod | `verification-before-completion` |
| No documentar lecciones | Repetir errores | `tasks/lessons.md` |
| Commits gigantes | Difficult review | Commits <200 líneas |
| Ignorar security review | Vulnerabilidades | `security-review` siempre en auth |
| No usar agentes en tareas complejas | Context overflow | Delegar a `general-purpose` |
| Mock data en prod | Confusión | Verificar endpoints reales |

---

## ✅ Checklist de Inicio Rápido

Para empezar a trabajar en Jobbot AHORA:

```bash
# 1. Verificar estado
git status && git log --oneline -3

# 2. Leer contexto
cat tasks/todo.md
cat tasks/lessons.md

# 3. Levantar servicios
docker-compose up -d

# 4. Verificar health
curl http://localhost:8000/health/ready

# 5. Crear rama (si nueva feature)
git checkout -b feat/nombre

# 6. Seleccionar skill según tarea
# → python-patterns, backend-patterns, etc.

# 7. Trabajar → verificar → commit → push → PR
```

---

*Este workflow se actualiza con cada lección aprendida. Última revisión: 2026-04-10*
