"""
Fix CTV accounts that were auto-approved with incremental IDs (1, 2, etc.)
instead of phone numbers.

This script:
1. Finds CTVs where ma_ctv is a short incremental number (not a phone number)
2. Updates ma_ctv to their actual phone number (sdt)
3. Updates all foreign key references:
   - ctv.nguoi_gioi_thieu (referrer links)
   - khach_hang.nguoi_chot (customer closer)
   - commissions.ctv_code (commission records)
   - ctv_registrations.referrer_code (registration referrer)

Usage:
  python fix_incremental_ctv_codes.py          # Dry run (preview)
  python fix_incremental_ctv_codes.py --apply  # Apply changes
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor


def find_bad_ctv_codes(cursor):
    """Find CTVs with short incremental ma_ctv (not phone numbers)"""
    cursor.execute("""
        SELECT ma_ctv, ten, sdt, email, cap_bac, nguoi_gioi_thieu, created_at
        FROM ctv
        WHERE ma_ctv ~ '^[0-9]+$'
          AND LENGTH(ma_ctv) <= 6
          AND sdt IS NOT NULL
          AND sdt != ''
          AND ma_ctv != sdt
        ORDER BY CAST(ma_ctv AS BIGINT)
    """)
    return cursor.fetchall()


def find_references(cursor, old_code):
    """Find all foreign key references to an old ma_ctv"""
    refs = {}

    # ctv.nguoi_gioi_thieu 
    cursor.execute("SELECT ma_ctv, ten FROM ctv WHERE nguoi_gioi_thieu = %s", (old_code,))
    refs['ctv_referrals'] = cursor.fetchall()

    # khach_hang.nguoi_chot
    cursor.execute("SELECT id, ten_khach FROM khach_hang WHERE nguoi_chot = %s", (old_code,))
    refs['khach_hang'] = cursor.fetchall()

    # commissions.ctv_code
    cursor.execute("SELECT id, transaction_id, commission_amount FROM commissions WHERE ctv_code = %s", (old_code,))
    refs['commissions'] = cursor.fetchall()

    # ctv_registrations.referrer_code
    cursor.execute("SELECT id, full_name FROM ctv_registrations WHERE referrer_code = %s", (old_code,))
    refs['registrations'] = cursor.fetchall()

    return refs


def fix_ctv_code(cursor, old_code, new_code, dry_run=True):
    """Update ma_ctv and all foreign key references"""
    action = "WOULD UPDATE" if dry_run else "UPDATING"

    # Check if new_code already exists
    cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (new_code,))
    if cursor.fetchone():
        print(f"  ❌ SKIP: Phone number {new_code} already exists as a ma_ctv!")
        return False

    refs = find_references(cursor, old_code)

    print(f"\n  {action}: ma_ctv '{old_code}' → '{new_code}'")

    # Show all references
    if refs['ctv_referrals']:
        print(f"    → {len(refs['ctv_referrals'])} CTV(s) have nguoi_gioi_thieu = '{old_code}':")
        for r in refs['ctv_referrals']:
            print(f"      - {r['ma_ctv']} ({r['ten']})")

    if refs['khach_hang']:
        print(f"    → {len(refs['khach_hang'])} khach_hang record(s) have nguoi_chot = '{old_code}':")
        for r in refs['khach_hang']:
            print(f"      - ID {r['id']} ({r['ten_khach']})")

    if refs['commissions']:
        print(f"    → {len(refs['commissions'])} commission record(s) have ctv_code = '{old_code}':")
        for r in refs['commissions']:
            print(f"      - ID {r['id']} (txn {r['transaction_id']}, {r['commission_amount']})")

    if refs['registrations']:
        print(f"    → {len(refs['registrations'])} registration(s) have referrer_code = '{old_code}':")
        for r in refs['registrations']:
            print(f"      - ID {r['id']} ({r['full_name']})")

    if not any(refs.values()):
        print(f"    → No foreign key references found")

    if not dry_run:
        # Update the primary key and all references
        # FKs are already dropped at the transaction level by main()
        cursor.execute("UPDATE ctv SET nguoi_gioi_thieu = %s WHERE nguoi_gioi_thieu = %s", (new_code, old_code))
        cursor.execute("UPDATE khach_hang SET nguoi_chot = %s WHERE nguoi_chot = %s", (new_code, old_code))
        cursor.execute("UPDATE commissions SET ctv_code = %s WHERE ctv_code = %s", (new_code, old_code))
        cursor.execute("UPDATE ctv_registrations SET referrer_code = %s WHERE referrer_code = %s", (new_code, old_code))
        cursor.execute("UPDATE ctv SET ma_ctv = %s WHERE ma_ctv = %s", (new_code, old_code))
        print(f"  ✅ DONE: {old_code} → {new_code}")

    return True


def main():
    dry_run = '--apply' not in sys.argv

    if dry_run:
        print("=" * 60)
        print("  DRY RUN MODE - No changes will be made")
        print("  Run with --apply to execute changes")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  ⚠️  APPLYING CHANGES TO DATABASE")
        print("=" * 60)

    connection = get_db_connection()
    if not connection:
        print("❌ Database connection failed")
        sys.exit(1)

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        bad_ctvs = find_bad_ctv_codes(cursor)

        if not bad_ctvs:
            print("\n✅ No CTVs with incremental IDs found. All good!")
            return

        print(f"\nFound {len(bad_ctvs)} CTV(s) with incremental IDs:\n")

        if not dry_run:
            # Drop FK constraints that reference ctv(ma_ctv)
            print("  🔧 Temporarily dropping FK constraints...")
            fk_constraints = []
            cursor.execute("""
                SELECT tc.constraint_name, tc.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu 
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND ccu.table_name = 'ctv'
                  AND ccu.column_name = 'ma_ctv'
            """)
            fk_constraints = cursor.fetchall()
            
            for fk in fk_constraints:
                print(f"    Dropping: {fk['table_name']}.{fk['constraint_name']}")
                cursor.execute(f"ALTER TABLE {fk['table_name']} DROP CONSTRAINT {fk['constraint_name']}")

        fixed = 0
        skipped = 0
        for ctv in bad_ctvs:
            old_code = ctv['ma_ctv']
            new_code = ctv['sdt']

            print(f"─── CTV: {ctv['ten']} ───")
            print(f"  Current ma_ctv: {old_code}")
            print(f"  Phone (sdt):    {new_code}")
            print(f"  Email:          {ctv['email'] or '-'}")
            print(f"  Level:          {ctv['cap_bac']}")
            print(f"  Referrer:       {ctv['nguoi_gioi_thieu'] or '-'}")
            print(f"  Created:        {ctv['created_at']}")

            if fix_ctv_code(cursor, old_code, new_code, dry_run):
                fixed += 1
            else:
                skipped += 1

        if not dry_run:
            # Re-create FK constraints (one by one, some may fail due to pre-existing data)
            print("\n  🔧 Re-creating FK constraints...")
            
            fk_definitions = [
                ("ctv", "ctv_nguoi_gioi_thieu_fkey",
                 "FOREIGN KEY (nguoi_gioi_thieu) REFERENCES ctv(ma_ctv) ON DELETE SET NULL"),
                ("commissions", "commissions_ctv_code_fkey",
                 "FOREIGN KEY (ctv_code) REFERENCES ctv(ma_ctv) ON DELETE CASCADE"),
                ("khach_hang", "khach_hang_nguoi_chot_fkey",
                 "FOREIGN KEY (nguoi_chot) REFERENCES ctv(ma_ctv) ON DELETE SET NULL"),
            ]
            
            for table, name, fk_sql in fk_definitions:
                try:
                    # Use SAVEPOINT so a single FK failure doesn't kill the transaction
                    cursor.execute(f"SAVEPOINT sp_{name}")
                    cursor.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} {fk_sql}")
                    print(f"    ✅ {table}.{name} restored")
                except Exception as fk_err:
                    cursor.execute(f"ROLLBACK TO SAVEPOINT sp_{name}")
                    print(f"    ⚠️  {table}.{name} skipped (pre-existing orphan data: {fk_err})")
            
            print("  FK constraint restoration complete")
            
            connection.commit()
            print(f"\n{'=' * 60}")
            print(f"  ✅ Committed: {fixed} fixed, {skipped} skipped")
            print(f"{'=' * 60}")
        else:
            print(f"\n{'=' * 60}")
            print(f"  Preview: {fixed} would be fixed, {skipped} would be skipped")
            print(f"  Run with --apply to execute")
            print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if not dry_run and connection:
            connection.rollback()
            print("  Changes rolled back")
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            cursor.close()
            return_db_connection(connection)


if __name__ == '__main__':
    main()
