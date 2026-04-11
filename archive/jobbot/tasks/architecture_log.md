# 🏛️ Architecture Log — Jobbot

> Registro de decisiones de selección de recursos según la DIRECTIVA PRINCIPAL.
> Cada entrada documenta: fecha, tarea, recurso seleccionado y justificación.

---

## Formato de Entrada

```markdown
### [FECHA] — [TAREA]
- **Recurso seleccionado**: `nombre-del-recurso` (skill/workflow/agente)
- **Ruta**: `C:/Users/ignac/.agents/...`
- **Justificación**: Por qué fue pertinente en este contexto.
- **Resultado**: Qué se logró con su uso.
```

## Log

### 2026-03-14 — Escalamiento: Migración a Supabase (Postgres)

- **Recurso seleccionado**: `supabase-postgres-best-practices` (skill)
  - **Ruta**: `C:/Users/ignac/.agents/skills/supabase-postgres-best-practices/SKILL.md`
  - **Justificación**: Necesaria para garantizar un esquema eficiente y seguro en el paso a una base de datos distribuida/nube.
  - **Resultado**: Plan de migración diseñado con foco en performance (índices) y seguridad (RLS).

---

### 2026-03-14 — Update a Producción & IA (Simulador + Cartas)

- **Recurso seleccionado**: `new_feature.md` (workflow)
  - **Ruta**: `.agents/workflows/new_feature.md`
  - **Justificación**: Guía para la implementación cohesiva de múltiples funcionalidades relacionadas con IA y scrapping.
  - **Resultado**: Implementación exitosa de `/entrevista`, `/carta`, Himalayas API y Modality Filter.

- **Recurso seleccionado**: `writing-plans` (skill)
  - **Ruta**: `C:/Users/ignac/.agents/skills/writing-plans/SKILL.md`
  - **Justificación**: Utilizado conceptualmente para diseñar la lógica de feedback de la entrevista y el prompt engineering para Groq.
  - **Resultado**: Prompts robustos que garantizan feedback útil y calificaciones coherentes.

- **Recurso seleccionado**: `frontend-design` (skill)
  - **Ruta**: `C:/Users/ignac/.agents/skills/frontend-design/SKILL.md`
  - **Justificación**: Guía para el rediseño de la landing page con estética cyberpunk y dark mode.
  - **Resultado**: Landing page premium con CSS moderno y micro-animaciones.

- **Recurso seleccionado**: `systematic-debugging` (skill)
  - **Ruta**: `C:/Users/ignac/.agents/skills/systematic-debugging/SKILL.md`
  - **Justificación**: Aplicado para resolver problemas de importación y errores de regex en el parseo de preguntas de la IA.
  - **Resultado**: Bot estable y manejo de errores implementado en `cv_analyzer.py`.

---

### 2026-03-14 — Bootstrap del Modelo Operativo Global

- **Recurso seleccionado**: `work_policy.md` (workflow)
  - **Ruta**: `C:/Users/ignac/.agents/workflows/work_policy.md`
  - **Justificación**: Necesario como base de orquestación. Define el ciclo Plan→Ejecutar→Verificar→Documentar que rige toda sesión.
  - **Resultado**: Creación de `tasks/` con `todo.md`, `lessons.md` y `architecture_log.md`.

- **Recurso seleccionado**: `pr_policy.md` (workflow)
  - **Ruta**: `C:/Users/ignac/.agents/workflows/pr_policy.md`
  - **Justificación**: Establece el estándar de commits, push y PRs para mantener el historial limpio.
  - **Resultado**: Adoptado como política de commits para el proyecto.

- **Recurso seleccionado**: `harvard_teacher.md` (workflow)
  - **Ruta**: `C:/Users/ignac/.agents/workflows/harvard_teacher.md`
  - **Justificación**: Activa la enseñanza proactiva post-cambio significativo.
  - **Resultado**: Integrado en el flujo de trabajo local como paso 4 (ENSEÑAR).

- **Recurso seleccionado**: `agent-development` (skill)
  - **Ruta**: `C:/Users/ignac/.agents/skills/agent-development/SKILL.md`
  - **Justificación**: Guía de estructura y buenas prácticas para definir agentes del proyecto.
  - **Resultado**: Base para ampliar `job_bot/agents/` con nuevos agentes especializados.

---

_Agregar nuevas entradas en la parte superior, con la fecha de la sesión._
