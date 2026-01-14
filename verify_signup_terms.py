"""
Verify Signup Terms Feature Status
Run this to check if signup terms are properly set up
"""
import sys
sys.path.insert(0, '.')

from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor

def verify_signup_terms():
    """Verify signup terms in database"""
    print("=" * 60)
    print("SIGNUP TERMS VERIFICATION")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        print("❌ ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Check if table exists
        print("\n1. Checking if signup_terms table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'signup_terms'
            )
        """)
        exists = cursor.fetchone()['exists']
        
        if not exists:
            print("   ❌ FAIL: signup_terms table does NOT exist")
            print("   → Run: python3 migrate_signup_terms.py")
            cursor.close()
            return_db_connection(connection)
            return False
        
        print("   ✅ PASS: signup_terms table exists")
        
        # Check if there are any records
        print("\n2. Checking for signup terms records...")
        cursor.execute("SELECT COUNT(*) as count FROM signup_terms")
        count = cursor.fetchone()['count']
        
        if count == 0:
            print("   ❌ FAIL: No signup terms found in database")
            print("   → Run: python3 migrate_signup_terms.py")
            cursor.close()
            return_db_connection(connection)
            return False
        
        print(f"   ✅ PASS: Found {count} signup terms record(s)")
        
        # Check Vietnamese terms
        print("\n3. Checking Vietnamese terms...")
        cursor.execute("""
            SELECT id, title, LENGTH(content) as content_length, is_active, version
            FROM signup_terms
            WHERE language = 'vi' AND is_active = TRUE
        """)
        vi_term = cursor.fetchone()
        
        if not vi_term:
            print("   ❌ FAIL: No active Vietnamese terms found")
        elif vi_term['content_length'] == 0:
            print("   ❌ FAIL: Vietnamese terms have NO content")
        else:
            print(f"   ✅ PASS: Vietnamese terms (ID: {vi_term['id']}, Version: {vi_term['version']})")
            print(f"      Title: {vi_term['title']}")
            print(f"      Content: {vi_term['content_length']} characters")
        
        # Check English terms
        print("\n4. Checking English terms...")
        cursor.execute("""
            SELECT id, title, LENGTH(content) as content_length, is_active, version
            FROM signup_terms
            WHERE language = 'en' AND is_active = TRUE
        """)
        en_term = cursor.fetchone()
        
        if not en_term:
            print("   ❌ FAIL: No active English terms found")
        elif en_term['content_length'] == 0:
            print("   ❌ FAIL: English terms have NO content")
        else:
            print(f"   ✅ PASS: English terms (ID: {en_term['id']}, Version: {en_term['version']})")
            print(f"      Title: {en_term['title']}")
            print(f"      Content: {en_term['content_length']} characters")
        
        # Show all terms summary
        print("\n5. All terms summary:")
        cursor.execute("""
            SELECT id, language, title, LENGTH(content) as len, is_active, version
            FROM signup_terms
            ORDER BY language, version DESC
        """)
        all_terms = cursor.fetchall()
        
        print("\n   ID | Lang | Active | Ver | Length | Title")
        print("   " + "-" * 70)
        for term in all_terms:
            active_mark = "✓" if term['is_active'] else " "
            print(f"   {term['id']:2} | {term['language']:4} |   {active_mark}    | {term['version']:2}  | {term['len']:5} | {term['title'][:40]}")
        
        cursor.close()
        return_db_connection(connection)
        
        print("\n" + "=" * 60)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test signup page: http://localhost:4000/ctv/signup")
        print("2. Test admin panel: http://localhost:4000/admin89")
        print("3. If deploying to Railway, run this script on Railway:")
        print("   railway run python3 verify_signup_terms.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        if connection:
            return_db_connection(connection)
        return False

if __name__ == '__main__':
    success = verify_signup_terms()
    sys.exit(0 if success else 1)
