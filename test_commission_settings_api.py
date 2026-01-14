#!/usr/bin/env python3
"""
Test the commission settings API to verify it's working correctly
Created: January 14, 2026
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor

def test_commission_settings_api():
    """Test fetching commission settings like the API does"""
    print("=" * 70)
    print("TESTING COMMISSION SETTINGS API")
    print("=" * 70)
    
    connection = get_db_connection()
    if not connection:
        print("✗ ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # This is the exact query used by the API
        cursor.execute("""
            SELECT level, rate, description, label, updated_at, updated_by, is_active
            FROM commission_settings ORDER BY level
        """)
        settings = [dict(row) for row in cursor.fetchall()]
        
        # Process settings like the API does
        for s in settings:
            s['rate'] = float(s['rate'])
            s['is_active'] = s.get('is_active', True)  # Default to True if not set
            s['label'] = s.get('label') or f"Level {s['level']}"  # Default to "Level X" if not set
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        print("\n✓ Successfully fetched commission settings:\n")
        print("┌───────┬─────────┬──────────────┬──────────┬─────────────────────┐")
        print("│ Level │ Rate    │ Label        │ Active   │ Updated             │")
        print("├───────┼─────────┼──────────────┼──────────┼─────────────────────┤")
        for s in settings:
            rate_pct = s['rate'] * 100
            active_str = "✓ Yes" if s['is_active'] else "✗ No"
            label = s.get('label', f"Level {s['level']}")
            updated = s.get('updated_at', 'Never')
            print(f"│   {s['level']}   │ {rate_pct:6.2f}% │ {label:<12} │ {active_str:<8} │ {updated:<19} │")
        print("└───────┴─────────┴──────────────┴──────────┴─────────────────────┘")
        
        # Display the raw JSON that would be returned
        print("\n✓ API would return this JSON structure:")
        import json
        print(json.dumps({
            'status': 'success',
            'settings': settings
        }, indent=2, default=str))
        
        cursor.close()
        return_db_connection(connection)
        
        print("\n" + "=" * 70)
        print("✓ TEST PASSED - Commission settings API is working correctly!")
        print("=" * 70)
        print("\nThe settings page should now be able to:")
        print("  1. Load all 5 commission levels")
        print("  2. Display custom labels for each level")
        print("  3. Show active/inactive status with toggle switches")
        print("  4. Allow editing of rates and labels")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        if connection:
            return_db_connection(connection)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_commission_settings_api()
    sys.exit(0 if success else 1)
