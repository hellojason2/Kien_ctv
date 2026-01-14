import psycopg2
from modules.db_pool import get_db_connection

def cleanup():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        print("Cleaning up test data...")
        cur.execute("DELETE FROM ctv WHERE email = 'browser@test.com'")
        conn.commit()
        print("Deleted test user.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup()
