#!/usr/bin/env python3
"""
Migration script to add enhanced task properties to the database.
This adds priority, dates, time tracking, and position fields to the tasks table.
"""

import sqlite3
from datetime import datetime

def run_migration():
    """Add new columns to the tasks table"""
    # Connect to the database
    conn = sqlite3.connect('./tasks.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations = []
        
        # Add priority column if it doesn't exist
        if 'priority' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN priority VARCHAR(10) DEFAULT 'medium' NOT NULL
            """)
        
        # Add date columns if they don't exist
        if 'due_date' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN due_date DATETIME
            """)
        
        if 'start_date' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN start_date DATETIME
            """)
            
        if 'completed_at' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN completed_at DATETIME
            """)
        
        # Add time tracking columns if they don't exist
        if 'estimated_hours' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN estimated_hours REAL
            """)
            
        if 'actual_hours' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN actual_hours REAL DEFAULT 0.0 NOT NULL
            """)
        
        # Add position column if it doesn't exist
        if 'position' not in columns:
            migrations.append("""
                ALTER TABLE tasks 
                ADD COLUMN position INTEGER DEFAULT 0 NOT NULL
            """)
        
        # Execute migrations
        for migration in migrations:
            print(f"Executing: {migration.strip()}")
            cursor.execute(migration)
        
        # Update existing tasks to have sequential positions
        if 'position' not in columns:
            cursor.execute("""
                SELECT id, user_id FROM tasks ORDER BY created_at
            """)
            tasks = cursor.fetchall()
            
            # Group by user and assign positions
            user_positions = {}
            for task_id, user_id in tasks:
                if user_id not in user_positions:
                    user_positions[user_id] = 0
                
                cursor.execute("""
                    UPDATE tasks SET position = ? WHERE id = ?
                """, (user_positions[user_id], task_id))
                
                user_positions[user_id] += 1
        
        # Create index on due_date for better query performance
        try:
            cursor.execute("""
                CREATE INDEX idx_tasks_due_date ON tasks(due_date)
            """)
            print("Created index on due_date")
        except sqlite3.OperationalError:
            print("Index on due_date already exists")
        
        # Commit changes
        conn.commit()
        print(f"\nMigration completed successfully! {len(migrations)} changes applied.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running migration: Add enhanced task properties...")
    run_migration()