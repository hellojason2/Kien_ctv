from flask import jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin, hash_password
from ..db_pool import get_db_connection, return_db_connection

@admin_bp.route('/api/admin/admins', methods=['GET'])
@require_admin
def list_admins():
    """List all admin accounts"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id, username, name, created_at FROM admins ORDER BY id")
        admins = [dict(row) for row in cursor.fetchall()]
        
        for a in admins:
            if a.get('created_at'):
                a['created_at'] = a['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'data': admins
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/admins', methods=['POST'])
@require_admin
def create_admin():
    """Create new admin account"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    required = ['username', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id FROM admins WHERE username = %s", (data['username'],))
        if cursor.fetchone():
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
        
        password_hash = hash_password(data['password'])
        
        cursor.execute("""
            INSERT INTO admins (username, password_hash, name)
            VALUES (%s, %s, %s)
        """, (data['username'], password_hash, data.get('name', '')))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Admin created successfully'
        }), 201
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500

