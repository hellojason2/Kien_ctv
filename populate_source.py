#!/usr/bin/env python3
"""
Populate Source Column Script
- Reads Google Sheets
- Updates 'source' column in database for existing records
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import RealDictCursor

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.absolute()
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ')
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'

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

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════════════════

def get_google_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
    return gspread.authorize(credentials)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def clean_phone(phone):
    if not phone: return None
    cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
    return cleaned[:15] if cleaned else None

def normalize_header(header):
    import unicodedata
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

def find_worksheet(spreadsheet, tab_variations):
    worksheets = spreadsheet.worksheets()
    for variation in tab_variations:
        for ws in worksheets:
            if ws.title == variation: return ws
            if ws.title.lower() == variation.lower(): return ws
            if normalize_header(ws.title) == normalize_header(variation): return ws
    return None

# ══════════════════════════════════════════════════════════════════════════════
# LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def update_khach_hang_source(conn, row_data, tab_type):
    cur = conn.cursor()
    
    if tab_type == 'tham_my':
        sdt = clean_phone(row_data.get('SDT', ''))
    else:
        sdt = clean_phone(row_data.get('So dien thoai', ''))
    
    if not sdt:
        cur.close()
        return False

    # Find record by phone
    cur.execute("SELECT id FROM khach_hang WHERE sdt = %s ORDER BY id DESC LIMIT 1", (sdt,))
    existing = cur.fetchone()
    
    if existing:
        record_id = existing[0]
        cur.execute("UPDATE khach_hang SET source = %s WHERE id = %s", (tab_type, record_id))
        conn.commit()
        cur.close()
        return True
    
    print(f"DEBUG: No match for {sdt} in {tab_type}")
    cur.close()
    return False

def update_services_source(conn, row_data):
    cur = conn.cursor()
    
    phone = clean_phone(row_data.get('So dien thoai', ''))
    service_name = str(row_data.get('Dich vu Quan tam', '')).strip()[:200]
    
    if not phone:
        cur.close()
        return False

    # Find customer
    cur.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
    customer = cur.fetchone()
    
    if customer:
        customer_id = customer[0]
        # Find service
        cur.execute("SELECT id FROM services WHERE customer_id = %s AND service_name = %s LIMIT 1", (customer_id, service_name))
        service = cur.fetchone()
        
        if service:
            service_id = service[0]
            cur.execute("UPDATE services SET source = 'gioi_thieu' WHERE id = %s", (service_id,))
            conn.commit()
            cur.close()
            return True
        else:
            print(f"DEBUG: No service match for {phone} - {service_name}")
    else:
        print(f"DEBUG: No customer match for {phone}")
            
    cur.close()
    return False

def process_tab(spreadsheet, conn, tab_type):
    if tab_type == 'tham_my':
        variations = ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']
    elif tab_type == 'nha_khoa':
        variations = ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']
    else:
        variations = ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral']
    
    worksheet = find_worksheet(spreadsheet, variations)
    if not worksheet:
        logger.warning(f"Tab not found: {tab_type}")
        return 0
    
    logger.info(f"Processing {tab_type} from {worksheet.title}...")
    all_values = worksheet.get_all_values()
    if len(all_values) < 2: return 0
    
    headers = all_values[0]
    normalized_headers = [normalize_header(h) for h in headers]
    
    updated_count = 0
    for row in all_values[1:]:
        if not row: continue
        
        row_data = {}
        for i, header in enumerate(normalized_headers):
            if i < len(row):
                row_data[header] = row[i]
        
        if tab_type in ['tham_my', 'nha_khoa']:
            if update_khach_hang_source(conn, row_data, tab_type):
                updated_count += 1
        else:
            if update_services_source(conn, row_data):
                updated_count += 1
                
    return updated_count

def main():
    logger.info("Starting Source Population...")
    client = get_google_client()
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    conn = get_db_connection()
    
    count_tm = process_tab(spreadsheet, conn, 'tham_my')
    logger.info(f"Updated {count_tm} records for Tham My")
    
    count_nk = process_tab(spreadsheet, conn, 'nha_khoa')
    logger.info(f"Updated {count_nk} records for Nha Khoa")
    
    count_gt = process_tab(spreadsheet, conn, 'gioi_thieu')
    logger.info(f"Updated {count_gt} records for Gioi Thieu")
    
    conn.close()
    logger.info("Done.")

if __name__ == '__main__':
    main()
