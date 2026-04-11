# 📚 Lessons Learned — Jobbot

> Actualizado según `work_policy.md` después de cada corrección o aprendizaje nuevo.
> Formato: "Para evitar [X], hacer [Y]."

## Sesión: 2026-04-10 (Workflow Global con Skills, Agentes y MCPs)

### 📚 Clase del Profesor — Orquestación Perfecta de Recursos

#### 🎯 Problema
Tenía skills, agentes y MCPs disponibles pero no había un workflow global que integrara todos los recursos de forma coherente. Cada sesión empezaba desde cero sin referenciar el catálogo completo.

#### 🧠 Concepto Clave
"Tool Selection is Architecture": La diferencia entre un dev eficiente y uno que pierde tiempo no es el conocimiento, sino saber QUÉ herramienta usar CUÁNDO. Un workflow documentado elimina la ambigüedad y acelera la ejecución.

#### 🔬 La Solución
1. **GLOBAL_WORKFLOW.md**: 7 fases (Session Start → Planificación → Implementación → Verificación → MCPs → Documentación → Deploy)
2. **Matriz de decisiones**: Tabla rápida de "si necesito X → uso Y"
3. **Workflows por tipo de tarea**: Nueva feature, bug fix, code review, DB changes, UI changes, security changes
4. **Quick reference card**: Para consulta rápida sin leer todo el doc
5. **Integración de MCPs**: Fase 5 dedicada a Google Workspace (Docs, Sheets, Gmail, Calendar, Drive, Tasks)

#### ⚖️ Trade-offs
- **Documentación vs Acción**: 30 min de documentación ahorra horas de búsqueda futura.
- **Flexibilidad vs Estructura**: El workflow es guía, no camisa de fuerza. Adaptar según contexto.

#### 🧪 Verificación
- Workflow referenced in `.agents/SKILL.md`
- Quick ref card para consultas rápidas
- Architecture log actualizado con decisión

#### 💡 Lección
**Para perder tiempo en cada sesión**:
1. Crear un workflow global documentado ANTES de empezar a codear
2. Incluir matriz de decisiones para selección rápida de herramientas
3. Documentar anti-patrones para evitar errores conocidos
4. Actualizar con cada nueva lección aprendida

---

## Sesión: 2026-04-09 (Fase 3: Hardening Operativo - Plan Final Implementation)

### 📚 Clase del Profesor — De "Funcional" a "Resiliente"

#### 🎯 Problema
El producto funciona pero no escala: scraping bloquea requests, sin health checks para Kubernetes, no hay CI/CD, y cache está implementado pero no activo en todos los endpoints.

#### 🧠 Concepto Clave
"Operability is a Feature": Un producto launchable no es solo que funcione, es que sea observable, resiliente, y escalable horizontalmente.

#### 🔬 La Solución
1. **Cache Activation**: Importar cache en `main.py`, agregar decorator a `/jobs/search`, configurar TTLs por tipo de dato
2. **Async Workers**: Celery + Redis broker, 4 colas por prioridad, retries con backoff exponencial
3. **Health Checks**: 3 endpoints (/health, /health/ready, /health/live) para Kubernetes/ALB readiness
4. **CI/CD**: GitHub Actions con 5 jobs (backend tests, security scan, frontend tests, integration, deploy)

#### ⚖️ Trade-offs
- **Celery vs In-process**: Añade complejidad operativa (Redis, workers) pero desacopla scraping de API requests
- **Cache TTL corto**: 5min para jobs = frescura vs performance. Ajustable por env.
- **GitHub Actions vs Jenkins**: Menos configurable pero cero mantenimiento de infraestructura CI

#### 🧪 Verificación
- `/health/ready` retorna 200 solo si PostgreSQL responde
- Workers: `python workers/run_worker.py worker -q scraping` procesa jobs
- CI: PR a `develop` ejecuta tests + security scan
- Cache: Redis hit/miss logs visible en debug mode

#### 💡 Lección
**Para evitar "funciona en mi máquina" y downtime en producción**:
1. Health checks explícitos: DB, cache, servicios externos antes de recibir tráfico
2. Async workers para cualquier operación >2s: evita timeouts y mejora UX
3. CI/CD desde el día 0: tests automatizados son más baratos que hotfixes
4. Observabilidad: metrics básicas (latency, errors, cache hit rate) antes de necesitarlas

---

## Sesión: 2026-04-09 (Fase 2: Producto Real End-to-End - Plan Final Implementation)

### 📚 Clase del Profesor — De "Demo Potente" a "Producto Real"

#### 🎯 Problema
El dashboard parecía tener mock data, el sistema de pagos parecía no estar conectado, y la landing no estaba clara si era funcional o un template default.

#### 🧠 Concepto Clave
"Real over Perfect": Un producto launchable no necesita 100 features; necesita 10 features que funcionen 100% real, conectadas end-to-end, sin humo.

#### 🔬 La Solución
1. **Auditar antes de asumir**: Revisar endpoints de API antes de asumir que faltaba integración. Resultado: Dashboard YA estaba conectado 100% a API real.
2. **Verificar webhooks**: Confirmar que `/webhook/stripe` y `/webhook/mercadopago` existían con signature verification HMAC.
3. **Documentar transparencia**: Landing page actualizada con badge "Controlled launch beta" - honestidad genera confianza.
4. **Eliminar duplicación**: Archivar `jobbot/`, `jobobt/`, `y/` - un solo árbol canónico (`api/`, `dashboard/`, `job_bot/`).

#### ⚖️ Trade-offs
- **Auditar vs Implementar**: 30 min de auditoría evitó re-implentar lo que ya funcionaba.
- **Transparencia vs Marketing**: "Controlled launch beta" puede parecer menos impresionante que "¡Lanzamos!", pero previene churn de usuarios con expectativas incorrectas.

#### 🧪 Verificación
- Dashboard carga datos reales de PostgreSQL (no mock)
- Checkout crea sessions en Stripe/MercadoPago
- Webhooks actualizan plan automáticamente
- Landing es Next.js real con SSR, no HTML estático

#### 💡 Lección
**Para evitar re-trabajo y confusión**: 
1. Auditar el estado actual antes de asumir qué falta.
2. Documentar explícitamente qué está "real" vs "beta" vs "no disponible".
3. Consolidar estructura: un solo árbol canónico, eliminar duplicados.
4. Priorizar conexiones reales sobre polish cosmético.

---

## Sesión: 2026-04-09 (Fase 1: Contención y Verdad - Plan Final Implementation)

### 📚 Clase del Profesor — Security Hardening y Saneamiento de Repositorio

#### 🎯 Problema
El security audit identificó 3 issues críticos (CVSS 8.8-9.8): credenciales admin por defecto, JWT en localStorage, y secrets débiles en docker-compose. Además, el repo tenía directorios duplicados y PII no adecuadamente excluida.

#### 🧠 Concepto Clave
"Security by Default": En producción, los defaults DEBEN ser seguros. No puede existir un "fallback inseguro" que funcione si el admin olvida configurar una variable.

#### 🔬 La Solución
1. **C1 (Admin email default)**: Cambiar `or "admin@jobbot.com"` a `os.getenv("PRIMARY_ADMIN_EMAIL", "")` - si no está seteado, no hay admin por defecto.
2. **C2 (JWT storage)**: Confirmar que `api.ts` ya usa `credentials: "include"` y no almacena tokens en localStorage (httpOnly cookies manejadas por el proxy).
3. **C3 (Weak secrets)**: Eliminar default `-change-me-in-production` en docker-compose; el contenedor debe fallar si `JWT_SECRET_KEY` no está seteado.
4. **Sanitización**: Mover directorios duplicados a `archive/` y endurecer `.gitignore` para PII.
5. **PostgreSQL default**: Configurar `DATABASE_TYPE` para que en `APP_ENV=production` defaultee a `postgresql`, no a `sqlite`.

#### ⚖️ Trade-offs
- **Fail-secure vs Fail-functional**: Sin JWT_SECRET_KEY el servicio no arranca (fail-secure). Esto puede sorprender en despliegues nuevos, pero previene operar con seguridad comprometida.
- **SQLite como opción dev**: Mantenemos SQLite para desarrollo local (rápido, sin dependencias), pero NUNCA en producción.

#### 🧪 Verificación
- `grep -r "admin@jobbot.com" api/` → limpio
- `docker-compose.yml` → sin defaults inseguros
- `git status` → PII files not tracked
- `config.py` → producción defaultea a PostgreSQL

#### 💡 Lección
**Para evitar operar con seguridad comprometida por omisión**: 
1. Nunca usar defaults hardcodeados para credenciales, secrets, o database types en producción.
2. Hacer que la aplicación FALLE en startup si config crítica falta (fail-fast), en lugar de operar con valores inseguros.
3. Separar claramente config de desarrollo vs producción usando `APP_ENV` explícito.

---

## Sesión: 2026-03-14 (Upgrade a Producción)

### 📚 Clase del Profesor — Integración de IA y Escalabilidad
#### 🎯 Problema
Transformar un scraper local en un asistente personal de carrera funcional y atractivo.

#### 🧠 Concepto Clave
"IA-First Utility": El bot no solo entrega datos, sino que procesa la información para dar valor agregado (Match Score, Entrevistas, Cover Letters).

#### 🔬 La Solución
- Migración a **Groq (Llama 3.3)** para mayor velocidad y razonamiento en español.
- Implementación de **ConversationHandlers** específicos para flujos complejos como la entrevista.
- **Stats API** interna para desacoplar el estado del bot de la landing page.

#### ⚖️ Trade-offs
- **Regex vs JSON**: Usamos regex para parsear preguntas de la IA por simplicidad, pero un esquema JSON (Structured Output) sería más robusto a largo plazo.
- **SQLite**: Mantenemos SQLite por ahora por simplicidad, aunque limita el escalado horizontal.

#### 🧪 Verificación
- Pruebas manuales de `/entrevista` y `/carta`.
- Verificación de landing page en browser simulado y fetch de stats.

#### 💡 Lección
Para que un producto IT destaque, la **estética (UI)** y la **inteligencia aplicada (IA)** deben ir de la mano. Un backend potente sin una landing atractiva no genera confianza, y viceversa.

---

## Sesión: 2026-03-14 (Bootstrap)

### Lección 1: Modelo Operativo Global
**Contexto**: El proyecto no tenía estructura de gestión de tareas ni acceso documentado a los recursos globales del agente.

**Aprendido**: 
- Los recursos globales están en `C:\Users\ignac\.agents` y deben ser indexados al inicio de cada sesión.
- El agente debe consultar `work_policy.md`, `pr_policy.md` y `harvard_teacher.md` antes de comenzar cualquier tarea no trivial.
- **Para evitar olvidar recursos disponibles**: revisar el catálogo de 40 skills en `C:\Users\ignac\.agents\skills` al planificar una tarea.

### Lección 2: Estructura de Agentes
**Contexto**: El proyecto tenía un solo agente (`scouting-agent.md`) sin estructura formal.

**Aprendido**:
- Cada componente major del bot debería tener su propio agente especializado.
- **Para evitar lógica monolítica en el bot**: separar responsabilidades en agentes distintos (scouting, database, scheduler, notifications).

---

_Agregar nuevas lecciones en la parte superior, con la fecha de la sesión._
