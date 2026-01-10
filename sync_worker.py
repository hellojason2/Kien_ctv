#!/usr/bin/env python3
"""
Google Sheets Live Sync Worker (Count-Based)
- Syncs data from Google Sheets to PostgreSQL database
- Logic: Appends new rows only (Sheet Count > DB Count)
- Ignores "update" status column
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_sync(syncer):
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
        
        logger.info("\n--- Processing Tham My ---")
        p, e = syncer.sync_tab_by_count(spreadsheet, conn, 'tham_my')
        stats['tham_my'] = {'processed': p, 'errors': e}
        
        logger.info("\n--- Processing Nha Khoa ---")
        p, e = syncer.sync_tab_by_count(spreadsheet, conn, 'nha_khoa')
        stats['nha_khoa'] = {'processed': p, 'errors': e}
        
        logger.info("\n--- Processing Gioi Thieu ---")
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
    logger.info("Google Sheets Live Sync Worker (Count-Based)")
    logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
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
        
        stats = run_sync(syncer)
        
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
