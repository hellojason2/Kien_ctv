#!/usr/bin/env python3
"""
Import Thẩm Mỹ (Beauty/Aesthetic) Customer Data from CSV file
- Imports all customer records into khach_hang table
- nguoi_chot is stored as plain text (no CTV creation)
- Commission logic will later check if nguoi_chot matches existing CTV codes
"""

import csv
import psycopg2
from datetime import datetime

# Database configuration (Railway PostgreSQL)
DB_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 34643,
    'user': 'postgres',
    'password': 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl',
    'database': 'railway'
}

CSV_FILE = 'database/database_check_trung_khach_hang_tham_my.csv'

def parse_date(date_str):
    """Parse date from DD/MM/YYYY format"""
    if not date_str or date_str.strip() == '':
        return None
    date_str = date_str.strip()
    
    # Try different date formats
    formats = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def parse_money(value):
    """Parse money value, return 0 if empty"""
    if not value or value.strip() == '':
        return 0
    try:
        # Remove dots (thousands separator) and convert
        cleaned = value.strip().replace('.', '').replace(',', '')
        return int(float(cleaned))
    except ValueError:
        return 0

def main():
    print("=" * 60)
    print("Thẩm Mỹ Data Import Script (Clients Only)")
    print("=" * 60)
    
    # Read CSV file
    print(f"\n1. Reading CSV file: {CSV_FILE}")
    rows = []
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"   Found {len(rows)} customer records to import")
    
    # Connect to database
    print("\n2. Connecting to PostgreSQL database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("   Connected successfully!")
    
    try:
        # Check current data
        cur.execute("SELECT COUNT(*) FROM khach_hang")
        existing_kh = cur.fetchone()[0]
        print(f"\n3. Current database state:")
        print(f"   - Existing customers: {existing_kh}")
        
        # Import customer records
        print("\n4. Importing customer records...")
        imported = 0
        errors = 0
        
        for i, row in enumerate(rows):
            try:
                ngay_nhap = parse_date(row.get('Ngày nhập đơn', ''))
                ten_khach = row.get('Tên khách', '').strip()[:100]
                sdt = row.get('SĐT', '').strip()[:15]
                co_so = row.get('Cơ Sở', '').strip()[:100]
                ngay_lam = parse_date(row.get('Ngày hẹn làm', ''))
                gio = row.get('Giờ', '').strip()[:20]
                dich_vu = row.get('Dịch vụ', '').strip()[:500]
                tong_tien = parse_money(row.get('Tổng', ''))
                tien_coc = parse_money(row.get('Cọc', ''))
                phai_dong = parse_money(row.get('phải đóng', ''))
                nguoi_chot = row.get('Người chốt', '').strip()[:50] or None
                ghi_chu = row.get('Ghi Chú', '').strip()
                trang_thai = row.get('Trạng Thái', '').strip()[:50] or 'Cho xac nhan'
                
                cur.execute("""
                    INSERT INTO khach_hang 
                    (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                     dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (ngay_nhap, ten_khach, sdt, co_so, ngay_lam, gio,
                      dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai))
                imported += 1
                
                # Progress indicator every 1000 records
                if (i + 1) % 1000 == 0:
                    print(f"   ... processed {i + 1} records")
                    conn.commit()
                
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ! Error on row {i+1}: {e}")
        
        conn.commit()
        print(f"\n   ✓ Imported {imported} customer records!")
        if errors > 0:
            print(f"   ! {errors} errors occurred")
        
        # Verify import
        print("\n5. Verifying import...")
        cur.execute("SELECT COUNT(*) FROM khach_hang")
        kh_count = cur.fetchone()[0]
        print(f"   - Total customer records: {kh_count}")
        
        # Show unique nguoi_chot values
        cur.execute("""
            SELECT nguoi_chot, COUNT(*) as cnt 
            FROM khach_hang 
            WHERE nguoi_chot IS NOT NULL 
            GROUP BY nguoi_chot 
            ORDER BY cnt DESC 
            LIMIT 15
        """)
        print("\n6. Top 15 'Người chốt' values:")
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]} clients")
        
        # Count unique nguoi_chot
        cur.execute("SELECT COUNT(DISTINCT nguoi_chot) FROM khach_hang WHERE nguoi_chot IS NOT NULL")
        unique_count = cur.fetchone()[0]
        print(f"\n   Total unique 'Người chốt' values: {unique_count}")
        
        print("\n" + "=" * 60)
        print("Import completed successfully!")
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
