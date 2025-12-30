"""
Database Connection Pool Module
Provides a singleton connection pool to reduce connection overhead.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# FUNCTIONS:
# - get_db_pool() -> MySQLConnectionPool
#     DOES: Returns singleton connection pool instance
#
# - get_db_connection() -> PooledMySQLConnection
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
"""

import mysql.connector
from mysql.connector import pooling, Error

# Database configuration
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}

# Pool configuration
POOL_NAME = "ctv_pool"
POOL_SIZE = 10  # Number of connections to keep ready

# Singleton pool instance
_pool = None


def get_db_pool():
    """
    DOES: Get or create the singleton connection pool
    OUTPUTS: MySQLConnectionPool instance
    
    The pool maintains POOL_SIZE connections that are reused,
    eliminating the ~0.4s connection overhead per request.
    """
    global _pool
    
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                pool_reset_session=True,
                **DB_CONFIG
            )
            print(f"Database connection pool created: {POOL_NAME} (size={POOL_SIZE})")
        except Error as e:
            print(f"Error creating connection pool: {e}")
            return None
    
    return _pool


def get_db_connection():
    """
    DOES: Get a connection from the pool
    OUTPUTS: PooledMySQLConnection or None
    
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
    pool = get_db_pool()
    if pool is None:
        # Fallback to direct connection if pool fails
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    try:
        return pool.get_connection()
    except Error as e:
        print(f"Error getting connection from pool: {e}")
        # Fallback to direct connection
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e2:
            print(f"Fallback connection also failed: {e2}")
            return None


def init_pool(app=None):
    """
    DOES: Initialize the connection pool (call during app startup)
    INPUTS: Flask app instance (optional, for future use)
    
    Pre-creates the pool so first request doesn't have delay.
    """
    pool = get_db_pool()
    if pool:
        print(f"Connection pool initialized successfully")
        # Test a connection
        try:
            conn = pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            print("Pool connection test: OK")
        except Error as e:
            print(f"Pool connection test failed: {e}")
    else:
        print("WARNING: Connection pool initialization failed")


# Initialize pool on module import
_pool = get_db_pool()

