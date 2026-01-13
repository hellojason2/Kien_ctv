from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin, hash_password
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import get_max_depth_below, build_hierarchy_tree
from ..activity_logger import log_ctv_created, log_ctv_updated, log_ctv_deleted

@admin_bp.route('/api/admin/ctv/levels', methods=['GET'])
@require_admin
def get_ctv_levels():
    """Get all distinct CTV levels"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT DISTINCT cap_bac 
            FROM ctv 
            WHERE cap_bac IS NOT NULL 
            ORDER BY cap_bac
        """)
        
        levels = [row[0] for row in cursor.fetchall()]
        
        # Add default levels if they don't exist
        defaults = ['Đã đặt cọc', 'Đã đến làm']
        for d in defaults:
            if d not in levels:
                levels.append(d)
        
        # Sort levels alphabetically or by some custom logic
        # For now, just sort alphabetically
        levels.sort()
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'levels': levels
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/admin/ctv', methods=['GET'])
@require_admin
def list_ctv():
    """List all CTVs with hierarchy info"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = """
            SELECT 
                c.ma_ctv,
                c.ten,
                c.sdt,
                c.email,
                c.nguoi_gioi_thieu,
                c.nguoi_gioi_thieu as nguoi_gioi_thieu_code,
                c.cap_bac,
                c.is_active,
                c.created_at
            FROM ctv c
            LEFT JOIN ctv p ON c.nguoi_gioi_thieu = p.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (c.ma_ctv ILIKE %s OR c.ten ILIKE %s OR c.email ILIKE %s OR c.sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        if active_only:
            query += " AND (c.is_active = TRUE OR c.is_active IS NULL)"
        
        query += " ORDER BY c.created_at DESC"
        
        cursor.execute(query, params)
        ctv_list = [dict(row) for row in cursor.fetchall()]
        
        # Add max depth below each CTV for level badges
        for ctv in ctv_list:
            if ctv.get('created_at'):
                ctv['created_at'] = ctv['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            # Calculate max depth below this CTV
            ctv['max_depth_below'] = get_max_depth_below(ctv['ma_ctv'], connection)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'data': ctv_list,
            'total': len(ctv_list)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv', methods=['POST'])
@require_admin
def create_ctv():
    """Create new CTV"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    required = ['ma_ctv', 'ten']
    for field in required:
        if not data.get(field):
            return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (data['ma_ctv'],))
        if cursor.fetchone():
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'CTV code already exists'}), 400
        
        nguoi_gioi_thieu = data.get('nguoi_gioi_thieu')
        if nguoi_gioi_thieu:
            cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (nguoi_gioi_thieu,))
            if not cursor.fetchone():
                cursor.close()
                return_db_connection(connection)
                return jsonify({'status': 'error', 'message': 'Referrer CTV not found'}), 400
        
        default_password = hash_password('ctv123')
        
        cursor.execute("""
            INSERT INTO ctv (ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac, password_hash, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (
            data['ma_ctv'],
            data['ten'],
            data.get('sdt'),
            data.get('email'),
            nguoi_gioi_thieu,
            data.get('cap_bac', 'Bronze'),
            default_password
        ))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_ctv_created(admin_username, data['ma_ctv'], data['ten'])
        
        return jsonify({
            'status': 'success',
            'message': 'CTV created successfully',
            'ma_ctv': data['ma_ctv'],
            'default_password': 'ctv123'
        }), 201
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/generate-code', methods=['POST'])
@require_admin
def generate_ctv_code():
    """Generate a unique CTV code"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Find the highest numeric CTV code
        cursor.execute("""
            SELECT ma_ctv FROM ctv 
            WHERE ma_ctv ~ '^[0-9]+$'
            ORDER BY CAST(ma_ctv AS INTEGER) DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            next_code = str(int(result['ma_ctv']) + 1)
        else:
            # No numeric codes exist, start from 1
            next_code = '1'
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'ctv_code': next_code
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/<ctv_code>', methods=['PUT'])
@require_admin
def update_ctv(ctv_code):
    """Update CTV details"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        if not cursor.fetchone():
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
        
        updates = []
        params = []
        
        allowed_fields = ['ten', 'sdt', 'email', 'cap_bac', 'nguoi_gioi_thieu', 'is_active']
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        if data.get('password'):
            updates.append("password_hash = %s")
            params.append(hash_password(data['password']))
        
        if not updates:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        params.append(ctv_code)
        
        cursor.execute(f"""
            UPDATE ctv SET {', '.join(updates)} WHERE ma_ctv = %s
        """, params)
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        changes = {field: data[field] for field in allowed_fields if field in data}
        if data.get('password'):
            changes['password'] = '***changed***'
        log_ctv_updated(admin_username, ctv_code, changes)
        
        return jsonify({
            'status': 'success',
            'message': 'CTV updated successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/<ctv_code>', methods=['DELETE'])
@require_admin
def deactivate_ctv(ctv_code):
    """Deactivate CTV (soft delete)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("UPDATE ctv SET is_active = FALSE WHERE ma_ctv = %s", (ctv_code,))
        
        if cursor.rowcount == 0:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_ctv_deleted(admin_username, ctv_code)
        
        return jsonify({
            'status': 'success',
            'message': 'CTV deactivated successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/<ctv_code>/hard-delete', methods=['DELETE'])
@require_admin
def hard_delete_ctv(ctv_code):
    """Permanently delete a CTV from the database"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get CTV info before deleting
        cursor.execute("SELECT ma_ctv, ten FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        ctv = cursor.fetchone()
        
        if not ctv:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
        
        # Update any referrals to remove this CTV as referrer
        cursor.execute("""
            UPDATE ctv SET nguoi_gioi_thieu = NULL 
            WHERE nguoi_gioi_thieu = %s
        """, (ctv_code,))
        updated_referrals = cursor.rowcount
        
        # Delete related commissions
        cursor.execute("DELETE FROM commissions WHERE ctv_code = %s", (ctv_code,))
        deleted_commissions = cursor.rowcount
        
        # Delete the CTV
        cursor.execute("DELETE FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_ctv_deleted(admin_username, ctv_code)
        
        return jsonify({
            'status': 'success',
            'message': f'CTV {ctv_code} permanently deleted',
            'deleted_commissions': deleted_commissions,
            'updated_referrals': updated_referrals
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/delete-non-numeric', methods=['DELETE'])
@require_admin
def delete_non_numeric_ctv():
    """Delete all CTVs with non-numeric codes"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Find all CTVs with non-numeric codes
        cursor.execute("""
            SELECT ma_ctv, ten FROM ctv 
            WHERE ma_ctv !~ '^[0-9]+$'
        """)
        non_numeric_ctvs = cursor.fetchall()
        
        if not non_numeric_ctvs:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'success',
                'message': 'No non-numeric CTVs found',
                'deleted_count': 0
            })
        
        # Get the codes
        codes_to_delete = [ctv['ma_ctv'] for ctv in non_numeric_ctvs]
        
        # Update any referrals to remove deleted CTVs as referrers
        cursor.execute("""
            UPDATE ctv SET nguoi_gioi_thieu = NULL 
            WHERE nguoi_gioi_thieu = ANY(%s)
        """, (codes_to_delete,))
        
        # Delete related commissions
        cursor.execute("""
            DELETE FROM commissions WHERE ctv_code = ANY(%s)
        """, (codes_to_delete,))
        
        # Delete the CTVs
        cursor.execute("""
            DELETE FROM ctv WHERE ma_ctv !~ '^[0-9]+$'
        """)
        deleted_count = cursor.rowcount
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        for ctv in non_numeric_ctvs:
            log_ctv_deleted(admin_username, ctv['ma_ctv'])
        
        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted_count} CTVs with non-numeric codes',
            'deleted_count': deleted_count,
            'deleted_codes': codes_to_delete
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/hierarchy/<ctv_code>', methods=['GET'])
@require_admin
def get_hierarchy(ctv_code):
    """Get full hierarchy tree for a CTV"""
    tree = build_hierarchy_tree(ctv_code)
    
    if not tree:
        return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
    
    return jsonify({
        'status': 'success',
        'hierarchy': tree
    })
