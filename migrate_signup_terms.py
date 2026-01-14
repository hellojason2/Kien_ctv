"""
Migration Script: Create signup_terms table
Run this to add the signup terms management feature
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
        
        print("📋 Creating signup_terms table...")
        
        # Read the SQL file
        with open('schema/signup_terms.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute the SQL
        cursor.execute(sql)
        connection.commit()
        
        print("✅ Migration completed successfully!")
        print("   - Created signup_terms table")
        print("   - Inserted default Vietnamese terms")
        print("   - Inserted default English terms")
        print("   - Created indexes")
        
        cursor.close()
        return_db_connection(connection)
        return True
        
    except Error as e:
        print(f"❌ Migration failed: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Signup Terms Migration")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Restart your application")
        print("   2. Go to Admin Panel > Signup Terms")
        print("   3. Edit and customize the terms as needed")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
