# Plan: fuentes consolidadas de búsqueda

**Fecha:** 2026-10-14
**Objetivo:** incorporar al repositorio las rutas nuevas de las capturas y consolidarlas con el flujo remoto existente, manteniendo una sola salida de búsqueda y distinguiendo fuentes automáticas, manuales y trabajo por tarea.

## Decisiones y límites

- Reusar las APIs públicas ya integradas (Get on Board, Remotive, Arbeitnow, Jobicy, Himalayas) y la deduplicación/filtros existentes.
- No agregar scraping, login automatizado ni llamadas a endpoints internos de Startups Argentina, Wellfound, UADE, LinkedIn u otros sitios sin API/feed/permiso comprobado.
- Registrar FirstJob, EmpleosIT, YC, StartupJobs, Vibe Coding/Vibehackers, Wellfound y Startups Argentina como rutas de descubrimiento manual verificables en fuente primaria.
- Outlier, Alignerr, DataAnnotation y Prolific van en carril separado de tareas remuneradas; elegibilidad, cantidad de tareas e ingresos no se presumen.
- Mantener prioridades del usuario: startups argentinas; part-time local afín; startups extranjeras part-time contratables desde Argentina; otros matches fuertes. Full-time sólo con match alto o sueldo competitivo.
- Preservar el directorio local no versionado `jobbot/` y no alterar archivos fuera del scope.

## Archivos y orden

1. `job_bot/tests/test_search_source_registry.py` y `job_bot/tests/test_search_queries.py`: probar clasificación de fuentes y cobertura de consultas (RED antes de código).
2. `job_bot/search_sources.py`: catálogo tipado de rutas, modo de acceso, alcance geográfico y grupo de búsqueda.
3. `job_bot/config.py`: ampliar de manera balanceada la taxonomía general incluyendo agentes/workflows, prompt engineering, RPA/automatización, soporte/redes, QA, trainee y startups/remoto.
4. `job_bot/README.md` y `docs/search-sources-superjunte.md`: explicar el superjunte, las fuentes automáticas vs. manuales/tareas y los límites de elegibilidad.

## Aceptación

- Las pruebas fallan primero por funcionalidad ausente y pasan después de la implementación.
- Catálogo incluye las fuentes de capturas y los proveedores remotos ya conectados, sin confundir contrataciones con microtareas.
- El flujo unificado conserva fuentes y sigue deduplicando/filtrando ubicación y antigüedad; las fuentes manuales no se ejecutan como scrapers.
- Las consultas siguen limitadas por el presupuesto configurado y representan todos los grupos acordados.
- No se instalan dependencias ni se modifica el estado externo.

## Validación

```powershell
python -m unittest job_bot.tests.test_search_source_registry job_bot.tests.test_search_queries -v
python -m unittest job_bot.tests.test_scraper job_bot.tests.test_search_mode -v
```

Detener el alcance de conectores si el proveedor requiere autenticación automatizada, evadir controles, pago nuevo o un permiso no comprobado.
