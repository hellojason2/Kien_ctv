#!/usr/bin/env python3
"""
Migration script to add is_active column to commission_settings table
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

def migrate_commission_is_active():
    """Add is_active column to commission_settings table"""
    print("Starting migration: Adding is_active column to commission_settings...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if is_active column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='commission_settings' AND column_name='is_active'
        """)
        
        if cursor.fetchone():
            print("✓ is_active column already exists. Migration not needed.")
            cursor.close()
            conn.close()
            return
        
        # Add is_active column
        print("Adding is_active column...")
        cursor.execute("""
            ALTER TABLE commission_settings 
            ADD COLUMN is_active BOOLEAN DEFAULT TRUE
        """)
        
        # Set all existing levels to active by default
        print("Setting all existing levels to active...")
        cursor.execute("""
            UPDATE commission_settings 
            SET is_active = TRUE
            WHERE is_active IS NULL
        """)
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("SELECT level, rate, label, is_active FROM commission_settings ORDER BY level")
        settings = cursor.fetchall()
        
        print("\n✓ Migration completed successfully!")
        print("\nCurrent commission settings:")
        print("┌───────┬─────────┬──────────┬──────────┐")
        print("│ Level │ Rate    │ Label    │ Active   │")
        print("├───────┼─────────┼──────────┼──────────┤")
        for s in settings:
            rate_pct = float(s['rate']) * 100
            active_str = "Yes" if s.get('is_active', True) else "No"
            label = s.get('label') or f"Level {s['level']}"
            print(f"│   {s['level']}   │ {rate_pct:6.2f}% │ {label:<8} │ {active_str:<8} │")
        print("└───────┴─────────┴──────────┴──────────┘")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        exit(1)

if __name__ == '__main__':
    migrate_commission_is_active()
