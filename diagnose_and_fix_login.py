#!/usr/bin/env python3
"""
Complete admin login diagnostic and fix tool
Created: January 14, 2026
"""

import sys
sys.path.insert(0, '.')

from modules.db_pool import get_db_connection, return_db_connection
from modules.auth import hash_password, verify_password, admin_login
from psycopg2.extras import RealDictCursor

print("=" * 70)
print("ADMIN LOGIN DIAGNOSTIC & FIX")
print("=" * 70)

conn = get_db_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Step 1: Check admin account exists
print("\n[1/5] Checking admin account...")
cursor.execute('SELECT id, username, name, password_hash FROM admins WHERE username = %s', ('admin',))
admin = cursor.fetchone()

if not admin:
    print("✗ No admin account found!")
    print("Creating admin account...")
    password_hash = hash_password('admin123')
    cursor.execute("""
        INSERT INTO admins (username, password_hash, name)
        VALUES ('admin', %s, 'Administrator')
        RETURNING id, username, name
    """, (password_hash,))
    admin = cursor.fetchone()
    conn.commit()
    print(f"✓ Created admin account: {admin['username']}")
else:
    print(f"✓ Admin account found: {admin['username']} (ID: {admin['id']})")

# Step 2: Test password
print("\n[2/5] Testing password...")
test_result = verify_password('admin123', admin['password_hash'])
if test_result:
    print("✓ Password 'admin123' works correctly")
else:
    print("✗ Password doesn't work! Resetting...")
    new_hash = hash_password('admin123')
    cursor.execute('UPDATE admins SET password_hash = %s WHERE username = %s', (new_hash, 'admin'))
    conn.commit()
    print("✓ Password reset to 'admin123'")

# Step 3: Test login function
print("\n[3/5] Testing login function...")
login_result = admin_login('admin', 'admin123', remember_me=False)
if 'error' in login_result:
    print(f"✗ Login function failed: {login_result['error']}")
else:
    print(f"✓ Login function works! Token: {login_result['token'][:30]}...")

# Step 4: Check sessions table
print("\n[4/5] Checking sessions table...")
cursor.execute("SELECT COUNT(*) as count FROM sessions WHERE user_type = 'admin'")
session_count = cursor.fetchone()['count']
print(f"✓ Found {session_count} admin session(s) in database")

# Clean up old sessions (older than 30 days)
cursor.execute("DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '30 days'")
deleted = cursor.rowcount
if deleted > 0:
    conn.commit()
    print(f"✓ Cleaned up {deleted} old session(s)")

# Step 5: Provide test instructions
print("\n[5/5] Login test instructions...")
print("""
To test login, you have 2 options:

OPTION 1: Use the standalone test page
  1. Open your browser to: http://localhost:3001/test-login
  2. Username: admin
  3. Password: admin123
  4. Click "Test Login"
  5. Should see green success message
  
OPTION 2: Use the regular admin login
  1. Open your browser to: http://localhost:3001/admin89
  2. Username: admin
  3. Password: admin123
  4. Click "Login"
  5. Should redirect to dashboard

If login still fails:
  - Open browser DevTools (F12)
  - Go to Console tab
  - Look for red errors
  - Go to Network tab
  - Try logging in
  - Check the /admin89/login request
  - See if it returns status: success
""")

cursor.close()
return_db_connection(conn)

print("\n" + "=" * 70)
print("✓ DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\nAdmin Credentials:")
print("  Username: admin")
print("  Password: admin123")
print("\nTest Page: http://localhost:3001/test-login")
print("Admin Panel: http://localhost:3001/admin89")
