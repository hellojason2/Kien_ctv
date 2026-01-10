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
        success, stats, _ = self.hard_reset_with_logs()
        return success, stats

    def hard_reset_with_logs(self):
        """
        Deletes all data from khach_hang for specified sources and re-syncs everything.
        Returns detailed logs for frontend display.
        """
        stats = {
            'tham_my': {'processed': 0, 'errors': 0, 'total_rows': 0},
            'nha_khoa': {'processed': 0, 'errors': 0, 'total_rows': 0},
            'gioi_thieu': {'processed': 0, 'errors': 0, 'total_rows': 0}
        }
        
        logs = []
        conn = None
        
        def add_log(message, log_type='info', step='general'):
            logs.append({'message': message, 'type': log_type, 'step': step})
            if log_type == 'error':
                logger.error(message)
            elif log_type == 'warning':
                logger.warning(message)
            else:
                logger.info(message)
        
        try:
            add_log("=" * 50, 'info', 'start')
            add_log("HARD RESET - Starting", 'info', 'start')
            add_log("=" * 50, 'info', 'start')
            
            # Connect to Google Sheets
            add_log("Connecting to Google Sheets...", 'info', 'connect')
            try:
                client = self.get_google_client()
                spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
                add_log("✓ Google Sheets connected successfully", 'success', 'connect')
            except Exception as e:
                add_log(f"✗ Failed to connect to Google Sheets: {e}", 'error', 'connect')
                return False, stats, logs
            
            # Connect to database
            add_log("Connecting to database...", 'info', 'connect')
            try:
                conn = self.get_db_connection()
                add_log("✓ Database connected successfully", 'success', 'connect')
            except Exception as e:
                add_log(f"✗ Failed to connect to database: {e}", 'error', 'connect')
                return False, stats, logs
            
            # STEP 1: Clear existing data
            add_log("", 'info', 'delete')
            add_log("--- STEP 1: Clearing existing data ---", 'info', 'delete')
            
            try:
                cur = conn.cursor()
                
                add_log("Deleting khach_hang records...", 'info', 'delete')
                cur.execute("""
                    DELETE FROM khach_hang 
                    WHERE source IN ('tham_my', 'nha_khoa', 'gioi_thieu')
                """)
                deleted_count = cur.rowcount
                conn.commit()
                add_log(f"✓ Deleted {deleted_count:,} records from khach_hang", 'success', 'delete')
                
                add_log("Deleting commission records...", 'info', 'delete')
                cur.execute("DELETE FROM commissions WHERE level >= 0")
                deleted_comm = cur.rowcount
                conn.commit()
                add_log(f"✓ Deleted {deleted_comm:,} commission records", 'success', 'delete')
                
                cur.close()
            except Exception as e:
                add_log(f"✗ Error clearing data: {e}", 'error', 'delete')
                if conn:
                    conn.rollback()
                return False, stats, logs
            
            # STEP 2: Import Thẩm Mỹ (Beauty)
            add_log("", 'info', 'beauty')
            add_log("--- STEP 2: Importing Thẩm Mỹ (Beauty) ---", 'info', 'beauty')
            
            try:
                conn = self.ensure_connection(conn)
                p, e, tab_logs = self.sync_tab_with_logs(spreadsheet, conn, 'tham_my', hard_reset=True)
                stats['tham_my'] = {'processed': p, 'errors': e}
                logs.extend(tab_logs)
                
                if e > 0:
                    add_log(f"⚠ Thẩm Mỹ: {p:,} imported, {e} errors", 'warning', 'beauty')
                else:
                    add_log(f"✓ Thẩm Mỹ complete: {p:,} records imported", 'success', 'beauty')
            except Exception as e:
                add_log(f"✗ Thẩm Mỹ import failed: {e}", 'error', 'beauty')
                stats['tham_my']['errors'] = 1
            
            # STEP 3: Import Nha Khoa (Dental)
            add_log("", 'info', 'dental')
            add_log("--- STEP 3: Importing Nha Khoa (Dental) ---", 'info', 'dental')
            
            try:
                conn = self.ensure_connection(conn)
                p, e, tab_logs = self.sync_tab_with_logs(spreadsheet, conn, 'nha_khoa', hard_reset=True)
                stats['nha_khoa'] = {'processed': p, 'errors': e}
                logs.extend(tab_logs)
                
                if e > 0:
                    add_log(f"⚠ Nha Khoa: {p:,} imported, {e} errors", 'warning', 'dental')
                else:
                    add_log(f"✓ Nha Khoa complete: {p:,} records imported", 'success', 'dental')
            except Exception as e:
                add_log(f"✗ Nha Khoa import failed: {e}", 'error', 'dental')
                stats['nha_khoa']['errors'] = 1
            
            # STEP 4: Import Giới Thiệu (Referral)
            add_log("", 'info', 'referral')
            add_log("--- STEP 4: Importing Giới Thiệu (Referral) ---", 'info', 'referral')
            
            try:
                conn = self.ensure_connection(conn)
                p, e, tab_logs = self.sync_tab_with_logs(spreadsheet, conn, 'gioi_thieu', hard_reset=True)
                stats['gioi_thieu'] = {'processed': p, 'errors': e}
                logs.extend(tab_logs)
                
                if e > 0:
                    add_log(f"⚠ Giới Thiệu: {p:,} imported, {e} errors", 'warning', 'referral')
                else:
                    add_log(f"✓ Giới Thiệu complete: {p:,} records imported", 'success', 'referral')
            except Exception as e:
                add_log(f"✗ Giới Thiệu import failed: {e}", 'error', 'referral')
                stats['gioi_thieu']['errors'] = 1
            
            # STEP 5: Recalculate commissions
            total_processed = sum(s['processed'] for s in stats.values())
            total_errors = sum(s['errors'] for s in stats.values())
            
            if total_processed > 0:
                add_log("", 'info', 'commission')
                add_log("--- STEP 5: Recalculating Commissions ---", 'info', 'commission')
                
                try:
                    conn = self.ensure_connection(conn)
                    from modules.mlm_core import calculate_new_commissions_fast
                    comm_stats = calculate_new_commissions_fast(connection=conn)
                    add_log(f"✓ Commission calculation complete", 'success', 'commission')
                    if comm_stats:
                        add_log(f"  Commissions calculated: {comm_stats}", 'info', 'commission')
                except Exception as e:
                    add_log(f"⚠ Commission calculation warning: {e}", 'warning', 'commission')
            
            # Update heartbeat
            try:
                conn = self.ensure_connection(conn)
                self.update_heartbeat(conn, total_processed)
            except:
                pass
            
            # Final summary
            add_log("", 'info', 'complete')
            add_log("=" * 50, 'info', 'complete')
            add_log("HARD RESET - Complete", 'success', 'complete')
            add_log(f"Total imported: {total_processed:,} records", 'success', 'complete')
            if total_errors > 0:
                add_log(f"Total errors: {total_errors}", 'warning', 'complete')
            add_log("=" * 50, 'info', 'complete')
            
            if conn:
                conn.close()
            
            return True, stats, logs
            
        except Exception as e:
            add_log(f"✗ CRITICAL ERROR: {e}", 'error', 'exception')
            import traceback
            add_log(traceback.format_exc(), 'error', 'exception')
            
            if conn:
                try:
                    conn.close()
                except:
                    pass
            return False, stats, logs

    def sync_tab_with_logs(self, spreadsheet, conn, tab_type, hard_reset=False):
        """Sync a tab from Google Sheets to database with batch processing and logging"""
        logs = []
        
        def add_log(message, log_type='info'):
            logs.append({'message': message, 'type': log_type, 'step': tab_type})
        
        if tab_type == 'tham_my':
            variations = ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']
            tab_name = 'Thẩm Mỹ'
        elif tab_type == 'nha_khoa':
            variations = ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']
            tab_name = 'Nha Khoa'
        else:
            variations = ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral']
            tab_name = 'Giới Thiệu'
        
        worksheet = self.find_worksheet(spreadsheet, variations)
        if not worksheet:
            add_log(f"✗ Tab not found for {tab_name}", 'error')
            return 0, 1, logs
        
        add_log(f"Found worksheet: {worksheet.title}", 'info')
        
        try:
            add_log(f"Reading data from Google Sheets...", 'info')
            all_values = worksheet.get_all_values()
            add_log(f"✓ Data loaded from sheet", 'success')
        except Exception as e:
            add_log(f"✗ Error reading worksheet: {e}", 'error')
            return 0, 1, logs
        
        if len(all_values) < 2:
            add_log(f"No data rows found in {tab_name}", 'warning')
            return 0, 0, logs
        
        headers = all_values[0]
        normalized_headers = [self.normalize_header(h) for h in headers]
        
        sheet_count = len(all_values) - 1
        add_log(f"Total rows in sheet: {sheet_count:,}", 'info')
        
        conn = self.ensure_connection(conn)
        
        cur = conn.cursor()
        if hard_reset:
            db_count = 0
        else:
            cur.execute("SELECT COUNT(*) FROM khach_hang WHERE source = %s", (tab_type,))
            db_count = cur.fetchone()[0]
        cur.close()
        
        if sheet_count <= db_count:
            add_log(f"No new rows to sync (DB has {db_count:,} rows)", 'info')
            return 0, 0, logs
        
        new_rows_count = sheet_count - db_count
        add_log(f"Rows to import: {new_rows_count:,}", 'info')
        add_log(f"Processing in batches of {BATCH_SIZE}...", 'info')
        
        processed = 0
        errors = 0
        error_details = []
        
        start_idx = db_count + 1
        new_rows = all_values[start_idx:]
        
        batch = []
        ctv_phones = []
        batch_num = 0
        
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
                else:
                    prepared, ctv_phone = self.prepare_gioi_thieu_row(row_data)
                    if prepared:
                        batch.append(prepared)
                        ctv_phones.append(ctv_phone)
                
                if len(batch) >= BATCH_SIZE:
                    batch_num += 1
                    conn = self.ensure_connection(conn)
                    
                    if tab_type in ['tham_my', 'nha_khoa']:
                        inserted = self.bulk_insert_khach_hang(conn, batch, tab_type)
                    else:
                        inserted = self.bulk_insert_gioi_thieu(conn, batch, ctv_phones)
                    
                    processed += inserted
                    progress_pct = round((processed / new_rows_count) * 100, 1)
                    add_log(f"Batch {batch_num}: {processed:,}/{new_rows_count:,} ({progress_pct}%)", 'info')
                    batch = []
                    ctv_phones = []
                    
            except Exception as e:
                row_num = start_idx + i + 1
                error_msg = f"Row {row_num}: {str(e)[:100]}"
                error_details.append(error_msg)
                errors += 1
                if errors <= 5:  # Only log first 5 errors in detail
                    add_log(f"✗ {error_msg}", 'error')
        
        # Commit remaining rows
        if batch:
            try:
                batch_num += 1
                conn = self.ensure_connection(conn)
                
                if tab_type in ['tham_my', 'nha_khoa']:
                    inserted = self.bulk_insert_khach_hang(conn, batch, tab_type)
                else:
                    inserted = self.bulk_insert_gioi_thieu(conn, batch, ctv_phones)
                
                processed += inserted
                add_log(f"Final batch {batch_num}: {processed:,}/{new_rows_count:,} (100%)", 'info')
            except Exception as e:
                add_log(f"✗ Final batch error: {e}", 'error')
                errors += len(batch)
        
        # Summary
        if errors > 5:
            add_log(f"... and {errors - 5} more errors", 'warning')
        
        add_log(f"Completed: {processed:,} inserted, {errors} errors", 'success' if errors == 0 else 'warning')
        
        return processed, errors, logs
