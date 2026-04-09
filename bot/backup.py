"""
backup.py - Sistema de backup para la base de datos de JobBot

Backup manual: copiar .db file con timestamp
Backup automático: cron/daily backup
Compresión con gzip
Verificación de integridad (checksum)
Rotación de backups (mantener últimos N backups)
Restore desde backup
Listar backups disponibles

Uso:
    python -m job_bot.backup create      # Backup manual
    python -m job_bot.backup list        # Listar backups
    python -m job_bot.backup restore <id> # Restore backup
    python -m job_bot.backup verify <id> # Verificar integridad
    python -m job_bot.backup auto        # Setup cron automático
"""

import os
import sys
import gzip
import shutil
import hashlib
import sqlite3
import logging
import argparse
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict

# schedule es opcional para backups automáticos
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

# Imports tolerantes al contexto de ejecución
try:
    import config
except ImportError:
    from job_bot import config

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Información de un backup."""
    id: str
    timestamp: str
    original_file: str
    backup_file: str
    compressed: bool
    size_bytes: int
    checksum: str
    status: str  # 'ok', 'corrupted', 'unknown'
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupInfo':
        return cls(**data)


class BackupManager:
    """Gestiona backups de la base de datos SQLite."""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        backup_dir: Optional[str] = None,
        retention_days: Optional[int] = None,
        compress: Optional[bool] = None,
    ):
        """
        Inicializa el gestor de backups.
        
        Args:
            db_path: Ruta al archivo .db (default: config.DATABASE_PATH)
            backup_dir: Directorio para backups (default: config.BACKUP_DIR)
            retention_days: Días a retener (default: config.BACKUP_RETENTION_DAYS)
            compress: Comprimir backups (default: config.BACKUP_COMPRESS)
        """
        # Usar valores de config si no se proporcionan
        self.db_path = db_path or getattr(config, 'DATABASE_PATH', 'job_bot.db')
        self.backup_dir = Path(backup_dir or getattr(config, 'BACKUP_DIR', 'backups'))
        self.retention_days = retention_days or getattr(config, 'BACKUP_RETENTION_DAYS', 30)
        self.compress = compress if compress is not None else getattr(config, 'BACKUP_COMPRESS', True)
        
        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de metadatos
        self.metadata_file = self.backup_dir / 'backups_metadata.json'
        
        logger.info(f"BackupManager inicializado: db={self.db_path}, dir={self.backup_dir}")
    
    def _generate_backup_id(self) -> str:
        """Genera un ID único para el backup basado en timestamp."""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calcula el checksum SHA256 de un archivo."""
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _verify_sqlite_integrity(self, filepath: Path) -> Tuple[bool, str]:
        """
        Verifica la integridad de un archivo SQLite.
        
        Returns:
            Tuple[bool, str]: (es_válido, mensaje)
        """
        try:
            conn = sqlite3.connect(str(filepath))
            cursor = conn.cursor()
            
            # Verificar integridad con PRAGMA integrity_check
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0] == 'ok':
                return True, 'SQLite integrity check passed'
            else:
                return False, f'SQLite integrity check failed: {result}'
                
        except Exception as e:
            return False, f'Error verificando SQLite: {str(e)}'
    
    def create_backup(self, manual: bool = False) -> BackupInfo:
        """
        Crea un nuevo backup de la base de datos.
        
        Args:
            manual: True si es un backup manual (incluye 'manual' en el nombre)
            
        Returns:
            BackupInfo con la información del backup creado
        """
        backup_id = self._generate_backup_id()
        if manual:
            backup_id = f"{backup_id}_manual"
        
        # Archivos de destino
        backup_filename = f"job_bot_backup_{backup_id}"
        original_backup_path = self.backup_dir / f"{backup_filename}.db"
        
        if self.compress:
            final_backup_path = self.backup_dir / f"{backup_filename}.db.gz"
        else:
            final_backup_path = original_backup_path
        
        logger.info(f"Creando backup: {backup_id}")
        
        try:
            # 1. Copiar archivo original
            shutil.copy2(self.db_path, original_backup_path)
            
            # 2. Verificar integridad del original
            is_valid, msg = self._verify_sqlite_integrity(original_backup_path)
            if not is_valid:
                original_backup_path.unlink()
                raise RuntimeError(f"Integridad del DB comprometida: {msg}")
            
            # 3. Comprimir si es necesario
            if self.compress:
                with open(original_backup_path, 'rb') as f_in:
                    with gzip.open(final_backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                original_backup_path.unlink()  # Eliminar archivo no comprimido
            
            # 4. Calcular checksum
            checksum = self._calculate_checksum(final_backup_path)
            
            # 5. Crear registro
            backup_info = BackupInfo(
                id=backup_id,
                timestamp=datetime.now().isoformat(),
                original_file=str(self.db_path),
                backup_file=str(final_backup_path),
                compressed=self.compress,
                size_bytes=final_backup_path.stat().st_size,
                checksum=checksum,
                status='ok',
                created_at=datetime.now().isoformat()
            )
            
            # 6. Guardar metadatos
            self._save_metadata(backup_info)
            
            # 7. Rotar backups antiguos
            self._rotate_backups()
            
            logger.info(f"Backup creado exitosamente: {backup_id} ({backup_info.size_bytes} bytes)")
            
            return backup_info
            
        except Exception as e:
            # Limpieza en caso de error
            if original_backup_path.exists():
                original_backup_path.unlink()
            if final_backup_path.exists():
                final_backup_path.unlink()
            logger.error(f"Error creando backup: {e}")
            raise
    
    def _save_metadata(self, backup_info: BackupInfo):
        """Guarda los metadatos del backup en el archivo JSON."""
        metadata = self._load_metadata()
        metadata[backup_info.id] = backup_info.to_dict()
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_metadata(self) -> Dict:
        """Carga los metadatos de backups desde el archivo JSON."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando metadatos: {e}")
            return {}
    
    def list_backups(self) -> List[BackupInfo]:
        """
        Lista todos los backups disponibles ordenados por fecha (más reciente primero).
        
        Returns:
            Lista de BackupInfo
        """
        metadata = self._load_metadata()
        backups = []
        
        for backup_id, data in metadata.items():
            # Verificar que el archivo existe
            backup_file = Path(data['backup_file'])
            if backup_file.exists():
                backups.append(BackupInfo.from_dict(data))
            else:
                # Marcar como desconocido si el archivo no existe
                data['status'] = 'unknown'
                backups.append(BackupInfo.from_dict(data))
        
        # Ordenar por timestamp descendente
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups
    
    def _rotate_backups(self):
        """
        Elimina backups más antiguos según la política de retención.
        Mantiene al menos el backup más reciente.
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        backups = self.list_backups()
        
        if len(backups) <= 1:
            return  # Mantener al menos un backup
        
        deleted_count = 0
        for backup in backups[1:]:  # Saltar el más reciente
            backup_date = datetime.fromisoformat(backup.timestamp)
            
            if backup_date < cutoff_date:
                backup_file = Path(backup.backup_file)
                if backup_file.exists():
                    backup_file.unlink()
                    logger.info(f"Eliminado backup antiguo: {backup.id}")
                    deleted_count += 1
                
                # Eliminar metadatos
                metadata = self._load_metadata()
                if backup.id in metadata:
                    del metadata[backup.id]
                    with open(self.metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
        
        if deleted_count > 0:
            logger.info(f"Rotación completada: {deleted_count} backups eliminados")
    
    def verify_backup(self, backup_id: str) -> Tuple[bool, str]:
        """
        Verifica la integridad de un backup específico.
        
        Args:
            backup_id: ID del backup a verificar
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje)
        """
        metadata = self._load_metadata()
        
        if backup_id not in metadata:
            return False, f"Backup no encontrado: {backup_id}"
        
        backup_data = metadata[backup_id]
        backup_file = Path(backup_data['backup_file'])
        
        if not backup_file.exists():
            return False, f"Archivo de backup no encontrado: {backup_file}"
        
        # 1. Verificar checksum
        current_checksum = self._calculate_checksum(backup_file)
        stored_checksum = backup_data['checksum']
        
        if current_checksum != stored_checksum:
            return False, f"Checksum mismatch: esperado {stored_checksum}, actual {current_checksum}"
        
        # 2. Descomprimir temporalmente si es necesario y verificar SQLite
        temp_file = None
        try:
            if backup_data['compressed']:
                temp_file = self.backup_dir / f"temp_verify_{backup_id}.db"
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                is_valid, msg = self._verify_sqlite_integrity(temp_file)
            else:
                is_valid, msg = self._verify_sqlite_integrity(backup_file)
            
            # Actualizar estado en metadatos
            metadata[backup_id]['status'] = 'ok' if is_valid else 'corrupted'
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return is_valid, msg
            
        finally:
            if temp_file and temp_file.exists():
                temp_file.unlink()
    
    def restore_backup(self, backup_id: str, target_path: Optional[str] = None) -> str:
        """
        Restaura un backup a la ubicación especificada.
        
        Args:
            backup_id: ID del backup a restaurar
            target_path: Ruta destino (default: db_path original)
            
        Returns:
            Ruta donde se restauró el backup
        """
        target = Path(target_path or self.db_path)
        metadata = self._load_metadata()
        
        if backup_id not in metadata:
            raise ValueError(f"Backup no encontrado: {backup_id}")
        
        backup_data = metadata[backup_id]
        backup_file = Path(backup_data['backup_file'])
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Archivo de backup no encontrado: {backup_file}")
        
        # Verificar integridad antes de restaurar
        is_valid, msg = self.verify_backup(backup_id)
        if not is_valid:
            raise RuntimeError(f"Backup corrupto, no se puede restaurar: {msg}")
        
        logger.info(f"Restaurando backup {backup_id} a {target}")
        
        # Crear backup de seguridad del DB actual antes de restaurar
        if target.exists():
            safety_backup = target.parent / f"{target.name}.safety.{self._generate_backup_id()}"
            shutil.copy2(target, safety_backup)
            logger.info(f"Backup de seguridad creado: {safety_backup}")
        
        # Restaurar
        if backup_data['compressed']:
            with gzip.open(backup_file, 'rb') as f_in:
                with open(target, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_file, target)
        
        logger.info(f"Backup restaurado exitosamente: {target}")
        return str(target)
    
    def get_backup_by_id(self, backup_id: str) -> Optional[BackupInfo]:
        """Obtiene la información de un backup específico."""
        metadata = self._load_metadata()
        if backup_id in metadata:
            return BackupInfo.from_dict(metadata[backup_id])
        return None
    
    def auto_backup_job(self):
        """Job para ejecución automática (para usar con schedule)."""
        try:
            logger.info("Ejecutando backup automático programado")
            backup_info = self.create_backup(manual=False)
            logger.info(f"Backup automático completado: {backup_info.id}")
            return backup_info
        except Exception as e:
            logger.error(f"Error en backup automático: {e}")
            raise


def setup_auto_backup(schedule_time: str = "02:00"):
    """
    Configura el backup automático diario.
    
    Args:
        schedule_time: Hora en formato "HH:MM" para ejecutar el backup
        
    Returns:
        Función scheduler o None si schedule no está disponible
    """
    if not SCHEDULE_AVAILABLE:
        logger.error("❌ La librería 'schedule' no está instalada. Instalá con: pip install schedule")
        return None
    
    manager = BackupManager()
    
    # Parsear hora
    try:
        hour, minute = map(int, schedule_time.split(':'))
    except ValueError:
        logger.error(f"Formato de hora inválido: {schedule_time}. Use HH:MM")
        return None
    
    # Programar job
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(manager.auto_backup_job)
    
    logger.info(f"Backup automático configurado para las {schedule_time}")
    
    # Loop para mantener el scheduler corriendo
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    return run_scheduler


def format_backup_list(backups: List[BackupInfo]) -> str:
    """Formatea la lista de backups para mostrar al usuario."""
    if not backups:
        return "No hay backups disponibles."
    
    lines = ["📦 Backups disponibles:", ""]
    
    for i, backup in enumerate(backups, 1):
        # Parsear timestamp
        try:
            dt = datetime.fromisoformat(backup.timestamp)
            date_str = dt.strftime('%Y-%m-%d %H:%M')
        except:
            date_str = backup.timestamp
        
        # Formatear tamaño
        size_mb = backup.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{backup.size_bytes} bytes"
        
        # Indicador de compresión
        compression = "🗜️" if backup.compressed else "📄"
        
        # Estado
        status_icon = "✅" if backup.status == 'ok' else "⚠️" if backup.status == 'corrupted' else "❓"
        
        lines.append(f"{i}. `{backup.id}`")
        lines.append(f"   {compression} {date_str} | {size_str} | {status_icon} {backup.status}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """CLI para gestión de backups."""
    parser = argparse.ArgumentParser(
        description='JobBot Backup System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m job_bot.backup create              # Crear backup manual
  python -m job_bot.backup list                # Listar backups
  python -m job_bot.backup restore 20241201_143022  # Restaurar backup
  python -m job_bot.backup verify 20241201_143022   # Verificar backup
  python -m job_bot.backup auto --time 02:00   # Iniciar backup automático
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # create
    create_parser = subparsers.add_parser('create', help='Crear backup manual')
    
    # list
    list_parser = subparsers.add_parser('list', help='Listar backups disponibles')
    
    # restore
    restore_parser = subparsers.add_parser('restore', help='Restaurar backup')
    restore_parser.add_argument('backup_id', help='ID del backup a restaurar')
    restore_parser.add_argument('--target', '-t', help='Ruta destino (default: DB original)')
    
    # verify
    verify_parser = subparsers.add_parser('verify', help='Verificar integridad de backup')
    verify_parser.add_argument('backup_id', help='ID del backup a verificar')
    
    # auto
    auto_parser = subparsers.add_parser('auto', help='Iniciar backup automático')
    auto_parser.add_argument('--time', default='02:00', help='Hora diaria (HH:MM, default: 02:00)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = BackupManager()
    
    try:
        if args.command == 'create':
            backup_info = manager.create_backup(manual=True)
            print(f"✅ Backup creado exitosamente")
            print(f"   ID: {backup_info.id}")
            print(f"   Archivo: {backup_info.backup_file}")
            print(f"   Tamaño: {backup_info.size_bytes} bytes")
            print(f"   Checksum: {backup_info.checksum}")
        
        elif args.command == 'list':
            backups = manager.list_backups()
            print(format_backup_list(backups))
        
        elif args.command == 'restore':
            target = manager.restore_backup(args.backup_id, args.target)
            print(f"✅ Backup restaurado exitosamente: {target}")
        
        elif args.command == 'verify':
            is_valid, msg = manager.verify_backup(args.backup_id)
            if is_valid:
                print(f"✅ {msg}")
            else:
                print(f"❌ {msg}")
                sys.exit(1)
        
        elif args.command == 'auto':
            print(f"🔄 Iniciando backup automático (hora: {args.time})...")
            print("Presiona Ctrl+C para detener")
            scheduler_func = setup_auto_backup(args.time)
            scheduler_func()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
