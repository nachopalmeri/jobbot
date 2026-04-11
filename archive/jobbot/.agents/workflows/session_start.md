---
description: Inicio de sesión de trabajo — indexar recursos globales, revisar estado del proyecto y planificar la sesión
---

# Workflow: Session Start — Jobbot

Ejecutar este flujo al INICIO de cada sesión de trabajo con el agente.

---

## Paso 1 — Indexar Recursos Globales

Verificar disponibilidad de recursos:

```
AGENTS_DIR    = C:/Users/ignac/.agents
SKILLS_DIR    = C:/Users/ignac/.agents/skills
WORKFLOWS_DIR = C:/Users/ignac/.agents/workflows
```

Recursos disponibles:
- **4 Workflows**: `work_policy.md`, `pr_policy.md`, `harvard_teacher.md`, `pr_code_review.md`
- **40 Skills**: agent-development, systematic-debugging, subagent-driven-development, test-driven-development, supabase-postgres-best-practices, writing-plans, verification-before-completion, finishing-a-development-branch, requesting-code-review, frontend-design, y más.

---

## Paso 2 — Revisar Estado del Proyecto

1. Leer `tasks/todo.md` → ¿qué quedó pendiente?
2. Leer `tasks/lessons.md` → ¿qué aprendimos antes?
3. Revisar `tasks/architecture_log.md` → ¿qué decisiones ya se tomaron?

---

## Paso 3 — Ver Estado del Repositorio

```bash
git status
git log --oneline -10
```

---

## Paso 4 — Planificar la Sesión

1. Definir el objetivo claro de la sesión.
2. Seleccionar la skill/workflow apropiado del catálogo global.
3. Actualizar `tasks/todo.md` con los items verificables.
4. Registrar la selección en `tasks/architecture_log.md`.

---

## Paso 5 — Ejecutar

Seguir el flujo según el tipo de trabajo:
- Nueva feature → `.agents/workflows/new_feature.md`
- Bug fix → `systematic-debugging` skill
- Code review → `pr_code_review.md`
- DB changes → `supabase-postgres-best-practices` skill
