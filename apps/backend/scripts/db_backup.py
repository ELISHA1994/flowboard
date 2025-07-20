#!/usr/bin/env python3
"""
Database Backup Utility

This script provides database backup functionality for different database backends.
Supports SQLite, PostgreSQL, and MySQL with compression and retention policies.

Usage:
    python scripts/db_backup.py             # Create backup
    python scripts/db_backup.py --list      # List backups
    python scripts/db_backup.py --clean     # Clean old backups
    python scripts/db_backup.py --restore   # Restore from backup
"""
import sys
import os
import subprocess
import shutil
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Database backup manager supporting multiple backends"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.retention_days = 30  # Keep backups for 30 days by default
        
    def get_backup_metadata(self) -> dict:
        """Load backup metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_backup_metadata(self, metadata: dict):
        """Save backup metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def create_backup_name(self, prefix: str = "backup") -> str:
        """Generate backup filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_type = self._get_db_type()
        return f"{prefix}_{db_type}_{settings.ENVIRONMENT}_{timestamp}"
    
    def _get_db_type(self) -> str:
        """Get database type from URL"""
        if settings.DATABASE_URL.startswith("sqlite"):
            return "sqlite"
        elif settings.DATABASE_URL.startswith("postgresql"):
            return "postgresql"
        elif settings.DATABASE_URL.startswith("mysql"):
            return "mysql"
        else:
            return "unknown"
    
    def backup_sqlite(self) -> Path:
        """Backup SQLite database"""
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        backup_name = self.create_backup_name()
        backup_path = self.backup_dir / f"{backup_name}.db"
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Compress the backup
        compressed_path = self.backup_dir / f"{backup_name}.db.gz"
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_path.unlink()
        
        return compressed_path
    
    def backup_postgresql(self) -> Path:
        """Backup PostgreSQL database"""
        # Parse connection URL
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        backup_name = self.create_backup_name()
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        # Build pg_dump command
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'pg_dump',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading /
            '-f', str(backup_path),
            '--verbose',
            '--clean',
            '--if-exists'
        ]
        
        # Run pg_dump
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")
        
        # Compress the backup
        compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_path.unlink()
        
        return compressed_path
    
    def backup_mysql(self) -> Path:
        """Backup MySQL database"""
        # Parse connection URL
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        backup_name = self.create_backup_name()
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        # Build mysqldump command
        cmd = [
            'mysqldump',
            f'-h{parsed.hostname}',
            f'-P{parsed.port or 3306}',
            f'-u{parsed.username}',
            f'-p{parsed.password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            parsed.path[1:],  # Database name
        ]
        
        # Run mysqldump
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"mysqldump failed: {result.stderr}")
        
        # Compress the backup
        compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_path.unlink()
        
        return compressed_path
    
    def create_backup(self) -> Path:
        """Create database backup based on database type"""
        logger.info(f"Creating backup for {settings.DATABASE_URL}")
        
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                backup_path = self.backup_sqlite()
            elif settings.DATABASE_URL.startswith("postgresql"):
                backup_path = self.backup_postgresql()
            elif settings.DATABASE_URL.startswith("mysql"):
                backup_path = self.backup_mysql()
            else:
                raise ValueError(f"Unsupported database type: {settings.DATABASE_URL}")
            
            # Save metadata
            metadata = self.get_backup_metadata()
            metadata[backup_path.name] = {
                "created_at": datetime.now(),
                "database_url": settings.DATABASE_URL,
                "environment": settings.ENVIRONMENT,
                "size_bytes": backup_path.stat().st_size,
                "compressed": True
            }
            self.save_backup_metadata(metadata)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def list_backups(self):
        """List all backups with metadata"""
        metadata = self.get_backup_metadata()
        
        if not metadata:
            print("No backups found")
            return
        
        print(f"\n{'Backup File':<50} {'Created':<20} {'Size':<10} {'Environment':<15}")
        print("-" * 95)
        
        for filename, info in sorted(metadata.items(), key=lambda x: x[1]['created_at'], reverse=True):
            backup_path = self.backup_dir / filename
            if backup_path.exists():
                created = datetime.fromisoformat(str(info['created_at'])).strftime("%Y-%m-%d %H:%M:%S")
                size = f"{info['size_bytes'] / 1024 / 1024:.1f} MB"
                env = info.get('environment', 'unknown')
                print(f"{filename:<50} {created:<20} {size:<10} {env:<15}")
    
    def clean_old_backups(self, retention_days: int = None):
        """Remove backups older than retention period"""
        if retention_days is None:
            retention_days = self.retention_days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        metadata = self.get_backup_metadata()
        removed_count = 0
        
        for filename, info in list(metadata.items()):
            created_at = datetime.fromisoformat(str(info['created_at']))
            if created_at < cutoff_date:
                backup_path = self.backup_dir / filename
                if backup_path.exists():
                    backup_path.unlink()
                    del metadata[filename]
                    removed_count += 1
                    logger.info(f"Removed old backup: {filename}")
        
        self.save_backup_metadata(metadata)
        print(f"Removed {removed_count} old backups")
    
    def restore_backup(self, backup_file: str = None):
        """Restore from backup (interactive)"""
        metadata = self.get_backup_metadata()
        
        if not backup_file:
            # Show available backups
            self.list_backups()
            backup_file = input("\nEnter backup filename to restore: ")
        
        if backup_file not in metadata:
            print(f"ERROR: Backup {backup_file} not found")
            return False
        
        backup_path = self.backup_dir / backup_file
        if not backup_path.exists():
            print(f"ERROR: Backup file {backup_path} does not exist")
            return False
        
        # Confirm restoration
        print(f"\nWARNING: This will replace the current database!")
        print(f"Backup: {backup_file}")
        print(f"Created: {metadata[backup_file]['created_at']}")
        response = input("\nProceed with restoration? (yes/no): ")
        
        if response.lower() != "yes":
            print("Restoration cancelled")
            return False
        
        # Perform restoration based on database type
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                self._restore_sqlite(backup_path)
            elif settings.DATABASE_URL.startswith("postgresql"):
                self._restore_postgresql(backup_path)
            elif settings.DATABASE_URL.startswith("mysql"):
                self._restore_mysql(backup_path)
            else:
                raise ValueError(f"Unsupported database type for restoration")
            
            print(f"Successfully restored from {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            return False
    
    def _restore_sqlite(self, backup_path: Path):
        """Restore SQLite database"""
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        # Decompress if needed
        if backup_path.suffix == '.gz':
            decompressed_path = backup_path.with_suffix('')
            with gzip.open(backup_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_path = decompressed_path
        
        # Replace database file
        shutil.copy2(backup_path, db_path)
        
        # Clean up decompressed file
        if backup_path.suffix != '.gz' and backup_path.name.endswith('.db'):
            backup_path.unlink()
    
    def _restore_postgresql(self, backup_path: Path):
        """Restore PostgreSQL database"""
        # Implementation depends on specific PostgreSQL setup
        raise NotImplementedError("PostgreSQL restoration not yet implemented")
    
    def _restore_mysql(self, backup_path: Path):
        """Restore MySQL database"""
        # Implementation depends on specific MySQL setup
        raise NotImplementedError("MySQL restoration not yet implemented")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database backup utility")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--clean", action="store_true", help="Clean old backups")
    parser.add_argument("--restore", nargs="?", const=True, help="Restore from backup")
    parser.add_argument("--retention", type=int, help="Retention period in days")
    
    args = parser.parse_args()
    
    backup_manager = DatabaseBackup()
    
    if args.list:
        backup_manager.list_backups()
    elif args.clean:
        backup_manager.clean_old_backups(args.retention)
    elif args.restore:
        if isinstance(args.restore, str):
            backup_manager.restore_backup(args.restore)
        else:
            backup_manager.restore_backup()
    else:
        # Default action: create backup
        try:
            backup_path = backup_manager.create_backup()
            print(f"Backup created: {backup_path}")
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()