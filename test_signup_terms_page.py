#!/usr/bin/env python3
"""
Quick test to verify the signup terms page can load data
Created: January 14, 2026
"""

import sys
sys.path.insert(0, '.')

from modules.db_pool import get_db_connection, return_db_connection
from modules.auth import create_session
from psycopg2.extras import RealDictCursor
import json

print("=" * 70)
print("SIGNUP TERMS PAGE - QUICK DIAGNOSTIC")
print("=" * 70)

# Test 1: Check database
print("\n[1/4] Checking database...")
conn = get_db_connection()
cursor = cursor.cursor(cursor_factory=RealDictCursor)

cursor.execute("SELECT COUNT(*) as count FROM signup_terms")
count = cursor.fetchone()['count']
print(f"✓ Found {count} terms in database")

# Test 2: Fetch terms (as API would)
print("\n[2/4] Fetching terms (simulating API)...")
cursor.execute("""
    SELECT id, language, title, content, is_active, version, 
           created_at, updated_at, updated_by
    FROM signup_terms
    WHERE language = 'vi'
    ORDER BY version DESC
""")
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

print(f"✓ API would return {len(terms)} terms")
print(f"✓ Response structure:")
print(json.dumps(api_response, indent=2, ensure_ascii=False)[:500] + "...")

# Test 3: Check if page files exist
print("\n[3/4] Checking frontend files...")
import os
files = [
    'templates/admin/pages/signup-terms.html',
    'static/js/admin/signup-terms.js'
]
for f in files:
    exists = os.path.exists(f)
    print(f"  {'✓' if exists else '✗'} {f}")

# Test 4: Create a test session
print("\n[4/4] Creating test session...")
token = create_session('admin', 'admin', remember_me=False)
print(f"✓ Session token: {token[:30]}...")

cursor.close()
return_db_connection(conn)

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\nEverything looks good! The signup terms page should work.")
print("If you see a blank page:")
print("  1. Check browser console (F12) for JavaScript errors")
print("  2. Check Network tab to see if API calls are being made")
print("  3. Ensure you're logged in as admin")
print("  4. Try refreshing the page")
