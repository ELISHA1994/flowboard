# Database Migration Guide

This guide explains how to use the production-grade migration system powered by Alembic.

## Overview

The migration system provides:
- Automatic migration generation from model changes
- Safe migration execution with backups
- Multi-environment support (development, staging, production)
- Support for multiple database backends (SQLite, PostgreSQL, MySQL)
- Migration testing and rollback capabilities

## Quick Start

### 1. Check Migration Status
```bash
python scripts/migrate.py status
```

### 2. Create a New Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add new feature"

# Or create an empty migration
alembic revision -m "Custom migration"
```

### 3. Apply Migrations
```bash
# Apply all pending migrations
python scripts/migrate.py upgrade

# Or apply to a specific revision
python scripts/migrate.py upgrade <revision>
```

### 4. Rollback Migrations
```bash
# Rollback one migration
python scripts/migrate.py downgrade -1

# Rollback to specific revision
python scripts/migrate.py downgrade <revision>
```

## Advanced Usage

### Database Backups
```bash
# Create manual backup
python scripts/db_backup.py

# List backups
python scripts/db_backup.py --list

# Restore from backup
python scripts/db_backup.py --restore

# Clean old backups
python scripts/db_backup.py --clean
```

### Testing Migrations
```bash
# Test migrations (upgrade and downgrade)
python scripts/migrate.py test
```

### Migration Best Practices

1. **Always test migrations locally first**
   ```bash
   python scripts/migrate.py test
   ```

2. **Review auto-generated migrations**
   - Check the generated SQL
   - Ensure data migrations are safe
   - Add custom logic if needed

3. **Use helper functions for idempotent operations**
   ```python
   from alembic import op
   
   # Use these helpers in your migrations
   add_column_if_not_exists(table_name, column)
   drop_column_if_exists(table_name, column_name)
   create_index_if_not_exists(index_name, table_name, columns)
   drop_index_if_exists(index_name, table_name)
   ```

4. **Document your migrations**
   - Fill in the description section
   - Document safety considerations
   - Provide rollback instructions

## Environment Configuration

### Required Environment Variables
```bash
# Database connection
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Environment
ENVIRONMENT=development  # or staging, production

# Optional: Database pool settings for production
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### Database URLs by Backend
- SQLite: `sqlite:///./tasks.db`
- PostgreSQL: `postgresql://user:pass@host:5432/dbname`
- MySQL: `mysql://user:pass@host:3306/dbname`

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run migrations
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    ENVIRONMENT: production
  run: |
    python scripts/migrate.py upgrade
```

### Pre-deployment Checklist
1. ✓ Test migrations locally
2. ✓ Create database backup
3. ✓ Review migration in staging
4. ✓ Plan rollback strategy
5. ✓ Schedule maintenance window (if needed)

## Troubleshooting

### Common Issues

1. **Migration conflicts**
   ```bash
   # Check current state
   alembic current
   
   # Force to specific revision (use with caution)
   alembic stamp <revision>
   ```

2. **Failed migration**
   - Check logs for errors
   - Restore from backup if needed
   - Fix the migration and retry

3. **Missing dependencies**
   ```bash
   pip install alembic sqlalchemy
   ```

## Migration File Structure

```
alembic/
├── env.py              # Alembic environment config
├── script.py.mako      # Migration template
└── versions/           # Migration files
    └── 3cd3b4a03107_initial_baseline.py

scripts/
├── migrate.py          # Migration management
└── db_backup.py        # Backup utility
```

## Safety Features

1. **Automatic Backups**: SQLite databases are backed up before migrations
2. **Production Confirmations**: Requires explicit confirmation in production
3. **Rollback Support**: All migrations include downgrade methods
4. **Dry Run Mode**: Test migrations without applying changes
5. **Connection Testing**: Validates database connection before migrations

## Next Steps

1. Review existing manual migrations in `/migrations/`
2. Create new migrations as you add features
3. Set up CI/CD pipeline for automated migration testing
4. Configure monitoring for migration health

For more information, see the [Alembic documentation](https://alembic.sqlalchemy.org/).