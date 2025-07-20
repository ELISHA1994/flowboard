#!/usr/bin/env python3
"""
Script to set up the test database for PostgreSQL.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parents[1]))

from scripts.setup_postgres import create_database
from app.core.config import settings

# Ensure we're using test database
os.environ["TESTING"] = "True"

def main():
    """Set up test database and run migrations."""
    print("Setting up test database...")
    
    # Create test database
    if not create_database(settings.TEST_DB_NAME):
        return 1
    
    # Run migrations on test database
    print("\nRunning migrations on test database...")
    os.system("TESTING=True alembic upgrade head")
    
    print("\n✅ Test database setup complete!")
    return 0

if __name__ == "__main__":
    exit(main())