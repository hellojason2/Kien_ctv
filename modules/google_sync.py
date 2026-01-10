import os
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import execute_values

# Configuration
BASE_DIR = Path(__file__).parent.parent.absolute()
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ')
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'

# Batch size for bulk inserts - process this many rows before committing
BATCH_SIZE = 500

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
        'sslmode': 'require',
        'connect_timeout': 30,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5
    }
else:
    DB_CONFIG = {
        'host': os.getenv('PGHOST', 'caboose.proxy.rlwy.net'),
        'port': int(os.getenv('PGPORT', 34643)),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl'),
        'database': os.getenv('PGDATABASE', 'railway'),
        'sslmode': 'require',
        'connect_timeout': 30,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5
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
        """Get a fresh database connection with keepalive settings"""
        return psycopg2.connect(**DB_CONFIG)

    def ensure_connection(self, conn):
        """Check if connection is alive, reconnect if needed"""
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return conn
        except Exception as e:
            logger.warning(f"Connection lost, reconnecting... ({e})")
            try:
                conn.close()
            except:
                pass
            return self.get_db_connection()

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

    def prepare_khach_hang_row(self, row_data, tab_type):
        """Prepare a single row for bulk insert into khach_hang"""
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
            return None
        
        return (ngay_nhap, ten_khach, sdt, co_so, ngay_lam, gio,
                dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai, tab_type)

    def prepare_gioi_thieu_row(self, row_data):
        """Prepare a single row for bulk insert into khach_hang (gioi_thieu)"""
        ngay_nhap = self.parse_date(row_data.get('Ngay nhap don', ''))
        ten_khach = str(row_data.get('Ten khach hang', '')).strip()[:100]
        sdt = self.clean_phone(row_data.get('So dien thoai', ''))
        dich_vu = str(row_data.get('Dich vu Quan tam', '')).strip()[:500]
        ghi_chu = str(row_data.get('Ghi chu', '')).strip()
        khu_vuc = str(row_data.get('Khu vuc cua khach hang', '')).strip()[:50]
        nguoi_chot = str(row_data.get('SDT nguoi gioi thieu', '')).strip()[:50] or None
        
        if not sdt:
            return None, None
        
        return (ngay_nhap, ten_khach, sdt, dich_vu, ghi_chu, khu_vuc, nguoi_chot), nguoi_chot

    def bulk_insert_khach_hang(self, conn, rows, tab_type):
        """Bulk insert rows into khach_hang table"""
        if not rows:
            return 0
        
        cur = conn.cursor()
        
        insert_sql = """
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
             dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai, source)
            VALUES %s
        """
        
        try:
            execute_values(cur, insert_sql, rows, page_size=BATCH_SIZE)
            conn.commit()
            inserted = len(rows)
            cur.close()
            return inserted
        except Exception as e:
            conn.rollback()
            cur.close()
            raise e

    def bulk_insert_gioi_thieu(self, conn, rows, ctv_phones):
        """Bulk insert referral rows and create CTVs if needed"""
        if not rows:
            return 0
        
        cur = conn.cursor()
        
        # First, create any missing CTVs
        unique_ctvs = set(p for p in ctv_phones if p)
        if unique_ctvs:
            # Check which CTVs already exist
            cur.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = ANY(%s)", (list(unique_ctvs),))
            existing = set(row[0] for row in cur.fetchall())
            
            # Create missing CTVs
            new_ctvs = unique_ctvs - existing
            if new_ctvs:
                import hashlib
                import secrets
                ctv_rows = []
                for phone in new_ctvs:
                    salt = secrets.token_hex(16)
                    password = 'ctv123'
                    hash_obj = hashlib.sha256((salt + password).encode())
                    password_hash = f"{salt}:{hash_obj.hexdigest()}"
                    ctv_rows.append((phone, phone, password_hash, True))
                
                execute_values(cur, 
                    "INSERT INTO ctv (ma_ctv, ten, password_hash, is_active) VALUES %s ON CONFLICT DO NOTHING",
                    ctv_rows)
                logger.info(f"  Created {len(new_ctvs)} new CTV accounts")
        
        # Now insert the referral records
        insert_sql = """
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, dich_vu, ghi_chu, khu_vuc, nguoi_chot, source, trang_thai)
            VALUES %s
        """
        
        # Add source and trang_thai to each row
        full_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], 'gioi_thieu', 'Cho xac nhan') for r in rows]
        
        try:
            execute_values(cur, insert_sql, full_rows, page_size=BATCH_SIZE)
            conn.commit()
            inserted = len(rows)
            cur.close()
            return inserted
        except Exception as e:
            conn.rollback()
            cur.close()
            raise e

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
        except Exception as e:
            logger.warning(f"Failed to update heartbeat: {e}")

    def sync_tab_by_count(self, spreadsheet, conn, tab_type, hard_reset=False):
        """Sync a tab from Google Sheets to database with batch processing"""
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
        
        # Ensure connection is alive
        conn = self.ensure_connection(conn)
        
        cur = conn.cursor()
        if hard_reset:
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
        logger.info(f"  Found {new_rows_count} rows to import. Processing in batches of {BATCH_SIZE}...")
        
        processed = 0
        errors = 0
        
        start_idx = db_count + 1
        new_rows = all_values[start_idx:]
        
        # Process in batches
        batch = []
        ctv_phones = []  # For gioi_thieu only
        
        for i, row in enumerate(new_rows):
            if not row: 
                continue
            
            row_data = {}
            for j, header in enumerate(normalized_headers):
                if j < len(row):
                    row_data[header] = row[j]
            
            try:
                if tab_type in ['tham_my', 'nha_khoa']:
                    prepared = self.prepare_khach_hang_row(row_data, tab_type)
                    if prepared:
                        batch.append(prepared)
                else:  # gioi_thieu
                    prepared, ctv_phone = self.prepare_gioi_thieu_row(row_data)
                    if prepared:
                        batch.append(prepared)
                        ctv_phones.append(ctv_phone)
                
                # Commit batch when full
                if len(batch) >= BATCH_SIZE:
                    # Ensure connection before batch insert
                    conn = self.ensure_connection(conn)
                    
                    if tab_type in ['tham_my', 'nha_khoa']:
                        inserted = self.bulk_insert_khach_hang(conn, batch, tab_type)
                    else:
                        inserted = self.bulk_insert_gioi_thieu(conn, batch, ctv_phones)
                    
                    processed += inserted
                    logger.info(f"    Batch committed: {processed}/{new_rows_count} rows processed")
                    batch = []
                    ctv_phones = []
                    
            except Exception as e:
                logger.error(f"    Row {start_idx + i + 1}: Error - {e}")
                errors += 1
        
        # Commit remaining rows
        if batch:
            try:
                conn = self.ensure_connection(conn)
                
                if tab_type in ['tham_my', 'nha_khoa']:
                    inserted = self.bulk_insert_khach_hang(conn, batch, tab_type)
                else:
                    inserted = self.bulk_insert_gioi_thieu(conn, batch, ctv_phones)
                
                processed += inserted
                logger.info(f"    Final batch committed: {processed}/{new_rows_count} rows processed")
            except Exception as e:
                logger.error(f"    Final batch error: {e}")
                errors += len(batch)
        
        logger.info(f"  Completed: {processed} inserted, {errors} errors")
        return processed, errors

    def hard_reset(self):
        """
        Deletes all data from khach_hang for specified sources and re-syncs everything.
        Uses batch processing to handle large datasets without timeouts.
        """
        stats = {
            'tham_my': {'processed': 0, 'errors': 0},
            'nha_khoa': {'processed': 0, 'errors': 0},
            'gioi_thieu': {'processed': 0, 'errors': 0}
        }
        
        conn = None
        
        try:
            logger.info("=" * 60)
            logger.info("HARD RESET - Starting")
            logger.info("=" * 60)
            
            logger.info("Connecting to Google Sheets...")
            client = self.get_google_client()
            spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
            logger.info("Google Sheets connected successfully")
            
            logger.info("Connecting to database...")
            conn = self.get_db_connection()
            logger.info("Database connected successfully")
            
            # 1. Clear existing data
            logger.info("\n--- STEP 1: Clearing existing data ---")
            cur = conn.cursor()
            
            # Delete in smaller chunks to avoid lock timeout
            logger.info("Deleting khach_hang records...")
            cur.execute("""
                DELETE FROM khach_hang 
                WHERE source IN ('tham_my', 'nha_khoa', 'gioi_thieu')
            """)
            deleted_count = cur.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted_count} records from khach_hang")
            
            logger.info("Deleting commission records...")
            cur.execute("DELETE FROM commissions WHERE level >= 0")
            deleted_comm = cur.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted_comm} commission records")
            
            cur.close()
            
            # 2. Re-import everything with batch processing
            logger.info("\n--- STEP 2: Importing Thẩm Mỹ (Beauty) ---")
            conn = self.ensure_connection(conn)
            p, e = self.sync_tab_by_count(spreadsheet, conn, 'tham_my', hard_reset=True)
            stats['tham_my'] = {'processed': p, 'errors': e}
            logger.info(f"Thẩm Mỹ complete: {p} records, {e} errors")
            
            logger.info("\n--- STEP 3: Importing Nha Khoa (Dental) ---")
            conn = self.ensure_connection(conn)
            p, e = self.sync_tab_by_count(spreadsheet, conn, 'nha_khoa', hard_reset=True)
            stats['nha_khoa'] = {'processed': p, 'errors': e}
            logger.info(f"Nha Khoa complete: {p} records, {e} errors")
            
            logger.info("\n--- STEP 4: Importing Giới Thiệu (Referral) ---")
            conn = self.ensure_connection(conn)
            p, e = self.sync_tab_by_count(spreadsheet, conn, 'gioi_thieu', hard_reset=True)
            stats['gioi_thieu'] = {'processed': p, 'errors': e}
            logger.info(f"Giới Thiệu complete: {p} records, {e} errors")
            
            # 3. Recalculate commissions
            total_processed = sum(s['processed'] for s in stats.values())
            if total_processed > 0:
                logger.info("\n--- STEP 5: Recalculating Commissions ---")
                conn = self.ensure_connection(conn)
                try:
                    from modules.mlm_core import calculate_new_commissions_fast
                    comm_stats = calculate_new_commissions_fast(connection=conn)
                    logger.info(f"Commission calculation complete: {comm_stats}")
                except Exception as e:
                    logger.warning(f"Commission calculation warning: {e}")
            
            # Update heartbeat
            conn = self.ensure_connection(conn)
            self.update_heartbeat(conn, total_processed)
            
            logger.info("\n" + "=" * 60)
            logger.info("HARD RESET - Complete")
            logger.info(f"Total imported: {total_processed} records")
            logger.info("=" * 60)
            
            conn.close()
            return True, stats
            
        except Exception as e:
            logger.error(f"Hard reset error: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                try:
                    conn.close()
                except:
                    pass
            return False, str(e)
