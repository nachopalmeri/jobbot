# 🚀 Jobbot — Quick Reference Card

> Workflow global con Skills, Agentes y MCPs

---

## 📞 ¿Qué Usar y Cuándo?

| Necesito | Herramienta | Cómo |
|----------|------------|------|
| Planificar | `writing-plans` | `/plan [descripción]` |
| Buscar código | Agente `Explore` | `agent: Explore` |
| Python code | `python-patterns` | Cargar skill |
| FastAPI routes | `backend-patterns` | Cargar skill |
| React/Next.js | `frontend-patterns` | Cargar skill |
| DB changes | `postgres-patterns` | Cargar skill |
| Security | `security-review` | Cargar skill (auth/inputs/secrets) |
| UI/UX | `ui-ux-pro-max` | Cargar skill |
| Code review | `review` | `/review <file>` o `/review <pr>` |
| Pre-commit | `verification-before-completion` | Cargar skill |
| Debug | Agente `general-purpose` | `agent: general-purpose` |
| Google Workspace | MCPs `gws-*` | Cargar skill específico |

---

## 🔄 7 Fases del Workflow

```
1. Session Start → Leer todo.md, lessons.md, git status
2. Planificación → writing-plans → NO código todavía
3. Implementación → Skill según contexto + agentes si complejo
4. Verificación → verification-before-completion → Tests SIEMPRE
5. MCPs (si aplica) → gws-sheets/gmail/calendar para integraciones
6. Documentación → lessons.md + architecture_log.md
7. Deploy → CI/CD automático en merge
```

---

## ⚡ Comandos Clave

```bash
# Tests
cd api && python -m pytest tests/ -v

# Security scan
grep -rn "password\|secret\|token" --include="*.py" api/

# Health check
curl http://localhost:8000/health/ready

# Docker
docker-compose up -d

# Git
git checkout -b feat/nombre
git commit -m "feat(scope): descripción"
git push origin feat/nombre
```

---

## 🚫 Nunca Hacer

- ❌ Escribir código sin plan
- ❌ Commit sin tests
- ❌ Auth sin security-review
- ❌ No documentar lecciones
- ❌ Commits >200 líneas

---

## ✅ Siempre Hacer

- ✅ Planificar primero
- ✅ Tests antes de commit
- ✅ Verificar con verification-before-completion
- ✅ Documentar en lessons.md
- ✅ Commits pequeños y temáticos

---

*Imprimir o mantener como referencia rápida*
