#!/usr/bin/env python3
"""
Migration script to add custom level labels to commission_settings table
Created: January 14, 2026
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    exit(1)

def migrate_level_labels():
    """Add label column to commission_settings table"""
    print("Starting migration: Adding label column to commission_settings...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if label column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='commission_settings' AND column_name='label'
        """)
        
        if cursor.fetchone():
            print("✓ Label column already exists. Migration not needed.")
            cursor.close()
            conn.close()
            return
        
        # Add label column
        print("Adding label column...")
        cursor.execute("""
            ALTER TABLE commission_settings 
            ADD COLUMN label VARCHAR(50)
        """)
        
        # Set default labels for existing rows
        print("Setting default labels for existing levels...")
        cursor.execute("""
            UPDATE commission_settings 
            SET label = 'Level ' || level::text
            WHERE label IS NULL
        """)
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("SELECT level, rate, label FROM commission_settings ORDER BY level")
        settings = cursor.fetchall()
        
        print("\n✓ Migration completed successfully!")
        print("\nCurrent commission settings:")
        print("┌───────┬─────────┬──────────┐")
        print("│ Level │ Rate    │ Label    │")
        print("├───────┼─────────┼──────────┤")
        for s in settings:
            rate_pct = float(s['rate']) * 100
            print(f"│   {s['level']}   │ {rate_pct:6.2f}% │ {s['label']:<8} │")
        print("└───────┴─────────┴──────────┘")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        exit(1)

if __name__ == '__main__':
    migrate_level_labels()
