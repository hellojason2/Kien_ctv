import os
import psycopg2
from modules.db_pool import get_db_connection

def check_ctv():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("Checking for Test Browser CTV in ctv table...")
        cur.execute("SELECT ma_ctv, ten, email, sdt, is_active FROM ctv WHERE email = 'browser@test.com' OR sdt = '0911222333'")
        users = cur.fetchall()
        
        if users:
            print(f"Found in ctv table: {users}")
        else:
            print("Not found in ctv table.")
            
        cur.execute("SELECT id, full_name, email, phone, status FROM ctv_registrations WHERE email = 'browser@test.com' OR phone = '0911222333'")
        regs = cur.fetchall()
        
        if regs:
            print(f"Found in ctv_registrations table: {regs}")
        else:
            print("Not found in ctv_registrations table.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ctv()
