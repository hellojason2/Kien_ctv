#!/usr/bin/env python3
"""
Google Sheets Live Sync Worker (Hybrid Mode)
- Syncs data from Google Sheets to PostgreSQL database
- For Tham My: Uses phone matching to detect updates AND new rows (catches mid-sheet edits)
- For Nha Khoa & Gioi Thieu: Uses phone matching for full sync
- Syncs pricing data from a separate Google Sheet
- Runs every 30 seconds
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from modules.google_sync import GoogleSheetSync
from modules.mlm_core import calculate_new_commissions_fast

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

SYNC_INTERVAL = 30
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ')
PRICING_SHEET_ID = '19YZB-SgpqvI3-hu93xOk0OCDWtUPxrAAfR6CiFpU4GY'
BASE_DIR = Path(__file__).parent.absolute()
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'
# Environment variable for credentials (JSON string) - used in production
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')

# Use phone matching sync (processes ALL rows, detects updates)
# Set to 'false' to use old count-based sync (only appends new rows at end)
USE_PHONE_MATCHING = os.getenv('SYNC_USE_PHONE_MATCHING', 'true').lower() == 'true'

# Optional: timestamp column name for detecting changed rows
# If set, only rows with timestamp > last_sync will be processed
TIMESTAMP_COLUMN = os.getenv('SYNC_TIMESTAMP_COLUMN', None)

# Custom Database Handler
class DBLogHandler(logging.Handler):
    def __init__(self, syncer):
        super().__init__()
        self.syncer = syncer
        self.conn = None
        
    def emit(self, record):
        try:
            msg = self.format(record)
            if not self.conn or self.conn.closed:
                self.conn = self.syncer.get_db_connection()
                
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO worker_logs (level, message, created_at, source) VALUES (%s, %s, %s, 'sync_worker')",
                        (record.levelname, msg, datetime.now())
                    )
                self.conn.commit()
        except Exception:
            # Fallback to stderr if DB logging fails
            import sys
            sys.stderr.write(f"Failed to log to DB: {record.msg}\n")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def _sync_single_tab(syncer, spreadsheet, conn, tab_type, use_phone_matching, timestamp_column):
    """Sync a single tab with error isolation. Returns (processed, errors)."""
    try:
        logger.info(f"\n--- Processing {tab_type.replace('_', ' ').title()} ---")
        if use_phone_matching:
            p, e = syncer.sync_tab_by_phone_matching(spreadsheet, conn, tab_type, timestamp_column)
        else:
            p, e = syncer.sync_tab_by_count(spreadsheet, conn, tab_type)
        return p, e
    except Exception as e:
        logger.error(f"  Tab {tab_type} error: {e}")
        return 0, 1


def run_sync(syncer, use_phone_matching=True, timestamp_column=None):
    """Run the main data sync (tham_my, nha_khoa, gioi_thieu).
    Each tab syncs independently — one tab failing won't skip the others.
    """
    stats = {
        'tham_my': {'processed': 0, 'errors': 0},
        'nha_khoa': {'processed': 0, 'errors': 0},
        'gioi_thieu': {'processed': 0, 'errors': 0}
    }
    
    try:
        logger.info("Connecting to Google Sheets...")
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        logger.info("Connecting to database...")
        conn = syncer.get_db_connection()
        
        try:
            sync_mode = "phone matching" if use_phone_matching else "count-based"
            logger.info(f"Sync mode: {sync_mode}")
            if timestamp_column:
                logger.info(f"Timestamp column: {timestamp_column}")
            
            # Sync each tab independently (one failure doesn't block the others)
            for tab_type in ['tham_my', 'nha_khoa', 'gioi_thieu']:
                p, e = _sync_single_tab(syncer, spreadsheet, conn, tab_type, use_phone_matching, timestamp_column)
                stats[tab_type] = {'processed': p, 'errors': e}
            
            if sum(s['processed'] for s in stats.values()) > 0:
                logger.info("\n--- Calculating Commissions ---")
                start_time = time.time()
                comm_stats = calculate_new_commissions_fast(connection=conn)
                duration = time.time() - start_time
                logger.info(f"Commission calculation: {comm_stats} (took {duration:.2f}s)")
            
            # Update heartbeat after successful sync with count of new records
            total_new = sum(s['processed'] for s in stats.values())
            syncer.update_heartbeat(conn, total_new)
            
        except Exception as e:
            raise e
        finally:
            if conn:
                conn.close()
                logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
        import traceback
        traceback.print_exc()
    
    return stats


def run_pricing_sync(syncer):
    """Run the pricing sheet sync independently.
    Uses its own Google client call and has internal retry logic.
    """
    try:
        from modules.pricing_sync import sync_pricing_sheet
        client = syncer.get_google_client()
        result = sync_pricing_sheet(client, PRICING_SHEET_ID)
        if result > 0:
            logger.info(f"  ✅ Pricing Data: Synced successfully ({result} categories)")
        else:
            logger.warning("  ⚠️ Pricing Data: Sync returned 0 categories")
    except Exception as e:
        logger.error(f"  ❌ Pricing Sync Error: {e}")


def main():
    logger.info("=" * 60)
    logger.info("Google Sheets Live Sync Worker (Hybrid Mode)")
    logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
    logger.info(f"Pricing Sheet ID: {PRICING_SHEET_ID}")
    logger.info(f"Phone Matching: {'enabled' if USE_PHONE_MATCHING else 'disabled (count-based)'}")
    if TIMESTAMP_COLUMN:
        logger.info(f"Timestamp Column: {TIMESTAMP_COLUMN}")
    logger.info("=" * 60)
    
    # Check for credentials (either env var or file)
    if not GOOGLE_CREDENTIALS_JSON and not CREDENTIALS_FILE.exists():
        logger.error("Google credentials not found!")
        logger.error("Please set GOOGLE_CREDENTIALS_JSON env var or add google_credentials.json file")
        sys.exit(1)
    
    if GOOGLE_CREDENTIALS_JSON:
        logger.info("Using Google credentials from environment variable")
    else:
        logger.info(f"Using Google credentials from file: {CREDENTIALS_FILE}")
    
    syncer = GoogleSheetSync()
    
    # Add Database Logger
    db_handler = None
    try:
        db_handler = DBLogHandler(syncer)
        db_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s') # Cleaner logs for UI
        db_handler.setFormatter(formatter)
        logging.getLogger().addHandler(db_handler)
        logger.info("Database logging enabled")
    except Exception as e:
        logger.error(f"Failed to setup DB logging: {e}")
    
    cycle = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 10  # After 10 failures, wait longer
    
    while True:
        cycle += 1
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Sync Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            # ── Step 1: Main data sync (tham_my, nha_khoa, gioi_thieu) ──
            stats = run_sync(syncer, use_phone_matching=USE_PHONE_MATCHING, timestamp_column=TIMESTAMP_COLUMN)
            
            total_processed = sum(s['processed'] for s in stats.values())
            total_errors = sum(s['errors'] for s in stats.values())
            logger.info(f"\nData Sync Summary:")
            logger.info(f"  - Tham My: {stats['tham_my']['processed']} processed")
            logger.info(f"  - Nha Khoa: {stats['nha_khoa']['processed']} processed")
            logger.info(f"  - Gioi Thieu: {stats['gioi_thieu']['processed']} processed")
            logger.info(f"  - Total: {total_processed} processed, {total_errors} errors")

            # ── Step 2: Pricing sync (INDEPENDENT - always runs) ──
            logger.info("\n--- Pricing Sync ---")
            run_pricing_sync(syncer)
            
            # Reset failure counter on success
            consecutive_failures = 0
            
            logger.info(f"\nCycle #{cycle} Complete. Sleeping for {SYNC_INTERVAL}s...")
            time.sleep(SYNC_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("Worker stopped by user (Ctrl+C)")
            logger.info("=" * 60)
            break
            
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"\n{'!'*60}")
            logger.error(f"CYCLE #{cycle} CRASHED: {e}")
            logger.error(f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}")
            logger.error("!" * 60)
            
            import traceback
            traceback.print_exc()
            
            # Even if the main loop crashes, still try pricing sync
            try:
                logger.info("Attempting pricing sync despite main cycle failure...")
                run_pricing_sync(syncer)
            except Exception as pe:
                logger.error(f"Pricing sync also failed: {pe}")
            
            # Exponential backoff on failures
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                wait_time = 300  # 5 minutes after too many failures
                logger.error(f"Too many consecutive failures! Waiting {wait_time}s before retry...")
            else:
                wait_time = min(SYNC_INTERVAL * (2 ** consecutive_failures), 300)  # Max 5 min
                logger.warning(f"Retrying in {wait_time}s...")
            
            time.sleep(wait_time)
            
            # Try to recreate syncer on repeated failures (connection may be stale)
            if consecutive_failures >= 3:
                logger.info("Recreating GoogleSheetSync instance...")
                try:
                    syncer = GoogleSheetSync()
                    # Reconnect DB handler
                    if db_handler:
                        db_handler.syncer = syncer
                        db_handler.conn = None
                    logger.info("GoogleSheetSync recreated successfully")
                except Exception as re_e:
                    logger.error(f"Failed to recreate syncer: {re_e}")

if __name__ == '__main__':
    main()

