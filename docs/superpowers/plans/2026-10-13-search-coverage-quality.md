# Plan de mejora: cobertura y calidad de búsqueda de oportunidades

**Fecha:** 2026-10-13
**Estado:** mejora de búsqueda implementada en la rama; quedan conectores y evaluación de calidad que requieren fuentes autorizadas y muestra etiquetada.

## Estado de implementación

- [x] Quitar caché insegura del endpoint personalizado: el decorador tenía una firma incompatible y podía omitir la contabilización de cuotas. La ruta vuelve a validar e incrementar el uso en cada llamada; cachear resultados públicos queda para una capa separada.
- [x] Corregir el contrato del worker para deduplicación y registro de avisos usando `is_job_seen(telegram_id, url)` y `mark_job_seen(telegram_id, job)`.
- [x] Incluir los RSS personales también en búsqueda API y deduplicar esos resultados con el resto, conservando todas las fuentes asociadas.
- [x] Añadir ocho consultas generales balanceadas más hasta dos keywords personales; las consultas manuales explícitas no expanden la taxonomía. El backfill premium se limita a una consulta por búsqueda para no multiplicar cuotas/costos.
- [x] Integrar Get on Board mediante su API pública: Argentina, dos consultas acotadas de jornada parcial, máximo de resultados por página, atribución de fuente y moneda desconocida sin inventarla.
- [x] Clasificar jornada desde texto y `employment_type`, ordenar part-time antes de otras jornadas en API y alertas, y conservar salary ranges estructurados sin asignarles moneda no documentada.
- [x] Canonicalizar URLs para deduplicar tracking común sin alterar el enlace de postulación original; parsear fecha ISO/date-only, RFC822 y epoch s/ms, marcando fechas desconocidas.
- [x] Marcar elegibilidad geográfica confirmada vs. incierta; lo remoto sin país queda visible como incierto y no se presenta como contratación confirmada desde Argentina.
- [x] Mantener roles exploratorios en búsqueda API amplia, agregando nivel de relevancia al perfil en lugar de excluir todo lo que no coincida literalmente.
- [x] En búsqueda API, filtrar RSS personalizado también por ubicación/antigüedad y exponer métricas por fuente (estado, cantidad, duración, hora de control); limitar logs a tipo de error para evitar filtrar secretos de URL.
- [x] Para full-time sin salario reportado, exigir score de coincidencia claramente alto (85/95); exponer estado de salario, fecha y ubicación en cada resultado.
- [ ] Fuentes de StartupsArgentinas y startups globales: investigación completada, conectores adicionales pendientes por límites de acceso documentados abajo.
- [ ] Línea base de precisión/recall, ranking de roles con muestra etiquetada, métricas persistidas/históricas y política de sueldo competitivo siguen pendientes.

## Investigación de fuentes delegada a OpenCode

**Worker:** `opencode/muse-spark-1.3-contributor-free` (Muse Spark 1.3, candidato gratuito verificado en el catálogo local). **Resultado:** investigación web de solo lectura y verificación de las APIs; el worker no editó archivos. **Costo/uso reportado:** no disponible en la salida del CLI.

- **StartupsArgentinas (reverificado 14/10/2026):** el dominio correcto es `startupsargentina.com`, con directorio público, sitemap y fichas públicas; no confundir con `startups.com.ar`. OpenCode verificó 420 avisos listados y no encontró fichas con fecha de publicación 13–14/10. No se usó `/api/` (robots lo prohíbe), login ni endpoints internos; no se halló API/MCP/feed oficial documentado ni permiso explícito de scraping masivo. Se mantiene sin conector automático hasta permiso/API/feed. Ver [empleos](https://www.startupsargentina.com/empleos), [robots](https://www.startupsargentina.com/robots.txt), [sitemap](https://www.startupsargentina.com/sitemap.xml) y [términos](https://www.startupsargentina.com/terminos).
- **Get on Board:** docs [API](https://www.getonbrd.com/api-doc.html), [OpenAPI](https://www.getonbrd.com/doc/openapi.yaml?v=2026-05-08-agent-docs), [guía de uso](https://www.getonbrd.com/help/what-can-i-do-with-get-on-board-s-api). Se verificó `GET /api/v0/search/jobs`, público sin autenticación, con `country_code`, `query`, `page` y `per_page`; la API permite buscar y mostrar avisos publicados. La cuota numérica no está documentada y los términos permiten throttling. El response no documenta moneda salarial; el código conserva la cifra con moneda `null`.
- **Startups extranjeras/ATS:** se encontraron avisos puntuales, pero no se implementó API pública genérica para Workable/Ashby/YC. Wellfound no se automatiza. El 14/10, el barrido buscó roles con fecha 13–14/10 y no verificó un match junior/trainee; Clara AI Growth Automation (11/10) y Jeeves AI/Forward Deployed (10/10) son anteriores y de seniority mayor.

La investigación cubrió páginas públicas verificables, no postulaciones ni perfiles autenticados. La evidencia completa fue devuelta por OpenCode en esta sesión; consultar esas URLs antes de ampliar conectores si sus condiciones de acceso pudieran haber cambiado.

## Objetivo

Mejorar JobBot para encontrar más oportunidades relevantes y actuales para Ignacio, priorizando la jornada part-time y sin limitar la búsqueda a su carrera. El orden de búsqueda y presentación acordado es: **1)** StartupsArgentinas; **2)** puestos part-time en Argentina de desarrollo, QA, IA, sistemas y afines; **3)** startups extranjeras part-time que contraten desde Argentina; **4)** otras oportunidades con buen match. Full-time se admite como excepción por match claramente alto o sueldo competitivo frente al mercado. Si no publica sueldo, solo incluir full-time cuando el match sea claramente alto y marcar “sueldo no informado”. Oportunidades remotas internacionales cuentan únicamente si aceptan contratar desde Argentina. Cada resultado debe conservar fuente, enlace de postulación y fechas con su nivel de certeza.

El éxito no se mide por la cantidad bruta de avisos: se mide por cobertura observable, oportunidades pertinentes que llegan al usuario, vigencia y deduplicación, manteniendo transparencia sobre por qué se incluyó o descartó cada resultado.

## Hallazgos que motivan el plan

- El endpoint tenía `@job_search_cache` en `api/routes/jobs.py:191`, mientras `job_search_key` exigía solo `query`, `location`, `limit` y `offset` (`api/core/cache.py:343`). La primera entrega eliminó el decorador de la ruta: además de la incompatibilidad, una respuesta cacheada habría omitido validación/consumo de cuota. Falta diseñar caché aislada para resultados públicos.
- `JobScraper.search_all` trunca las consultas a cinco (`job_bot/job_scraper.py:82`), aunque el generador de palabras clave puede producir más. La configuración inicial (`job_bot/config.py:74`) no cubre de forma sistemática las familias de roles que el usuario pidió.
- El flujo directo de búsqueda no parece consumir las fuentes RSS personalizadas que procesa el scheduler. Tampoco hay evidencia de conectores directos para UADE, startups o publicaciones públicas de LinkedIn; conviene verificar opciones públicas y términos antes de agregar fuentes.
- Los filtros de ubicación, antigüedad, experiencia y relevancia pueden excluir equivalencias o aceptar datos inciertos sin explicarlos (`job_bot/job_scraper.py:971`, `1150`, `1202`; `api/routes/jobs.py:111`, `215`).
- La deduplicación debe tolerar URLs con parámetros de tracking y conservar procedencia. Además, el worker tiene llamadas que no coinciden con la interfaz aparente del scraper/base (`workers/tasks.py:90`; `job_bot/database.py:949`, `958`), que deben verificarse con pruebas antes de confiar en alertas periódicas.
- La suite del venv sigue limitada por `pydantic_core` incompleto y Celery ausente; no instalar dependencias sin autorización. En el Python del sistema sí se validaron las suites API y del bot (detalle actualizado al avanzar las fases).

## Decisiones y límites

- Primero instrumentar y establecer una línea base; no aumentar fuentes a ciegas.
- Separar elegibilidad básica de ranking. Usar niveles de match explicables y no un umbral alto que silencie resultados potencialmente útiles.
- Tratar ubicación o fecha desconocidas como incertidumbre visible, no como coincidencia segura ni como descarte automático.
- Las búsquedas deben incluir equivalentes en español e inglés, y no usar la carrera como filtro excluyente.
- Aplicar el orden de prioridad acordado: StartupsArgentinas; part-time argentino en desarrollo/QA/IA/sistemas y afines; startups extranjeras part-time con contratación desde Argentina; resto de oportunidades con buen match.
- Part-time es la preferencia. Full-time es excepción si el match es claramente alto o hay sueldo competitivo frente al mercado. Si el sueldo no se publica, exigir match claramente alto y etiquetar explícitamente el sueldo como no informado.
- Una oportunidad internacional remota solo es elegible si la empresa admite contratación desde Argentina; si la elegibilidad no está clara, marcarla incierta y no tratarla como confirmada.
- Para LinkedIn, portales y sitios de empresas: usar APIs, feeds o páginas públicas permitidas. No automatizar sesiones autenticadas, eludir controles, ni scrapear contra términos de uso.
- No enviar postulaciones ni modificar Notion u otros servicios externos en esta fase.
- Preservar íntegramente las carpetas locales no versionadas `jobbot/` y cualquier cambio ajeno existente.
- La investigación de fuentes y herramientas externas, al comenzar implementación, se delega a OpenCode con candidatos gratuitos verificados; no duplicar esa investigación en paralelo desde el agente principal.

## Fases y dependencias

### 0. Baseline reproducible y contrato de búsqueda

1. Registrar estado limpio/sucio del repo, versión y comandos de ejecución; preservar `jobbot/`.
2. Reproducir el endpoint con todos sus parámetros, revisar el wrapper de caché y fijar pruebas que fallen ante la incompatibilidad.
3. Definir una muestra de avisos etiquetados por familia, ubicación/modalidad, vigencia y relevancia, junto con métricas iniciales.

**Aceptación:** se puede distinguir error de proveedor, resultado descartado por filtro, duplicado y cero coincidencias legítimas; la línea base incluye conteos por fuente y categoría.

### 1. Corregir confiabilidad de API y worker

1. [x] Quitar la caché de la ruta de usuario hasta moverla a la capa de respuestas públicas; probar que cada solicitud sigue validando e incrementando cuota.
2. [x] Corregir el flujo de “visto/notificado” del worker con interfaces reales de scraper/base y prueba de idempotencia.
3. [x] Añadir pruebas de ruta y procesamiento, preservando pruebas restantes de aislamiento cuando se introduzca caché pública.

**Aceptación:** la búsqueda no falla por la firma del cache key; una consulta no devuelve datos de otro perfil o combinación de filtros; el worker procesa un aviso y lo marca una sola vez, sin error de firma.

### 2. Ampliar taxonomía y estrategia de consultas

1. [x] Crear una taxonomía común independiente de la carrera: part-time development, QA, IA/automatización/RPA, sistemas, trainee/pasantía/becario, análisis funcional, redes/soporte y startups remotas.
2. Añadir sinónimos, variantes locales y traducciones útiles; separar palabras de rol, nivel, tecnología y modalidad.
3. [x] Reemplazar el corte fijo de cinco por un lote configurado de hasta diez (ocho consultas generales + hasta dos personales) y limitar el backfill premium a una vez por búsqueda.
4. [x] Permitir búsqueda amplia sin carrera excluyente y mantener intacta una consulta manual explícita.

**Aceptación:** pruebas de parametrización prueban que cada familia aparece en el plan de consulta y que la diversidad se mantiene aunque existan más keywords que el límite por lote.

### 3. Ampliar fuentes con viabilidad y políticas comprobadas

1. [x] Investigar canales siguiendo el orden de prioridad acordado. StartupsArgentinas queda documentada como #1 pero sin automatización autorizada; el API de Get on Board queda como primer conector automatizado viable dentro del segundo grupo. UADE, ATS y publicaciones públicas requieren continuar su evaluación.
2. Delegar la investigación web de cobertura, acceso, restricciones, frescura y costo a OpenCode (solo modelos gratuitos verificados). Exigir URLs/evidencia, fecha de consulta y limitaciones; si el proveedor no está disponible, devolver el bloqueo sin cambiar a modelos pagos.
3. [x] Integrar el API oficial público de Get on Board con enlace de aviso y fuente preservados; no se implementó scraping de StartupsArgentinas ni Wellfound.
4. [x] Normalizar campos principales del API, jornada y datos salariales sin inventar moneda. Aún faltan métricas de salud por fuente.

**Aceptación:** cada adaptador tiene fixtures/pruebas; cada fuente reporta último éxito, latencia, cantidad obtenida y error; no se incorpora scraping que requiera login, evada controles o contradiga condiciones del sitio.

### 4. Hacer los filtros tolerantes y trazables

1. Ubicación: normalizar CABA/Ciudad Autónoma/Ciudad de Buenos Aires/AMBA y remoto; permitir “ubicación no informada” en una categoría separada; evitar coincidencias por substrings accidentales.
2. Fechas: parsear ISO con/sin hora, RFC822 y epoch segundos/milisegundos; distinguir publicación, primera detección y última observación. Fecha desconocida no equivale a recién publicada.
3. Experiencia: excluir seniority por título/requisito explícito; una mención aislada en el cuerpo no descarta automáticamente un puesto junior.
4. Tags y perfil: usar equivalencias y señales ponderadas en vez de exigir coincidencia literal exacta en todos los tags.
5. Duplicados: canonicalizar URL, retirar parámetros de tracking, comparar título/empresa/ubicación normalizados y conservar el origen múltiple y el mejor enlace directo.

**Aceptación:** fixtures cubren variantes, datos desconocidos y falsos positivos; cada descarte puede explicar su regla; una misma publicación replicada se muestra una vez con sus fuentes.

### 5. Ranking explicable y aprendizaje gradual

1. Separar reglas mínimas de elegibilidad de puntuación; sustituir el corte duro por grupos (fuerte, posible, exploratorio) con motivo del match y confianza. El orden por grupos respetará las cuatro prioridades definidas, sin permitir que el volumen de una fuente cambie silenciosamente ese orden.
2. Incorporar familia de rol, seniority, jornada, ubicación/contratabilidad desde Argentina, recencia y requisitos explícitos. Part-time gana prioridad; full-time solo entra por match claramente alto o sueldo competitivo de mercado. Sin sueldo publicado, la etiqueta de match alto es requisito y el salario queda como no informado. Evitar que un perfil escaso reciba puntaje base engañoso.
3. Guardar feedback interno ligero (descartar, guardar, postular) solo si ya existe soporte y el usuario lo puede inspeccionar; no entrenar automáticamente con señales ambiguas.
4. Ajustar pesos usando la muestra etiquetada, comparando precisión y recall en top 20, no por intuición o volumen.

**Aceptación:** un resultado explica al menos las señales positivas y las incertidumbres; se publica baseline y comparación antes/después en la muestra; no se sube un umbral sin demostrar su efecto.

### 6. Observabilidad, integración y rollout

1. Métricas estructuradas de fuente: intentos, avisos obtenidos, normalizados, duplicados, filtrados por causa, errores y antigüedad.
2. Probar en modo sombra y revisar muestras antes de alterar alertas visibles; activar fuentes por etapas con límites claros.
3. Documentar cómo añadir/desactivar una fuente y cómo diagnosticar cero resultados.

**Aceptación:** es posible explicar una búsqueda vacía sin inspeccionar logs crudos; los errores de fuentes quedan visibles; el modo anterior se puede recuperar sin pérdida de datos.

## Rutas de trabajo probables

- API/caché: `api/routes/jobs.py`, `api/core/cache.py`, `api/tests/`.
- Fuentes, keywords, filtros y normalización: `job_bot/config.py`, `job_bot/job_scraper.py`, `job_bot/database.py`, `job_bot/tests/`.
- Scheduler/worker y alertas: `job_bot/scheduler.py`, `workers/tasks.py`, pruebas asociadas.
- Documentación/telemetría: `docs/`, configuración de logging existente y reportes de búsqueda.

Confirmar rutas concretas durante cada fase; no ampliar carpetas o refactorizar frontend/dashboard salvo que una dependencia comprobada lo requiera.

## Validación

Comandos conocidos que ya ejecutan pruebas relevantes:

```powershell
.\.venv\Scripts\python.exe -m unittest job_bot.tests.test_scraper job_bot.tests.test_search_mode -v
```

Agregar y correr pruebas focalizadas para caché/ruta API y worker. Antes de elegir el comando de suite completa, confirmar el framework configurado y reparar el entorno de test de forma explícita; en la auditoría actual faltaba `pydantic_core` funcional para importar la API y `pytest` no estaba instalado. No ocultar esa limitación ni instalar dependencias sin autorización.

En cada fase: diff limitado a su alcance, estado Git para preservar cambios ajenos, pruebas afectadas y revisión de logs/secretos. No desplegar ni conectar sistemas externos durante la implementación sin autorización específica.

## Métricas y criterios de salida del proyecto

- Línea base y tendencia de `Recall@20`, `Precision@20`, porcentaje de resultados con URL directa y proporción duplicada.
- Cobertura por familia, fuente, remoto/local y nivel de incertidumbre.
- Cumplimiento del orden de prioridad (StartupsArgentinas → part-time argentino afín → startups extranjeras part-time elegibles → otros matches) y proporción de part-time vs. full-time por grupo.
- Elegibilidad internacional explícita desde Argentina; sueldo publicado/verificado frente al mercado o etiqueta “no informado”; full-time sin sueldo solo con match claramente alto.
- Antigüedad: publicación conocida vs. desconocida; latencia y disponibilidad de cada fuente.
- Cero errores silenciosos de API/worker y cero contaminación entre perfiles o filtros.
- Definir metas numéricas después de medir la línea base; no inventar porcentajes objetivo antes de contar con datos.

## Stop conditions

- Frenar un proveedor si exige pago, login automatizado o acceso no permitido; presentar alternativas públicas.
- Frenar cambios de ranking si no existe muestra etiquetada suficiente para medir regresiones.
- No continuar con API/worker si la prueba focalizada falla por el entorno sin identificar una ruta de validación confiable.
- No sobrescribir ni limpiar los directorios locales no versionados.
- Este documento no autoriza implementación, publicación, despliegue, cambios en Notion ni postulaciones.
