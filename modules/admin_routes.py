"""
Admin Routes Module
All API endpoints for the Admin Dashboard.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# ENDPOINTS:
#
# Authentication:
# - POST /admin/login         -> Admin login
# - POST /admin/logout        -> Admin logout
# - GET  /admin/dashboard     -> Serve admin dashboard HTML
#
# CTV Management:
# - GET    /api/admin/ctv            -> List all CTVs
# - POST   /api/admin/ctv            -> Create new CTV
# - PUT    /api/admin/ctv/<code>     -> Update CTV
# - DELETE /api/admin/ctv/<code>     -> Deactivate CTV
# - GET    /api/admin/hierarchy/<code> -> Get hierarchy tree
#
# Commission Settings:
# - GET /api/admin/commission-settings -> Get commission rates
# - PUT /api/admin/commission-settings -> Update commission rates
#
# Commission Management:
# - GET /api/admin/commissions         -> All commission reports
# - PUT /api/admin/commissions/<id>    -> Adjust commission record
#
# Statistics:
# - GET /api/admin/stats -> Dashboard statistics
#
# Admin Management:
# - GET  /api/admin/admins     -> List all admins
# - POST /api/admin/admins     -> Create new admin
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
"""

import os
from flask import Blueprint, jsonify, request, send_file, g, make_response
import mysql.connector
from mysql.connector import Error

from .auth import (
    require_admin,
    admin_login,
    destroy_session,
    hash_password,
    get_current_user
)
from .mlm_core import (
    build_hierarchy_tree,
    validate_ctv_data,
    get_commission_rates,
    get_all_descendants
)

# Create Blueprint
admin_bp = Blueprint('admin', __name__)

# Database configuration
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}

# Get base directory for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Admin Routes - Error connecting to MySQL: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/admin/login', methods=['POST'])
def login():
    """
    Admin login endpoint
    Body: {"username": "admin", "password": "admin123"}
    Returns: {"token": "...", "admin": {...}}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password required'}), 400
    
    result = admin_login(username, password)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 401
    
    # Set cookie with token
    response = make_response(jsonify({
        'status': 'success',
        'token': result['token'],
        'admin': result['admin']
    }))
    response.set_cookie('session_token', result['token'], httponly=True, max_age=86400)
    
    return response


@admin_bp.route('/admin/logout', methods=['POST'])
def logout():
    """
    Admin logout endpoint
    Destroys session and clears cookie
    """
    token = request.cookies.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if token:
        destroy_session(token)
    
    response = make_response(jsonify({'status': 'success', 'message': 'Logged out'}))
    response.delete_cookie('session_token')
    
    return response


@admin_bp.route('/admin/dashboard', methods=['GET'])
def dashboard():
    """Serve admin dashboard HTML"""
    template_path = os.path.join(BASE_DIR, 'templates', 'admin.html')
    if os.path.exists(template_path):
        return send_file(template_path)
    return jsonify({'status': 'error', 'message': 'Admin dashboard not found'}), 404


@admin_bp.route('/admin/check-auth', methods=['GET'])
def check_auth():
    """Check if current user is authenticated as admin"""
    user = get_current_user()
    if user and user.get('user_type') == 'admin':
        return jsonify({'status': 'success', 'authenticated': True, 'user': user})
    return jsonify({'status': 'error', 'authenticated': False}), 401


# ══════════════════════════════════════════════════════════════════════════════
# CTV MANAGEMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/ctv', methods=['GET'])
@require_admin
def list_ctv():
    """
    List all CTVs with hierarchy info
    Query params: ?search=term, ?active_only=true
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        search = request.args.get('search', '').strip()
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = """
            SELECT 
                c.ma_ctv,
                c.ten,
                c.sdt,
                c.email,
                c.nguoi_gioi_thieu,
                p.ten as nguoi_gioi_thieu_name,
                c.cap_bac,
                c.is_active,
                c.created_at
            FROM ctv c
            LEFT JOIN ctv p ON c.nguoi_gioi_thieu = p.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (c.ma_ctv LIKE %s OR c.ten LIKE %s OR c.email LIKE %s OR c.sdt LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        if active_only:
            query += " AND (c.is_active = TRUE OR c.is_active IS NULL)"
        
        query += " ORDER BY c.created_at DESC;"
        
        cursor.execute(query, params)
        ctv_list = cursor.fetchall()
        
        # Convert datetime objects
        for ctv in ctv_list:
            if ctv.get('created_at'):
                ctv['created_at'] = ctv['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'data': ctv_list,
            'total': len(ctv_list)
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv', methods=['POST'])
@require_admin
def create_ctv():
    """
    Create new CTV
    Body: {"ma_ctv": "CTV012", "ten": "Name", "email": "...", "nguoi_gioi_thieu": "CTV001"}
    """
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
        cursor = connection.cursor()
        
        # Check if CTV code already exists
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s;", (data['ma_ctv'],))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'CTV code already exists'}), 400
        
        # Verify referrer exists if provided
        nguoi_gioi_thieu = data.get('nguoi_gioi_thieu')
        if nguoi_gioi_thieu:
            cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s;", (nguoi_gioi_thieu,))
            if not cursor.fetchone():
                cursor.close()
                connection.close()
                return jsonify({'status': 'error', 'message': 'Referrer CTV not found'}), 400
        
        # Create default password
        default_password = hash_password('ctv123')
        
        cursor.execute("""
            INSERT INTO ctv (ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac, password_hash, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE);
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
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'CTV created successfully',
            'ma_ctv': data['ma_ctv'],
            'default_password': 'ctv123'
        }), 201
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/<ctv_code>', methods=['PUT'])
@require_admin
def update_ctv(ctv_code):
    """
    Update CTV details
    Body: {"ten": "New Name", "email": "new@email.com", ...}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Check CTV exists
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s;", (ctv_code,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
        
        # Build update query dynamically
        updates = []
        params = []
        
        allowed_fields = ['ten', 'sdt', 'email', 'cap_bac', 'nguoi_gioi_thieu', 'is_active']
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        # Handle password update separately
        if data.get('password'):
            updates.append("password_hash = %s")
            params.append(hash_password(data['password']))
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        params.append(ctv_code)
        
        cursor.execute(f"""
            UPDATE ctv SET {', '.join(updates)} WHERE ma_ctv = %s;
        """, params)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'CTV updated successfully'
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/<ctv_code>', methods=['DELETE'])
@require_admin
def deactivate_ctv(ctv_code):
    """
    Deactivate CTV (soft delete)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("UPDATE ctv SET is_active = FALSE WHERE ma_ctv = %s;", (ctv_code,))
        
        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'CTV not found'}), 404
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'CTV deactivated successfully'
        })
        
    except Error as e:
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


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION SETTINGS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/commission-settings', methods=['GET'])
@require_admin
def get_settings():
    """Get all commission rate settings"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT level, rate, description, updated_at, updated_by
            FROM commission_settings ORDER BY level;
        """)
        settings = cursor.fetchall()
        
        for s in settings:
            s['rate'] = float(s['rate'])
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'settings': settings
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commission-settings', methods=['PUT'])
@require_admin
def update_settings():
    """
    Update commission rate settings
    Body: {"settings": [{"level": 0, "rate": 0.25, "description": "..."}, ...]}
    """
    data = request.get_json()
    
    if not data or 'settings' not in data:
        return jsonify({'status': 'error', 'message': 'Settings array required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        admin_username = g.current_user.get('username', 'admin')
        
        for setting in data['settings']:
            level = setting.get('level')
            rate = setting.get('rate')
            description = setting.get('description')
            
            if level is None or rate is None:
                continue
            
            if level < 0 or level > 4:
                continue
            
            cursor.execute("""
                UPDATE commission_settings 
                SET rate = %s, description = %s, updated_by = %s
                WHERE level = %s;
            """, (rate, description, admin_username, level))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Commission settings updated'
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION MANAGEMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/commissions', methods=['GET'])
@require_admin
def list_commissions():
    """
    Get all commission records with filtering
    Query params: ?ctv_code=CTV001, ?month=2025-12, ?level=1
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        ctv_code = request.args.get('ctv_code')
        month = request.args.get('month')
        level = request.args.get('level')
        limit = request.args.get('limit', 100, type=int)
        
        query = """
            SELECT 
                c.id,
                c.transaction_id,
                c.ctv_code,
                ctv.ten as ctv_name,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if ctv_code:
            query += " AND c.ctv_code = %s"
            params.append(ctv_code)
        
        if month:
            query += " AND DATE_FORMAT(c.created_at, '%Y-%m') = %s"
            params.append(month)
        
        if level is not None:
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += f" ORDER BY c.created_at DESC LIMIT {limit};"
        
        cursor.execute(query, params)
        commissions = cursor.fetchall()
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Get summary
        cursor.execute("""
            SELECT 
                SUM(commission_amount) as total_commission,
                COUNT(*) as total_records,
                COUNT(DISTINCT ctv_code) as unique_ctv
            FROM commissions;
        """)
        summary = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'data': commissions,
            'summary': {
                'total_commission': float(summary['total_commission'] or 0),
                'total_records': summary['total_records'],
                'unique_ctv': summary['unique_ctv']
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/<int:commission_id>', methods=['PUT'])
@require_admin
def adjust_commission(commission_id):
    """
    Manually adjust a commission record
    Body: {"commission_amount": 50000, "note": "Manual adjustment"}
    """
    data = request.get_json()
    
    if not data or 'commission_amount' not in data:
        return jsonify({'status': 'error', 'message': 'commission_amount required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE commissions SET commission_amount = %s WHERE id = %s;
        """, (data['commission_amount'], commission_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'Commission record not found'}), 404
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Commission adjusted successfully'
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# STATISTICS ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/stats', methods=['GET'])
@require_admin
def get_stats():
    """Get dashboard statistics"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Total CTVs
        cursor.execute("SELECT COUNT(*) as count FROM ctv WHERE is_active = TRUE OR is_active IS NULL;")
        total_ctv = cursor.fetchone()['count']
        
        # Total commissions this month
        cursor.execute("""
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM commissions
            WHERE DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
        """)
        monthly_commission = float(cursor.fetchone()['total'])
        
        # Total transactions this month
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM services
            WHERE DATE_FORMAT(date_entered, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
        """)
        monthly_transactions = cursor.fetchone()['count']
        
        # Total transaction value this month
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as total
            FROM services
            WHERE DATE_FORMAT(date_entered, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
        """)
        monthly_revenue = float(cursor.fetchone()['total'])
        
        # CTV by level (cap_bac)
        cursor.execute("""
            SELECT cap_bac, COUNT(*) as count
            FROM ctv
            WHERE is_active = TRUE OR is_active IS NULL
            GROUP BY cap_bac;
        """)
        ctv_by_level = {row['cap_bac']: row['count'] for row in cursor.fetchall()}
        
        # Top earners this month
        cursor.execute("""
            SELECT 
                c.ctv_code,
                ctv.ten,
                SUM(c.commission_amount) as total_earned
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE DATE_FORMAT(c.created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')
            GROUP BY c.ctv_code, ctv.ten
            ORDER BY total_earned DESC
            LIMIT 5;
        """)
        top_earners = cursor.fetchall()
        for t in top_earners:
            t['total_earned'] = float(t['total_earned'])
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_ctv': total_ctv,
                'monthly_commission': monthly_commission,
                'monthly_transactions': monthly_transactions,
                'monthly_revenue': monthly_revenue,
                'ctv_by_level': ctv_by_level,
                'top_earners': top_earners
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN MANAGEMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/admins', methods=['GET'])
@require_admin
def list_admins():
    """List all admin accounts"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT id, username, name, created_at FROM admins ORDER BY id;")
        admins = cursor.fetchall()
        
        for a in admins:
            if a.get('created_at'):
                a['created_at'] = a['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'data': admins
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/admins', methods=['POST'])
@require_admin
def create_admin():
    """
    Create new admin account
    Body: {"username": "admin2", "password": "password", "name": "Admin Name"}
    """
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
        cursor = connection.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM admins WHERE username = %s;", (data['username'],))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
        
        password_hash = hash_password(data['password'])
        
        cursor.execute("""
            INSERT INTO admins (username, password_hash, name)
            VALUES (%s, %s, %s);
        """, (data['username'], password_hash, data.get('name', '')))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Admin created successfully'
        }), 201
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# CLIENT SERVICES ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/clients-with-services', methods=['GET'])
@require_admin
def get_clients_with_services():
    """
    Get all clients with their services grouped
    Groups khach_hang records by phone + name combination
    Returns up to 3 services per client
    
    Query params:
    - search: Search by name or phone
    - nguoi_chot: Filter by CTV code
    - limit: Max number of clients (default 50)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
        # First, get unique clients (grouped by phone + name)
        # MIN(ngay_nhap_don) = first time visiting (earliest date they entered the system)
        client_query = """
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(ngay_nhap_don) as first_visit_date,
                MIN(nguoi_chot) as nguoi_chot,
                COUNT(*) as service_count
            FROM khach_hang
            WHERE sdt IS NOT NULL AND sdt != ''
        """
        params = []
        
        if search:
            client_query += " AND (ten_khach LIKE %s OR sdt LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            client_query += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
        client_query += f"""
            GROUP BY sdt, ten_khach
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT {limit};
        """
        
        cursor.execute(client_query, params)
        clients_raw = cursor.fetchall()
        
        # For each client, get their services (up to 3)
        clients = []
        for client_row in clients_raw:
            sdt = client_row['sdt']
            ten_khach = client_row['ten_khach']
            
            # Get services for this client
            cursor.execute("""
                SELECT 
                    id,
                    dich_vu,
                    tong_tien,
                    tien_coc,
                    phai_dong,
                    ngay_hen_lam,
                    ngay_nhap_don,
                    trang_thai,
                    nguoi_chot
                FROM khach_hang
                WHERE sdt = %s AND ten_khach = %s
                ORDER BY ngay_nhap_don DESC
                LIMIT 3;
            """, (sdt, ten_khach))
            
            services_raw = cursor.fetchall()
            
            # Process services
            services = []
            for idx, svc in enumerate(services_raw):
                tien_coc = float(svc['tien_coc'] or 0)
                tong_tien = float(svc['tong_tien'] or 0)
                phai_dong = float(svc['phai_dong'] or 0)
                
                # Determine deposit status based on tien_coc
                if tien_coc > 0:
                    deposit_status = 'Da coc'
                else:
                    deposit_status = 'Chua coc'
                
                services.append({
                    'id': svc['id'],
                    'service_number': idx + 1,
                    'dich_vu': svc['dich_vu'] or '',
                    'tong_tien': tong_tien,
                    'tien_coc': tien_coc,
                    'phai_dong': phai_dong,
                    'ngay_nhap_don': svc['ngay_nhap_don'].strftime('%d/%m/%Y') if svc['ngay_nhap_don'] else None,
                    'ngay_hen_lam': svc['ngay_hen_lam'].strftime('%d/%m/%Y') if svc['ngay_hen_lam'] else None,
                    'trang_thai': svc['trang_thai'] or '',
                    'deposit_status': deposit_status
                })
            
            # Determine overall client status (from most recent service)
            overall_status = services[0]['trang_thai'] if services else ''
            overall_deposit = services[0]['deposit_status'] if services else 'Chua coc'
            
            # Format first_visit_date (earliest date they entered the system)
            first_visit = client_row['first_visit_date']
            if first_visit:
                first_visit_str = first_visit.strftime('%d/%m/%Y')
            else:
                first_visit_str = None
            
            clients.append({
                'ten_khach': ten_khach or '',
                'sdt': sdt or '',
                'co_so': client_row['co_so'] or '',
                'first_visit_date': first_visit_str,
                'nguoi_chot': client_row['nguoi_chot'] or '',
                'service_count': client_row['service_count'],
                'overall_status': overall_status,
                'overall_deposit': overall_deposit,
                'services': services
            })
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'clients': clients,
            'total': len(clients)
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

