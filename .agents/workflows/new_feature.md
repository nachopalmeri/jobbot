---
description: Flujo completo de desarrollo de una nueva feature en jobbot
---
# // turbo-all

# Workflow: Nueva Feature en Jobbot

Seguir este flujo para CUALQUIER feature nueva. Usa los recursos globales para cada paso.

---

## Paso 1 — Planificación

**Skill**: `writing-plans` (`C:/Users/ignac/.agents/skills/writing-plans/SKILL.md`)

1. Actualizar `tasks/todo.md` con items verificables de la feature.
2. Crear rama temática:
   ```bash
   git checkout -b feat/nombre-descriptivo
   ```
3. Si la feature es compleja (múltiples archivos), usar `subagent-driven-development`.

---

## Paso 2 — Implementación

**Workflow**: `work_policy.md` (Plan → Ejecuta → Verifica → Documenta)

- Commits chicos y temáticos: `feat(scope): descripción`
- Push cada 1–3 commits (ver `pr_policy.md`)
- Si hay bugs durante la implementación → `systematic-debugging`

---

## Paso 3 — Tests

**Skill**: `test-driven-development`

```bash
cd job_bot
python -m pytest test_*.py -v
```

Nunca marcar "done" sin que los tests pasen.

---

## Paso 4 — Enseñanza (Harvard Teacher)

**Workflow**: `harvard_teacher.md`

Después de cualquier cambio significativo, agregar a `tasks/lessons.md`:
```markdown
## 📚 Clase del Profesor — [Título del Cambio]
### 🎯 Problema
### 🧠 Concepto Clave
### 🔬 La Solución
### ⚖️ Trade-offs
### 🧪 Verificación
### 💡 Lección
```

---

## Paso 5 — Verificación Final

**Skill**: `verification-before-completion`

- [ ] Tests pasan
- [ ] Bot corre sin errores
- [ ] No hay prints de debug ni código comentado
- [ ] Diff es legible

---

## Paso 6 — PR

**Workflow**: `pr_policy.md` + `finishing-a-development-branch`

```bash
git push origin feat/nombre-descriptivo
# Abrir PR en GitHub con título: feat: descripción
```

Si la PR > 200 líneas → usar `pr_code_review.md` con 3 subagentes paralelos.

---

## Paso 7 — Registro

Agregar entrada en `tasks/architecture_log.md` con:
- Skills/workflows usados
- Decisiones de diseño tomadas
- Resultado obtenido
