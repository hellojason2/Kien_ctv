#!/usr/bin/env python3
"""
Google Sheets Live Sync Worker
- Syncs data from Google Sheets to PostgreSQL database
- Processes rows marked "update" in Column A
- Marks rows as "DONE" after successful database upsert
- Runs every 30 seconds

DOES: Syncs 3 tabs from Google Sheets to database
INPUTS: Google Sheet ID, credentials
OUTPUTS: Database records, Sheet status updates
FLOW: Connect -> Read Sheet -> Process Rows -> Upsert DB -> Mark Done
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import RealDictCursor
from modules.mlm.commissions import recalculate_commissions_for_record
from modules.mlm_core import calculate_new_commissions_fast

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent.absolute()

# Google Sheets Configuration
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ')
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'

# Tab names in the Google Sheet
TAB_THAM_MY = 'Khach hang Tham my'  # Will try variations
TAB_NHA_KHOA = 'Khach hang Nha khoa'
TAB_GIOI_THIEU = 'Khach gioi thieu'

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
        'sslmode': 'require'
    }
else:
    DB_CONFIG = {
        'host': os.getenv('PGHOST', 'caboose.proxy.rlwy.net'),
        'port': int(os.getenv('PGPORT', 34643)),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl'),
        'database': os.getenv('PGDATABASE', 'railway'),
        'sslmode': 'require'
    }

# Sync interval in seconds
SYNC_INTERVAL = 30

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE SHEETS CONNECTION
# ══════════════════════════════════════════════════════════════════════════════

def get_google_client():
    """
    DOES: Authenticate with Google Sheets API
    RETURNS: gspread.Client object
    """
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_file(
        str(CREDENTIALS_FILE),
        scopes=scopes
    )
    
    return gspread.authorize(credentials)


def get_spreadsheet(client):
    """
    DOES: Open the Google Spreadsheet by ID
    RETURNS: gspread.Spreadsheet object
    """
    return client.open_by_key(GOOGLE_SHEET_ID)


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ══════════════════════════════════════════════════════════════════════════════

def get_db_connection():
    """
    DOES: Create a new database connection
    RETURNS: psycopg2 connection object
    """
    return psycopg2.connect(**DB_CONFIG)


# ══════════════════════════════════════════════════════════════════════════════
# DATE/MONEY PARSING UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def parse_date(date_str):
    """
    DOES: Parse date from DD/MM/YYYY format
    INPUTS: date_str (string)
    RETURNS: datetime.date or None
    """
    if not date_str or not str(date_str).strip():
        return None
    date_str = str(date_str).strip()
    
    formats = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_money(value):
    """
    DOES: Parse money value, return 0 if empty
    INPUTS: value (string or number)
    RETURNS: int
    """
    if value is None or str(value).strip() == '':
        return 0
    try:
        cleaned = str(value).strip().replace('.', '').replace(',', '')
        return int(float(cleaned))
    except ValueError:
        return 0


def clean_phone(phone):
    """
    DOES: Clean phone number - remove non-digits, normalize, limit to 15 chars
    INPUTS: phone (string)
    RETURNS: string or None
    """
    if not phone:
        return None
    cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
    # Limit to 15 characters (database constraint)
    return cleaned[:15] if cleaned else None


# ══════════════════════════════════════════════════════════════════════════════
# THAM MY / NHA KHOA UPSERT LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def upsert_khach_hang(conn, row_data, tab_type):
    """
    DOES: Insert or update a khach_hang record based on phone number
    INPUTS: conn (db connection), row_data (dict), tab_type ('tham_my' or 'nha_khoa')
    RETURNS: (action, record_id) tuple - action is 'insert' or 'update'
    """
    cur = conn.cursor()
    
    # Extract fields based on tab type
    if tab_type == 'tham_my':
        ngay_nhap = parse_date(row_data.get('Ngay nhap don', ''))
        ten_khach = str(row_data.get('Ten khach', '')).strip()[:100]
        sdt = clean_phone(row_data.get('SDT', ''))
        co_so = str(row_data.get('Co So', '')).strip()[:100]
        ngay_lam = parse_date(row_data.get('Ngay hen lam', ''))
        gio = str(row_data.get('Gio', '')).strip()[:20]
        dich_vu = str(row_data.get('Dich vu', '')).strip()[:500]
        tong_tien = parse_money(row_data.get('Tong', ''))
        tien_coc = parse_money(row_data.get('Coc', ''))
        phai_dong = parse_money(row_data.get('phai dong', ''))
        nguoi_chot = str(row_data.get('Nguoi chot', '')).strip()[:50] or None
        ghi_chu = str(row_data.get('Ghi Chu', '')).strip()
        trang_thai = str(row_data.get('Trang Thai', '')).strip()[:50] or 'Cho xac nhan'
    else:  # nha_khoa
        ngay_nhap = parse_date(row_data.get('Ngay nhap don', ''))
        ten_khach = str(row_data.get('Ten khach hang', '')).strip()[:100]
        sdt = clean_phone(row_data.get('So dien thoai', ''))
        co_so = str(row_data.get('Co so', '')).strip()[:100]
        ngay_lam = parse_date(row_data.get('Ngay lam', ''))
        gio = str(row_data.get('Gio', '')).strip()[:20]
        dich_vu = str(row_data.get('Dich vu lam', '')).strip()[:500]
        tong_tien = parse_money(row_data.get('Gia tong don', ''))
        tien_coc = parse_money(row_data.get('Tien coc', ''))
        phai_dong = parse_money(row_data.get('Tien con phai tra', ''))
        nguoi_chot = str(row_data.get('Nguoi chot', '')).strip()[:50] or None
        ghi_chu = ''
        trang_thai = 'Cho xac nhan'
    
    if not sdt:
        cur.close()
        return None, None
    
    # Check if record exists by phone number
    cur.execute("SELECT id FROM khach_hang WHERE sdt = %s ORDER BY id DESC LIMIT 1", (sdt,))
    existing = cur.fetchone()
    
    if existing:
        # UPDATE existing record
        record_id = existing[0]
        cur.execute("""
            UPDATE khach_hang SET
                ngay_nhap_don = COALESCE(%s, ngay_nhap_don),
                ten_khach = COALESCE(NULLIF(%s, ''), ten_khach),
                co_so = COALESCE(NULLIF(%s, ''), co_so),
                ngay_hen_lam = COALESCE(%s, ngay_hen_lam),
                gio = COALESCE(NULLIF(%s, ''), gio),
                dich_vu = COALESCE(NULLIF(%s, ''), dich_vu),
                tong_tien = CASE WHEN %s > 0 THEN %s ELSE tong_tien END,
                tien_coc = CASE WHEN %s > 0 THEN %s ELSE tien_coc END,
                phai_dong = CASE WHEN %s > 0 THEN %s ELSE phai_dong END,
                nguoi_chot = COALESCE(%s, nguoi_chot),
                ghi_chu = COALESCE(NULLIF(%s, ''), ghi_chu),
                trang_thai = COALESCE(NULLIF(%s, ''), trang_thai),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            ngay_nhap, ten_khach, co_so, ngay_lam, gio, dich_vu,
            tong_tien, tong_tien, tien_coc, tien_coc, phai_dong, phai_dong,
            nguoi_chot, ghi_chu, trang_thai, record_id
        ))
        action = 'update'
    else:
        # INSERT new record
        cur.execute("""
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
             dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (ngay_nhap, ten_khach, sdt, co_so, ngay_lam, gio,
              dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai))
        record_id = cur.fetchone()[0]
        action = 'insert'
    
    conn.commit()
    cur.close()
    return action, record_id


# ══════════════════════════════════════════════════════════════════════════════
# KHACH GIOI THIEU (REFERRAL) UPSERT LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def upsert_gioi_thieu(conn, row_data):
    """
    DOES: Insert or update a customer and service record for referrals
    INPUTS: conn (db connection), row_data (dict)
    RETURNS: (action, customer_id, service_id) tuple
    """
    cur = conn.cursor()
    
    # Extract fields
    phone = clean_phone(row_data.get('So dien thoai', ''))
    name = str(row_data.get('Ten khach hang', '')).strip()[:100]
    ctv_code = str(row_data.get('SDT nguoi gioi thieu', '')).strip() or None
    service_name = str(row_data.get('Dich vu Quan tam', '')).strip()[:200]
    date_entered = parse_date(row_data.get('Ngay nhap don', ''))
    
    if not phone:
        cur.close()
        return None, None, None
    
    # Check if customer exists
    cur.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
    customer = cur.fetchone()
    
    if customer:
        customer_id = customer[0]
        # Update customer name if provided
        if name:
            cur.execute("UPDATE customers SET name = %s WHERE id = %s", (name, customer_id))
        customer_action = 'existing'
    else:
        # Create new customer
        cur.execute("""
            INSERT INTO customers (name, phone)
            VALUES (%s, %s)
            RETURNING id
        """, (name or 'Unknown', phone))
        customer_id = cur.fetchone()[0]
        customer_action = 'new'
    
    # Check if CTV exists, create if not
    if ctv_code:
        cur.execute("SELECT 1 FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        if not cur.fetchone():
            # Create CTV account with default password
            import hashlib
            import secrets
            salt = secrets.token_hex(16)
            password = 'ctv123'
            hash_obj = hashlib.sha256((salt + password).encode())
            password_hash = f"{salt}:{hash_obj.hexdigest()}"
            
            cur.execute("""
                INSERT INTO ctv (ma_ctv, ten, password_hash, is_active)
                VALUES (%s, %s, %s, TRUE)
            """, (ctv_code, ctv_code, password_hash))
            logger.info(f"  Created new CTV: {ctv_code}")
    
    # Check if service already exists for this customer + service name
    cur.execute("""
        SELECT id FROM services 
        WHERE customer_id = %s AND service_name = %s AND ctv_code = %s
        LIMIT 1
    """, (customer_id, service_name, ctv_code))
    existing_service = cur.fetchone()
    
    if existing_service:
        service_id = existing_service[0]
        # Update date if provided
        if date_entered:
            cur.execute("UPDATE services SET date_entered = %s WHERE id = %s", (date_entered, service_id))
        service_action = 'update'
    else:
        # Create new service record
        cur.execute("""
            INSERT INTO services 
            (customer_id, service_name, date_entered, ctv_code, status)
            VALUES (%s, %s, %s, %s, 'Cho xu ly')
            RETURNING id
        """, (customer_id, service_name, date_entered, ctv_code))
        service_id = cur.fetchone()[0]
        service_action = 'insert'
    
    conn.commit()
    cur.close()
    return f"{customer_action}/{service_action}", customer_id, service_id


# ══════════════════════════════════════════════════════════════════════════════
# SHEET PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def normalize_header(header):
    """
    DOES: Normalize header text by removing diacritics and special Vietnamese chars
    INPUTS: header (string)
    RETURNS: normalized string (ASCII-safe)
    """
    import unicodedata
    if not header:
        return ''
    
    # Vietnamese character replacements (using Unicode escapes for reliability)
    vn_map = {
        '\u0111': 'd', '\u0110': 'D',  # d, D (d-stroke)
        '\u0103': 'a', '\u0102': 'A',  # a, A (a-breve)
        '\u00e2': 'a', '\u00c2': 'A',  # a, A (a-circumflex)
        '\u00ea': 'e', '\u00ca': 'E',  # e, E (e-circumflex)
        '\u00f4': 'o', '\u00d4': 'O',  # o, O (o-circumflex)
        '\u01a1': 'o', '\u01a0': 'O',  # o, O (o-horn)
        '\u01b0': 'u', '\u01af': 'U',  # u, U (u-horn)
    }
    
    text = str(header)
    
    # Replace Vietnamese special letters first
    for vn_char, ascii_char in vn_map.items():
        text = text.replace(vn_char, ascii_char)
    
    # Remove diacritics (accents)
    normalized = unicodedata.normalize('NFD', text)
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    return ascii_text.strip()


def find_worksheet(spreadsheet, tab_variations):
    """
    DOES: Find a worksheet by trying multiple name variations
    INPUTS: spreadsheet (gspread.Spreadsheet), tab_variations (list of strings)
    RETURNS: gspread.Worksheet or None
    """
    worksheets = spreadsheet.worksheets()
    worksheet_titles = [ws.title for ws in worksheets]
    
    for variation in tab_variations:
        for ws in worksheets:
            # Try exact match first
            if ws.title == variation:
                return ws
            # Try case-insensitive match
            if ws.title.lower() == variation.lower():
                return ws
            # Try normalized match
            if normalize_header(ws.title) == normalize_header(variation):
                return ws
    
    return None


def process_tham_my_nha_khoa(spreadsheet, conn, tab_type):
    """
    DOES: Process Tham My or Nha Khoa tab
    INPUTS: spreadsheet, conn (db connection), tab_type ('tham_my' or 'nha_khoa')
    RETURNS: (processed_count, error_count)
    """
    if tab_type == 'tham_my':
        variations = ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']
    else:
        variations = ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']
    
    worksheet = find_worksheet(spreadsheet, variations)
    if not worksheet:
        logger.warning(f"  Tab not found for {tab_type}, tried: {variations}")
        return 0, 0
    
    logger.info(f"  Found worksheet: {worksheet.title}")
    
    # Get all records
    try:
        all_values = worksheet.get_all_values()
    except Exception as e:
        logger.error(f"  Error reading worksheet: {e}")
        return 0, 0
    
    if len(all_values) < 2:
        logger.info(f"  No data rows found")
        return 0, 0
    
    headers = all_values[0]
    # Normalize headers for matching
    normalized_headers = [normalize_header(h) for h in headers]
    
    processed = 0
    errors = 0
    rows_to_update = []
    
    for row_idx, row in enumerate(all_values[1:], start=2):  # Row 2 onwards (1-indexed in Sheets)
        if len(row) == 0:
            continue
        
        # Check Column A (Update status)
        status = str(row[0]).strip().lower() if row else ''
        
        # Process if status is 'update' or empty (default behavior)
        if status == 'update' or status == '':
            # Build row data dict
            row_data = {}
            for i, header in enumerate(normalized_headers):
                if i < len(row):
                    row_data[header] = row[i]
            
            try:
                action, record_id = upsert_khach_hang(conn, row_data, tab_type)
                if action:
                    logger.info(f"    Row {row_idx}: {action} (ID: {record_id})")
                    
                    # Trigger commission calculation
                    try:
                        recalculate_commissions_for_record(record_id, 'khach_hang', conn)
                        logger.info(f"      -> Commission recalculated for khach_hang {record_id}")
                    except Exception as comm_e:
                        logger.error(f"      -> Commission calc error: {comm_e}")
                        
                    rows_to_update.append(row_idx)
                    processed += 1
                else:
                    logger.debug(f"    Row {row_idx}: Skipped (no phone)")
            except Exception as e:
                conn.rollback()  # Reset transaction state
                logger.error(f"    Row {row_idx}: Error - {e}")
                errors += 1
    
    # Batch update Column A to 'DONE' using batch_update for efficiency
    if rows_to_update:
        try:
            # Build batch update data
            cells_to_update = []
            for row_idx in rows_to_update:
                cells_to_update.append({
                    'range': f'A{row_idx}',
                    'values': [['DONE']]
                })
            
            # Batch update in chunks of 50 to avoid quota limits
            chunk_size = 50
            for i in range(0, len(cells_to_update), chunk_size):
                chunk = cells_to_update[i:i + chunk_size]
                worksheet.batch_update(chunk)
                if i + chunk_size < len(cells_to_update):
                    import time
                    time.sleep(1)  # Rate limit pause
            
            logger.info(f"  Marked {len(rows_to_update)} rows as DONE")
        except Exception as e:
            logger.error(f"  Error updating sheet status: {e}")
    
    return processed, errors


def process_gioi_thieu(spreadsheet, conn):
    """
    DOES: Process Khach Gioi Thieu (referral) tab
    INPUTS: spreadsheet, conn (db connection)
    RETURNS: (processed_count, error_count)
    """
    variations = ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral']
    
    worksheet = find_worksheet(spreadsheet, variations)
    if not worksheet:
        logger.warning(f"  Tab not found for Gioi Thieu, tried: {variations}")
        return 0, 0
    
    logger.info(f"  Found worksheet: {worksheet.title}")
    
    # Get all records
    try:
        all_values = worksheet.get_all_values()
    except Exception as e:
        logger.error(f"  Error reading worksheet: {e}")
        return 0, 0
    
    if len(all_values) < 2:
        logger.info(f"  No data rows found")
        return 0, 0
    
    headers = all_values[0]
    normalized_headers = [normalize_header(h) for h in headers]
    
    processed = 0
    errors = 0
    rows_to_update = []
    
    for row_idx, row in enumerate(all_values[1:], start=2):
        if len(row) == 0:
            continue
        
        status = str(row[0]).strip().lower() if row else ''
        
        if status == 'update' or status == '':
            row_data = {}
            for i, header in enumerate(normalized_headers):
                if i < len(row):
                    row_data[header] = row[i]
            
            try:
                action, customer_id, service_id = upsert_gioi_thieu(conn, row_data)
                if action:
                    logger.info(f"    Row {row_idx}: {action} (Customer: {customer_id}, Service: {service_id})")
                    
                    # Trigger commission calculation
                    try:
                        recalculate_commissions_for_record(service_id, 'service', conn)
                        logger.info(f"      -> Commission recalculated for service {service_id}")
                    except Exception as comm_e:
                        logger.error(f"      -> Commission calc error: {comm_e}")
                        
                    rows_to_update.append(row_idx)
                    processed += 1
                else:
                    logger.debug(f"    Row {row_idx}: Skipped (no phone)")
            except Exception as e:
                conn.rollback()  # Reset transaction state
                logger.error(f"    Row {row_idx}: Error - {e}")
                errors += 1
    
    # Batch update Column A to 'DONE' using batch_update for efficiency
    if rows_to_update:
        try:
            cells_to_update = []
            for row_idx in rows_to_update:
                cells_to_update.append({
                    'range': f'A{row_idx}',
                    'values': [['DONE']]
                })
            
            # Batch update in chunks of 50 to avoid quota limits
            chunk_size = 50
            for i in range(0, len(cells_to_update), chunk_size):
                chunk = cells_to_update[i:i + chunk_size]
                worksheet.batch_update(chunk)
                if i + chunk_size < len(cells_to_update):
                    time.sleep(1)  # Rate limit pause
            
            logger.info(f"  Marked {len(rows_to_update)} rows as DONE")
        except Exception as e:
            logger.error(f"  Error updating sheet status: {e}")
    
    return processed, errors


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SYNC LOOP
# ══════════════════════════════════════════════════════════════════════════════

def run_sync():
    """
    DOES: Run one sync cycle - process all tabs
    RETURNS: dict with processing stats
    """
    stats = {
        'tham_my': {'processed': 0, 'errors': 0},
        'nha_khoa': {'processed': 0, 'errors': 0},
        'gioi_thieu': {'processed': 0, 'errors': 0}
    }
    
    try:
        # Connect to Google Sheets
        logger.info("Connecting to Google Sheets...")
        client = get_google_client()
        spreadsheet = get_spreadsheet(client)
        logger.info(f"Connected to: {spreadsheet.title}")
        
        # List all worksheets for debugging
        worksheets = spreadsheet.worksheets()
        logger.info(f"Available tabs: {[ws.title for ws in worksheets]}")
        
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_db_connection()
        logger.info("Database connected")
        
        # Process each tab
        logger.info("\n--- Processing Tham My ---")
        p, e = process_tham_my_nha_khoa(spreadsheet, conn, 'tham_my')
        stats['tham_my'] = {'processed': p, 'errors': e}
        
        logger.info("\n--- Processing Nha Khoa ---")
        p, e = process_tham_my_nha_khoa(spreadsheet, conn, 'nha_khoa')
        stats['nha_khoa'] = {'processed': p, 'errors': e}
        
        logger.info("\n--- Processing Gioi Thieu ---")
        p, e = process_gioi_thieu(spreadsheet, conn)
        stats['gioi_thieu'] = {'processed': p, 'errors': e}
        
        # Trigger commission calculation for any new records
        logger.info("\n--- Calculating Commissions ---")
        comm_stats = calculate_new_commissions_fast(connection=conn)
        logger.info(f"Commission calculation: {comm_stats}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
        import traceback
        traceback.print_exc()
    
    return stats


def main():
    """
    DOES: Main entry point - runs continuous sync loop
    """
    logger.info("=" * 60)
    logger.info("Google Sheets Live Sync Worker")
    logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
    logger.info(f"Sync Interval: {SYNC_INTERVAL} seconds")
    logger.info("=" * 60)
    
    # Check credentials file exists
    if not CREDENTIALS_FILE.exists():
        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
        logger.error("Please ensure google_credentials.json exists in the project root")
        sys.exit(1)
    
    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Sync Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        stats = run_sync()
        
        # Summary
        total_processed = sum(s['processed'] for s in stats.values())
        total_errors = sum(s['errors'] for s in stats.values())
        logger.info(f"\nCycle #{cycle} Complete:")
        logger.info(f"  - Tham My: {stats['tham_my']['processed']} processed, {stats['tham_my']['errors']} errors")
        logger.info(f"  - Nha Khoa: {stats['nha_khoa']['processed']} processed, {stats['nha_khoa']['errors']} errors")
        logger.info(f"  - Gioi Thieu: {stats['gioi_thieu']['processed']} processed, {stats['gioi_thieu']['errors']} errors")
        logger.info(f"  - Total: {total_processed} processed, {total_errors} errors")
        
        logger.info(f"\nSleeping for {SYNC_INTERVAL} seconds...")
        time.sleep(SYNC_INTERVAL)


if __name__ == '__main__':
    main()
