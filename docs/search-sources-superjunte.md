# Superjunte de búsqueda laboral

Actualizado: 2026-10-14.

## Qué combina JobBot hoy

`JobScraper.search_all` reúne las fuentes automatizadas habilitadas en una sola lista, conserva atribución de origen, deduplica resultados y filtra por ubicación/antigüedad. Actualmente incluye la API pública de Get on Board para consultas locales acotadas, Remotive, Arbeitnow, Jobicy, Himalayas y los feeds RSS configurados. LinkedIn vía índice/RSS y Twitter/X dependen de configuración/cobertura; Google Jobs y el backfill de proveedores premium dependen de credenciales, cuota y costo.

La taxonomía busca sin exigir una carrera específica: desarrollo, QA/testing, IA/IA generativa, automatización/RPA, agentes y workflows, prompt engineering, sistemas, análisis funcional, soporte/redes, trainee/pasantías/becas, startups y roles remotos. Las consultas generales siguen limitadas por `MAX_SEARCH_KEYWORDS`; se puede ampliar por configuración sin ejecutar búsquedas ilimitadas.

## Orden de prioridad

1. Startups argentinas.
2. Part-time en Argentina de desarrollo, QA, IA, sistemas y áreas afines.
3. Startups extranjeras part-time que confirmen contratación desde Argentina.
4. Otras oportunidades con match alto.

Full-time es excepcional: match claramente alto o sueldo competitivo. Si no hay sueldo publicado, debe indicarse como no informado y el match debe ser claramente alto. “Remote” sin países permitidos no confirma elegibilidad desde Argentina.

## Catálogo consolidado

El catálogo fuente de verdad para rutas y acceso está en [`job_bot/search_sources.py`](../job_bot/search_sources.py). Las fuentes se agrupan así:

| Carril | Rutas | Acceso actual |
|---|---|---|
| Startups Argentina | Startups Argentina; Startup Jobs Argentina | Revisión manual; verificar publicación y fecha en el aviso/empresa |
| Empleo local/primer empleo | UADE, FirstJob, Empleos IT, Indeed, Computrabajo, Bumeran, BecasIT, LinkedIn Jobs y publicaciones | Manual; UADE se consulta en sesión del usuario. Sin automatizar login ni eludir controles |
| Startups globales | Wellfound, Y Combinator Jobs, Work at a Startup | Descubrimiento manual; validar país, seniority, modalidad y fecha en la fuente primaria |
| Remoto integrado | Remotive, Arbeitnow, Jobicy, Himalayas; feeds RSS elegidos por el usuario | API/feed; resultados se consolidan en la lista de búsqueda y conservan la fuente |
| Índice y backfill | LinkedIn vía índice público, Google Jobs/SerpAPI, Active Jobs DB/JSearch, Twitter/X | Parcial u opcional; proveedores con costo sólo funcionan si están configurados y el uso está autorizado |
| Agregadores exploratorios | Vibe Coding Jobs, Vibehackers | Pistas solamente; validar vacante y ATS del empleador antes de contarla |
| Tareas de IA | Outlier, Alignerr, DataAnnotation, Prolific | Carril separado; disponibilidad, elegibilidad, cantidad de tareas y pagos pueden variar |
| Comunidad | Eventos de YC | Networking, no vacantes |

## Límites de automatización

- No se scrapean Startups Argentina, Wellfound, LinkedIn, UADE ni otras páginas con login/controles sin API, feed o permiso comprobado. Su inclusión en el catálogo no implica que JobBot las rastree automáticamente.
- No se presentan cifras agregadas de agregadores como número de vacantes aptas.
- Outlier, Alignerr, DataAnnotation y Prolific no se etiquetan como empleo con horario/sueldo estable. Confirmar país y condiciones oficiales antes de registrarse o compartir datos.
- Las APIs remotas pueden devolver una vacante “remote” sin países elegibles claros; esas filas quedan con elegibilidad geográfica incierta hasta verificación.
- Ninguna integración envía postulaciones ni modifica perfiles externos.

## Cómo extenderlo

Antes de sumar un scraper: buscar API/feed/ATS público documentado, revisar términos/robots y límites, probar una muestra pequeña, conservar enlace de aplicación y fecha original, y añadir tests con fixtures. Si sólo hay acceso manual permitido, agregar la ruta al catálogo con `access="manual"`; no imitar sesión autenticada ni llamar endpoints internos.
