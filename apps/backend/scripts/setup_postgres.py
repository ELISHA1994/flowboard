#!/usr/bin/env python3
"""
Script to set up PostgreSQL databases for the task management application.
"""
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "taskmanageruser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "taskmanagerpass")
DB_NAME = os.getenv("DB_NAME", "taskmanager")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "taskmanager_test")

def create_database(db_name):
    """Create a database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            )
            print(f"✅ Database '{db_name}' created successfully")
        else:
            print(f"ℹ️  Database '{db_name}' already exists")
            
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. The user has necessary permissions")
        print("3. The credentials in .env are correct")
        return False
    except Exception as e:
        print(f"❌ Error creating database '{db_name}': {e}")
        return False

def main():
    """Main function to set up databases."""
    print("Setting up PostgreSQL databases...")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print()
    
    # Test connection first
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres'
        )
        conn.close()
        print("✅ Successfully connected to PostgreSQL server")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL server: {e}")
        return 1
    
    # Create main database
    if not create_database(DB_NAME):
        return 1
        
    # Create test database
    if not create_database(TEST_DB_NAME):
        return 1
        
    print("\n✅ All databases set up successfully!")
    print(f"\nConnection strings:")
    print(f"Main: postgresql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Test: postgresql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}")
    
    return 0

if __name__ == "__main__":
    exit(main())