from flask import jsonify, request
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from .blueprint import api_bp
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import (
    validate_ctv_data, 
    build_hierarchy_tree, 
    calculate_level, 
    get_commission_rates,
    calculate_commission_for_service
)

@api_bp.route('/api/ctv/import', methods=['POST'])
def import_ctv():
    """Import CTV data with referral relationships"""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'status': 'error', 'message': 'JSON list of CTVs required'}), 400
    
    is_valid, error_msg = validate_ctv_data(data)
    if not is_valid:
        return jsonify({'status': 'error', 'message': error_msg}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        for ctv in data:
            cursor.execute("""
                INSERT INTO ctv (ma_ctv, ten, email, sdt, nguoi_gioi_thieu, cap_bac)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (ma_ctv) DO UPDATE SET
                    ten = EXCLUDED.ten,
                    email = EXCLUDED.email,
                    sdt = EXCLUDED.sdt,
                    nguoi_gioi_thieu = EXCLUDED.nguoi_gioi_thieu,
                    cap_bac = EXCLUDED.cap_bac;
            """, (
                ctv['ma_ctv'],
                ctv['ten'],
                ctv.get('email'),
                ctv.get('sdt'),
                ctv.get('nguoi_gioi_thieu'),
                ctv.get('cap_bac', 'Bronze')
            ))
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        return jsonify({'status': 'success', 'message': f'Imported {len(data)} CTVs'})
    except Error as e:
        if connection: connection.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/api/ctv/<ctv_code>/hierarchy', methods=['GET'])
def get_ctv_hierarchy(ctv_code):
    """Get hierarchy tree for a CTV"""
    tree = build_hierarchy_tree(ctv_code)
    if not tree:
        return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
    return jsonify({'status': 'success', 'hierarchy': tree})

@api_bp.route('/api/ctv/<ctv_code>/levels', methods=['GET'])
def get_ctv_levels(ctv_code):
    """Get all CTVs and their level relative to this CTV"""
    connection = get_db_connection()
    if not connection: return jsonify({'status': 'error', 'message': 'DB error'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT ma_ctv, ten FROM ctv;")
        all_ctvs = cursor.fetchall()
        
        results = []
        for other in all_ctvs:
            level = calculate_level(cursor, other['ma_ctv'], ctv_code)
            if level is not None:
                results.append({
                    'ma_ctv': other['ma_ctv'],
                    'ten': other['ten'],
                    'level': level
                })
        
        cursor.close()
        return_db_connection(connection)
        return jsonify({'status': 'success', 'ctv_code': ctv_code, 'network': results})
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/api/services', methods=['POST'])
def add_service():
    """Add a service and calculate commissions"""
    data = request.get_json()
    required = ['customer_id', 'service_name', 'amount', 'ctv_code']
    for f in required:
        if f not in data: return jsonify({'status': 'error', 'message': f'Missing {f}'}), 400
    
    connection = get_db_connection()
    if not connection: return jsonify({'status': 'error', 'message': 'DB error'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            INSERT INTO services (customer_id, service_name, amount, ctv_code, date_entered, status)
            VALUES (%s, %s, %s, %s, CURRENT_DATE, 'Completed')
            RETURNING id;
        """, (data['customer_id'], data['service_name'], data['amount'], data['ctv_code']))
        
        service_id = cursor.fetchone()['id']
        commissions = calculate_commission_for_service(service_id, data['ctv_code'], data['amount'], connection)
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        return jsonify({
            'status': 'success',
            'service_id': service_id,
            'commissions_calculated': len(commissions)
        })
    except Error as e:
        if connection: connection.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

