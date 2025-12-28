"""
CSV Data Import Script
Imports CTV and Customer data from CSV files into the database.

Usage:
  python import_csv_data.py                    - Import all data
  python import_csv_data.py --ctv-only         - Import CTVs only
  python import_csv_data.py --customers-only   - Import customers only
  python import_csv_data.py --dry-run          - Preview without inserting

Created: December 28, 2025
"""

import os
import sys
import csv
import re
from datetime import datetime
from collections import defaultdict
import mysql.connector
from mysql.connector import Error

# ============================================================
# CONFIGURATION
# ============================================================

DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}

# CSV file paths - use relative paths from script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CTV_CSV_PATH = os.path.expanduser('~/Downloads/Dữ liệu - CTV.csv')
CUSTOMER_CSV_PATH = os.path.expanduser('~/Downloads/Dữ liệu - Check trùng.csv')

# CTV code normalization map (lowercase -> correct case)
CTV_CODE_MAP = {}

# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# ============================================================
# DATA PARSING UTILITIES
# ============================================================

def parse_date(date_str):
    """
    Convert DD/MM/YYYY to YYYY-MM-DD format
    Returns None if invalid or empty
    """
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip()
    
    # Try DD/MM/YYYY format
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try other common formats
    for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    print(f"   WARNING: Could not parse date: '{date_str}'")
    return None

def parse_currency(amount_str):
    """
    Convert Vietnamese currency format to integer
    Examples: '14.100.000' -> 14100000, '1.000.000' -> 1000000
    Returns 0 if invalid or empty
    """
    if not amount_str or not amount_str.strip():
        return 0
    
    # Remove all dots and spaces
    cleaned = amount_str.strip().replace('.', '').replace(',', '').replace(' ', '')
    
    # Remove any non-digit characters
    cleaned = re.sub(r'[^\d]', '', cleaned)
    
    if not cleaned:
        return 0
    
    try:
        return int(cleaned)
    except ValueError:
        print(f"   WARNING: Could not parse currency: '{amount_str}'")
        return 0

def normalize_phone(phone_str):
    """Normalize phone number - keep digits only"""
    if not phone_str:
        return None
    
    # Keep only digits
    digits = re.sub(r'[^\d]', '', str(phone_str))
    
    if not digits:
        return None
    
    return digits

def normalize_ctv_code(code):
    """Normalize CTV code for matching (case-insensitive lookup)"""
    if not code or not code.strip():
        return None
    
    code = code.strip()
    
    # Check if we have a mapping for this code (case-insensitive)
    lower_code = code.lower()
    if lower_code in CTV_CODE_MAP:
        return CTV_CODE_MAP[lower_code]
    
    return code

# ============================================================
# CTV IMPORT
# ============================================================

def read_ctv_csv():
    """Read and parse CTV CSV file"""
    ctv_list = []
    
    print(f"\nReading CTV data from: {CTV_CSV_PATH}")
    
    try:
        with open(CTV_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ctv = {
                    'ma_ctv': row.get('Mã CTV', '').strip(),
                    'ten': row.get('Họ và tên', '').strip(),
                    'sdt': normalize_phone(row.get('SDT', '')),
                    'email': row.get('Email', '').strip() or None,
                    'nguoi_gioi_thieu': row.get('Người giới thiệu', '').strip() or None,
                    'cap_bac': row.get('Cấp bậc', '').strip() or 'Cong tac vien'
                }
                
                if ctv['ma_ctv']:
                    ctv_list.append(ctv)
                    # Build case-insensitive lookup map
                    CTV_CODE_MAP[ctv['ma_ctv'].lower()] = ctv['ma_ctv']
        
        print(f"   Found {len(ctv_list)} CTVs")
        return ctv_list
    
    except FileNotFoundError:
        print(f"   ERROR: File not found: {CTV_CSV_PATH}")
        return []
    except Exception as e:
        print(f"   ERROR reading CTV CSV: {e}")
        return []

def topological_sort_ctv(ctv_list):
    """
    Sort CTVs so that referrers come before their referees.
    This ensures foreign key constraints are satisfied during insert.
    """
    # Build adjacency list and in-degree count
    graph = defaultdict(list)
    in_degree = {}
    ctv_map = {}
    
    for ctv in ctv_list:
        code = ctv['ma_ctv']
        ctv_map[code] = ctv
        in_degree[code] = 0
    
    for ctv in ctv_list:
        code = ctv['ma_ctv']
        referrer = ctv['nguoi_gioi_thieu']
        
        if referrer and referrer in ctv_map:
            graph[referrer].append(code)
            in_degree[code] = in_degree.get(code, 0) + 1
    
    # Kahn's algorithm for topological sort
    queue = [code for code, degree in in_degree.items() if degree == 0]
    sorted_codes = []
    
    while queue:
        code = queue.pop(0)
        sorted_codes.append(code)
        
        for child in graph[code]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    
    # Handle any remaining (cycles or missing referrers)
    remaining = set(ctv_map.keys()) - set(sorted_codes)
    sorted_codes.extend(remaining)
    
    return [ctv_map[code] for code in sorted_codes]

def import_ctv(connection, ctv_list, dry_run=False):
    """Import CTVs into database"""
    print("\n" + "=" * 60)
    print("IMPORTING CTVs")
    print("=" * 60)
    
    # Sort topologically
    sorted_ctv = topological_sort_ctv(ctv_list)
    print(f"\nSorted {len(sorted_ctv)} CTVs for import (referrers first)")
    
    if dry_run:
        print("\n[DRY RUN] Would insert:")
        for i, ctv in enumerate(sorted_ctv[:10]):
            print(f"   {i+1}. {ctv['ma_ctv']} - {ctv['ten']} (ref: {ctv['nguoi_gioi_thieu']})")
        if len(sorted_ctv) > 10:
            print(f"   ... and {len(sorted_ctv) - 10} more")
        return {'inserted': 0, 'skipped': 0, 'errors': 0}
    
    cursor = connection.cursor()
    stats = {'inserted': 0, 'skipped': 0, 'errors': 0}
    
    for ctv in sorted_ctv:
        try:
            # Check if CTV already exists
            cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (ctv['ma_ctv'],))
            if cursor.fetchone():
                stats['skipped'] += 1
                continue
            
            # Validate referrer exists (or set to NULL)
            referrer = ctv['nguoi_gioi_thieu']
            if referrer:
                cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (referrer,))
                if not cursor.fetchone():
                    print(f"   WARNING: Referrer '{referrer}' not found for {ctv['ma_ctv']}, setting to NULL")
                    referrer = None
            
            # Insert CTV
            cursor.execute("""
                INSERT INTO ctv (ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                ctv['ma_ctv'],
                ctv['ten'],
                ctv['sdt'],
                ctv['email'],
                referrer,
                ctv['cap_bac']
            ))
            stats['inserted'] += 1
            
        except Error as e:
            print(f"   ERROR inserting CTV {ctv['ma_ctv']}: {e}")
            stats['errors'] += 1
    
    connection.commit()
    cursor.close()
    
    print(f"\nCTV Import Complete:")
    print(f"   Inserted: {stats['inserted']}")
    print(f"   Skipped (existing): {stats['skipped']}")
    print(f"   Errors: {stats['errors']}")
    
    return stats

# ============================================================
# CUSTOMER IMPORT
# ============================================================

def read_customer_csv():
    """Read and parse Customer CSV file"""
    customers = []
    unique_nguoi_chot = set()
    
    print(f"\nReading Customer data from: {CUSTOMER_CSV_PATH}")
    
    try:
        with open(CUSTOMER_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            line_num = 1
            
            for row in reader:
                line_num += 1
                
                # Parse customer data
                customer = {
                    'ngay_nhap_don': parse_date(row.get('Ngày nhập đơn', '')),
                    'ten_khach': row.get('Tên khách', '').strip(),
                    'sdt': normalize_phone(row.get('SĐT', '')),
                    'co_so': row.get('Cơ Sở', '').strip(),
                    'ngay_hen_lam': parse_date(row.get('Ngày hẹn làm', '')),
                    'gio': row.get('Giờ', '').strip() or None,
                    'dich_vu': row.get('Dịch vụ', '').strip(),
                    'tong_tien': parse_currency(row.get('Tổng', '')),
                    'tien_coc': parse_currency(row.get('Cọc', '')),
                    'phai_dong': parse_currency(row.get('phải đóng', '')),
                    'nguoi_chot': row.get('Người chốt', '').strip() or None,
                    'ghi_chu': row.get('Ghi Chú', '').strip() or None,
                    'trang_thai': row.get('Trạng Thái', '').strip() or 'Cho xac nhan',
                    'line_num': line_num
                }
                
                # Track unique nguoi_chot values
                if customer['nguoi_chot']:
                    unique_nguoi_chot.add(customer['nguoi_chot'])
                
                customers.append(customer)
        
        print(f"   Found {len(customers)} customers")
        print(f"   Found {len(unique_nguoi_chot)} unique 'Nguoi chot' values")
        
        return customers, unique_nguoi_chot
    
    except FileNotFoundError:
        print(f"   ERROR: File not found: {CUSTOMER_CSV_PATH}")
        return [], set()
    except Exception as e:
        print(f"   ERROR reading Customer CSV: {e}")
        import traceback
        traceback.print_exc()
        return [], set()

def find_missing_ctv(connection, nguoi_chot_set):
    """Find CTV codes in customer data that don't exist in database"""
    cursor = connection.cursor()
    missing = []
    
    for code in nguoi_chot_set:
        if not code:
            continue
        
        # Try exact match first
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (code,))
        if cursor.fetchone():
            continue
        
        # Try case-insensitive match
        cursor.execute("SELECT ma_ctv FROM ctv WHERE LOWER(ma_ctv) = LOWER(%s)", (code,))
        result = cursor.fetchone()
        if result:
            # Add to mapping
            CTV_CODE_MAP[code.lower()] = result[0]
            continue
        
        missing.append(code)
    
    cursor.close()
    return missing

def create_missing_ctv(connection, missing_codes, dry_run=False):
    """Create CTV records for missing codes found in customer data"""
    print("\n" + "=" * 60)
    print("CREATING MISSING CTVs")
    print("=" * 60)
    
    if not missing_codes:
        print("   No missing CTVs to create")
        return {'created': 0}
    
    print(f"\nFound {len(missing_codes)} CTV codes in customer data without CTV records:")
    for code in missing_codes:
        print(f"   - {code}")
    
    if dry_run:
        print("\n[DRY RUN] Would create these CTVs with nguoi_gioi_thieu = NULL")
        return {'created': 0}
    
    cursor = connection.cursor()
    created = 0
    
    for code in missing_codes:
        try:
            cursor.execute("""
                INSERT INTO ctv (ma_ctv, ten, nguoi_gioi_thieu, cap_bac)
                VALUES (%s, %s, NULL, 'Cong tac vien')
            """, (code, f"CTV {code}"))
            
            CTV_CODE_MAP[code.lower()] = code
            created += 1
            print(f"   Created: {code}")
            
        except Error as e:
            print(f"   ERROR creating CTV {code}: {e}")
    
    connection.commit()
    cursor.close()
    
    print(f"\nCreated {created} missing CTV records")
    return {'created': created}

def import_customers(connection, customers, dry_run=False):
    """Import customers into database"""
    print("\n" + "=" * 60)
    print("IMPORTING CUSTOMERS")
    print("=" * 60)
    
    if dry_run:
        print(f"\n[DRY RUN] Would insert {len(customers)} customers")
        print("\nSample records:")
        for i, cust in enumerate(customers[:5]):
            print(f"   {i+1}. {cust['ten_khach']} - {cust['sdt']} - {cust['nguoi_chot']} - {cust['trang_thai']}")
        return {'inserted': 0, 'skipped': 0, 'errors': 0}
    
    cursor = connection.cursor()
    stats = {'inserted': 0, 'skipped': 0, 'errors': 0}
    
    # Build CTV code lookup from database
    cursor.execute("SELECT ma_ctv FROM ctv")
    valid_ctv_codes = set()
    for row in cursor.fetchall():
        valid_ctv_codes.add(row[0])
        CTV_CODE_MAP[row[0].lower()] = row[0]
    
    batch_size = 100
    batch = []
    
    for customer in customers:
        # Normalize nguoi_chot
        nguoi_chot = customer['nguoi_chot']
        if nguoi_chot:
            normalized = normalize_ctv_code(nguoi_chot)
            if normalized and normalized in valid_ctv_codes:
                nguoi_chot = normalized
            elif nguoi_chot.lower() in CTV_CODE_MAP:
                nguoi_chot = CTV_CODE_MAP[nguoi_chot.lower()]
            else:
                # CTV not found - set to NULL
                nguoi_chot = None
        
        batch.append((
            customer['ngay_nhap_don'],
            customer['ten_khach'],
            customer['sdt'],
            customer['co_so'],
            customer['ngay_hen_lam'],
            customer['gio'],
            customer['dich_vu'],
            customer['tong_tien'],
            customer['tien_coc'],
            customer['phai_dong'],
            nguoi_chot,
            customer['ghi_chu'],
            customer['trang_thai']
        ))
        
        if len(batch) >= batch_size:
            try:
                cursor.executemany("""
                    INSERT INTO khach_hang 
                    (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                     dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch)
                stats['inserted'] += len(batch)
                connection.commit()
            except Error as e:
                print(f"   ERROR inserting batch: {e}")
                stats['errors'] += len(batch)
            
            batch = []
            
            # Progress indicator
            if stats['inserted'] % 1000 == 0:
                print(f"   Inserted {stats['inserted']} customers...")
    
    # Insert remaining batch
    if batch:
        try:
            cursor.executemany("""
                INSERT INTO khach_hang 
                (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                 dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            stats['inserted'] += len(batch)
            connection.commit()
        except Error as e:
            print(f"   ERROR inserting final batch: {e}")
            stats['errors'] += len(batch)
    
    cursor.close()
    
    print(f"\nCustomer Import Complete:")
    print(f"   Inserted: {stats['inserted']}")
    print(f"   Errors: {stats['errors']}")
    
    return stats

# ============================================================
# VERIFICATION
# ============================================================

def verify_import(connection):
    """Verify data integrity after import"""
    print("\n" + "=" * 60)
    print("VERIFYING IMPORT")
    print("=" * 60)
    
    cursor = connection.cursor(dictionary=True)
    
    # CTV count
    cursor.execute("SELECT COUNT(*) as count FROM ctv")
    ctv_count = cursor.fetchone()['count']
    print(f"\nTotal CTVs: {ctv_count}")
    
    # Customer count
    cursor.execute("SELECT COUNT(*) as count FROM khach_hang")
    customer_count = cursor.fetchone()['count']
    print(f"Total Customers: {customer_count}")
    
    # CTV hierarchy depth
    cursor.execute("""
        SELECT 
            cap_bac,
            COUNT(*) as count
        FROM ctv
        GROUP BY cap_bac
        ORDER BY count DESC
    """)
    print("\nCTV by Cap Bac:")
    for row in cursor.fetchall():
        print(f"   {row['cap_bac']}: {row['count']}")
    
    # Customer status distribution
    cursor.execute("""
        SELECT 
            trang_thai,
            COUNT(*) as count,
            SUM(tong_tien) as total_revenue
        FROM khach_hang
        GROUP BY trang_thai
        ORDER BY count DESC
        LIMIT 10
    """)
    print("\nCustomer Status Distribution (Top 10):")
    for row in cursor.fetchall():
        revenue = row['total_revenue'] or 0
        print(f"   {row['trang_thai']}: {row['count']} (Revenue: {revenue:,.0f}d)")
    
    # Top CTVs by customer count
    cursor.execute("""
        SELECT 
            nguoi_chot,
            COUNT(*) as customer_count,
            SUM(tong_tien) as total_revenue
        FROM khach_hang
        WHERE nguoi_chot IS NOT NULL
        GROUP BY nguoi_chot
        ORDER BY total_revenue DESC
        LIMIT 10
    """)
    print("\nTop 10 CTVs by Revenue:")
    for row in cursor.fetchall():
        revenue = row['total_revenue'] or 0
        print(f"   {row['nguoi_chot']}: {row['customer_count']} customers, {revenue:,.0f}d revenue")
    
    # Check orphan references
    cursor.execute("""
        SELECT DISTINCT nguoi_chot 
        FROM khach_hang 
        WHERE nguoi_chot IS NOT NULL 
        AND nguoi_chot NOT IN (SELECT ma_ctv FROM ctv)
    """)
    orphans = cursor.fetchall()
    if orphans:
        print(f"\nWARNING: {len(orphans)} orphan nguoi_chot references:")
        for row in orphans[:10]:
            print(f"   - {row['nguoi_chot']}")
    else:
        print("\nNo orphan references found - all nguoi_chot values are valid")
    
    cursor.close()

# ============================================================
# MAIN
# ============================================================

def main():
    """Main entry point"""
    print("=" * 60)
    print("CSV DATA IMPORT SCRIPT")
    print("=" * 60)
    
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    ctv_only = '--ctv-only' in sys.argv
    customers_only = '--customers-only' in sys.argv
    
    if dry_run:
        print("\n*** DRY RUN MODE - No data will be inserted ***")
    
    # Connect to database
    connection = get_db_connection()
    if not connection:
        print("\nERROR: Failed to connect to database")
        return 1
    
    print("\nConnected to database successfully")
    
    try:
        # Phase 1: Import CTVs
        if not customers_only:
            ctv_list = read_ctv_csv()
            if ctv_list:
                import_ctv(connection, ctv_list, dry_run)
        
        # Phase 2: Import Customers
        if not ctv_only:
            customers, nguoi_chot_set = read_customer_csv()
            
            if customers:
                # Find and create missing CTVs
                missing = find_missing_ctv(connection, nguoi_chot_set)
                if missing:
                    create_missing_ctv(connection, missing, dry_run)
                
                # Import customers
                import_customers(connection, customers, dry_run)
        
        # Phase 3: Verify
        if not dry_run:
            verify_import(connection)
        
        print("\n" + "=" * 60)
        print("IMPORT COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if connection and connection.is_connected():
            connection.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

