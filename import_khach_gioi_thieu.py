#!/usr/bin/env python3
"""
Import Khách Giới Thiệu (Referral Customers) TSV file
- Imports directly to khach_hang table (unified with Thẩm mỹ and Nha khoa)
- CTV accounts created from referrer phone numbers (SDT người giới thiệu)
- Sets source = 'gioi_thieu' to distinguish from other data sources
"""

import csv
import psycopg2
from datetime import datetime
import hashlib
import secrets

DB_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 34643,
    'user': 'postgres',
    'password': 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl',
    'database': 'railway'
}

TSV_FILE = 'database/khach_gioi_thieu.tsv'

def hash_password(password):
    """Create password hash (salt:sha256hash format)"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}:{hash_obj.hexdigest()}"

def parse_date(s):
    """Parse date from DD/MM/YYYY format"""
    if not s or not s.strip():
        return None
    for fmt in ['%d/%m/%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except:
            pass
    return None

def clean_phone(phone):
    """Clean phone number - remove non-digits, normalize"""
    if not phone:
        return None
    # Keep only digits
    cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
    return cleaned if cleaned else None

def main():
    print("=" * 60)
    print("Import Khách Giới Thiệu (Referral Customers)")
    print("Importing to UNIFIED khach_hang table")
    print("=" * 60)
    
    # Read TSV file
    print(f"\n1. Reading TSV file: {TSV_FILE}")
    rows = []
    ctv_codes = set()
    
    with open(TSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
            ctv_code = row.get('SDT người giới thiệu', '').strip()
            if ctv_code:
                ctv_codes.add(ctv_code)
    
    print(f"   Found {len(rows)} records to import")
    print(f"   Found {len(ctv_codes)} unique CTV codes (referrer phone numbers)")
    
    # Connect to database
    print("\n2. Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("   Connected!")
    
    try:
        # Step 1: Create CTV accounts from referrer phone numbers
        print("\n3. Creating CTV accounts from referrer phones...")
        default_password = hash_password('ctv123')
        created_ctv = 0
        
        for ctv_code in sorted(ctv_codes):
            # Check if CTV already exists
            cur.execute("SELECT 1 FROM ctv WHERE ma_ctv = %s", (ctv_code,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO ctv (ma_ctv, ten, password_hash, is_active)
                    VALUES (%s, %s, %s, TRUE)
                """, (ctv_code, ctv_code, default_password))
                created_ctv += 1
        
        conn.commit()
        print(f"   ✓ Created {created_ctv} new CTV accounts")
        
        # Step 2: Import records to khach_hang table
        print("\n4. Importing records to khach_hang table...")
        imported = 0
        errors = 0
        
        for i, row in enumerate(rows):
            try:
                ngay_nhap = parse_date(row.get('Ngày nhập đơn', ''))
                ten_khach = row.get('Tên khách hàng', '').strip()[:100]
                sdt = clean_phone(row.get('Số điện thoại', ''))
                dich_vu = row.get('Dịch vụ Quan tâm', '').strip()[:500]
                ghi_chu = row.get('Ghi chú', '').strip()
                khu_vuc = row.get('Khu vực của khách hàng', '').strip()[:50]
                nguoi_chot = row.get('SDT người giới thiệu', '').strip()[:50] or None  # Referrer = Closer
                
                cur.execute("""
                    INSERT INTO khach_hang 
                    (ngay_nhap_don, ten_khach, sdt, dich_vu, ghi_chu, 
                     khu_vuc, nguoi_chot, source, trang_thai)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'gioi_thieu', 'Cho xac nhan')
                """, (ngay_nhap, ten_khach, sdt, dich_vu, ghi_chu, 
                      khu_vuc, nguoi_chot))
                imported += 1
                
                # Progress indicator every 100 records
                if (i + 1) % 100 == 0:
                    print(f"   ... processed {i + 1} records")
                    conn.commit()
                
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ! Error on row {i+1}: {e}")
        
        conn.commit()
        print(f"\n   ✓ Imported {imported} records to khach_hang!")
        if errors > 0:
            print(f"   ! {errors} errors occurred")
        
        # Verify import
        print("\n5. Verification...")
        cur.execute("SELECT COUNT(*) FROM ctv")
        ctv_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM khach_hang WHERE source = 'gioi_thieu'")
        gioi_thieu_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM khach_hang")
        total_kh = cur.fetchone()[0]
        
        print(f"   - Total CTVs: {ctv_count}")
        print(f"   - Khách giới thiệu records: {gioi_thieu_count}")
        print(f"   - Total khach_hang records: {total_kh}")
        
        # Show breakdown by source
        print("\n6. Breakdown by source:")
        cur.execute("""
            SELECT COALESCE(source, 'unknown') as src, COUNT(*) as cnt 
            FROM khach_hang 
            GROUP BY source 
            ORDER BY cnt DESC
        """)
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]} records")
        
        # Top referrers
        print("\n7. Top 10 referrers by customer count:")
        cur.execute("""
            SELECT sdt_nguoi_gioi_thieu, COUNT(*) as cnt 
            FROM khach_hang 
            WHERE sdt_nguoi_gioi_thieu IS NOT NULL 
            GROUP BY sdt_nguoi_gioi_thieu 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]} customers")
        
        print("\n" + "=" * 60)
        print("Import completed successfully!")
        print("=" * 60)
        print("\nCTV Login: Use any CTV code with password 'ctv123'")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
