"""
CTV Code Sanitization and Password Reset Migration Script

This script:
1. Removes Vietnamese diacritics from CTV codes (ma_ctv)
2. Removes spaces and special characters (only letters/numbers allowed)
3. Updates nguoi_gioi_thieu references to match new codes
4. Resets all CTV passwords to "123456"

Created: December 29, 2025
"""

import os
import sys
import unicodedata
import re
import hashlib
import secrets
import mysql.connector
from mysql.connector import Error

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


def hash_password(password):
    """
    Hash password using SHA256 with salt
    Returns: salt:hash format
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def sanitize_ctv_code(text):
    """
    Remove accents, spaces, and special chars - keep only letters and numbers
    
    Examples:
    - "Bs Dieu" -> "BsDieu"
    - "CTV-001" -> "CTV001"
    - "Nguyen Van A" -> "NguyenVanA"
    """
    if not text:
        return text
    
    # Remove Vietnamese diacritics using Unicode normalization
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
    
    # Keep only alphanumeric characters (letters and numbers)
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', ascii_text)
    
    return sanitized


def run_migration():
    """Run the CTV code sanitization and password reset migration"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        print("=" * 60)
        print("CTV Code Sanitization and Password Reset Migration")
        print("=" * 60)
        
        # Step 1: Get all current CTV codes
        print("\n[1/4] Fetching all CTV records...")
        cursor.execute("SELECT ma_ctv, ten, nguoi_gioi_thieu FROM ctv;")
        ctv_list = cursor.fetchall()
        print(f"   Found {len(ctv_list)} CTV records")
        
        if not ctv_list:
            print("   No CTV records to migrate")
            cursor.close()
            connection.close()
            return True
        
        # Step 2: Build mapping of old codes to new sanitized codes
        print("\n[2/4] Building code mapping...")
        code_mapping = {}  # old_code -> new_code
        
        for ctv in ctv_list:
            old_code = ctv['ma_ctv']
            new_code = sanitize_ctv_code(old_code)
            
            if old_code != new_code:
                code_mapping[old_code] = new_code
                print(f"   '{old_code}' -> '{new_code}'")
        
        if not code_mapping:
            print("   No codes need sanitization")
        else:
            print(f"   {len(code_mapping)} codes will be updated")
        
        # Step 3: Check for duplicate new codes
        print("\n[3/4] Checking for duplicate codes after sanitization...")
        new_codes = []
        for ctv in ctv_list:
            old_code = ctv['ma_ctv']
            new_code = code_mapping.get(old_code, old_code)
            new_codes.append(new_code.lower())  # Case-insensitive check
        
        duplicates = [code for code in set(new_codes) if new_codes.count(code) > 1]
        if duplicates:
            print(f"   WARNING: Duplicate codes detected after sanitization:")
            for dup in duplicates:
                print(f"      - {dup}")
            print("   Please resolve these manually before proceeding")
            cursor.close()
            connection.close()
            return False
        
        print("   No duplicates found")
        
        # Step 4: Update database
        print("\n[4/4] Updating database...")
        
        # Disable foreign key checks temporarily
        print("   Disabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # 4a: First update ma_ctv codes (must do this first with FK disabled)
        if code_mapping:
            print("   Updating ma_ctv codes...")
            for old_code, new_code in code_mapping.items():
                cursor.execute("""
                    UPDATE ctv SET ma_ctv = %s WHERE ma_ctv = %s;
                """, (new_code, old_code))
                print(f"      '{old_code}' -> '{new_code}'")
            
            # 4b: Update nguoi_gioi_thieu references
            print("   Updating nguoi_gioi_thieu references...")
            for old_code, new_code in code_mapping.items():
                cursor.execute("""
                    UPDATE ctv SET nguoi_gioi_thieu = %s 
                    WHERE nguoi_gioi_thieu = %s;
                """, (new_code, old_code))
                affected = cursor.rowcount
                if affected > 0:
                    print(f"      Updated {affected} reference(s) from '{old_code}' to '{new_code}'")
            
            # 4c: Update khach_hang.nguoi_chot references
            print("   Updating khach_hang.nguoi_chot references...")
            for old_code, new_code in code_mapping.items():
                cursor.execute("""
                    UPDATE khach_hang SET nguoi_chot = %s 
                    WHERE nguoi_chot = %s;
                """, (new_code, old_code))
                affected = cursor.rowcount
                if affected > 0:
                    print(f"      Updated {affected} khach_hang record(s) from '{old_code}' to '{new_code}'")
        
        # Re-enable foreign key checks
        print("   Re-enabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        # 4d: Reset all passwords to "123456"
        print("   Resetting all passwords to '123456'...")
        default_password = "123456"
        password_hash = hash_password(default_password)
        
        cursor.execute("""
            UPDATE ctv SET password_hash = %s;
        """, (password_hash,))
        print(f"      Reset passwords for {cursor.rowcount} CTV(s)")
        
        # Commit all changes
        connection.commit()
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
        # Show final state
        print("\n--- Final CTV List ---")
        cursor.execute("SELECT ma_ctv, ten, nguoi_gioi_thieu FROM ctv ORDER BY ma_ctv;")
        final_list = cursor.fetchall()
        for ctv in final_list:
            ref = ctv['nguoi_gioi_thieu'] or '(none)'
            print(f"  {ctv['ma_ctv']} - {ctv['ten']} [ref: {ref}]")
        
        print(f"\nAll {len(final_list)} CTVs can now login with:")
        print("  - Username: Their CTV code (case-insensitive)")
        print("  - Password: 123456")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\nERROR during migration: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False


def preview_changes():
    """Preview what changes would be made without applying them"""
    connection = get_db_connection()
    if not connection:
        print("ERROR: Failed to connect to database")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        print("=" * 60)
        print("PREVIEW MODE - No changes will be made")
        print("=" * 60)
        
        cursor.execute("SELECT ma_ctv, ten, nguoi_gioi_thieu FROM ctv ORDER BY ma_ctv;")
        ctv_list = cursor.fetchall()
        
        print(f"\nFound {len(ctv_list)} CTV records:\n")
        print(f"{'Current Code':<20} {'New Code':<20} {'Name':<20} {'Referrer'}")
        print("-" * 80)
        
        for ctv in ctv_list:
            old_code = ctv['ma_ctv']
            new_code = sanitize_ctv_code(old_code)
            name = ctv['ten'] or ''
            ref = ctv['nguoi_gioi_thieu'] or ''
            new_ref = sanitize_ctv_code(ref) if ref else ''
            
            changed = " *" if old_code != new_code else ""
            print(f"{old_code:<20} {new_code:<20} {name:<20} {ref} -> {new_ref}{changed}")
        
        print("\n* = Code will be changed")
        print("\nRun with 'migrate' argument to apply changes:")
        print("  python migrate_ctv_codes.py migrate")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"ERROR: {e}")
        if connection:
            connection.close()


if __name__ == '__main__':
    print("\nCTV Code Migration Script")
    print("Usage:")
    print("  python migrate_ctv_codes.py          - Preview changes (no modifications)")
    print("  python migrate_ctv_codes.py migrate  - Apply changes to database")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        run_migration()
    else:
        preview_changes()
    
    print()

