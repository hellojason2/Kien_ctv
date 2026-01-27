from modules.db_pool import get_db_connection, return_db_connection

def create_worker_logs_table():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS worker_logs (
                id SERIAL PRIMARY KEY,
                level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source VARCHAR(50) DEFAULT 'worker'
            );
            
            -- Create index for fast retrieval of latest logs
            CREATE INDEX IF NOT EXISTS idx_worker_logs_created_at ON worker_logs(created_at DESC);
            
            -- Auto-cleanup function (keep last 7 days)
            CREATE OR REPLACE FUNCTION cleanup_worker_logs() RETURNS trigger AS $$
            BEGIN
                DELETE FROM worker_logs WHERE created_at < NOW() - INTERVAL '7 days';
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Trigger for cleanup (simplified: run on insert, random chance optional but keep simple for now)
            DROP TRIGGER IF EXISTS trigger_cleanup_worker_logs ON worker_logs;
            -- We won't use a trigger for cleanup to avoid overhead on every insert. 
            -- We'll trust the worker to clean up occasionally.
        """)
        conn.commit()
        print("Table 'worker_logs' created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
    finally:
        return_db_connection(conn)

if __name__ == "__main__":
    create_worker_logs_table()
