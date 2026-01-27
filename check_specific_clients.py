
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from modules.db_pool import get_db_connection, return_db_connection

def check_clients():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        phones = ['0941199403', '0938295355']
        
        print(f"Checking for phones: {phones}")
        print("-" * 50)
        
        for phone in phones:
            # Check exact match or containing the last 9 digits
            short_phone = phone[-9:]
            query = """
                SELECT id, ngay_nhap_don, ten_khach, sdt, source, trang_thai, created_at
                FROM khach_hang 
                WHERE sdt LIKE %s
            """
            cur.execute(query, (f'%{short_phone}',))
            rows = cur.fetchall()
            
            if rows:
                print(f"✅ FOUND: {phone}")
                for row in rows:
                    print(f"   - ID: {row['id']}")
                    print(f"   - Name: {row['ten_khach']}")
                    print(f"   - Phone: {row['sdt']}")
                    print(f"   - Source: {row['source']}")
                    print(f"   - Status: {row['trang_thai']}")
                    print(f"   - Date: {row['ngay_nhap_don']}")
                    print("")
            else:
                print(f"❌ NOT FOUND: {phone}")
                print("")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            return_db_connection(conn)

if __name__ == "__main__":
    check_clients()
