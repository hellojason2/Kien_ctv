"""
MLM Database Migration Script
Creates the ctv table with referral relationships and commissions table.

Created: December 28, 2025
"""

import os
import sys
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

def run_migration():
    """Run the MLM database migration"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        print("=" * 50)
        print("MLM Database Migration")
        print("=" * 50)
        
        # Step 1: Create the new ctv table with referral relationships
        print("\n[1/4] Creating ctv table with referral structure...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ctv (
                ma_ctv VARCHAR(20) PRIMARY KEY,
                ten VARCHAR(100) NOT NULL,
                sdt VARCHAR(15),
                email VARCHAR(100),
                nguoi_gioi_thieu VARCHAR(20),
                cap_bac VARCHAR(50) DEFAULT 'Bronze',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (nguoi_gioi_thieu) REFERENCES ctv(ma_ctv) ON DELETE SET NULL
            );
        """)
        connection.commit()
        print("   SUCCESS: ctv table created/verified")
        
        # Step 2: Create commissions table
        print("\n[2/4] Creating commissions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commissions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                transaction_id INT NOT NULL,
                ctv_code VARCHAR(20) NOT NULL,
                level INT NOT NULL CHECK (level >= 0 AND level <= 4),
                commission_rate DECIMAL(5,4) NOT NULL,
                transaction_amount DECIMAL(15,0) NOT NULL,
                commission_amount DECIMAL(15,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ctv_code) REFERENCES ctv(ma_ctv) ON DELETE CASCADE,
                INDEX idx_transaction (transaction_id),
                INDEX idx_ctv_code (ctv_code),
                INDEX idx_created_at (created_at)
            );
        """)
        connection.commit()
        print("   SUCCESS: commissions table created/verified")
        
        # Step 3: Migrate existing ctv_accounts data to new ctv table
        print("\n[3/4] Checking for existing ctv_accounts data to migrate...")
        cursor.execute("SHOW TABLES LIKE 'ctv_accounts';")
        ctv_accounts_exists = cursor.fetchone()
        
        if ctv_accounts_exists:
            # Check if there's data in ctv_accounts
            cursor.execute("SELECT COUNT(*) FROM ctv_accounts;")
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Check if ctv table is empty
                cursor.execute("SELECT COUNT(*) FROM ctv;")
                ctv_count = cursor.fetchone()[0]
                
                if ctv_count == 0:
                    print(f"   Migrating {count} records from ctv_accounts...")
                    cursor.execute("""
                        INSERT INTO ctv (ma_ctv, ten, cap_bac)
                        SELECT ctv_code, name, level
                        FROM ctv_accounts
                        ON DUPLICATE KEY UPDATE ten = VALUES(ten), cap_bac = VALUES(cap_bac);
                    """)
                    connection.commit()
                    print(f"   SUCCESS: Migrated {count} CTV records")
                else:
                    print(f"   SKIPPED: ctv table already has {ctv_count} records")
            else:
                print("   INFO: ctv_accounts table is empty, nothing to migrate")
        else:
            print("   INFO: ctv_accounts table does not exist, skipping migration")
        
        # Step 4: Ensure services table has nguoi_chot column
        print("\n[4/4] Checking services table for nguoi_chot column...")
        cursor.execute("SHOW TABLES LIKE 'services';")
        services_exists = cursor.fetchone()
        
        if services_exists:
            cursor.execute("SHOW COLUMNS FROM services LIKE 'nguoi_chot';")
            nguoi_chot_exists = cursor.fetchone()
            
            if not nguoi_chot_exists:
                print("   Adding nguoi_chot column to services table...")
                cursor.execute("""
                    ALTER TABLE services 
                    ADD COLUMN nguoi_chot VARCHAR(20),
                    ADD FOREIGN KEY (nguoi_chot) REFERENCES ctv(ma_ctv) ON DELETE SET NULL;
                """)
                connection.commit()
                print("   SUCCESS: nguoi_chot column added")
            else:
                print("   INFO: nguoi_chot column already exists")
            
            # Check for tong_tien column (total amount)
            cursor.execute("SHOW COLUMNS FROM services LIKE 'tong_tien';")
            tong_tien_exists = cursor.fetchone()
            
            if not tong_tien_exists:
                print("   Adding tong_tien column to services table...")
                cursor.execute("""
                    ALTER TABLE services 
                    ADD COLUMN tong_tien DECIMAL(15,0) DEFAULT 0;
                """)
                connection.commit()
                # Copy existing amount data to tong_tien if amount exists
                # Handle formatted strings like '2,500,000 VND' by extracting numbers
                cursor.execute("SHOW COLUMNS FROM services LIKE 'amount';")
                if cursor.fetchone():
                    try:
                        # Try to convert formatted amount strings to numeric values
                        cursor.execute("""
                            UPDATE services 
                            SET tong_tien = CAST(
                                REPLACE(REPLACE(REPLACE(amount, ',', ''), ' VND', ''), ' ', '') 
                                AS DECIMAL(15,0)
                            )
                            WHERE (tong_tien = 0 OR tong_tien IS NULL) 
                            AND amount IS NOT NULL 
                            AND amount REGEXP '^[0-9,. VND]+$';
                        """)
                        connection.commit()
                    except Error:
                        print("   INFO: Could not auto-convert amount values")
                print("   SUCCESS: tong_tien column added")
            else:
                print("   INFO: tong_tien column already exists")
        else:
            print("   WARNING: services table does not exist")
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        
        # Show table structure
        print("\n--- CTV Table Structure ---")
        cursor.execute("DESCRIBE ctv;")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} {'(PK)' if row[3] == 'PRI' else ''} {'(FK)' if row[3] == 'MUL' else ''}")
        
        print("\n--- Commissions Table Structure ---")
        cursor.execute("DESCRIBE commissions;")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} {'(PK)' if row[3] == 'PRI' else ''}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\nERROR during migration: {e}")
        connection.rollback()
        return False

def insert_sample_data():
    """Insert sample CTV data with referral relationships for testing"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        print("\n" + "=" * 50)
        print("Inserting Sample MLM Data")
        print("=" * 50)
        
        # Sample data based on the diagram
        # A (Kien) -> B (Dung) -> C (Tung) -> D (Tu) -> E (Linh) -> F (Hanh)
        sample_ctv = [
            ('CTV001', 'KienTT', '0901234567', 'kien@example.com', None, 'Gold'),
            ('CTV002', 'DungNTT', '0902345678', 'dung@example.com', 'CTV001', 'Silver'),
            ('CTV003', 'TungHV', '0903456789', 'tung@example.com', 'CTV001', 'Silver'),
            ('CTV004', 'LinhNP', '0904567890', 'linh@example.com', 'CTV001', 'Bronze'),
            ('CTV005', 'TuTT', '0905678901', 'tu@example.com', 'CTV002', 'Bronze'),
            ('CTV006', 'LinhVT', '0906789012', 'linhvt@example.com', 'CTV002', 'Bronze'),
            ('CTV007', 'AnhNT', '0907890123', 'anh@example.com', 'CTV003', 'Bronze'),
            ('CTV008', 'TungPT', '0908901234', 'tungpt@example.com', 'CTV005', 'Bronze'),
            ('CTV009', 'VuNL', '0909012345', 'vu@example.com', 'CTV005', 'Bronze'),
            ('CTV010', 'TrangNTT', '0910123456', 'trang@example.com', 'CTV006', 'Bronze'),
            ('CTV011', 'HanhNT', '0911234567', 'hanh@example.com', 'CTV008', 'Bronze'),
        ]
        
        print("\nInserting sample CTV hierarchy:")
        print("  CTV001 (KienTT) - Root")
        print("    |- CTV002 (DungNTT)")
        print("    |    |- CTV005 (TuTT)")
        print("    |    |    |- CTV008 (TungPT)")
        print("    |    |    |    |- CTV011 (HanhNT)")
        print("    |    |    |- CTV009 (VuNL)")
        print("    |    |- CTV006 (LinhVT)")
        print("    |         |- CTV010 (TrangNTT)")
        print("    |- CTV003 (TungHV)")
        print("    |    |- CTV007 (AnhNT)")
        print("    |- CTV004 (LinhNP)")
        
        for ctv in sample_ctv:
            try:
                cursor.execute("""
                    INSERT INTO ctv (ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        ten = VALUES(ten),
                        sdt = VALUES(sdt),
                        email = VALUES(email),
                        nguoi_gioi_thieu = VALUES(nguoi_gioi_thieu),
                        cap_bac = VALUES(cap_bac);
                """, ctv)
            except Error as e:
                print(f"  Warning: Could not insert {ctv[0]}: {e}")
        
        connection.commit()
        print("\nSUCCESS: Sample data inserted")
        
        # Verify the data
        cursor.execute("SELECT ma_ctv, ten, nguoi_gioi_thieu, cap_bac FROM ctv ORDER BY ma_ctv;")
        print("\n--- Inserted CTV Records ---")
        print(f"{'Code':<10} {'Name':<15} {'Referrer':<10} {'Level':<10}")
        print("-" * 45)
        for row in cursor.fetchall():
            referrer = row[2] if row[2] else '-'
            print(f"{row[0]:<10} {row[1]:<15} {referrer:<10} {row[3]:<10}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == '__main__':
    print("\nMLM Migration Script")
    print("Usage:")
    print("  python migrate_mlm.py          - Run migration only")
    print("  python migrate_mlm.py sample   - Run migration + insert sample data")
    print()
    
    # Run migration
    success = run_migration()
    
    # Insert sample data if requested
    if success and len(sys.argv) > 1 and sys.argv[1] == 'sample':
        insert_sample_data()
    
    print()

