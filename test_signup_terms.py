"""
Complete Diagnostic Test for Signup Terms
This will test database, APIs, and show exactly what content exists
"""
import sys
sys.path.insert(0, '.')

from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor
import requests

def test_database():
    """Test what's actually in the database"""
    print("\n" + "=" * 80)
    print("TEST 1: DATABASE CONTENT")
    print("=" * 80)
    
    connection = get_db_connection()
    if not connection:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        for lang in ['vi', 'en']:
            cursor.execute("""
                SELECT id, language, title, content, is_active, version
                FROM signup_terms
                WHERE language = %s AND is_active = TRUE
            """, (lang,))
            
            term = cursor.fetchone()
            if term:
                print(f"\n{lang.upper()} TERMS:")
                print(f"  ID: {term['id']}")
                print(f"  Title: {term['title']}")
                print(f"  Content Length: {len(term['content'])} characters")
                print(f"  Content Preview (first 200 chars):")
                print(f"  {term['content'][:200]}...")
                print(f"  Is Active: {term['is_active']}")
                print(f"  Version: {term['version']}")
                
                # Check if content is actually empty
                if not term['content'] or term['content'].strip() == '':
                    print(f"  ⚠️  WARNING: Content is EMPTY or whitespace only!")
                else:
                    print(f"  ✅ Content exists and has {len(term['content'])} characters")
            else:
                print(f"\n{lang.upper()} TERMS: NOT FOUND")
        
        cursor.close()
        return_db_connection(connection)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if connection:
            return_db_connection(connection)

def test_public_api():
    """Test the public API endpoint"""
    print("\n" + "=" * 80)
    print("TEST 2: PUBLIC API ENDPOINT")
    print("=" * 80)
    
    for lang in ['vi', 'en']:
        try:
            url = f"http://localhost:4000/api/admin/signup-terms/active?language={lang}"
            print(f"\n{lang.upper()} API Request:")
            print(f"  URL: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and data.get('term'):
                    term = data['term']
                    print(f"  ✅ Success")
                    print(f"  Title: {term.get('title', 'N/A')}")
                    print(f"  Content Length: {len(term.get('content', ''))} characters")
                    print(f"  Content Preview:")
                    print(f"  {term.get('content', '')[:200]}...")
                else:
                    print(f"  ❌ API returned error: {data.get('message', 'Unknown')}")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_admin_api():
    """Test the admin API endpoint (without auth, will fail but shows structure)"""
    print("\n" + "=" * 80)
    print("TEST 3: ADMIN API ENDPOINT (will require auth)")
    print("=" * 80)
    
    for lang in ['vi', 'en']:
        try:
            url = f"http://localhost:4000/api/admin/signup-terms?language={lang}"
            print(f"\n{lang.upper()} API Request:")
            print(f"  URL: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"  Status: {response.status_code}")
            
            data = response.json()
            print(f"  Response: {data}")
            
            if data.get('status') == 'error' and 'Authentication' in data.get('message', ''):
                print(f"  ℹ️  Authentication required (this is expected)")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

def check_environment():
    """Check what environment we're connected to"""
    print("\n" + "=" * 80)
    print("ENVIRONMENT CHECK")
    print("=" * 80)
    
    from modules.db_pool import DB_CONFIG
    print(f"\nDatabase Connection:")
    print(f"  Host: {DB_CONFIG.get('host')}")
    print(f"  Port: {DB_CONFIG.get('port')}")
    print(f"  Database: {DB_CONFIG.get('database')}")
    print(f"  User: {DB_CONFIG.get('user')}")
    
    if 'railway' in str(DB_CONFIG.get('host', '')).lower():
        print("\n  📍 Connected to: RAILWAY PRODUCTION")
    elif 'localhost' in str(DB_CONFIG.get('host', '')).lower():
        print("\n  📍 Connected to: LOCAL DATABASE")
    else:
        print("\n  📍 Connected to: UNKNOWN")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SIGNUP TERMS DIAGNOSTIC")
    print("=" * 80)
    
    check_environment()
    test_database()
    test_public_api()
    test_admin_api()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print("\nIf database shows content but API doesn't:")
    print("  → Check if backend is running: ps aux | grep backend.py")
    print("  → Restart backend: python3 backend.py")
    print("\nIf admin panel shows empty:")
    print("  → Open browser console (F12) and check for errors")
    print("  → Check if you're logged in to admin panel")
    print("  → Try hard refresh (Cmd+Shift+R or Ctrl+Shift+R)")
