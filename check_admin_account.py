#!/usr/bin/env python3
"""
Check and create admin account if needed
Created: January 14, 2026
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_pool import get_db_connection, return_db_connection
from modules.auth import hash_password
from psycopg2.extras import RealDictCursor

def check_and_create_admin():
    """Check if admin account exists, create if not"""
    print("=" * 70)
    print("CHECKING ADMIN ACCOUNT")
    print("=" * 70)
    
    connection = get_db_connection()
    if not connection:
        print("✗ ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Check if any admin accounts exist
        cursor.execute("SELECT COUNT(*) as count FROM admins")
        result = cursor.fetchone()
        admin_count = result['count']
        
        print(f"\nCurrent admin accounts: {admin_count}")
        
        if admin_count == 0:
            print("\n✓ No admin accounts found. Creating default admin...")
            default_password = "admin123"
            password_hash = hash_password(default_password)
            
            cursor.execute("""
                INSERT INTO admins (username, password_hash, name)
                VALUES (%s, %s, %s)
                RETURNING id, username, name
            """, ('admin', password_hash, 'System Administrator'))
            
            new_admin = cursor.fetchone()
            connection.commit()
            
            print(f"\n✓ Created admin account:")
            print(f"   ID: {new_admin['id']}")
            print(f"   Username: {new_admin['username']}")
            print(f"   Password: {default_password}")
            print(f"   Name: {new_admin['name']}")
            print("\n⚠️  IMPORTANT: Change this password in production!")
        else:
            # List existing admin accounts
            cursor.execute("SELECT id, username, name, created_at FROM admins")
            admins = cursor.fetchall()
            
            print("\n✓ Existing admin accounts:")
            print("┌────┬──────────────┬───────────────────────────┬─────────────────────┐")
            print("│ ID │ Username     │ Name                      │ Created             │")
            print("├────┼──────────────┼───────────────────────────┼─────────────────────┤")
            for admin in admins:
                created = admin['created_at'].strftime('%Y-%m-%d %H:%M:%S') if admin.get('created_at') else 'N/A'
                print(f"│ {admin['id']:<2} │ {admin['username']:<12} │ {admin['name']:<25} │ {created:<19} │")
            print("└────┴──────────────┴───────────────────────────┴─────────────────────┘")
            
            print("\n✓ Admin accounts already exist. No action needed.")
        
        cursor.close()
        return_db_connection(connection)
        
        print("\n" + "=" * 70)
        print("✓ ADMIN CHECK COMPLETED")
        print("=" * 70)
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
    success = check_and_create_admin()
    sys.exit(0 if success else 1)
