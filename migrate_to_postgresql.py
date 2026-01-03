"""
MySQL to PostgreSQL Migration Script
Migrates data from MySQL to PostgreSQL for the CTV System.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# FUNCTIONS:
# - get_mysql_connection() -> MySQL connection
# - get_postgres_connection() -> PostgreSQL connection
# - run_schema() -> Create tables in PostgreSQL
# - migrate_table(table_name) -> Migrate single table
# - migrate_all() -> Migrate all tables
# - verify_migration() -> Verify record counts match
#
# USAGE:
# python migrate_to_postgresql.py schema     - Create PostgreSQL schema only
# python migrate_to_postgresql.py migrate    - Migrate data from MySQL
# python migrate_to_postgresql.py verify     - Verify migration
# python migrate_to_postgresql.py full       - Schema + Migrate + Verify
#
# Created: January 2, 2026
# ══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import psycopg2
from psycopg2 import sql, Error as PgError
from psycopg2.extras import execute_values
import mysql.connector
from mysql.connector import Error as MySQLError
from datetime import datetime

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATIONS
# ══════════════════════════════════════════════════════════════════════════════

# MySQL (Source)
MYSQL_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}

# PostgreSQL (Target)
POSTGRES_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 34643,
    'user': 'postgres',
    'password': 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl',
    'database': 'railway'
}

# Tables to migrate in order (respecting foreign key dependencies)
MIGRATION_ORDER = [
    'admins',
    'ctv',
    'sessions',
    'customers',
    'khach_hang',
    'services',
    'hoa_hong_config',
    'commission_settings',
    'commissions',
    'activity_logs'
]


def get_mysql_connection():
    """Create and return a MySQL connection"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            return connection
    except MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def get_postgres_connection():
    """Create and return a PostgreSQL connection"""
    try:
        connection = psycopg2.connect(**POSTGRES_CONFIG)
        connection.autocommit = False
        return connection
    except PgError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


def test_connections():
    """Test both database connections"""
    print("=" * 60)
    print("Testing Database Connections")
    print("=" * 60)
    
    # Test MySQL
    print("\n[1/2] Testing MySQL connection...")
    mysql_conn = get_mysql_connection()
    if mysql_conn:
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        print(f"   SUCCESS: Connected to MySQL database '{db_name}'")
        cursor.close()
        mysql_conn.close()
    else:
        print("   FAILED: Could not connect to MySQL")
        return False
    
    # Test PostgreSQL
    print("\n[2/2] Testing PostgreSQL connection...")
    pg_conn = get_postgres_connection()
    if pg_conn:
        cursor = pg_conn.cursor()
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        print(f"   SUCCESS: Connected to PostgreSQL database '{db_name}'")
        cursor.close()
        pg_conn.close()
    else:
        print("   FAILED: Could not connect to PostgreSQL")
        return False
    
    print("\n" + "=" * 60)
    print("Both connections successful!")
    print("=" * 60)
    return True


def run_schema():
    """Execute the PostgreSQL schema file to create tables"""
    print("\n" + "=" * 60)
    print("Creating PostgreSQL Schema")
    print("=" * 60)
    
    schema_path = os.path.join(BASE_DIR, 'schema', 'postgresql_schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"   ERROR: Schema file not found: {schema_path}")
        return False
    
    pg_conn = get_postgres_connection()
    if not pg_conn:
        return False
    
    try:
        cursor = pg_conn.cursor()
        
        # Read and execute schema file
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print("   Executing schema...")
        cursor.execute(schema_sql)
        pg_conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   Created {len(tables)} tables:")
        for table in tables:
            print(f"      - {table}")
        
        cursor.close()
        pg_conn.close()
        
        print("\n   Schema creation completed successfully!")
        return True
        
    except PgError as e:
        print(f"   ERROR: {e}")
        pg_conn.rollback()
        pg_conn.close()
        return False


def get_table_columns(mysql_cursor, table_name):
    """Get column names for a table from MySQL"""
    mysql_cursor.execute(f"DESCRIBE {table_name}")
    columns = [row[0] for row in mysql_cursor.fetchall()]
    return columns


def migrate_table(table_name, batch_size=1000):
    """
    Migrate a single table from MySQL to PostgreSQL
    
    Uses batch inserts for better performance
    """
    print(f"\n   Migrating table: {table_name}")
    
    mysql_conn = get_mysql_connection()
    pg_conn = get_postgres_connection()
    
    if not mysql_conn or not pg_conn:
        print(f"      ERROR: Could not establish connections")
        return False
    
    try:
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        pg_cursor = pg_conn.cursor()
        
        # Check if table exists in MySQL
        mysql_cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not mysql_cursor.fetchone():
            print(f"      SKIP: Table does not exist in MySQL")
            mysql_cursor.close()
            mysql_conn.close()
            pg_cursor.close()
            pg_conn.close()
            return True
        
        # Get column names
        columns = get_table_columns(mysql_cursor, table_name)
        
        # Count records
        mysql_cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
        total_records = mysql_cursor.fetchone()['cnt']
        print(f"      Found {total_records} records")
        
        if total_records == 0:
            print(f"      SKIP: No records to migrate")
            mysql_cursor.close()
            mysql_conn.close()
            pg_cursor.close()
            pg_conn.close()
            return True
        
        # Clear existing data in PostgreSQL (if any)
        try:
            pg_cursor.execute(f"DELETE FROM {table_name}")
            pg_conn.commit()
        except PgError:
            pg_conn.rollback()
        
        # Disable triggers temporarily for faster inserts
        pg_cursor.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER ALL")
        
        # Fetch and insert in batches
        offset = 0
        inserted = 0
        
        while offset < total_records:
            mysql_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
            rows = mysql_cursor.fetchall()
            
            if not rows:
                break
            
            # Prepare values for batch insert
            values = []
            for row in rows:
                row_values = []
                for col in columns:
                    val = row.get(col)
                    # Handle special conversions
                    if val is None:
                        row_values.append(None)
                    elif isinstance(val, bytes):
                        row_values.append(val.decode('utf-8', errors='replace'))
                    else:
                        row_values.append(val)
                values.append(tuple(row_values))
            
            # Build INSERT statement
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            try:
                pg_cursor.executemany(insert_sql, values)
                pg_conn.commit()
                inserted += len(values)
            except PgError as e:
                print(f"      ERROR inserting batch: {e}")
                pg_conn.rollback()
                # Try one by one
                for row_tuple in values:
                    try:
                        pg_cursor.execute(insert_sql, row_tuple)
                        pg_conn.commit()
                        inserted += 1
                    except PgError as e2:
                        pg_conn.rollback()
                        # Skip problematic rows
                        continue
            
            offset += batch_size
            print(f"      Progress: {min(offset, total_records)}/{total_records}")
        
        # Re-enable triggers
        pg_cursor.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL")
        pg_conn.commit()
        
        # Reset sequence if table has SERIAL column
        if table_name in ['admins', 'customers', 'khach_hang', 'services', 'commissions', 'activity_logs']:
            try:
                pg_cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 
                           COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false)
                """)
                pg_conn.commit()
            except PgError:
                pg_conn.rollback()
        
        print(f"      SUCCESS: Migrated {inserted}/{total_records} records")
        
        mysql_cursor.close()
        mysql_conn.close()
        pg_cursor.close()
        pg_conn.close()
        
        return True
        
    except Exception as e:
        print(f"      ERROR: {e}")
        if mysql_conn:
            mysql_conn.close()
        if pg_conn:
            pg_conn.rollback()
            pg_conn.close()
        return False


def migrate_all():
    """Migrate all tables from MySQL to PostgreSQL"""
    print("\n" + "=" * 60)
    print("Migrating Data from MySQL to PostgreSQL")
    print("=" * 60)
    
    success_count = 0
    failed_tables = []
    
    for table in MIGRATION_ORDER:
        if migrate_table(table):
            success_count += 1
        else:
            failed_tables.append(table)
    
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"   Successful: {success_count}/{len(MIGRATION_ORDER)}")
    
    if failed_tables:
        print(f"   Failed: {', '.join(failed_tables)}")
        return False
    
    print("   All tables migrated successfully!")
    return True


def verify_migration():
    """Verify that record counts match between MySQL and PostgreSQL"""
    print("\n" + "=" * 60)
    print("Verifying Migration")
    print("=" * 60)
    
    mysql_conn = get_mysql_connection()
    pg_conn = get_postgres_connection()
    
    if not mysql_conn or not pg_conn:
        print("   ERROR: Could not establish connections")
        return False
    
    try:
        mysql_cursor = mysql_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        all_match = True
        
        for table in MIGRATION_ORDER:
            # Check MySQL count
            try:
                mysql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                mysql_count = mysql_cursor.fetchone()[0]
            except MySQLError:
                mysql_count = 0
            
            # Check PostgreSQL count
            try:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cursor.fetchone()[0]
            except PgError:
                pg_count = 0
            
            status = "OK" if mysql_count == pg_count else "MISMATCH"
            if mysql_count != pg_count:
                all_match = False
            
            print(f"   {table:<20} MySQL: {mysql_count:<8} PostgreSQL: {pg_count:<8} [{status}]")
        
        mysql_cursor.close()
        mysql_conn.close()
        pg_cursor.close()
        pg_conn.close()
        
        print("\n" + "=" * 60)
        if all_match:
            print("Verification PASSED: All record counts match!")
        else:
            print("Verification FAILED: Some tables have mismatched counts")
        print("=" * 60)
        
        return all_match
        
    except Exception as e:
        print(f"   ERROR: {e}")
        if mysql_conn:
            mysql_conn.close()
        if pg_conn:
            pg_conn.close()
        return False


def full_migration():
    """Run full migration: schema + data + verification"""
    print("\n" + "=" * 60)
    print("Full Migration: MySQL to PostgreSQL")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Test connections
    if not test_connections():
        print("\nABORTED: Connection test failed")
        return False
    
    # Step 2: Create schema
    if not run_schema():
        print("\nABORTED: Schema creation failed")
        return False
    
    # Step 3: Migrate data
    if not migrate_all():
        print("\nWARNING: Some tables failed to migrate")
    
    # Step 4: Verify
    verify_migration()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update modules/db_pool.py to use PostgreSQL")
    print("2. Test all API endpoints")
    print("3. Monitor performance")
    
    return True


def print_usage():
    """Print usage instructions"""
    print("\nMySQL to PostgreSQL Migration Script")
    print("=" * 60)
    print("\nUsage:")
    print("  python migrate_to_postgresql.py <command>")
    print("\nCommands:")
    print("  test     - Test database connections")
    print("  schema   - Create PostgreSQL schema only")
    print("  migrate  - Migrate data from MySQL to PostgreSQL")
    print("  verify   - Verify record counts match")
    print("  full     - Run full migration (schema + data + verify)")
    print("\nExamples:")
    print("  python migrate_to_postgresql.py test")
    print("  python migrate_to_postgresql.py full")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'test':
        success = test_connections()
    elif command == 'schema':
        success = run_schema()
    elif command == 'migrate':
        success = migrate_all()
    elif command == 'verify':
        success = verify_migration()
    elif command == 'full':
        success = full_migration()
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
    
    sys.exit(0 if success else 1)

