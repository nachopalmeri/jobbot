# Legacy Surfaces

El árbol canónico de producto y release es:

- `api/`
- `dashboard/`
- `job_bot/`

Todo lo demás debe tratarse como legado o histórico hasta que sea migrado o archivado.

## Directorios fuera del camino canónico

- `archive/jobbot/`
- `archive/jobobt/`
- `archive/y/`

## Regla operativa

- No usar esos directorios para claims de producto, deploy, pricing o debugging principal.
- No agregar features nuevas allí.
- No extender CI ni documentación activa usando esos paths.
- Si se necesita conservar material histórico, moverlo a una estrategia explícita de archivo.

## Excepción activa

- `job_bot/landing/` ya no se trata como legacy de deploy.
- Hoy funciona como la landing pública marketinera separada de la app.
