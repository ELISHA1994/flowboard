"""
Migration script to add categories and tags support to the task management system.

This migration:
1. Creates categories table
2. Creates tags table  
3. Creates association tables for many-to-many relationships
4. Updates user relationships

Run with: python migrations/002_add_categories_and_tags.py
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """Add categories and tags tables"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tasks.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id VARCHAR PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                color VARCHAR(7),
                icon VARCHAR(50),
                user_id VARCHAR NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("✓ Created categories table")
        
        # Create index on user_id for categories
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_categories_user_id 
            ON categories(user_id)
        """)
        print("✓ Created index on categories.user_id")
        
        # Create tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id VARCHAR PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                color VARCHAR(7) NOT NULL DEFAULT '#808080',
                user_id VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("✓ Created tags table")
        
        # Create index on user_id for tags
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_user_id 
            ON tags(user_id)
        """)
        print("✓ Created index on tags.user_id")
        
        # Create task_categories association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_categories (
                task_id VARCHAR NOT NULL,
                category_id VARCHAR NOT NULL,
                PRIMARY KEY (task_id, category_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        print("✓ Created task_categories association table")
        
        # Create task_tags association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id VARCHAR NOT NULL,
                tag_id VARCHAR NOT NULL,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        print("✓ Created task_tags association table")
        
        # Commit the changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print("\nCurrent tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running migration: Add categories and tags support...")
    migrate()