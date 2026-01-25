
import os
import sys
from modules.db_pool import get_db_connection, return_db_connection

def check_tables():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"Connected to database '{db_name[0]}'")
            
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()
            if tables:
                print(f"Found {len(tables)} table(s):")
                found_activity_logs = False
                for table in tables:
                    print(f"  - {table[0]}")
                    if table[0] == 'activity_logs':
                        found_activity_logs = True
                        
                if found_activity_logs:
                    print("\nChecking activity_logs count:")
                    cursor.execute("SELECT COUNT(*) FROM activity_logs")
                    count = cursor.fetchone()[0]
                    print(f"Total rows: {count}")
                else:
                    print("\nWARNING: activity_logs table NOT found!")
            else:
                print("No tables found in database")
            
            cursor.close()
            return_db_connection(connection)
        except Exception as e:
            print(f"ERROR: {e}")
            if connection:
                return_db_connection(connection)
    else:
        print("ERROR: Failed to connect to database")

if __name__ == "__main__":
    check_tables()
