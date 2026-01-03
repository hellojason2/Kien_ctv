#!/usr/bin/env python3
"""
Import Khách Giới Thiệu (Referral Customers) TSV file
- Each row = one service record
- Customers deduplicated by phone number
- CTV accounts created from referrer codes (Column G)
- Services linked to customers and CTVs
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
    
    print(f"   Found {len(rows)} service records")
    print(f"   Found {len(ctv_codes)} unique CTV codes (referrers)")
    
    # Connect to database
    print("\n2. Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("   Connected!")
    
    try:
        # Step 1: Create CTV accounts
        print("\n3. Creating CTV accounts...")
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
        
        # Step 2: Build customer lookup by phone (deduplicate)
        print("\n4. Processing customers and services...")
        
        # First pass: collect unique customers by phone
        customers_by_phone = {}  # phone -> {name, phone}
        for row in rows:
            phone = clean_phone(row.get('Số điện thoại', ''))
            name = row.get('Tên khách hàng', '').strip()[:100]
            
            if phone and phone not in customers_by_phone:
                customers_by_phone[phone] = {'name': name, 'phone': phone}
        
        print(f"   Found {len(customers_by_phone)} unique customers by phone")
        
        # Insert customers and build phone -> id mapping
        phone_to_customer_id = {}
        customers_created = 0
        
        for phone, cust in customers_by_phone.items():
            # Check if customer already exists
            cur.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
            result = cur.fetchone()
            
            if result:
                phone_to_customer_id[phone] = result[0]
            else:
                cur.execute("""
                    INSERT INTO customers (name, phone)
                    VALUES (%s, %s)
                    RETURNING id
                """, (cust['name'], cust['phone']))
                customer_id = cur.fetchone()[0]
                phone_to_customer_id[phone] = customer_id
                customers_created += 1
        
        conn.commit()
        print(f"   ✓ Created {customers_created} new customers")
        
        # Step 3: Create service records
        print("\n5. Creating service records...")
        services_created = 0
        services_skipped = 0
        
        for row in rows:
            phone = clean_phone(row.get('Số điện thoại', ''))
            
            if not phone or phone not in phone_to_customer_id:
                services_skipped += 1
                continue
            
            customer_id = phone_to_customer_id[phone]
            ctv_code = row.get('SDT người giới thiệu', '').strip() or None
            service_name = row.get('Dịch vụ Quan tâm', '').strip()[:200]
            date_entered = parse_date(row.get('Ngày nhập đơn', ''))
            
            cur.execute("""
                INSERT INTO services 
                (customer_id, service_name, date_entered, ctv_code, status)
                VALUES (%s, %s, %s, %s, 'Cho xu ly')
            """, (customer_id, service_name, date_entered, ctv_code))
            services_created += 1
        
        conn.commit()
        print(f"   ✓ Created {services_created} service records")
        if services_skipped > 0:
            print(f"   ! Skipped {services_skipped} rows (no valid phone)")
        
        # Verify
        print("\n6. Verification...")
        cur.execute("SELECT COUNT(*) FROM ctv")
        ctv_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM customers")
        cust_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM services")
        svc_count = cur.fetchone()[0]
        
        print(f"   - Total CTVs: {ctv_count}")
        print(f"   - Total customers: {cust_count}")
        print(f"   - Total services: {svc_count}")
        
        # Top CTVs by service count
        print("\n7. Top 10 CTVs by service count:")
        cur.execute("""
            SELECT ctv_code, COUNT(*) as cnt 
            FROM services 
            WHERE ctv_code IS NOT NULL 
            GROUP BY ctv_code 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]} services")
        
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

