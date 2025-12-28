"""
Authentication Database Migration Script
Creates admins, sessions, commission_settings tables and adds password fields to ctv.

Created: December 28, 2025
"""

import os
import sys
import hashlib
import secrets
import mysql.connector
from mysql.connector import Error

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database configuration (same as backend.py)
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


def hash_password(password):
    """
    Hash password using SHA256 with salt
    Returns: salt:hash format
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def run_migration():
    """Run the authentication database migration"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        print("=" * 50)
        print("Authentication Database Migration")
        print("=" * 50)
        
        # Step 1: Create admins table
        print("\n[1/5] Creating admins table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username)
            );
        """)
        connection.commit()
        print("   SUCCESS: admins table created/verified")
        
        # Step 2: Create sessions table
        print("\n[2/5] Creating sessions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(64) PRIMARY KEY,
                user_type ENUM('admin', 'ctv') NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                INDEX idx_user (user_type, user_id),
                INDEX idx_expires (expires_at)
            );
        """)
        connection.commit()
        print("   SUCCESS: sessions table created/verified")
        
        # Step 3: Create commission_settings table
        print("\n[3/5] Creating commission_settings table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commission_settings (
                level INT PRIMARY KEY CHECK (level >= 0 AND level <= 4),
                rate DECIMAL(5,4) NOT NULL,
                description VARCHAR(100),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                updated_by VARCHAR(50)
            );
        """)
        connection.commit()
        
        # Insert default commission rates if table is empty
        cursor.execute("SELECT COUNT(*) FROM commission_settings;")
        count = cursor.fetchone()[0]
        if count == 0:
            print("   Inserting default commission rates...")
            default_rates = [
                (0, 0.25, 'Self (Doanh so ban than) - 25%'),
                (1, 0.05, 'Direct referral - 5%'),
                (2, 0.025, 'Level 2 - 2.5%'),
                (3, 0.0125, 'Level 3 - 1.25%'),
                (4, 0.00625, 'Level 4 (max) - 0.625%'),
            ]
            cursor.executemany("""
                INSERT INTO commission_settings (level, rate, description)
                VALUES (%s, %s, %s);
            """, default_rates)
            connection.commit()
        print("   SUCCESS: commission_settings table created/verified")
        
        # Step 4: Add password_hash and is_active to ctv table
        print("\n[4/5] Adding password fields to ctv table...")
        
        # Check if password_hash column exists
        cursor.execute("SHOW COLUMNS FROM ctv LIKE 'password_hash';")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE ctv 
                ADD COLUMN password_hash VARCHAR(255);
            """)
            connection.commit()
            print("   Added password_hash column")
        else:
            print("   INFO: password_hash column already exists")
        
        # Check if is_active column exists
        cursor.execute("SHOW COLUMNS FROM ctv LIKE 'is_active';")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE ctv 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
            """)
            connection.commit()
            print("   Added is_active column")
        else:
            print("   INFO: is_active column already exists")
        
        print("   SUCCESS: ctv table updated")
        
        # Step 5: Create default admin account
        print("\n[5/5] Creating default admin account...")
        cursor.execute("SELECT COUNT(*) FROM admins;")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            default_password = "admin123"  # Change this in production!
            password_hash = hash_password(default_password)
            cursor.execute("""
                INSERT INTO admins (username, password_hash, name)
                VALUES (%s, %s, %s);
            """, ('admin', password_hash, 'System Administrator'))
            connection.commit()
            print(f"   Created default admin account:")
            print(f"   Username: admin")
            print(f"   Password: {default_password}")
            print("   WARNING: Change this password immediately in production!")
        else:
            print(f"   INFO: {admin_count} admin account(s) already exist")
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        
        # Show table structures
        print("\n--- Admins Table Structure ---")
        cursor.execute("DESCRIBE admins;")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        print("\n--- Sessions Table Structure ---")
        cursor.execute("DESCRIBE sessions;")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        print("\n--- Commission Settings ---")
        cursor.execute("SELECT level, rate, description FROM commission_settings ORDER BY level;")
        for row in cursor.fetchall():
            print(f"  Level {row[0]}: {float(row[1])*100}% - {row[2]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\nERROR during migration: {e}")
        connection.rollback()
        return False


def set_ctv_passwords():
    """Set default passwords for existing CTVs"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        print("\n" + "=" * 50)
        print("Setting CTV Passwords")
        print("=" * 50)
        
        # Get CTVs without passwords
        cursor.execute("""
            SELECT ma_ctv, ten, email 
            FROM ctv 
            WHERE password_hash IS NULL OR password_hash = '';
        """)
        ctv_list = cursor.fetchall()
        
        if not ctv_list:
            print("All CTVs already have passwords set.")
            cursor.close()
            connection.close()
            return True
        
        print(f"\nSetting default passwords for {len(ctv_list)} CTVs...")
        print("Default password: ctv123 (change in production!)\n")
        
        default_password = "ctv123"
        password_hash = hash_password(default_password)
        
        for ctv in ctv_list:
            cursor.execute("""
                UPDATE ctv SET password_hash = %s WHERE ma_ctv = %s;
            """, (password_hash, ctv['ma_ctv']))
            print(f"  Set password for {ctv['ma_ctv']} ({ctv['ten']})")
        
        connection.commit()
        print(f"\nSUCCESS: Updated {len(ctv_list)} CTV passwords")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\nERROR: {e}")
        return False


if __name__ == '__main__':
    print("\nAuthentication Migration Script")
    print("Usage:")
    print("  python migrate_auth.py          - Run migration only")
    print("  python migrate_auth.py passwords - Run migration + set CTV passwords")
    print()
    
    # Run migration
    success = run_migration()
    
    # Set CTV passwords if requested
    if success and len(sys.argv) > 1 and sys.argv[1] == 'passwords':
        set_ctv_passwords()
    
    print()

