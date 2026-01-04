from flask import jsonify
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from .blueprint import api_bp
from ..db_pool import get_db_connection, return_db_connection

# Required tables and their essential columns for the CTV system
REQUIRED_SCHEMA = {
    'ctv': ['ma_ctv', 'ten', 'sdt', 'nguoi_gioi_thieu', 'cap_bac'],
    'khach_hang': ['id', 'ten_khach', 'sdt', 'tong_tien', 'nguoi_chot', 'trang_thai', 'ngay_hen_lam'],
    'commissions': ['id', 'transaction_id', 'ctv_code', 'commission_amount', 'transaction_amount'],
    'admins': ['id', 'username', 'password_hash'],
    'sessions': ['id', 'user_type', 'user_id', 'expires_at']
}

@api_bp.route('/api/validate-schema', methods=['GET'])
def validate_schema():
    """
    Validate that the database has the correct schema for the CTV system.
    Returns detailed info about missing tables/columns.
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'status': 'error',
            'valid': False,
            'error_type': 'connection_failed',
            'message': 'Cannot connect to database'
        }), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get database name
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()['current_database']
        
        # Get all existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = {row['table_name'] for row in cursor.fetchall()}
        
        missing_tables = []
        missing_columns = {}
        
        for table, required_cols in REQUIRED_SCHEMA.items():
            if table not in existing_tables:
                missing_tables.append(table)
            else:
                # Check columns for this table
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table,))
                existing_cols = {row['column_name'] for row in cursor.fetchall()}
                
                missing_cols = [col for col in required_cols if col not in existing_cols]
                if missing_cols:
                    missing_columns[table] = missing_cols
        
        cursor.close()
        return_db_connection(connection)
        
        # Determine if schema is valid
        is_valid = len(missing_tables) == 0 and len(missing_columns) == 0
        
        if is_valid:
            return jsonify({
                'status': 'success',
                'valid': True,
                'database': db_name,
                'message': 'Database schema is valid'
            })
        else:
            error_details = []
            if missing_tables:
                error_details.append(f"Missing tables: {', '.join(missing_tables)}")
            if missing_columns:
                for table, cols in missing_columns.items():
                    error_details.append(f"Table '{table}' missing columns: {', '.join(cols)}")
            
            return jsonify({
                'status': 'error',
                'valid': False,
                'error_type': 'schema_mismatch',
                'database': db_name,
                'message': 'Wrong database or schema mismatch',
                'missing_tables': missing_tables,
                'missing_columns': missing_columns,
                'details': error_details
            })
            
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({
            'status': 'error',
            'valid': False,
            'error_type': 'query_error',
            'message': f'Database error: {str(e)}'
        }), 500


@api_bp.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test database connection"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'success',
                'message': 'Database connected successfully',
                'database': db_name[0]
            })
        except Error as e:
            if connection:
                return_db_connection(connection)
            return jsonify({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to database'
        }), 500

@api_bp.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of all tables in the database"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return_db_connection(connection)
        return jsonify({
            'status': 'success',
            'tables': tables
        })
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({
            'status': 'error',
            'message': f'Error fetching tables: {str(e)}'
        }), 500

@api_bp.route('/api/data', methods=['GET'])
def get_data():
    """Fetch customer data (id, name, email, phone)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'customers'
            );
        """)
        result = cursor.fetchone()
        table_exists = result['exists'] if result else False
        
        if not table_exists:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'success',
                'data': [],
                'message': 'Customers table not found.'
            })
        
        cursor.execute("SELECT id, name, email, phone FROM customers ORDER BY id;")
        data = cursor.fetchall()
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'table': 'customers',
            'data': data
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching data: {str(e)}'
        }), 500

