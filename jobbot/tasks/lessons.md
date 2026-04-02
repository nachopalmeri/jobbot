# 📚 Lessons Learned — Jobbot

> Actualizado según `work_policy.md` después de cada corrección o aprendizaje nuevo.
> Formato: "Para evitar [X], hacer [Y]."

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
