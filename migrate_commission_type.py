"""
Migration script to add commission_type column to commissions table.
This distinguishes between:
- 'direct' - Normal commission (CTV closed the customer)
- 'cskh' - Customer care commission (Staff closed a returning customer, credit to original CTV)
"""

import os
import sys
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

# Add parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_pool import get_db_connection, return_db_connection


def migrate():
    """Add commission_type column to commissions table"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'commissions' AND column_name = 'commission_type'
        """)
        
        if cursor.fetchone():
            print("Column 'commission_type' already exists in commissions table")
            cursor.close()
            return_db_connection(connection)
            return True
        
        # Add the commission_type column
        print("Adding 'commission_type' column to commissions table...")
        cursor.execute("""
            ALTER TABLE commissions 
            ADD COLUMN commission_type VARCHAR(20) DEFAULT 'direct'
        """)
        
        # Update existing records to 'direct'
        print("Setting existing records to 'direct'...")
        cursor.execute("""
            UPDATE commissions 
            SET commission_type = 'direct' 
            WHERE commission_type IS NULL
        """)
        updated_count = cursor.rowcount
        
        # Add index for commission_type for filtering
        print("Creating index on commission_type...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_commissions_type 
            ON commissions(commission_type)
        """)
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        print(f"SUCCESS: Added commission_type column, updated {updated_count} existing records to 'direct'")
        return True
        
    except Error as e:
        print(f"ERROR: Migration failed: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("CSKH Commission Type Migration")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("\nMigration completed successfully!")
    else:
        print("\nMigration failed!")
        sys.exit(1)
