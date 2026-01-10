import os
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from modules.mlm_core import calculate_new_commissions_fast

# Configuration
BASE_DIR = Path(__file__).parent.parent.absolute()
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

logger = logging.getLogger(__name__)

class GoogleSheetSync:
    def __init__(self):
        self.client = None
        self.spreadsheet = None

    def get_google_client(self):
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
        return gspread.authorize(credentials)

    def get_db_connection(self):
        return psycopg2.connect(**DB_CONFIG)

    def parse_date(self, date_str):
        if not date_str or not str(date_str).strip(): return None
        date_str = str(date_str).strip()
        formats = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError: continue
        return None

    def parse_money(self, value):
        if value is None or str(value).strip() == '': return 0
        try:
            cleaned = str(value).strip().replace('.', '').replace(',', '')
            return int(float(cleaned))
        except ValueError: return 0

    def clean_phone(self, phone):
        if not phone: return None
        cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
        return cleaned[:15] if cleaned else None

    def normalize_header(self, header):
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

    def find_worksheet(self, spreadsheet, tab_variations):
        worksheets = spreadsheet.worksheets()
        for variation in tab_variations:
            for ws in worksheets:
                if ws.title == variation: return ws
                if ws.title.lower() == variation.lower(): return ws
                if self.normalize_header(ws.title) == self.normalize_header(variation): return ws
        return None

    def insert_khach_hang(self, conn, row_data, tab_type):
        cur = conn.cursor()
        
        if tab_type == 'tham_my':
            ngay_nhap = self.parse_date(row_data.get('Ngay nhap don', ''))
            ten_khach = str(row_data.get('Ten khach', '')).strip()[:100]
            sdt = self.clean_phone(row_data.get('SDT', ''))
            co_so = str(row_data.get('Co So', '')).strip()[:100]
            ngay_lam = self.parse_date(row_data.get('Ngay hen lam', ''))
            gio = str(row_data.get('Gio', '')).strip()[:20]
            dich_vu = str(row_data.get('Dich vu', '')).strip()[:500]
            tong_tien = self.parse_money(row_data.get('Tong', ''))
            tien_coc = self.parse_money(row_data.get('Coc', ''))
            phai_dong = self.parse_money(row_data.get('phai dong', ''))
            nguoi_chot = str(row_data.get('Nguoi chot', '')).strip()[:50] or None
            ghi_chu = str(row_data.get('Ghi Chu', '')).strip()
            trang_thai = str(row_data.get('Trang Thai', '')).strip()[:50] or 'Cho xac nhan'
        else:  # nha_khoa
            ngay_nhap = self.parse_date(row_data.get('Ngay nhap don', ''))
            ten_khach = str(row_data.get('Ten khach hang', '')).strip()[:100]
            sdt = self.clean_phone(row_data.get('So dien thoai', ''))
            co_so = str(row_data.get('Co so', '')).strip()[:100]
            ngay_lam = self.parse_date(row_data.get('Ngay lam', ''))
            gio = str(row_data.get('Gio', '')).strip()[:20]
            dich_vu = str(row_data.get('Dich vu lam', '')).strip()[:500]
            tong_tien = self.parse_money(row_data.get('Gia tong don', ''))
            tien_coc = self.parse_money(row_data.get('Tien coc', ''))
            phai_dong = self.parse_money(row_data.get('Tien con phai tra', ''))
            nguoi_chot = str(row_data.get('Nguoi chot', '')).strip()[:50] or None
            ghi_chu = ''
            trang_thai = 'Cho xac nhan'
        
        if not sdt:
            cur.close()
            return None
        
        # Insert new record
        cur.execute("""
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
                dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (ngay_nhap, ten_khach, sdt, co_so, ngay_lam, gio,
                dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai, tab_type))
        record_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        return record_id

    def insert_gioi_thieu(self, conn, row_data):
        cur = conn.cursor()
        
        ngay_nhap = self.parse_date(row_data.get('Ngay nhap don', ''))
        ten_khach = str(row_data.get('Ten khach hang', '')).strip()[:100]
        sdt = self.clean_phone(row_data.get('So dien thoai', ''))
        dich_vu = str(row_data.get('Dich vu Quan tam', '')).strip()[:500]
        ghi_chu = str(row_data.get('Ghi chu', '')).strip()
        khu_vuc = str(row_data.get('Khu vuc cua khach hang', '')).strip()[:50]
        nguoi_chot = str(row_data.get('SDT nguoi gioi thieu', '')).strip()[:50] or None
        
        if not sdt:
            cur.close()
            return None
        
        if nguoi_chot:
            cur.execute("SELECT 1 FROM ctv WHERE ma_ctv = %s", (nguoi_chot,))
            if not cur.fetchone():
                import hashlib
                import secrets
                salt = secrets.token_hex(16)
                password = 'ctv123'
                hash_obj = hashlib.sha256((salt + password).encode())
                password_hash = f"{salt}:{hash_obj.hexdigest()}"
                cur.execute("INSERT INTO ctv (ma_ctv, ten, password_hash, is_active) VALUES (%s, %s, %s, TRUE)", 
                            (nguoi_chot, nguoi_chot, password_hash))
                logger.info(f"  Created new CTV: {nguoi_chot}")
        
        cur.execute("""
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, dich_vu, ghi_chu, 
             khu_vuc, nguoi_chot, source, trang_thai)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'gioi_thieu', 'Cho xac nhan')
            RETURNING id
        """, (ngay_nhap, ten_khach, sdt, dich_vu, ghi_chu, 
              khu_vuc, nguoi_chot))
        record_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        return record_id

    def update_heartbeat(self, conn, new_records_count=0):
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO commission_cache (cache_key, cache_value, last_updated)
                VALUES ('sync_worker_heartbeat', %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    cache_value = (COALESCE(commission_cache.cache_value::int, 0) + %s)::text,
                    last_updated = CURRENT_TIMESTAMP
            """, (str(new_records_count), new_records_count))
            conn.commit()
            cur.close()
            if new_records_count > 0:
                logger.info(f"Heartbeat updated. New records added: {new_records_count}")
            else:
                logger.info("Heartbeat updated.")
        except Exception as e:
            logger.warning(f"Failed to update heartbeat: {e}")

    def sync_tab_by_count(self, spreadsheet, conn, tab_type, hard_reset=False):
        if tab_type == 'tham_my':
            variations = ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']
        elif tab_type == 'nha_khoa':
            variations = ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']
        else:
            variations = ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral']
        
        worksheet = self.find_worksheet(spreadsheet, variations)
        if not worksheet:
            logger.warning(f"  Tab not found for {tab_type}")
            return 0, 0
        
        logger.info(f"  Found worksheet: {worksheet.title}")
        
        try:
            all_values = worksheet.get_all_values()
        except Exception as e:
            logger.error(f"  Error reading worksheet: {e}")
            return 0, 0
        
        if len(all_values) < 2:
            logger.info(f"  No data rows found")
            return 0, 0
        
        headers = all_values[0]
        normalized_headers = [self.normalize_header(h) for h in headers]
        
        sheet_count = len(all_values) - 1
        
        cur = conn.cursor()
        if hard_reset:
            # For hard reset, we insert EVERYTHING
            db_count = 0
            logger.info("  Hard reset mode: Syncing ALL rows")
        else:
            cur.execute("SELECT COUNT(*) FROM khach_hang WHERE source = %s", (tab_type,))
            db_count = cur.fetchone()[0]
        
        cur.close()
        
        logger.info(f"  Sheet Rows: {sheet_count} | DB Rows: {db_count}")
        
        if sheet_count <= db_count:
            logger.info("  No new rows to sync.")
            return 0, 0
        
        new_rows_count = sheet_count - db_count
        logger.info(f"  Found {new_rows_count} new rows. Importing...")
        
        processed = 0
        errors = 0
        
        start_idx = db_count + 1
        new_rows = all_values[start_idx:]
        
        for i, row in enumerate(new_rows):
            row_idx = start_idx + i + 1
            
            if not row: continue
            
            row_data = {}
            for j, header in enumerate(normalized_headers):
                if j < len(row):
                    row_data[header] = row[j]
            
            try:
                if tab_type in ['tham_my', 'nha_khoa']:
                    record_id = self.insert_khach_hang(conn, row_data, tab_type)
                    if record_id:
                        if processed % 50 == 0:
                            logger.info(f"    ... Inserted {processed} rows ...")
                        processed += 1
                else:
                    record_id = self.insert_gioi_thieu(conn, row_data)
                    if record_id:
                        if processed % 50 == 0:
                            logger.info(f"    ... Inserted {processed} rows ...")
                        processed += 1
            except Exception as e:
                conn.rollback()
                logger.error(f"    Row {row_idx}: Error - {e}")
                errors += 1
                
        return processed, errors

    def hard_reset(self):
        """
        Deletes all data from khach_hang for specified sources and re-syncs everything.
        """
        stats = {
            'tham_my': {'processed': 0, 'errors': 0},
            'nha_khoa': {'processed': 0, 'errors': 0},
            'gioi_thieu': {'processed': 0, 'errors': 0}
        }
        
        try:
            logger.info("Connecting to Google Sheets...")
            client = self.get_google_client()
            spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
            
            logger.info("Connecting to database...")
            conn = self.get_db_connection()
            
            # 1. Clear existing data
            logger.info("CLEARING EXISTING DATA...")
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM khach_hang 
                WHERE source IN ('tham_my', 'nha_khoa', 'gioi_thieu')
            """)
            deleted_count = cur.rowcount
            logger.info(f"Deleted {deleted_count} records from khach_hang.")
            
            # Also clear commissions related to these transactions? 
            # Ideally commissions are linked via foreign keys or IDs. 
            # If we delete transactions, we should probably clear commissions too to avoid orphans/inconsistencies.
            # However, the current commission logic might rely on transaction IDs. 
            # If we re-import, we get NEW IDs. So old commissions pointing to old IDs are invalid.
            # Assuming cascading delete or manual cleanup is needed.
            # For now, let's just assume we need to recalculate from scratch.
            
            cur.execute("DELETE FROM commissions WHERE level >= 0") # Clear all commissions to be safe and re-calc
            logger.info("Cleared all commissions.")
            
            conn.commit()
            cur.close()
            
            # 2. Re-import everything
            logger.info("\n--- Processing Tham My (Full Import) ---")
            p, e = self.sync_tab_by_count(spreadsheet, conn, 'tham_my', hard_reset=True)
            stats['tham_my'] = {'processed': p, 'errors': e}
            
            logger.info("\n--- Processing Nha Khoa (Full Import) ---")
            p, e = self.sync_tab_by_count(spreadsheet, conn, 'nha_khoa', hard_reset=True)
            stats['nha_khoa'] = {'processed': p, 'errors': e}
            
            logger.info("\n--- Processing Gioi Thieu (Full Import) ---")
            p, e = self.sync_tab_by_count(spreadsheet, conn, 'gioi_thieu', hard_reset=True)
            stats['gioi_thieu'] = {'processed': p, 'errors': e}
            
            # 3. Recalculate commissions
            if sum(s['processed'] for s in stats.values()) > 0:
                logger.info("\n--- Recalculating Commissions ---")
                comm_stats = calculate_new_commissions_fast(connection=conn)
                logger.info(f"Commission calculation: {comm_stats}")
            
            # Update heartbeat
            total_new = sum(s['processed'] for s in stats.values())
            self.update_heartbeat(conn, total_new)
            
            conn.close()
            return True, stats
            
        except Exception as e:
            logger.error(f"Hard reset error: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
