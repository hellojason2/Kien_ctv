"""
Activity Logs Migration Script
Creates the activity_logs table for tracking all website activities.

# ══════════════════════════════════════════════════════════════════════════════
# TABLE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
#
# activity_logs:
#   - id: Auto-increment primary key
#   - timestamp: When the event occurred
#   - event_type: Type of event (login, logout, api_call, etc.)
#   - user_type: admin, ctv, or null for anonymous
#   - user_id: Username or ma_ctv
#   - ip_address: Client IP (supports IPv4 and IPv6)
#   - user_agent: Browser/device information
#   - endpoint: API endpoint or page accessed
#   - method: HTTP method (GET, POST, PUT, DELETE)
#   - status_code: HTTP response status code
#   - details: JSON field for additional context
#   - country: Geolocation country (optional)
#   - city: Geolocation city (optional)
#
# INDEXES:
#   - idx_timestamp: For date range queries
#   - idx_user: For user-specific queries
#   - idx_event: For event type filtering
#   - idx_ip: For IP-based lookups
#
# Created: December 29, 2025
# ══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import mysql.connector
from mysql.connector import Error

# Get database config
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def migrate():
    """Run the activity_logs table migration"""
    print("=" * 60)
    print("ACTIVITY LOGS MIGRATION")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        print("ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if table already exists
        cursor.execute("SHOW TABLES LIKE 'activity_logs';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Table 'activity_logs' already exists.")
            print("Checking for schema updates...")
            
            # Check if all columns exist
            cursor.execute("DESCRIBE activity_logs;")
            existing_columns = {row[0] for row in cursor.fetchall()}
            
            required_columns = {
                'id', 'timestamp', 'event_type', 'user_type', 'user_id',
                'ip_address', 'user_agent', 'endpoint', 'method',
                'status_code', 'details', 'country', 'city'
            }
            
            missing_columns = required_columns - existing_columns
            
            if missing_columns:
                print(f"Adding missing columns: {missing_columns}")
                
                column_definitions = {
                    'timestamp': "DATETIME DEFAULT CURRENT_TIMESTAMP",
                    'event_type': "VARCHAR(50) NOT NULL DEFAULT 'unknown'",
                    'user_type': "VARCHAR(20)",
                    'user_id': "VARCHAR(100)",
                    'ip_address': "VARCHAR(45)",
                    'user_agent': "TEXT",
                    'endpoint': "VARCHAR(255)",
                    'method': "VARCHAR(10)",
                    'status_code': "INT",
                    'details': "JSON",
                    'country': "VARCHAR(50)",
                    'city': "VARCHAR(100)"
                }
                
                for col in missing_columns:
                    if col in column_definitions:
                        cursor.execute(f"""
                            ALTER TABLE activity_logs 
                            ADD COLUMN {col} {column_definitions[col]};
                        """)
                        print(f"  Added column: {col}")
                
                connection.commit()
            else:
                print("All required columns exist.")
        else:
            # Create the table
            print("Creating 'activity_logs' table...")
            
            cursor.execute("""
                CREATE TABLE activity_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type VARCHAR(50) NOT NULL,
                    user_type VARCHAR(20),
                    user_id VARCHAR(100),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    endpoint VARCHAR(255),
                    method VARCHAR(10),
                    status_code INT,
                    details JSON,
                    country VARCHAR(50),
                    city VARCHAR(100),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_user (user_type, user_id),
                    INDEX idx_event (event_type),
                    INDEX idx_ip (ip_address)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            
            connection.commit()
            print("SUCCESS: Table 'activity_logs' created successfully!")
        
        # Verify table structure
        print("\nTable structure:")
        print("-" * 60)
        cursor.execute("DESCRIBE activity_logs;")
        for row in cursor.fetchall():
            print(f"  {row[0]:<15} {row[1]:<20} {row[2]:<5} {row[3] or ''}")
        
        # Show indexes
        print("\nIndexes:")
        print("-" * 60)
        cursor.execute("SHOW INDEX FROM activity_logs;")
        indexes = cursor.fetchall()
        shown_indexes = set()
        for idx in indexes:
            idx_name = idx[2]
            if idx_name not in shown_indexes:
                print(f"  {idx_name}")
                shown_indexes.add(idx_name)
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        return True
        
    except Error as e:
        print(f"ERROR: {e}")
        if connection:
            connection.close()
        return False


if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)

