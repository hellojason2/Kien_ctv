#!/usr/bin/env python3
"""
Database Integrity Check Script

This script helps diagnose sync issues between Google Sheets and the database.
It can:
1. Check if a specific phone number exists in Google Sheet and database
2. Compare row counts between sheet and database
3. List missing phone numbers (in sheet but not in DB)
4. Check heartbeat status of sync worker

Usage:
    python check_database_integrity.py --phone 0332901077
    python check_database_integrity.py --integrity
    python check_database_integrity.py --missing --tab tham_my
    python check_database_integrity.py --heartbeat
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from modules.google_sync import GoogleSheetSync, GOOGLE_SHEET_ID, DB_CONFIG
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def check_phone(phone):
    """Check if a phone number exists in Google Sheet and database"""
    print(f"\n{'='*60}")
    print(f"📱 Checking phone: {phone}")
    print(f"{'='*60}")
    
    # Clean phone number
    phone_digits = ''.join(c for c in phone if c.isdigit())
    phone_suffix = phone_digits[-8:] if len(phone_digits) >= 8 else phone_digits
    
    print(f"  Cleaned: {phone_digits}")
    print(f"  Suffix (last 8): {phone_suffix}")
    
    # Check database
    print(f"\n📊 Checking Database...")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, ten_khach, sdt, co_so, ngay_nhap_don, ngay_hen_lam, 
                       dich_vu, tong_tien, nguoi_chot, source, trang_thai
                FROM khach_hang
                WHERE sdt = %s 
                   OR sdt LIKE %s
                   OR sdt LIKE %s
                ORDER BY ngay_nhap_don DESC NULLS LAST
                LIMIT 10
            """, (phone_digits, '%' + phone_suffix, phone_suffix + '%'))
            
            records = cursor.fetchall()
            if records:
                print(f"  ✅ Found {len(records)} record(s) in database:")
                for r in records:
                    print(f"     - ID: {r['id']}, Name: {r['ten_khach']}, Phone: {r['sdt']}")
                    print(f"       Service: {r['dich_vu'][:50]}..." if r['dich_vu'] and len(r['dich_vu']) > 50 else f"       Service: {r['dich_vu']}")
                    print(f"       Source: {r['source']}, Date: {r['ngay_nhap_don']}, Status: {r['trang_thai']}")
            else:
                print(f"  ❌ NOT FOUND in database!")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            conn.close()
    
    # Check Google Sheet
    print(f"\n📋 Checking Google Sheets...")
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        tabs_config = [
            ('tham_my', ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']),
            ('nha_khoa', ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']),
            ('gioi_thieu', ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral'])
        ]
        
        found_in_sheet = False
        for tab_type, variations in tabs_config:
            worksheet = syncer.find_worksheet(spreadsheet, variations)
            if not worksheet:
                continue
            
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                continue
            
            headers = all_values[0]
            normalized_headers = [syncer.normalize_header(h) for h in headers]
            
            # Find phone column
            phone_col_idx = None
            for idx, h in enumerate(normalized_headers):
                if 'sdt' in h.lower() or 'dien thoai' in h.lower() or 'phone' in h.lower():
                    phone_col_idx = idx
                    break
            
            if phone_col_idx is None:
                continue
            
            # Search for phone
            for row_idx, row in enumerate(all_values[1:], start=2):
                if phone_col_idx < len(row):
                    row_phone = syncer.clean_phone(row[phone_col_idx])
                    if row_phone and (row_phone == phone_digits or 
                                      row_phone.endswith(phone_suffix) or 
                                      phone_suffix in row_phone):
                        found_in_sheet = True
                        print(f"  ✅ Found in {tab_type} tab, row {row_idx}:")
                        print(f"     Phone: {row[phone_col_idx]}")
                        if len(row) > 1:
                            print(f"     Name: {row[1]}")
                        if len(row) > 2 and row[2]:
                            print(f"     Service/Info: {row[2][:50]}...")
        
        if not found_in_sheet:
            print(f"  ❌ NOT FOUND in Google Sheets!")
            
    except Exception as e:
        print(f"  ❌ Google Sheets error: {e}")
    
    print(f"\n{'='*60}")
    print("DIAGNOSIS:")
    print(f"{'='*60}")


def check_integrity():
    """Compare row counts between Google Sheet and database"""
    print(f"\n{'='*60}")
    print("📊 Database Integrity Check")
    print(f"{'='*60}")
    
    # Get database counts
    print("\n📊 Database counts:")
    conn = get_db_connection()
    db_counts = {}
    
    if conn:
        try:
            cursor = conn.cursor()
            for source in ['tham_my', 'nha_khoa', 'gioi_thieu']:
                cursor.execute("SELECT COUNT(*) FROM khach_hang WHERE source = %s", (source,))
                count = cursor.fetchone()[0]
                db_counts[source] = count
                print(f"  {source}: {count:,} records")
            
            # Get heartbeat
            cursor.execute("""
                SELECT last_updated, cache_value 
                FROM commission_cache 
                WHERE cache_key = 'sync_worker_heartbeat'
            """)
            heartbeat = cursor.fetchone()
            if heartbeat:
                print(f"\n⏰ Sync Worker Heartbeat:")
                print(f"  Last run: {heartbeat[0]}")
                print(f"  New records since reset: {heartbeat[1]}")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            conn.close()
    
    # Get Google Sheet counts
    print("\n📋 Google Sheets counts:")
    sheet_counts = {}
    
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        tabs_config = [
            ('tham_my', ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']),
            ('nha_khoa', ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']),
            ('gioi_thieu', ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral'])
        ]
        
        for tab_type, variations in tabs_config:
            worksheet = syncer.find_worksheet(spreadsheet, variations)
            if worksheet:
                all_values = worksheet.get_all_values()
                count = len(all_values) - 1 if len(all_values) > 1 else 0
                sheet_counts[tab_type] = count
                print(f"  {tab_type}: {count:,} rows")
            else:
                print(f"  {tab_type}: ❌ Tab not found!")
                
    except Exception as e:
        print(f"  ❌ Google Sheets error: {e}")
    
    # Compare
    print(f"\n{'='*60}")
    print("📈 Comparison (Sheet - Database):")
    print(f"{'='*60}")
    
    has_discrepancy = False
    for source in ['tham_my', 'nha_khoa', 'gioi_thieu']:
        sheet = sheet_counts.get(source, 0)
        db = db_counts.get(source, 0)
        diff = sheet - db
        
        if diff == 0:
            status = "✅"
        elif diff > 0:
            status = "⚠️  MISSING FROM DB"
            has_discrepancy = True
        else:
            status = "⚠️  EXTRA IN DB"
            has_discrepancy = True
        
        print(f"  {source}: {diff:+d} ({sheet:,} sheet, {db:,} DB) {status}")
    
    if has_discrepancy:
        print(f"\n⚠️  Discrepancies detected! Run with --missing to find specific issues.")
        print(f"    Or use 'Force Sync' in admin panel to fix.")


def find_missing_phones(tab_filter=None, limit=50):
    """Find phones that are in Google Sheet but not in database"""
    print(f"\n{'='*60}")
    print("🔍 Finding Missing Phone Numbers")
    print(f"{'='*60}")
    
    # Get all phones from database
    print("\n📊 Loading database phones...")
    conn = get_db_connection()
    db_phones = set()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT sdt FROM khach_hang WHERE sdt IS NOT NULL")
            db_phones = set(row[0] for row in cursor.fetchall())
            print(f"  Loaded {len(db_phones):,} unique phone numbers from database")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            conn.close()
            return
    
    # Check Google Sheets
    print("\n📋 Scanning Google Sheets...")
    missing = []
    
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        tabs_config = [
            ('tham_my', ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']),
            ('nha_khoa', ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']),
            ('gioi_thieu', ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral'])
        ]
        
        if tab_filter:
            tabs_config = [(t, v) for t, v in tabs_config if t == tab_filter]
        
        for tab_type, variations in tabs_config:
            print(f"  Checking {tab_type}...")
            
            worksheet = syncer.find_worksheet(spreadsheet, variations)
            if not worksheet:
                print(f"    ❌ Tab not found")
                continue
            
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                print(f"    No data rows")
                continue
            
            headers = all_values[0]
            normalized_headers = [syncer.normalize_header(h) for h in headers]
            
            # Find phone column
            phone_col_idx = None
            for idx, h in enumerate(normalized_headers):
                if 'sdt' in h.lower() or 'dien thoai' in h.lower() or 'phone' in h.lower():
                    phone_col_idx = idx
                    break
            
            if phone_col_idx is None:
                print(f"    ❌ Phone column not found")
                continue
            
            # Find missing
            tab_missing = 0
            for row_idx, row in enumerate(all_values[1:], start=2):
                if len(missing) >= limit:
                    break
                    
                if phone_col_idx < len(row):
                    sheet_phone = syncer.clean_phone(row[phone_col_idx])
                    if sheet_phone and sheet_phone not in db_phones:
                        # Double check with suffix matching
                        phone_suffix = sheet_phone[-8:] if len(sheet_phone) >= 8 else sheet_phone
                        found = any(db_phone.endswith(phone_suffix) for db_phone in db_phones)
                        
                        if not found:
                            name = row[1] if len(row) > 1 else ''
                            missing.append({
                                'phone': sheet_phone,
                                'name': name,
                                'tab': tab_type,
                                'row': row_idx
                            })
                            tab_missing += 1
            
            print(f"    Found {tab_missing} missing phones")
        
    except Exception as e:
        print(f"  ❌ Google Sheets error: {e}")
        return
    
    # Print results
    print(f"\n{'='*60}")
    print(f"📋 Missing Phones (showing first {limit}):")
    print(f"{'='*60}")
    
    if missing:
        for m in missing:
            print(f"  Row {m['row']:4d} | {m['tab']:12s} | {m['phone']:15s} | {m['name'][:30]}")
        
        print(f"\n⚠️  Total missing: {len(missing)}")
        print(f"    Use 'Force Sync' in admin panel to sync these records.")
    else:
        print("  ✅ No missing phones found!")


def check_heartbeat():
    """Check sync worker heartbeat status"""
    print(f"\n{'='*60}")
    print("⏰ Sync Worker Heartbeat Status")
    print(f"{'='*60}")
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT last_updated, cache_value 
                FROM commission_cache 
                WHERE cache_key = 'sync_worker_heartbeat'
            """)
            heartbeat = cursor.fetchone()
            
            if heartbeat and heartbeat['last_updated']:
                last_run = heartbeat['last_updated']
                now = datetime.now(last_run.tzinfo) if last_run.tzinfo else datetime.now()
                age = now - last_run
                
                print(f"\n  Last sync: {last_run}")
                print(f"  Time ago: {age}")
                print(f"  New records since reset: {heartbeat['cache_value']}")
                
                if age.total_seconds() < 60:
                    print(f"\n  ✅ Sync worker is running (synced less than 1 minute ago)")
                elif age.total_seconds() < 300:
                    print(f"\n  ✅ Sync worker is running (synced within 5 minutes)")
                else:
                    print(f"\n  ⚠️  Sync worker may be stopped (last sync was {age} ago)")
            else:
                print(f"\n  ❌ No heartbeat found - sync worker may never have run")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            conn.close()


def main():
    parser = argparse.ArgumentParser(description='Database Integrity Check Tool')
    parser.add_argument('--phone', '-p', type=str, help='Check a specific phone number')
    parser.add_argument('--integrity', '-i', action='store_true', help='Run full integrity check')
    parser.add_argument('--missing', '-m', action='store_true', help='Find missing phone numbers')
    parser.add_argument('--heartbeat', '-b', action='store_true', help='Check sync worker heartbeat')
    parser.add_argument('--tab', '-t', type=str, choices=['tham_my', 'nha_khoa', 'gioi_thieu'],
                        help='Filter by tab (for --missing)')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Limit results (for --missing)')
    
    args = parser.parse_args()
    
    if args.phone:
        check_phone(args.phone)
    elif args.integrity:
        check_integrity()
    elif args.missing:
        find_missing_phones(args.tab, args.limit)
    elif args.heartbeat:
        check_heartbeat()
    else:
        # Default: show integrity check and heartbeat
        check_integrity()
        check_heartbeat()
        print(f"\n{'='*60}")
        print("TIP: Run with --help to see all options")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
