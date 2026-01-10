
import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

try:
    from modules.db_pool import get_db_connection
    
    print("Attempting to connect to database...")
    conn = get_db_connection()
    
    if conn:
        print("Connection successful!")
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT version()')
                version = cur.fetchone()
                print(f"Database version: {version}")
        except Exception as e:
            print(f"Query failed: {e}")
        finally:
            conn.close()
    else:
        print("Connection failed (returned None).")

except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
