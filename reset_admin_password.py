#!/usr/bin/env python3
"""
Reset admin password
Created: January 14, 2026
"""

import sys
sys.path.insert(0, '.')

from modules.auth import hash_password
from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor

def reset_admin_password():
    """Reset admin password to admin123"""
    print("=" * 70)
    print("RESETTING ADMIN PASSWORD")
    print("=" * 70)
    
    connection = get_db_connection()
    if not connection:
        print("✗ ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Generate new password hash
        new_password = "admin123"
        password_hash = hash_password(new_password)
        
        print(f"\nUpdating admin password...")
        print(f"New password: {new_password}")
        print(f"New hash: {password_hash[:50]}...")
        
        # Update admin password
        cursor.execute("""
            UPDATE admins 
            SET password_hash = %s
            WHERE username = 'admin'
            RETURNING id, username, name
        """, (password_hash,))
        
        admin = cursor.fetchone()
        connection.commit()
        
        if admin:
            print(f"\n✓ Password updated successfully!")
            print(f"   Username: {admin['username']}")
            print(f"   Name: {admin['name']}")
            print(f"   Password: {new_password}")
        else:
            print("\n✗ ERROR: Admin user not found")
            return False
        
        cursor.close()
        return_db_connection(connection)
        
        print("\n" + "=" * 70)
        print("✓ ADMIN PASSWORD RESET COMPLETE")
        print("=" * 70)
        print(f"\nYou can now log in with:")
        print(f"   Username: admin")
        print(f"   Password: {new_password}")
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
    success = reset_admin_password()
    sys.exit(0 if success else 1)
