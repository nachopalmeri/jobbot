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
| Startups globales | Startups Argentina, Wellfound, Cosign, Y Combinator Jobs, Work at a Startup, Startup Jobs | Descubrimiento manual; validar país, seniority, modalidad y fecha en la fuente primaria. Cosign permite explorar roles en empresas recomendadas por su red; no se verificó API/feed público |
| Remoto integrado | Remotive, Arbeitnow, Jobicy, Himalayas; feeds RSS elegidos por el usuario | API/feed; resultados se consolidan en la lista de búsqueda y conservan la fuente |
| Índice y backfill | LinkedIn vía índice público, Google Jobs/SerpAPI, Active Jobs DB/JSearch, Twitter/X | Parcial u opcional; proveedores con costo sólo funcionan si están configurados y el uso está autorizado |
| Agregadores exploratorios | Vibe Coding Jobs, Vibehackers | Pistas solamente; validar vacante y ATS del empleador antes de contarla |
| Tareas de IA | Outlier, Alignerr, DataAnnotation, Prolific | Carril separado; disponibilidad, elegibilidad, cantidad de tareas y pagos pueden variar |
| Comunidad | Eventos de YC, Appgentina (eventos tech argentinos) | Networking, no vacantes |

## Límites de automatización

- No se scrapean Startups Argentina, Wellfound, LinkedIn, UADE ni otras páginas con login/controles sin API, feed o permiso comprobado. Su inclusión en el catálogo no implica que JobBot las rastree automáticamente.
- No se presentan cifras agregadas de agregadores como número de vacantes aptas.
- Outlier, Alignerr, DataAnnotation y Prolific no se etiquetan como empleo con horario/sueldo estable. Confirmar país y condiciones oficiales antes de registrarse o compartir datos.
- Las APIs remotas pueden devolver una vacante “remote” sin países elegibles claros; esas filas quedan con elegibilidad geográfica incierta hasta verificación.
- Ninguna integración envía postulaciones ni modifica perfiles externos.

## Protocolo de pasada diaria completa

La pasada diaria debe recorrer **todos los IDs del catálogo**, no sólo las APIs. En cada ejecución:

1. Consultar las fuentes `automated_api`, `search_index` y `user_feed` con los conectores ya disponibles, sin activar proveedores pagos ni credenciales nuevas.
2. Revisar cada fuente `manual` en su página pública o fuente primaria; si requiere sesión, usar únicamente la sesión que ya esté abierta y no enviar datos ni postulaciones.
3. Priorizar Startups Argentina; después roles part-time argentinos relacionados con sistemas/IA/QA/dev; luego startups extranjeras part-time que acepten Argentina; finalmente otros matches altos. Para full-time exigir match claramente alto o sueldo competitivo.
4. Usar OpenCode con un candidato gratuito verificado para dividir búsquedas independientes. Si OpenCode y los canales directos no logran verificar una fuente, continuar en Brave del usuario cuando esté accesible.
5. Registrar por fuente: consultada con resultados, consultada sin resultados, bloqueada (motivo), o no aplicable. No llamar “completa” a la pasada si queda una fuente sin verificar.
6. Verificar vacantes en el empleador/ATS, elegibilidad desde Argentina, modalidad y seniority; conservar URL de origen y fecha original de publicación. Deduplicar y ordenar por match.
7. Mantener separadas las oportunidades de empleo de las plataformas de tareas (Outlier, Alignerr, DataAnnotation, Prolific) y los eventos de networking (YC Events, Appgentina).
8. **Siempre finalizar en Notion:** actualizar el tablero correspondiente sin duplicados, con match descendente, fuente, fecha original de publicación y fecha de alta. Si no hubo oportunidades nuevas, registrar la cobertura en el seguimiento existente; si Notion o el destino no están accesibles, informar el bloqueo y no declarar la actualización como realizada.

El recorrido cubre las fuentes laborales visibles en las capturas del usuario (incluidas UADE, LinkedIn, Bumeran/Indeed/Computrabajo, FirstJob, Empleos IT, Get on Board, Wellfound, YC, Vibe Coding Jobs, Vibehackers, Cosign y las plataformas de tareas). Marcadores que son perfiles individuales, credenciales o un aviso puntual no se tratan como portales/fuentes generales.

## Cómo extenderlo

Antes de sumar un scraper: buscar API/feed/ATS público documentado, revisar términos/robots y límites, probar una muestra pequeña, conservar enlace de aplicación y fecha original, y añadir tests con fixtures. Si sólo hay acceso manual permitido, agregar la ruta al catálogo con `access="manual"`; no imitar sesión autenticada ni llamar endpoints internos.
