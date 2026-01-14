"""
Admin CTV Registration Management
Handles viewing and approving/rejecting CTV registration requests
"""
from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin
from ..db_pool import get_db_connection, return_db_connection
from datetime import datetime

@admin_bp.route('/api/admin/registrations', methods=['GET'])
@require_admin
def get_registrations():
    """Get all CTV registration requests"""
    status_filter = request.args.get('status', 'pending')  # pending, approved, rejected, all
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Build where clause
        where = ""
        params = []
        if status_filter != 'all':
            where = "WHERE status = %s"
            params.append(status_filter)
        
        # Get registrations
        offset = (page - 1) * per_page
        query = f"""
            SELECT 
                r.*,
                c.ten as referrer_name
            FROM ctv_registrations r
            LEFT JOIN ctv c ON r.referrer_code = c.ma_ctv
            {where}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        registrations = [dict(row) for row in cursor.fetchall()]
        
        # Format dates
        for reg in registrations:
            if reg['created_at']:
                reg['created_at'] = reg['created_at'].strftime('%d/%m/%Y %H:%M')
            if reg['reviewed_at']:
                reg['reviewed_at'] = reg['reviewed_at'].strftime('%d/%m/%Y %H:%M')
            if reg['dob']:
                reg['dob'] = reg['dob'].strftime('%d/%m/%Y')
        
        # Get total count
        count_params = [status_filter] if status_filter != 'all' else []
        cursor.execute(f"SELECT COUNT(*) as total FROM ctv_registrations {where}", count_params)
        total = cursor.fetchone()['total']
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'registrations': registrations,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@admin_bp.route('/api/admin/registrations/count', methods=['GET'])
@require_admin
def get_pending_registrations_count():
    """Get count of pending registrations"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ctv_registrations WHERE status = 'pending'")
        count = cursor.fetchone()[0]
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'count': count
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@admin_bp.route('/api/admin/registrations/<int:registration_id>/approve', methods=['POST'])
@require_admin
def approve_registration(registration_id):
    """Approve a CTV registration and create the CTV account"""
    data = request.get_json() or {}
    admin_username = g.current_user.get('username', 'admin') if hasattr(g, 'current_user') and g.current_user else 'admin'
    ctv_code = data.get('ctv_code')  # Optional: admin can specify CTV code
    level = data.get('level', 'Đồng')  # Default level
    
    if not ctv_code:
        return jsonify({'status': 'error', 'message': 'CTV code is required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get registration details
        cursor.execute("SELECT * FROM ctv_registrations WHERE id = %s", (registration_id,))
        registration = cursor.fetchone()
        
        if not registration:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Registration not found'}), 404
        
        if registration['status'] != 'pending':
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': f'Registration already {registration["status"]}'}), 400
        
        # Check if CTV code already exists
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        if cursor.fetchone():
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': f'CTV code {ctv_code} already exists'}), 400
        
        # Create CTV account
        cursor.execute("""
            INSERT INTO ctv 
            (ma_ctv, ten, sdt, email, cap_bac, nguoi_gioi_thieu, password_hash, is_active, created_at, signature_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), %s)
        """, (
            ctv_code,
            registration['full_name'],
            registration['phone'],
            registration['email'],
            level,
            registration['referrer_code'],
            registration['password_hash'],
            registration.get('signature_image')
        ))
        
        # Update registration status
        cursor.execute("""
            UPDATE ctv_registrations 
            SET status = 'approved', 
                reviewed_at = NOW(), 
                reviewed_by = %s,
                admin_notes = %s
            WHERE id = %s
        """, (admin_username, f'Approved as {ctv_code}', registration_id))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': f'Registration approved. CTV account {ctv_code} created.',
            'ctv_code': ctv_code
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@admin_bp.route('/api/admin/registrations/<int:registration_id>/reject', methods=['POST'])
@require_admin
def reject_registration(registration_id):
    """Reject a CTV registration"""
    data = request.get_json() or {}
    admin_username = g.current_user.get('username', 'admin') if hasattr(g, 'current_user') and g.current_user else 'admin'
    reason = data.get('reason', 'No reason provided')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Check registration exists and is pending
        cursor.execute("SELECT status FROM ctv_registrations WHERE id = %s", (registration_id,))
        registration = cursor.fetchone()
        
        if not registration:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Registration not found'}), 404
        
        if registration['status'] != 'pending':
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': f'Registration already {registration["status"]}'}), 400
        
        # Update registration status
        cursor.execute("""
            UPDATE ctv_registrations 
            SET status = 'rejected', 
                reviewed_at = NOW(), 
                reviewed_by = %s,
                admin_notes = %s
            WHERE id = %s
        """, (admin_username, reason, registration_id))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Registration rejected'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500
