#!/usr/bin/env python3
"""
Google Sheets Live Sync Worker (Hybrid Mode)
- Syncs data from Google Sheets to PostgreSQL database
- For Tham My: Uses phone matching to detect updates AND new rows (catches mid-sheet edits)
- For Nha Khoa & Gioi Thieu: Uses phone matching for full sync
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
BASE_DIR = Path(__file__).parent.absolute()
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'

# Use phone matching sync (processes ALL rows, detects updates)
# Set to 'false' to use old count-based sync (only appends new rows at end)
USE_PHONE_MATCHING = os.getenv('SYNC_USE_PHONE_MATCHING', 'true').lower() == 'true'

# Optional: timestamp column name for detecting changed rows
# If set, only rows with timestamp > last_sync will be processed
TIMESTAMP_COLUMN = os.getenv('SYNC_TIMESTAMP_COLUMN', None)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_sync(syncer, use_phone_matching=True, timestamp_column=None):
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
        
        sync_mode = "phone matching" if use_phone_matching else "count-based"
        logger.info(f"Sync mode: {sync_mode}")
        if timestamp_column:
            logger.info(f"Timestamp column: {timestamp_column}")
        
        logger.info("\n--- Processing Tham My ---")
        if use_phone_matching:
            p, e = syncer.sync_tab_by_phone_matching(spreadsheet, conn, 'tham_my', timestamp_column)
        else:
            p, e = syncer.sync_tab_by_count(spreadsheet, conn, 'tham_my')
        stats['tham_my'] = {'processed': p, 'errors': e}
        
        logger.info("\n--- Processing Nha Khoa ---")
        if use_phone_matching:
            p, e = syncer.sync_tab_by_phone_matching(spreadsheet, conn, 'nha_khoa', timestamp_column)
        else:
            p, e = syncer.sync_tab_by_count(spreadsheet, conn, 'nha_khoa')
        stats['nha_khoa'] = {'processed': p, 'errors': e}
        
        logger.info("\n--- Processing Gioi Thieu ---")
        if use_phone_matching:
            p, e = syncer.sync_tab_by_phone_matching(spreadsheet, conn, 'gioi_thieu', timestamp_column)
        else:
            p, e = syncer.sync_tab_by_count(spreadsheet, conn, 'gioi_thieu')
        stats['gioi_thieu'] = {'processed': p, 'errors': e}
        
        if sum(s['processed'] for s in stats.values()) > 0:
            logger.info("\n--- Calculating Commissions ---")
            comm_stats = calculate_new_commissions_fast(connection=conn)
            logger.info(f"Commission calculation: {comm_stats}")
        
        # Update heartbeat after successful sync with count of new records
        total_new = sum(s['processed'] for s in stats.values())
        syncer.update_heartbeat(conn, total_new)
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
        import traceback
        traceback.print_exc()
    
    return stats

def main():
    logger.info("=" * 60)
    logger.info("Google Sheets Live Sync Worker (Hybrid Mode)")
    logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
    logger.info(f"Phone Matching: {'enabled' if USE_PHONE_MATCHING else 'disabled (count-based)'}")
    if TIMESTAMP_COLUMN:
        logger.info(f"Timestamp Column: {TIMESTAMP_COLUMN}")
    logger.info("=" * 60)
    
    if not CREDENTIALS_FILE.exists():
        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
        sys.exit(1)
    
    syncer = GoogleSheetSync()
    
    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Sync Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        stats = run_sync(syncer, use_phone_matching=USE_PHONE_MATCHING, timestamp_column=TIMESTAMP_COLUMN)
        
        total_processed = sum(s['processed'] for s in stats.values())
        total_errors = sum(s['errors'] for s in stats.values())
        logger.info(f"\nCycle #{cycle} Complete:")
        logger.info(f"  - Tham My: {stats['tham_my']['processed']} processed")
        logger.info(f"  - Nha Khoa: {stats['nha_khoa']['processed']} processed")
        logger.info(f"  - Gioi Thieu: {stats['gioi_thieu']['processed']} processed")
        logger.info(f"  - Total: {total_processed} processed, {total_errors} errors")
        
        logger.info(f"\nSleeping for {SYNC_INTERVAL} seconds...")
        time.sleep(SYNC_INTERVAL)

if __name__ == '__main__':
    main()
