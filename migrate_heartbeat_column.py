#!/usr/bin/env python3
"""
Migration: Add cache_value column to commission_cache table

This column is used by the sync worker to store the heartbeat status
and track the count of new records synced.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from modules.google_sync import DB_CONFIG
import psycopg2


def migrate():
    print("=" * 60)
    print("Migration: Add cache_value column to commission_cache")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'commission_cache' 
            AND column_name = 'cache_value'
        """)
        exists = cursor.fetchone()
        
        if exists:
            print("✅ Column 'cache_value' already exists. No migration needed.")
        else:
            print("Adding 'cache_value' column...")
            cursor.execute("""
                ALTER TABLE commission_cache 
                ADD COLUMN IF NOT EXISTS cache_value TEXT DEFAULT '0'
            """)
            conn.commit()
            print("✅ Column 'cache_value' added successfully!")
        
        # Verify the heartbeat row exists
        cursor.execute("""
            SELECT cache_key FROM commission_cache 
            WHERE cache_key = 'sync_worker_heartbeat'
        """)
        heartbeat = cursor.fetchone()
        
        if not heartbeat:
            print("Creating heartbeat row...")
            cursor.execute("""
                INSERT INTO commission_cache (cache_key, cache_value, last_updated)
                VALUES ('sync_worker_heartbeat', '0', CURRENT_TIMESTAMP)
                ON CONFLICT (cache_key) DO NOTHING
            """)
            conn.commit()
            print("✅ Heartbeat row created!")
        else:
            print("✅ Heartbeat row already exists.")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Migration complete!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True


if __name__ == '__main__':
    migrate()
