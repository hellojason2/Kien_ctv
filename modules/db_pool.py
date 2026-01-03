"""
Database Connection Pool Module
Provides a singleton connection pool for PostgreSQL to reduce connection overhead.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# FUNCTIONS:
# - get_db_pool() -> psycopg2.pool.ThreadedConnectionPool
#     DOES: Returns singleton connection pool instance
#
# - get_db_connection() -> connection
#     DOES: Get a connection from the pool (MUST be returned with .close())
#
# - init_pool(app) -> None
#     DOES: Initialize pool with Flask app context
#
# USAGE:
# from modules.db_pool import get_db_connection
# conn = get_db_connection()
# try:
#     cursor = conn.cursor()
#     # ... do work
# finally:
#     conn.close()  # Returns to pool, doesn't actually close
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 30, 2025
Updated: January 2, 2026 - Migrated to PostgreSQL
"""

import os
import psycopg2
from psycopg2 import pool, Error
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Database configuration - PostgreSQL
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'caboose.proxy.rlwy.net'),
    'port': int(os.environ.get('DB_PORT', 34643)),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl'),
    'database': os.environ.get('DB_NAME', 'railway')
}

# Pool configuration
POOL_MIN_CONNECTIONS = 5   # Minimum connections to keep ready
POOL_MAX_CONNECTIONS = 20  # Maximum connections allowed

# Singleton pool instance
_pool = None


def get_db_pool():
    """
    DOES: Get or create the singleton connection pool
    OUTPUTS: ThreadedConnectionPool instance
    
    The pool maintains connections that are reused,
    eliminating the connection overhead per request.
    """
    global _pool
    
    if _pool is None:
        try:
            _pool = pool.ThreadedConnectionPool(
                POOL_MIN_CONNECTIONS,
                POOL_MAX_CONNECTIONS,
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            print(f"PostgreSQL connection pool created (min={POOL_MIN_CONNECTIONS}, max={POOL_MAX_CONNECTIONS})")
        except Error as e:
            print(f"Error creating connection pool: {e}")
            return None
    
    return _pool


def get_db_connection():
    """
    DOES: Get a connection from the pool
    OUTPUTS: Connection or None
    
    IMPORTANT: Always call .close() on the connection when done.
    This returns it to the pool (doesn't actually close it).
    
    Example:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # ... do work
            finally:
                conn.close()
    """
    pool_instance = get_db_pool()
    if pool_instance is None:
        # Fallback to direct connection if pool fails
        try:
            connection = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            return connection
        except Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return None
    
    try:
        return pool_instance.getconn()
    except Error as e:
        print(f"Error getting connection from pool: {e}")
        # Fallback to direct connection
        try:
            connection = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            return connection
        except Error as e2:
            print(f"Fallback connection also failed: {e2}")
            return None


def return_db_connection(connection):
    """
    DOES: Return a connection to the pool
    INPUTS: Connection to return
    
    Note: You can also call connection.close() which does the same thing
    when using pooled connections.
    """
    pool_instance = get_db_pool()
    if pool_instance and connection:
        try:
            pool_instance.putconn(connection)
        except Error:
            pass


@contextmanager
def get_db_cursor(dictionary=True):
    """
    DOES: Context manager for getting a database cursor
    INPUTS: dictionary - if True, returns rows as dictionaries
    
    Example:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM ctv")
            rows = cursor.fetchall()
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Failed to get database connection")
    
    try:
        if dictionary:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = connection.cursor()
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        return_db_connection(connection)


def init_pool(app=None):
    """
    DOES: Initialize the connection pool (call during app startup)
    INPUTS: Flask app instance (optional, for future use)
    
    Pre-creates the pool so first request doesn't have delay.
    """
    pool_instance = get_db_pool()
    if pool_instance:
        print("Connection pool initialized successfully")
        # Test a connection
        try:
            conn = pool_instance.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            pool_instance.putconn(conn)
            print("Pool connection test: OK")
        except Error as e:
            print(f"Pool connection test failed: {e}")
    else:
        print("WARNING: Connection pool initialization failed")


def close_pool():
    """
    DOES: Close all connections in the pool
    Call this on application shutdown
    """
    global _pool
    if _pool:
        try:
            _pool.closeall()
            print("Connection pool closed")
        except Error as e:
            print(f"Error closing pool: {e}")
        _pool = None


# ══════════════════════════════════════════════════════════════════════════════
# POSTGRESQL-SPECIFIC UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def execute_query(query, params=None, fetch_one=False, fetch_all=True, dictionary=True):
    """
    DOES: Execute a query and return results
    INPUTS: 
        query - SQL query with %s placeholders
        params - tuple or list of parameters
        fetch_one - return single row
        fetch_all - return all rows
        dictionary - return rows as dictionaries
    OUTPUTS: Query results or None on error
    
    Example:
        rows = execute_query("SELECT * FROM ctv WHERE ma_ctv = %s", ('CTV001',))
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        if dictionary:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = connection.cursor()
        
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return result
        
    except Error as e:
        print(f"Query error: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return None


def execute_insert(query, params=None, return_id=True):
    """
    DOES: Execute an INSERT query and optionally return the inserted ID
    INPUTS: 
        query - INSERT query (should include RETURNING id if return_id is True)
        params - tuple or list of parameters
        return_id - whether to return the inserted row's ID
    OUTPUTS: Inserted ID or True on success, None on error
    
    Example:
        # Query should include RETURNING id for PostgreSQL
        id = execute_insert(
            "INSERT INTO ctv (ma_ctv, ten) VALUES (%s, %s) RETURNING id",
            ('CTV001', 'Test')
        )
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        
        if return_id:
            result = cursor.fetchone()
            result_id = result[0] if result else None
        else:
            result_id = True
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return result_id
        
    except Error as e:
        print(f"Insert error: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return None


def execute_update(query, params=None):
    """
    DOES: Execute an UPDATE or DELETE query
    INPUTS: 
        query - UPDATE/DELETE query
        params - tuple or list of parameters
    OUTPUTS: Number of affected rows or None on error
    
    Example:
        affected = execute_update("UPDATE ctv SET ten = %s WHERE ma_ctv = %s", ('New Name', 'CTV001'))
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return rowcount
        
    except Error as e:
        print(f"Update error: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return None


# Initialize pool on module import
_pool = get_db_pool()
