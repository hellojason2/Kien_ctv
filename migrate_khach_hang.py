"""
Khach Hang (Customer) Database Migration Script
Creates the khach_hang table and hoa_hong_config table with sample data.

Based on CTV System Specification v1.0
Created: December 28, 2025
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# Database configuration
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
    """Run the khach_hang database migration"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        print("=" * 60)
        print("Khach Hang (Customer) Database Migration")
        print("=" * 60)
        
        # Step 1: Create hoa_hong_config table (Commission Rates)
        print("\n[1/3] Creating hoa_hong_config table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hoa_hong_config (
                level INT PRIMARY KEY,
                percent DECIMAL(5,3) NOT NULL,
                description VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
        """)
        connection.commit()
        
        # Insert default commission rates
        cursor.execute("SELECT COUNT(*) FROM hoa_hong_config")
        if cursor.fetchone()[0] == 0:
            print("   Inserting default commission rates...")
            rates = [
                (0, 25.0, 'Doanh so ban than (Level 0)'),
                (1, 5.0, 'Doanh so Level 1 (truc tiep gioi thieu)'),
                (2, 2.5, 'Doanh so Level 2'),
                (3, 1.25, 'Doanh so Level 3'),
                (4, 0.625, 'Doanh so Level 4 (cap cuoi)')
            ]
            cursor.executemany("""
                INSERT INTO hoa_hong_config (level, percent, description)
                VALUES (%s, %s, %s)
            """, rates)
            connection.commit()
        print("   SUCCESS: hoa_hong_config table created/verified")
        
        # Step 2: Create khach_hang table (Customer Transactions)
        print("\n[2/3] Creating khach_hang table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS khach_hang (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ngay_nhap_don DATE,
                ten_khach VARCHAR(100),
                sdt VARCHAR(15),
                co_so VARCHAR(100),
                ngay_hen_lam DATE,
                gio VARCHAR(20),
                dich_vu VARCHAR(500),
                tong_tien DECIMAL(15,0) DEFAULT 0,
                tien_coc DECIMAL(15,0) DEFAULT 0,
                phai_dong DECIMAL(15,0) DEFAULT 0,
                nguoi_chot VARCHAR(20),
                ghi_chu TEXT,
                trang_thai VARCHAR(50) DEFAULT 'Cho xac nhan',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_sdt (sdt),
                INDEX idx_nguoi_chot (nguoi_chot),
                INDEX idx_ngay_hen_lam (ngay_hen_lam),
                INDEX idx_trang_thai (trang_thai),
                FOREIGN KEY (nguoi_chot) REFERENCES ctv(ma_ctv) ON DELETE SET NULL
            );
        """)
        connection.commit()
        print("   SUCCESS: khach_hang table created/verified")
        
        # Step 3: Show table structures
        print("\n[3/3] Verifying table structures...")
        
        print("\n--- hoa_hong_config Table ---")
        cursor.execute("SELECT * FROM hoa_hong_config ORDER BY level")
        print(f"{'Level':<8} {'Percent':<10} {'Description':<40}")
        print("-" * 58)
        for row in cursor.fetchall():
            print(f"{row[0]:<8} {row[1]:<10} {row[2]:<40}")
        
        print("\n--- khach_hang Table Structure ---")
        cursor.execute("DESCRIBE khach_hang")
        for row in cursor.fetchall():
            pk = '(PK)' if row[3] == 'PRI' else ''
            idx = '(IDX)' if row[3] == 'MUL' else ''
            print(f"  {row[0]:<15} {row[1]:<20} {pk}{idx}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        return True
        
    except Error as e:
        print(f"\nERROR during migration: {e}")
        connection.rollback()
        return False

def insert_sample_data():
    """Insert sample customer data based on the specification"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        print("\n" + "=" * 60)
        print("Inserting Sample Customer Data")
        print("=" * 60)
        
        # Get today's date for relative calculations
        today = datetime.now().date()
        
        # Sample customer data based on the specification
        # Different statuses and dates to test duplicate check logic
        sample_customers = [
            # Customers closed by CTV001 (KienTT)
            (today - timedelta(days=10), 'Pham Thu Ha', '0979832523', 'Co so 1', 
             today - timedelta(days=5), '10:00', 'Cat chi mat 2 mi', 
             8000000, 2000000, 6000000, 'CTV001', 'Khach VIP', 'Da den lam'),
            
            (today - timedelta(days=20), 'Nguyen Van A', '0912345678', 'Co so 2',
             today - timedelta(days=15), '14:00', 'Nang mui S-line',
             15000000, 5000000, 10000000, 'CTV001', '', 'Da den lam'),
            
            # Customers closed by CTV002 (DungNTT)
            (today - timedelta(days=5), 'Tran Thi B', '0923456789', 'Co so 1',
             today + timedelta(days=10), '09:00', 'Tiem filler',
             5000000, 1000000, 4000000, 'CTV002', 'Hen lai', 'Da coc'),
            
            (today - timedelta(days=30), 'Le Van C', '0934567890', 'Co so 3',
             today - timedelta(days=25), '11:00', 'Cay mo',
             11000000, 3000000, 8000000, 'CTV002', '', 'Da den lam'),
            
            # Customers closed by CTV003 (TungHV) - high revenue
            (today - timedelta(days=15), 'Hoang Thi D', '0945678901', 'Co so 1',
             today - timedelta(days=10), '15:00', 'Don cam + Nang mui',
             53818000, 10000000, 43818000, 'CTV003', 'Khach gioi thieu', 'Da den lam'),
            
            (today - timedelta(days=8), 'Vu Van E', '0956789012', 'Co so 2',
             today - timedelta(days=3), '10:30', 'Tiem botox',
             8000000, 2000000, 6000000, 'CTV003', '', 'Da den lam'),
            
            # Customers closed by CTV100 (CTV One - ctv1@a.com)
            (today - timedelta(days=12), 'Pham Thi F', '0967890123', 'Co so 1',
             today - timedelta(days=7), '14:30', 'Cat mi',
             6000000, 1500000, 4500000, 'CTV100', '', 'Da den lam'),
            
            (today - timedelta(days=3), 'Nguyen Van G', '0978901234', 'Co so 2',
             today + timedelta(days=5), '09:30', 'Tiem filler moi',
             4000000, 1000000, 3000000, 'CTV100', 'Khach moi', 'Da coc'),
            
            # Customers closed by CTV101 (CTV Two - ctv2@a.com)
            (today - timedelta(days=25), 'Tran Van H', '0989012345', 'Co so 3',
             today - timedelta(days=20), '11:30', 'Nang nguc',
             40345000, 15000000, 25345000, 'CTV101', '', 'Da den lam'),
            
            # Customers closed by CTV102 (CTV Three - ctv3@a.com)
            (today - timedelta(days=7), 'Le Thi I', '0990123456', 'Co so 1',
             today - timedelta(days=2), '16:00', 'Hut mo bung',
             25000000, 8000000, 17000000, 'CTV102', '', 'Da den lam'),
            
            # Future appointments (for testing duplicate check)
            (today, 'Hoang Van J', '0901234567', 'Co so 2',
             today + timedelta(days=30), '10:00', 'Tu van nang mui',
             0, 0, 0, 'CTV001', 'Chua chot gia', 'Cho xac nhan'),
            
            # Cancelled appointment
            (today - timedelta(days=40), 'Vu Thi K', '0912345670', 'Co so 1',
             today - timedelta(days=35), '14:00', 'Cat mi',
             5000000, 1000000, 4000000, 'CTV002', 'Khach huy', 'Huy lich'),
            
            # Very high revenue customer (for testing L3 commission)
            (today - timedelta(days=18), 'Nguyen Thi L', '0923456780', 'Co so 1',
             today - timedelta(days=12), '09:00', 'Combo: Nang mui + Don cam + Hut mo',
             495202000, 100000000, 395202000, 'CTV007', 'Khach VIP Gold', 'Da den lam'),
        ]
        
        print("\nInserting sample customer records...")
        
        # Clear existing sample data first
        cursor.execute("DELETE FROM khach_hang WHERE id > 0")
        connection.commit()
        
        for customer in sample_customers:
            cursor.execute("""
                INSERT INTO khach_hang 
                (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                 dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, customer)
        
        connection.commit()
        
        # Show inserted data
        print("\n--- Inserted Customer Records ---")
        cursor.execute("""
            SELECT id, ten_khach, sdt, nguoi_chot, tong_tien, trang_thai, ngay_hen_lam
            FROM khach_hang 
            ORDER BY id
        """)
        
        print(f"{'ID':<4} {'Ten Khach':<20} {'SDT':<12} {'CTV':<8} {'Tong Tien':<15} {'Trang Thai':<15} {'Ngay Hen':<12}")
        print("-" * 90)
        for row in cursor.fetchall():
            tong_tien = f"{row[4]:,.0f}" if row[4] else "0"
            ngay_hen = row[6].strftime('%Y-%m-%d') if row[6] else '-'
            print(f"{row[0]:<4} {row[1]:<20} {row[2]:<12} {row[3]:<8} {tong_tien:<15} {row[5]:<15} {ngay_hen:<12}")
        
        # Show summary by CTV
        print("\n--- Revenue Summary by CTV ---")
        cursor.execute("""
            SELECT 
                nguoi_chot,
                COUNT(*) as orders,
                SUM(CASE WHEN trang_thai = 'Da den lam' THEN tong_tien ELSE 0 END) as revenue
            FROM khach_hang
            WHERE nguoi_chot IS NOT NULL
            GROUP BY nguoi_chot
            ORDER BY revenue DESC
        """)
        
        print(f"{'CTV Code':<10} {'Orders':<10} {'Revenue (Da den lam)':<20}")
        print("-" * 40)
        for row in cursor.fetchall():
            revenue = f"{row[2]:,.0f}d" if row[2] else "0d"
            print(f"{row[0]:<10} {row[1]:<10} {revenue:<20}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("Sample data inserted successfully!")
        print("=" * 60)
        return True
        
    except Error as e:
        print(f"\nERROR inserting sample data: {e}")
        connection.rollback()
        return False

if __name__ == '__main__':
    print("\nKhach Hang Migration Script")
    print("Usage:")
    print("  python migrate_khach_hang.py          - Run migration only")
    print("  python migrate_khach_hang.py sample   - Run migration + insert sample data")
    print()
    
    # Run migration
    success = run_migration()
    
    # Insert sample data if requested or by default
    if success:
        if len(sys.argv) > 1 and sys.argv[1] == 'sample':
            insert_sample_data()
        else:
            # Auto-insert sample data
            insert_sample_data()
    
    print()

