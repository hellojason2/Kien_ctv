#!/usr/bin/env python3
"""
Comprehensive fix for commission settings table
- Ensures 'label' column exists
- Ensures 'is_active' column exists
- Sets proper defaults

Run this script to fix the database schema for the settings page.
Created: January 14, 2026
"""

import os
import sys

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor

def fix_commission_settings_table():
    """Add missing columns to commission_settings table"""
    print("=" * 70)
    print("FIXING COMMISSION_SETTINGS TABLE")
    print("=" * 70)
    
    connection = get_db_connection()
    if not connection:
        print("✗ ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        changes_made = False
        
        # Check if label column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='commission_settings' AND column_name='label'
        """)
        
        if not cursor.fetchone():
            print("\n1. Adding 'label' column...")
            cursor.execute("""
                ALTER TABLE commission_settings 
                ADD COLUMN label VARCHAR(50)
            """)
            cursor.execute("""
                UPDATE commission_settings 
                SET label = 'Level ' || level::text
                WHERE label IS NULL
            """)
            print("   ✓ Added 'label' column")
            changes_made = True
        else:
            print("\n1. ✓ 'label' column already exists")
        
        # Check if is_active column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='commission_settings' AND column_name='is_active'
        """)
        
        if not cursor.fetchone():
            print("\n2. Adding 'is_active' column...")
            cursor.execute("""
                ALTER TABLE commission_settings 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE
            """)
            cursor.execute("""
                UPDATE commission_settings 
                SET is_active = TRUE
                WHERE is_active IS NULL
            """)
            print("   ✓ Added 'is_active' column")
            changes_made = True
        else:
            print("\n2. ✓ 'is_active' column already exists")
            # Ensure no NULL values
            cursor.execute("""
                UPDATE commission_settings 
                SET is_active = TRUE
                WHERE is_active IS NULL
            """)
        
        if changes_made:
            connection.commit()
            print("\n" + "=" * 70)
            print("CHANGES COMMITTED TO DATABASE")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("NO CHANGES NEEDED - TABLE ALREADY UP TO DATE")
            print("=" * 70)
        
        # Display current state
        cursor.execute("""
            SELECT level, rate, label, is_active 
            FROM commission_settings 
            ORDER BY level
        """)
        settings = cursor.fetchall()
        
        print("\nCURRENT COMMISSION SETTINGS:")
        print("┌───────┬─────────┬──────────────┬──────────┐")
        print("│ Level │ Rate    │ Label        │ Active   │")
        print("├───────┼─────────┼──────────────┼──────────┤")
        for s in settings:
            rate_pct = float(s['rate']) * 100
            active_str = "✓ Yes" if s.get('is_active', True) else "✗ No"
            label = s.get('label') or f"Level {s['level']}"
            print(f"│   {s['level']}   │ {rate_pct:6.2f}% │ {label:<12} │ {active_str:<8} │")
        print("└───────┴─────────┴──────────────┴──────────┘")
        
        cursor.close()
        return_db_connection(connection)
        
        print("\n" + "=" * 70)
        print("✓ FIX COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nThe admin settings page should now work correctly!")
        print("Refresh your browser to see the changes.")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\nThis script will fix the commission_settings table structure.")
    print("It will add any missing columns needed for the admin settings page.\n")
    
    success = fix_commission_settings_table()
    
    if not success:
        print("\n✗ Fix failed. Please check the error messages above.")
        sys.exit(1)
    else:
        print("\n✓ All fixes applied successfully!")
        sys.exit(0)
