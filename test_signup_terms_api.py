#!/usr/bin/env python3
"""
Test signup terms API endpoint
"""
import sys
sys.path.insert(0, '.')

from modules.auth import admin_login, create_session
from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor
import json

print("=" * 70)
print("TESTING SIGNUP TERMS API")
print("=" * 70)

# Create a session
print("\n[1/3] Creating admin session...")
login_result = admin_login('admin', 'admin123')
if 'error' in login_result:
    print(f"✗ Login failed: {login_result['error']}")
    sys.exit(1)

token = login_result['token']
print(f"✓ Session created: {token[:30]}...")

# Simulate the API call
print("\n[2/3] Fetching terms (simulating API)...")
conn = get_db_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT id, language, title, content, is_active, version, 
           created_at, updated_at, updated_by
    FROM signup_terms
    WHERE language = %s
    ORDER BY version DESC
""", ('vi',))

terms = [dict(row) for row in cursor.fetchall()]

# Convert datetime to string (as API does)
for term in terms:
    if term.get('created_at'):
        term['created_at'] = term['created_at'].isoformat()
    if term.get('updated_at'):
        term['updated_at'] = term['updated_at'].isoformat()

api_response = {
    'status': 'success',
    'terms': terms
}

print(f"✓ Found {len(terms)} terms")
print(f"\nAPI Response:")
print(json.dumps(api_response, indent=2, ensure_ascii=False)[:500])

cursor.close()
return_db_connection(conn)

# Check what would be loaded
print("\n[3/3] Checking what would load in editor...")
if terms:
    active_term = next((t for t in terms if t.get('is_active')), terms[0])
    print(f"✓ Would load term ID {active_term['id']}")
    print(f"  Title: {active_term['title']}")
    print(f"  Content: {len(active_term['content'])} characters")
    print(f"  Version: {active_term['version']}")
else:
    print("✗ No terms to load - editor would be blank!")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
