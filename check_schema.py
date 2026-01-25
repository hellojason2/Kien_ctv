
import os
import sys
from modules.db_pool import get_db_connection, return_db_connection

def check_schema():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            print("Checking schema of activity_logs table:")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'activity_logs'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
            
            cursor.close()
            return_db_connection(connection)
        except Exception as e:
            print(f"ERROR: {e}")
            if connection:
                return_db_connection(connection)
    else:
        print("ERROR: Failed to connect to database")

if __name__ == "__main__":
    check_schema()
