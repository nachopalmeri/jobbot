# Sistema de Backup de JobBot

Sistema completo de backup para la base de datos SQLite de JobBot con soporte para backups manuales, automáticos, compresión, verificación de integridad y rotación.

## Características

- **Backup Manual**: Crear backups bajo demanda
- **Backup Automático**: Programado diariamente mediante scheduler integrado
- **Compresión**: Soporte para compresión gzip (opcional)
- **Verificación de Integridad**: Checksums SHA256 + verificación SQLite
- **Rotación**: Eliminación automática de backups antiguos según retención configurada
- **Restore**: Restauración completa desde cualquier backup
- **Notificaciones**: Alertas al administrador vía Telegram

## Configuración

Variables de entorno (añadir a `.env`):

```bash
# Directorio donde guardar backups (default: backups)
BACKUP_DIR=backups

# Días de retención de backups (default: 30)
BACKUP_RETENTION_DAYS=30

# Hora diaria para backup automático, formato 24h (default: 02:00)
BACKUP_SCHEDULE=02:00

# Habilitar compresión gzip (default: true)
BACKUP_COMPRESS=true

# Telegram ID del admin para notificaciones (default: 0 = deshabilitado)
BACKUP_ADMIN_USER_ID=123456789
```

## Uso CLI

### Crear backup manual
```bash
python -m job_bot.backup create
```

### Listar backups disponibles
```bash
python -m job_bot.backup list
```

### Verificar integridad de un backup
```bash
python -m job_bot.backup verify 20241201_143022_manual
```

### Restaurar backup
```bash
# Restaurar al DB original
python -m job_bot.backup restore 20241201_143022_manual

# Restaurar a una ubicación específica
python -m job_bot.backup restore 20241201_143022_manual --target /path/to/restore.db
```

### Backup automático (modo daemon)
```bash
python -m job_bot.backup auto --time 02:00
```

## Comandos del Bot (Admin)

El comando `/backup` está disponible solo para el usuario admin configurado:

```
/backup              # Listar backups
/backup create       # Crear backup manual
/backup restore ID   # Restaurar backup específico
/backup verify ID     # Verificar integridad
```

## Estructura de Archivos

```
backups/
├── job_bot_backup_YYYYMMDD_HHMMSS.db.gz     # Backup comprimido
├── job_bot_backup_YYYYMMDD_HHMMSS_manual.db.gz  # Backup manual
└── backups_metadata.json                     # Metadatos de backups
```

## Metadatos

Cada backup almacena metadatos en `backups_metadata.json`:

```json
{
  "20241201_143022_manual": {
    "id": "20241201_143022_manual",
    "timestamp": "2024-12-01T14:30:22.123456",
    "original_file": "job_bot.db",
    "backup_file": "backups/job_bot_backup_20241201_143022_manual.db.gz",
    "compressed": true,
    "size_bytes": 1234567,
    "checksum": "sha256_hash",
    "status": "ok",
    "created_at": "2024-12-01T14:30:22.123456"
  }
}
```

## Integración con Scheduler

El sistema de backup está integrado con el scheduler del bot. Cuando el bot se inicia, el scheduler verifica periódicamente si es hora de ejecutar el backup automático (según `BACKUP_SCHEDULE`).

El scheduler:
1. Ejecuta el backup en la hora configurada
2. Notifica al admin si está configurado
3. Notifica errores si ocurren
4. Mantiene un log de todas las operaciones

## Tests

El sistema incluye tests unitarios completos:

```bash
# Desde el directorio jobbot/
python -m unittest job_bot.tests.test_backup -v
```

Tests incluidos:
- `test_backup_creation`: Creación de backups
- `test_backup_listing`: Listado de backups
- `test_backup_integrity_verification`: Verificación de integridad
- `test_backup_restore`: Restauración de backups
- `test_backup_rotation`: Rotación de backups antiguos
- `test_uncompressed_backup`: Backups sin compresión
- `test_corrupted_backup_detection`: Detección de corrupción
- `test_nonexistent_backup`: Manejo de IDs inexistentes
- `test_backup_metadata_persistence`: Persistencia de metadatos
- `test_sqlite_integrity_check`: Verificación SQLite PRAGMA

## Seguridad

- **Backup de seguridad**: Antes de restaurar, se crea automáticamente un backup de seguridad del DB actual
- **Verificación de checksum**: Cada backup tiene un checksum SHA256 para detectar corrupción
- **Verificación SQLite**: Se ejecuta `PRAGMA integrity_check` en cada backup
- **Autenticación**: El comando `/backup` del bot solo funciona para el admin configurado

## Troubleshooting

### Error "No module named 'schedule'"
Instalar dependencia:
```bash
pip install schedule
```

### Error al restaurar: "Backup corrupto"
Verificar integridad antes de restaurar:
```bash
python -m job_bot.backup verify <backup_id>
```

### Backups no se crean automáticamente
Verificar:
1. `BACKUP_SCHEDULE` está configurado correctamente (HH:MM)
2. El directorio `BACKUP_DIR` tiene permisos de escritura
3. Revisar logs del bot para errores

### No se reciben notificaciones de backup
Verificar que `BACKUP_ADMIN_USER_ID` está configurado con el Telegram ID correcto del admin.

## Archivos Implementados

- `job_bot/backup.py` — Sistema de backup completo
- `job_bot/tests/test_backup.py` — Tests unitarios
- `config.py` — Configuración de backup (BACKUP_* variables)
- `bot.py` — Comando `/backup` y integración con scheduler
- `requirements.txt` — Dependencia `schedule`
