#!/usr/bin/env python3
"""
Import Nha Khoa Customer Data from TSV file
- Clears existing CTV and customer data
- Creates CTV records from unique "Người chốt" values
- Imports all customer records into khach_hang table
"""

import csv
import psycopg2
from datetime import datetime
import hashlib
import secrets

# Database configuration (Railway PostgreSQL)
DB_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 34643,
    'user': 'postgres',
    'password': 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl',
    'database': 'railway'
}

TSV_FILE = 'database/database_check_trung_khach_hang_nha_khoa.tsv'

def hash_password(password):
    """Create password hash (salt:sha256hash format)"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}:{hash_obj.hexdigest()}"

def parse_date(date_str):
    """Parse date from DD/MM/YYYY format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        return None

def parse_money(value):
    """Parse money value, return 0 if empty"""
    if not value or value.strip() == '':
        return 0
    try:
        return int(float(value.strip().replace(',', '')))
    except ValueError:
        return 0

def main():
    print("=" * 60)
    print("Nha Khoa Data Import Script")
    print("=" * 60)
    
    # Read TSV file
    print(f"\n1. Reading TSV file: {TSV_FILE}")
    rows = []
    ctv_codes = set()
    
    with open(TSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
            nguoi_chot = row.get('Người chốt', '').strip()
            if nguoi_chot:
                ctv_codes.add(nguoi_chot)
    
    print(f"   Found {len(rows)} customer records")
    print(f"   Found {len(ctv_codes)} unique CTV codes: {', '.join(sorted(ctv_codes))}")
    
    # Connect to database
    print("\n2. Connecting to PostgreSQL database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("   Connected successfully!")
    
    try:
        # Clear existing data (in order due to foreign keys)
        print("\n3. Clearing existing data...")
        
        cur.execute("DELETE FROM commissions")
        print("   - Cleared commissions")
        
        cur.execute("DELETE FROM khach_hang")
        print("   - Cleared khach_hang")
        
        cur.execute("DELETE FROM services")
        print("   - Cleared services")
        
        cur.execute("DELETE FROM customers")
        print("   - Cleared customers")
        
        cur.execute("DELETE FROM sessions WHERE user_type = 'ctv'")
        print("   - Cleared CTV sessions")
        
        cur.execute("DELETE FROM ctv")
        print("   - Cleared ctv")
        
        conn.commit()
        print("   ✓ All existing data cleared!")
        
        # Create CTV records
        print("\n4. Creating CTV records...")
        default_password = hash_password('ctv123')  # Default password for all CTVs
        
        for ctv_code in sorted(ctv_codes):
            cur.execute("""
                INSERT INTO ctv (ma_ctv, ten, password_hash, is_active)
                VALUES (%s, %s, %s, TRUE)
            """, (ctv_code, ctv_code, default_password))
            print(f"   - Created CTV: {ctv_code}")
        
        conn.commit()
        print(f"   ✓ Created {len(ctv_codes)} CTV records!")
        
        # Import customer records
        print("\n5. Importing customer records...")
        imported = 0
        errors = 0
        
        for row in rows:
            try:
                ngay_nhap = parse_date(row.get('Ngày nhập đơn', ''))
                ten_khach = row.get('Tên khách hàng', '').strip()
                sdt = row.get('Số điện thoại', '').strip()
                co_so = row.get('Cơ sở', '').strip()
                ngay_lam = parse_date(row.get('Ngày làm', ''))
                gio = row.get('Giờ', '').strip()
                dich_vu = row.get('Dịch vụ làm', '').strip()
                tong_tien = parse_money(row.get('Giá tổng đơn', ''))
                tien_coc = parse_money(row.get('Tiền cọc', ''))
                phai_dong = parse_money(row.get('Tiền còn phải trả', ''))
                nguoi_chot = row.get('Người chốt', '').strip() or None
                
                cur.execute("""
                    INSERT INTO khach_hang 
                    (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                     dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, trang_thai)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Cho xac nhan')
                """, (ngay_nhap, ten_khach, sdt, co_so, ngay_lam, gio,
                      dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot))
                imported += 1
                
            except Exception as e:
                errors += 1
                print(f"   ! Error importing row: {e}")
                print(f"     Row data: {row}")
        
        conn.commit()
        print(f"   ✓ Imported {imported} customer records!")
        if errors > 0:
            print(f"   ! {errors} errors occurred")
        
        # Verify import
        print("\n6. Verifying import...")
        cur.execute("SELECT COUNT(*) FROM ctv")
        ctv_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM khach_hang")
        kh_count = cur.fetchone()[0]
        
        print(f"   - CTV records: {ctv_count}")
        print(f"   - Customer records: {kh_count}")
        
        # Show CTV summary
        print("\n7. CTV Summary:")
        cur.execute("""
            SELECT c.ma_ctv, c.ten, COUNT(k.id) as client_count
            FROM ctv c
            LEFT JOIN khach_hang k ON k.nguoi_chot = c.ma_ctv
            GROUP BY c.ma_ctv, c.ten
            ORDER BY client_count DESC
        """)
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[2]} clients")
        
        print("\n" + "=" * 60)
        print("Import completed successfully!")
        print("=" * 60)
        print("\nCTV Login Credentials:")
        print("  Username: [CTV Code from above]")
        print("  Password: ctv123")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()

