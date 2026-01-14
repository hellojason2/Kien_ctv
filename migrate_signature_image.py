"""
Migration Script: Add signature_image column to ctv_registrations and ctv tables
Run this to add signature storage capability for CTV signups
"""
import psycopg2
from psycopg2 import Error
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_pool import get_db_connection as get_pool_connection, return_db_connection

def get_db_connection():
    """Get database connection"""
    connection = get_pool_connection()
    if not connection:
        print("❌ Database connection failed")
    return connection

def run_migration():
    """Run the migration"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        print("=" * 60)
        print("Signature Image Column Migration")
        print("=" * 60)
        
        # Check if column already exists in ctv_registrations
        print("\n[1/2] Checking ctv_registrations table...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ctv_registrations' 
            AND column_name = 'signature_image'
        """)
        if cursor.fetchone():
            print("   ⚠️  signature_image column already exists in ctv_registrations")
        else:
            print("   ➕ Adding signature_image column to ctv_registrations...")
            cursor.execute("""
                ALTER TABLE ctv_registrations 
                ADD COLUMN signature_image TEXT
            """)
            print("   ✅ Added signature_image column to ctv_registrations")
        
        # Check if column already exists in ctv
        print("\n[2/2] Checking ctv table...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ctv' 
            AND column_name = 'signature_image'
        """)
        if cursor.fetchone():
            print("   ⚠️  signature_image column already exists in ctv")
        else:
            print("   ➕ Adding signature_image column to ctv...")
            cursor.execute("""
                ALTER TABLE ctv 
                ADD COLUMN signature_image TEXT
            """)
            print("   ✅ Added signature_image column to ctv")
        
        connection.commit()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\n📝 Summary:")
        print("   - Added signature_image column to ctv_registrations table")
        print("   - Added signature_image column to ctv table")
        print("   - Signature images will now be stored when CTVs sign up")
        
        cursor.close()
        return_db_connection(connection)
        return True
        
    except Error as e:
        print(f"\n❌ Migration failed: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Signature Image Column Migration")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Restart your application")
        print("   2. Test CTV signup with signature")
        print("   3. Verify signature appears in admin registration review")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
