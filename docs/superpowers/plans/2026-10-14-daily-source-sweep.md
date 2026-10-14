# Plan: pasada diaria completa de fuentes

**Fecha:** 2026-10-14
**Objetivo:** dejar configurada una pasada diaria que cubra todas las fuentes compartidas por Nacho, incluidas las de las capturas y Cosign, y que informe cobertura real sin presentar como consultadas las fuentes bloqueadas.

## Decisiones y límites

- El catálogo de `job_bot/search_sources.py` es la fuente de verdad; incluir eventos Appgentina como ecosistema/networking, no como vacantes.
- Ejecutar los proveedores API/feed públicos; revisar rutas manuales en fuente primaria y en Brave cuando sea necesario y esté disponible.
- Para investigación delegada, usar OpenCode con modelos gratuitos verificados. Si OpenCode y las vías directas no completan la consulta, probar Brave del usuario; no insistir en el mismo método fallido.
- No automatizar login, evadir controles ni postularse. Etiquetar cada fuente como consultada, sin novedades, bloqueada o fuera de cobertura y explicar por qué.
- Crear una tarea recurrente de Codex para una pasada diaria a las 09:00 (hora de Buenos Aires), en este chat/proyecto; dejar notificación sólo para hallazgos, bloqueo o acción requerida.
- Respetar `AGENTS.md`: commit y push de la rama actual; no hacer merge a `main`.

## Secuencia

1. Añadir una prueba que exija la cobertura de todas las fuentes visibles en las capturas, incluyendo Cosign y Appgentina Events.
2. Completar el catálogo y su documentación con clasificación/acceso correcto.
3. Validar tests específicos, diff y configuración del Git remoto/identidad antes de commit.
4. Configurar y verificar la tarea diaria persistente.
5. Commit y push de la rama; dejar integración a `main` para el director.

## Aceptación

- Todas las plataformas de oportunidades mostradas en las capturas están presentes en el catálogo y son distinguibles por tipo/acceso.
- Cosign figura como exploración manual; Appgentina como networking, no empleo.
- La pasada diaria incluye cada fuente, fuente primaria, país/jornada/seniority, fecha original, deduplicación y reporte explícito de cobertura/bloqueos.
- No se afirma cobertura completa si una fuente manual no se pudo revisar.
- Tests pasan, cambios se commitean y la rama se pushea sin merge a `main`.

## Verificación

```powershell
python -m pytest job_bot/tests/test_search_source_registry.py -q
git diff --check
```
