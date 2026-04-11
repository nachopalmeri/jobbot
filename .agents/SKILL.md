---
name: Jobbot Local Skill Override
description: Override local del modelo operativo global. Define selección de recursos, rutas de acceso al catálogo global y política de logging de arquitectura para el proyecto jobbot.
---

# 🤖 Jobbot — Modelo Operativo Local

Este archivo sobreescribe/extiende el modelo global de `C:\Users\ignac\.agents\SKILL.md`.

---

## DIRECTIVA PRINCIPAL (siempre activa)

1. **INDEXAR**: Al iniciar cualquier tarea, consultar los recursos globales:
   - Agentes: `C:/Users/ignac/.agents/` 
   - Skills: `C:/Users/ignac/.agents/skills/`
   - Workflows: `C:/Users/ignac/.agents/workflows/`

2. **SELECCIONAR**: Elegir el agente/skill/workflow adecuado según el contexto:
   - Bugs → `systematic-debugging`
   - Nuevas features → `writing-plans` + `subagent-driven-development`
   - PRs grandes → `pr_code_review.md` (3 subagentes paralelos)
   - DB / Supabase → `supabase-postgres-best-practices`
   - Frontend → `frontend-design`
   - Tests → `test-driven-development`
   - Finalizar rama → `finishing-a-development-branch`

3. **VALIDAR**: Antes de aplicar un recurso, verificar que sea pertinente al contexto del jobbot.

4. **REGISTRAR**: Loggear en `tasks/architecture_log.md` cada decisión de selección.

---

## Variables de Entorno (Rutas Globales)

```bash
AGENTS_DIR="C:/Users/ignac/.agents"
SKILLS_DIR="C:/Users/ignac/.agents/skills"
WORKFLOWS_DIR="C:/Users/ignac/.agents/workflows"
```

---

## Estructura del Proyecto

```
jobbot/
├── job_bot/
│   ├── agents/                # Agentes específicos del proyecto
│   │   └── scouting-agent.md
│   ├── bot.py
│   ├── job_scraper.py
│   ├── database.py
│   ├── scheduler.py
│   └── ...
├── tasks/                     # Gestión de tareas (obligatorio según work_policy)
│   ├── todo.md                # Checklist de la sesión actual
│   ├── lessons.md             # Lecciones aprendidas acumuladas
│   └── architecture_log.md   # Log de decisiones de arquitectura
├── .agents/
│   └── SKILL.md               # Este archivo
└── ...
```

---

## Agentes del Proyecto

| Agente | Archivo | Responsabilidad |
|--------|---------|----------------|
| `scouting-agent` | `job_bot/agents/scouting-agent.md` | Monitorear y ejecutar búsqueda de ofertas laborales |

---

## Skills Globales Más Relevantes para Jobbot

| Skill | Cuándo Usarla |
|-------|--------------|
| `subagent-driven-development` | Ejecutar planes con tareas independientes |
| `writing-plans` | Antes de cualquier feature nueva |
| `systematic-debugging` | Cuando algo falla en el bot o scraper |
| `test-driven-development` | Al escribir nuevas funciones |
| `supabase-postgres-best-practices` | Cambios en la DB |
| `verification-before-completion` | Antes de marcar cualquier tarea como done |
| `finishing-a-development-branch` | Al cerrar una feature branch |
| `requesting-code-review` | Antes de abrir una PR |

---

## Flujo de Trabajo para Jobbot

Ver `GLOBAL_WORKFLOW.md` en la raíz del proyecto para el workflow global completo con Skills, Agentes y MCPs.

Resumen rápido:
```
1. PLANIFICAR   → tasks/todo.md con items verificables
2. SELECCIONAR  → Skills/workflows del catálogo global según contexto
3. EJECUTAR     → Commits chicos y temáticos (ver pr_policy.md)
4. VERIFICAR    → verification-before-completion (tests, logs, diff)
5. DOCUMENTAR   → tasks/lessons.md + tasks/architecture_log.md
6. INTEGRAR     → MCPs (Google Workspace) si aplica
7. PR           → Branch temática, checklist, draft → ready
```
