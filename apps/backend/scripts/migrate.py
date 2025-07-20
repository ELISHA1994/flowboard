#!/usr/bin/env python3
"""
Database Migration Management Script

This script provides a safe and comprehensive way to manage database migrations
with proper checks, backups, and rollback capabilities.

Usage:
    python scripts/migrate.py status          # Show migration status
    python scripts/migrate.py upgrade         # Apply all pending migrations
    python scripts/migrate.py upgrade head    # Apply all migrations
    python scripts/migrate.py downgrade -1    # Rollback last migration
    python scripts/migrate.py test            # Test migrations (up and down)
    python scripts/migrate.py backup          # Create database backup
"""
import sys
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import argparse
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations with safety features"""
    
    def __init__(self):
        self.alembic_cfg = Config("alembic.ini")
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_current_revision(self) -> str:
        """Get current database revision"""
        try:
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "No revision found"
    
    def create_backup(self) -> Path:
        """Create database backup before migration"""
        if not settings.DATABASE_URL.startswith("sqlite"):
            logger.warning("Automatic backup only supported for SQLite. Please backup manually.")
            return None
        
        # Extract database file path
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return None
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{self.get_current_revision().replace(' ', '_')}.db"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def show_status(self):
        """Show current migration status"""
        print("\n=== Migration Status ===")
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"Database URL: {settings.DATABASE_URL}")
        print(f"Current revision: {self.get_current_revision()}")
        
        # Show pending migrations
        try:
            result = subprocess.run(
                ["alembic", "history", "-r", "current:"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                print("\nPending migrations:")
                print(result.stdout)
            else:
                print("\nNo pending migrations")
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
    
    def upgrade(self, revision: str = "head"):
        """Apply migrations with safety checks"""
        print(f"\n=== Upgrading to {revision} ===")
        
        # Safety checks
        if not self.test_connection():
            print("ERROR: Cannot connect to database")
            return False
        
        # Create backup for SQLite
        if settings.DATABASE_URL.startswith("sqlite"):
            backup_path = self.create_backup()
            if not backup_path and settings.is_production:
                print("ERROR: Failed to create backup in production")
                return False
        
        # Show what will be applied
        print("\nMigrations to be applied:")
        subprocess.run(["alembic", "history", "-r", f"current:{revision}"])
        
        # Confirm in production
        if settings.is_production:
            response = input("\nProceed with migration in PRODUCTION? (yes/no): ")
            if response.lower() != "yes":
                print("Migration cancelled")
                return False
        
        # Run migration
        try:
            command.upgrade(self.alembic_cfg, revision)
            print(f"\nSuccessfully upgraded to {revision}")
            return True
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if backup_path:
                print(f"\nRestore from backup: {backup_path}")
            return False
    
    def downgrade(self, revision: str):
        """Rollback migrations with safety checks"""
        print(f"\n=== Downgrading to {revision} ===")
        
        # Safety checks
        if not self.test_connection():
            print("ERROR: Cannot connect to database")
            return False
        
        # Create backup
        backup_path = self.create_backup()
        
        # Confirm in production
        if settings.is_production:
            response = input("\nProceed with downgrade in PRODUCTION? (yes/no): ")
            if response.lower() != "yes":
                print("Downgrade cancelled")
                return False
        
        # Run downgrade
        try:
            command.downgrade(self.alembic_cfg, revision)
            print(f"\nSuccessfully downgraded to {revision}")
            return True
        except Exception as e:
            logger.error(f"Downgrade failed: {e}")
            if backup_path:
                print(f"\nRestore from backup: {backup_path}")
            return False
    
    def test_migrations(self):
        """Test migrations by applying and rolling back"""
        print("\n=== Testing Migrations ===")
        
        if settings.is_production:
            print("ERROR: Cannot test migrations in production")
            return False
        
        # Ensure we're using test database
        os.environ["TESTING"] = "true"
        
        # Get current revision
        current = self.get_current_revision()
        
        # Test upgrade
        print("\nTesting upgrade to head...")
        if not self.upgrade("head"):
            print("ERROR: Upgrade test failed")
            return False
        
        # Test downgrade
        print("\nTesting downgrade to base...")
        if not self.downgrade("base"):
            print("ERROR: Downgrade test failed")
            return False
        
        # Restore to original state
        print(f"\nRestoring to original revision: {current}")
        if "No revision" not in current:
            self.upgrade(current.split()[0])
        
        print("\nMigration tests passed!")
        return True
    
    def create_migration(self, message: str):
        """Create a new migration"""
        try:
            command.revision(self.alembic_cfg, message=message, autogenerate=True)
            print(f"Created migration: {message}")
            
            # Show the generated migration
            result = subprocess.run(
                ["alembic", "show", "head"],
                capture_output=True,
                text=True
            )
            print(f"\nGenerated migration:\n{result.stdout}")
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument("command", choices=["status", "upgrade", "downgrade", "test", "backup", "create"],
                       help="Command to execute")
    parser.add_argument("revision", nargs="?", default=None,
                       help="Target revision (for upgrade/downgrade)")
    parser.add_argument("-m", "--message", help="Migration message (for create)")
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.command == "status":
        manager.show_status()
    elif args.command == "upgrade":
        manager.upgrade(args.revision or "head")
    elif args.command == "downgrade":
        if not args.revision:
            print("ERROR: Revision required for downgrade")
            sys.exit(1)
        manager.downgrade(args.revision)
    elif args.command == "test":
        if not manager.test_migrations():
            sys.exit(1)
    elif args.command == "backup":
        backup_path = manager.create_backup()
        if backup_path:
            print(f"Backup created: {backup_path}")
    elif args.command == "create":
        if not args.message:
            print("ERROR: Message required for create")
            sys.exit(1)
        manager.create_migration(args.message)


if __name__ == "__main__":
    main()