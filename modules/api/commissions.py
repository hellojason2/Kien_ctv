from flask import jsonify
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from .blueprint import api_bp
from ..db_pool import get_db_connection, return_db_connection

@api_bp.route('/api/commissions/transaction/<int:transaction_id>', methods=['GET'])
def get_transaction_commissions(transaction_id):
    """Get all commissions for a specific transaction"""
    connection = get_db_connection()
    if not connection: return jsonify({'status': 'error', 'message': 'DB error'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT c.*, ctv.ten as ctv_name
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE c.transaction_id = %s
            ORDER BY c.level;
        """, (transaction_id,))
        commissions = cursor.fetchall()
        
        cursor.close()
        return_db_connection(connection)
        return jsonify({'status': 'success', 'transaction_id': transaction_id, 'commissions': commissions})
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/api/ctv/<ctv_code>/commissions', methods=['GET'])
def get_ctv_commissions_legacy(ctv_code):
    """Legacy endpoint for CTV commissions"""
    connection = get_db_connection()
    if not connection: return jsonify({'status': 'error', 'message': 'DB error'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT c.*, s.service_name, s.date_entered
            FROM commissions c
            LEFT JOIN services s ON c.transaction_id = s.id
            WHERE c.ctv_code = %s
            ORDER BY c.created_at DESC;
        """, (ctv_code,))
        commissions = cursor.fetchall()
        
        for c in commissions:
            if c['date_entered']:
                c['date_entered'] = c['date_entered'].strftime('%Y-%m-%d')
            if c['created_at']:
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        return jsonify({'status': 'success', 'ctv_code': ctv_code, 'commissions': commissions})
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

