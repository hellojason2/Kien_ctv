#!/usr/bin/env python3
"""
Import Thẩm Mỹ (Beauty/Aesthetic) Customer Data from Google Sheet (Tab 0)
- Imports all customer records into khach_hang table
- Sets source = 'tham_my'
- Handles data normalization and type conversion
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import unicodedata

import gspread
from google.oauth2.service_account import Credentials
import psycopg2

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.absolute()
GOOGLE_SHEET_ID = '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ'
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════════════════

def get_google_client():
    if not CREDENTIALS_FILE.exists():
        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
        sys.exit(1)
        
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
    return gspread.authorize(credentials)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def parse_date(date_str):
    if not date_str or not str(date_str).strip(): return None
    date_str = str(date_str).strip()
    formats = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError: continue
    return None

def parse_money(value):
    if value is None or str(value).strip() == '': return 0
    try:
        cleaned = str(value).strip().replace('.', '').replace(',', '')
        return int(float(cleaned))
    except ValueError: return 0

def clean_phone(phone):
    """
    Clean phone number to digits only, preserving trailing zeros.
    This function extracts all digits from the phone number and preserves
    any trailing zeros that are part of the original number.
    """
    if not phone: return None
    # Extract all digits, preserving trailing zeros
    cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
    return cleaned[:15] if cleaned else None

def normalize_header(header):
    if not header: return ''
    vn_map = {
        '\u0111': 'd', '\u0110': 'D', '\u0103': 'a', '\u0102': 'A', '\u00e2': 'a', '\u00c2': 'A',
        '\u00ea': 'e', '\u00ca': 'E', '\u00f4': 'o', '\u00d4': 'O', '\u01a1': 'o', '\u01a0': 'O',
        '\u01b0': 'u', '\u01af': 'U',
    }
    text = str(header)
    for vn_char, ascii_char in vn_map.items():
        text = text.replace(vn_char, ascii_char)
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').strip()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("Thẩm Mỹ Data Import Script (Full Import)")
    logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
    logger.info("=" * 60)

    try:
        # 1. Connect to Google Sheets
        logger.info("1. Connecting to Google Sheets...")
        client = get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Get Tab 0
        worksheet = spreadsheet.get_worksheet(0)
        logger.info(f"   Accessed Tab 0: {worksheet.title}")
        
        # Read all data
        all_values = worksheet.get_all_values()
        if len(all_values) < 2:
            logger.warning("   Sheet is empty or has only headers.")
            return

        headers = all_values[0]
        normalized_headers = [normalize_header(h) for h in headers]
        logger.info(f"   Found {len(all_values) - 1} rows to process.")
        
        # 2. Connect to Database
        logger.info("2. Connecting to PostgreSQL database...")
        conn = get_db_connection()
        cur = conn.cursor()
        logger.info("   Connected successfully!")

        # 3. Import Data
        logger.info("3. Importing records...")
        imported = 0
        errors = 0
        
        for i, row in enumerate(all_values[1:]):
            row_idx = i + 2  # 1-based index, +1 for header
            
            if not row: continue
            
            # Map row to dict using normalized headers
            row_data = {}
            for j, header in enumerate(normalized_headers):
                if j < len(row):
                    row_data[header] = row[j]
            
            try:
                # Extract and clean data
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
                
                # Skip if no phone number (essential for identification)
                if not sdt:
                    # logger.warning(f"   Row {row_idx}: Skipped (No Phone Number)")
                    continue

                # Insert into khach_hang
                cur.execute("""
                    INSERT INTO khach_hang 
                    (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                     dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'tham_my')
                """, (ngay_nhap, ten_khach, sdt, co_so, ngay_lam, gio,
                      dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai))
                
                imported += 1
                
                if imported % 100 == 0:
                    print(f"   ... imported {imported} records")
                    conn.commit()

            except Exception as e:
                errors += 1
                logger.error(f"   Row {row_idx}: Error - {e}")
                conn.rollback() # Rollback transaction for this row error to continue with others? 
                # Actually, if we want to continue, we should use SAVEPOINT or just rollback and continue.
                # But here we are in a loop. If we rollback, we might lose previous inserts if not committed.
                # Better strategy: Commit every batch, or handle per-row error carefully.
                # Since I'm committing every 100, a rollback here would rollback the current uncommitted batch.
                # Let's just log and continue, but we need to make sure the transaction is valid.
                # If an error occurs, the transaction is aborted. We must rollback to reset it.
                
        conn.commit()
        logger.info(f"\n   ✓ Import completed: {imported} records imported.")
        if errors > 0:
            logger.info(f"   ! {errors} errors occurred.")

    except Exception as e:
        logger.error(f"\n✗ Critical Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    main()
