"""
Filter Valid CTVs Migration Script

This script:
1. Reads the 52 valid CTV codes from the CSV file
2. Updates CTVs in the CSV: is_active = 1, syncs their details
3. Deactivates all other CTVs: is_active = 0, password_hash = NULL

Client service associations (khach_hang.nguoi_chot) are preserved - 
deactivated CTVs remain in the database, they just can't login.

Usage:
    python filter_valid_ctv.py          - Preview mode (no changes)
    python filter_valid_ctv.py execute  - Apply changes to database

Created: December 30, 2025
"""

import os
import sys
import csv
import mysql.connector
from mysql.connector import Error

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV file path - use relative path from script location or Downloads folder
CSV_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "Du lieu - CTV.csv")

# Database configuration (same as backend.py)
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def remove_vietnamese_diacritics(text):
    """Remove Vietnamese diacritics for easier matching"""
    import unicodedata
    if not text:
        return ""
    # Normalize and remove combining characters
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def read_csv_data(csv_path):
    """
    Read CSV file and extract valid CTV data
    
    Returns: List of dicts with CTV data
    """
    ctv_list = []
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                # Read first line to detect delimiter
                first_line = f.readline()
                f.seek(0)
                
                # Detect delimiter
                delimiter = ',' if ',' in first_line else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Get the actual column headers
                fieldnames = reader.fieldnames
                print(f"   CSV columns found: {fieldnames}")
                
                # Map column names to our field names
                column_map = {}
                for col in fieldnames:
                    if not col:
                        continue
                    col_normalized = remove_vietnamese_diacritics(col)
                    
                    # Match: "Ma CTV" or "Mã CTV"
                    if 'ctv' in col_normalized and 'ma' in col_normalized:
                        column_map['ma_ctv'] = col
                    # Match: "Ho va ten" or "Họ và tên"
                    elif 'ten' in col_normalized or ('ho' in col_normalized and 'va' in col_normalized):
                        column_map['ten'] = col
                    # Match: "SDT"
                    elif 'sdt' in col_normalized:
                        column_map['sdt'] = col
                    # Match: "Email"
                    elif 'email' in col_normalized:
                        column_map['email'] = col
                    # Match: "Nguoi gioi thieu" or "Người giới thiệu"
                    elif 'gioi thieu' in col_normalized:
                        column_map['nguoi_gioi_thieu'] = col
                    # Match: "Cap bac" or "Cấp bậc"
                    elif 'cap' in col_normalized and 'bac' in col_normalized:
                        column_map['cap_bac'] = col
                
                print(f"   Column mapping: {column_map}")
                
                if 'ma_ctv' not in column_map:
                    print("   WARNING: Could not find 'Ma CTV' column")
                    continue
                
                for row in reader:
                    ctv_data = {
                        'ma_ctv': row.get(column_map.get('ma_ctv', ''), '').strip() or None,
                        'ten': row.get(column_map.get('ten', ''), '').strip() or None,
                        'sdt': row.get(column_map.get('sdt', ''), '').strip() or None,
                        'email': row.get(column_map.get('email', ''), '').strip() or None,
                        'nguoi_gioi_thieu': row.get(column_map.get('nguoi_gioi_thieu', ''), '').strip() or None,
                        'cap_bac': row.get(column_map.get('cap_bac', ''), '').strip() or None
                    }
                    
                    # Only add if we have a valid CTV code
                    if ctv_data['ma_ctv']:
                        ctv_list.append(ctv_data)
                
                if ctv_list:
                    print(f"   Successfully read {len(ctv_list)} CTVs with encoding: {encoding}")
                    return ctv_list
                    
        except (UnicodeDecodeError, FileNotFoundError) as e:
            continue
    
    return ctv_list


def preview_changes(csv_path):
    """Preview what changes would be made without applying them"""
    print("=" * 70)
    print("PREVIEW MODE - No changes will be made")
    print("=" * 70)
    
    # Read CSV data
    print(f"\n[1/3] Reading CSV file: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"   ERROR: CSV file not found at {csv_path}")
        return False
    
    csv_ctv_list = read_csv_data(csv_path)
    if not csv_ctv_list:
        print("   ERROR: No valid CTV data found in CSV")
        return False
    
    print(f"   Found {len(csv_ctv_list)} valid CTVs in CSV")
    
    # Get valid CTV codes (case-insensitive)
    valid_codes = {ctv['ma_ctv'].lower(): ctv for ctv in csv_ctv_list}
    
    # Connect to database
    print("\n[2/3] Connecting to database...")
    connection = get_db_connection()
    if not connection:
        print("   ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all current CTVs
        cursor.execute("SELECT ma_ctv, ten, sdt, email, cap_bac, nguoi_gioi_thieu, is_active FROM ctv;")
        db_ctv_list = cursor.fetchall()
        print(f"   Found {len(db_ctv_list)} CTVs in database")
        
        # Categorize CTVs
        to_keep_active = []
        to_deactivate = []
        not_in_db = []
        
        # Check which CTVs in CSV are in database
        db_codes_lower = {ctv['ma_ctv'].lower(): ctv for ctv in db_ctv_list}
        
        for csv_ctv in csv_ctv_list:
            csv_code_lower = csv_ctv['ma_ctv'].lower()
            if csv_code_lower in db_codes_lower:
                db_ctv = db_codes_lower[csv_code_lower]
                to_keep_active.append({
                    'csv': csv_ctv,
                    'db': db_ctv
                })
            else:
                not_in_db.append(csv_ctv)
        
        # Find CTVs to deactivate (in DB but not in CSV)
        for db_ctv in db_ctv_list:
            db_code_lower = db_ctv['ma_ctv'].lower()
            if db_code_lower not in valid_codes:
                to_deactivate.append(db_ctv)
        
        # Print results
        print("\n[3/3] Analysis Results:")
        print("-" * 70)
        
        print(f"\n>>> CTVs to KEEP ACTIVE ({len(to_keep_active)}):")
        print(f"    {'Code':<15} {'Name':<25} {'Rank':<25}")
        print("    " + "-" * 65)
        for item in to_keep_active:
            csv_ctv = item['csv']
            print(f"    {csv_ctv['ma_ctv']:<15} {(csv_ctv['ten'] or ''):<25} {(csv_ctv['cap_bac'] or ''):<25}")
        
        print(f"\n>>> CTVs to DEACTIVATE ({len(to_deactivate)}):")
        if to_deactivate:
            print(f"    {'Code':<15} {'Name':<25} {'Current Status':<15}")
            print("    " + "-" * 55)
            for ctv in to_deactivate:
                status = "Active" if ctv.get('is_active', True) else "Inactive"
                print(f"    {ctv['ma_ctv']:<15} {(ctv['ten'] or ''):<25} {status:<15}")
        else:
            print("    (None)")
        
        if not_in_db:
            print(f"\n>>> CTVs in CSV but NOT in database ({len(not_in_db)}):")
            print("    These will be SKIPPED (not added to database)")
            for ctv in not_in_db:
                print(f"    - {ctv['ma_ctv']} ({ctv['ten']})")
        
        print("\n" + "=" * 70)
        print("SUMMARY:")
        print(f"  - CTVs to keep active:  {len(to_keep_active)}")
        print(f"  - CTVs to deactivate:   {len(to_deactivate)}")
        print(f"  - CTVs not in database: {len(not_in_db)} (will be skipped)")
        print("=" * 70)
        
        print("\nTo apply these changes, run:")
        print("  python filter_valid_ctv.py execute")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"   ERROR: {e}")
        if connection:
            connection.close()
        return False


def execute_changes(csv_path):
    """Execute the changes - deactivate invalid CTVs"""
    print("=" * 70)
    print("EXECUTE MODE - Applying changes to database")
    print("=" * 70)
    
    # Read CSV data
    print(f"\n[1/5] Reading CSV file: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"   ERROR: CSV file not found at {csv_path}")
        return False
    
    csv_ctv_list = read_csv_data(csv_path)
    if not csv_ctv_list:
        print("   ERROR: No valid CTV data found in CSV")
        return False
    
    print(f"   Found {len(csv_ctv_list)} valid CTVs in CSV")
    
    # Get valid CTV codes (case-insensitive)
    valid_codes = {ctv['ma_ctv'].lower(): ctv for ctv in csv_ctv_list}
    
    # Connect to database
    print("\n[2/5] Connecting to database...")
    connection = get_db_connection()
    if not connection:
        print("   ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all current CTVs
        print("\n[3/5] Fetching current CTV records...")
        cursor.execute("SELECT ma_ctv, ten, is_active FROM ctv;")
        db_ctv_list = cursor.fetchall()
        print(f"   Found {len(db_ctv_list)} CTVs in database")
        
        # Build lookup for database CTVs
        db_codes_lower = {ctv['ma_ctv'].lower(): ctv['ma_ctv'] for ctv in db_ctv_list}
        
        # Step 4: Update valid CTVs (set is_active = 1, update details)
        print("\n[4/5] Updating valid CTVs...")
        updated_count = 0
        
        for csv_ctv in csv_ctv_list:
            csv_code_lower = csv_ctv['ma_ctv'].lower()
            
            if csv_code_lower in db_codes_lower:
                actual_code = db_codes_lower[csv_code_lower]
                
                # Update CTV details and ensure is_active = 1
                cursor.execute("""
                    UPDATE ctv 
                    SET is_active = 1,
                        ten = COALESCE(%s, ten),
                        sdt = COALESCE(%s, sdt),
                        email = COALESCE(%s, email),
                        cap_bac = COALESCE(%s, cap_bac),
                        nguoi_gioi_thieu = COALESCE(%s, nguoi_gioi_thieu)
                    WHERE ma_ctv = %s;
                """, (
                    csv_ctv['ten'],
                    csv_ctv['sdt'],
                    csv_ctv['email'],
                    csv_ctv['cap_bac'],
                    csv_ctv['nguoi_gioi_thieu'],
                    actual_code
                ))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    print(f"   [ACTIVE] {actual_code} - {csv_ctv['ten']}")
        
        print(f"   Updated {updated_count} CTVs as active")
        
        # Step 5: Deactivate all CTVs not in the valid list
        print("\n[5/5] Deactivating invalid CTVs...")
        
        # Build list of valid codes (actual case from database)
        valid_actual_codes = []
        for csv_ctv in csv_ctv_list:
            csv_code_lower = csv_ctv['ma_ctv'].lower()
            if csv_code_lower in db_codes_lower:
                valid_actual_codes.append(db_codes_lower[csv_code_lower])
        
        if valid_actual_codes:
            # Create placeholders for IN clause
            placeholders = ', '.join(['%s'] * len(valid_actual_codes))
            
            # First, get count of CTVs to deactivate
            cursor.execute(f"""
                SELECT ma_ctv, ten FROM ctv 
                WHERE ma_ctv NOT IN ({placeholders}) AND is_active = 1;
            """, valid_actual_codes)
            
            to_deactivate = cursor.fetchall()
            
            if to_deactivate:
                for ctv in to_deactivate:
                    print(f"   [DEACTIVATED] {ctv['ma_ctv']} - {ctv['ten']}")
                
                # Deactivate them
                cursor.execute(f"""
                    UPDATE ctv 
                    SET is_active = 0, password_hash = NULL
                    WHERE ma_ctv NOT IN ({placeholders});
                """, valid_actual_codes)
                
                deactivated_count = cursor.rowcount
                print(f"   Deactivated {deactivated_count} CTVs")
            else:
                print("   No CTVs to deactivate")
        
        # Commit all changes
        connection.commit()
        
        # Print final summary
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETE!")
        print("=" * 70)
        
        # Get final counts
        cursor.execute("SELECT COUNT(*) as total FROM ctv;")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as active FROM ctv WHERE is_active = 1;")
        active = cursor.fetchone()['active']
        
        cursor.execute("SELECT COUNT(*) as inactive FROM ctv WHERE is_active = 0;")
        inactive = cursor.fetchone()['inactive']
        
        print(f"\nFinal Database State:")
        print(f"  - Total CTVs:    {total}")
        print(f"  - Active CTVs:   {active} (can login)")
        print(f"  - Inactive CTVs: {inactive} (cannot login, but client links preserved)")
        
        # Check khach_hang links are preserved
        cursor.execute("""
            SELECT COUNT(DISTINCT nguoi_chot) as linked_ctvs 
            FROM khach_hang 
            WHERE nguoi_chot IS NOT NULL;
        """)
        result = cursor.fetchone()
        linked_ctvs = result['linked_ctvs'] if result else 0
        print(f"  - CTVs linked to clients: {linked_ctvs} (all preserved)")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\nERROR during migration: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False


def find_csv_file():
    """Try to find the CSV file in common locations"""
    possible_paths = [
        os.path.join(os.path.expanduser("~"), "Downloads", "Du lieu - CTV.csv"),
        os.path.join(os.path.expanduser("~"), "Downloads", "Dữ liệu - CTV.csv"),
        os.path.join(BASE_DIR, "Du lieu - CTV.csv"),
        os.path.join(BASE_DIR, "Dữ liệu - CTV.csv"),
        os.path.join(BASE_DIR, "ctv_data.csv"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Filter Valid CTVs Migration Script")
    print("=" * 70)
    print("\nUsage:")
    print("  python filter_valid_ctv.py          - Preview changes (no modifications)")
    print("  python filter_valid_ctv.py execute  - Apply changes to database")
    print()
    
    # Find CSV file
    csv_path = find_csv_file()
    if not csv_path:
        print("ERROR: Could not find CSV file.")
        print("Please ensure the file is in one of these locations:")
        print("  - ~/Downloads/Du lieu - CTV.csv")
        print("  - ~/Downloads/Dữ liệu - CTV.csv")
        print("  - Same directory as this script")
        sys.exit(1)
    
    print(f"Using CSV file: {csv_path}\n")
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'execute':
        # Confirm before executing
        print("WARNING: This will modify the database!")
        print("  - Valid CTVs will be kept active")
        print("  - Invalid CTVs will be deactivated (no login, but records preserved)")
        print()
        
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        
        print()
        execute_changes(csv_path)
    else:
        preview_changes(csv_path)
    
    print()

