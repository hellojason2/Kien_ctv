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
# - POST /admin89/login       -> Admin login
# - POST /admin89/logout      -> Admin logout
# - GET  /admin89             -> Serve admin dashboard HTML (secret URL)
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
# Activity Logs:
# - GET  /api/admin/activity-logs        -> List logs with filtering
# - GET  /api/admin/activity-logs/stats  -> Get log statistics
# - GET  /api/admin/activity-logs/export -> Export logs as CSV
# - POST /api/admin/activity-logs/cleanup -> Clean up old logs
# - GET  /api/admin/activity-logs/event-types -> Get event types list
#
# Excel Export:
# - GET /api/admin/ctv/export                  -> Export CTVs to Excel
# - GET /api/admin/commissions/export          -> Export commissions to Excel
# - GET /api/admin/commissions/summary/export  -> Export commission summary to Excel
# - GET /api/admin/clients/export              -> Export clients to Excel
# - GET /api/admin/activity-logs/export-xlsx   -> Export activity logs to Excel
# - GET /api/admin/commission-settings/export  -> Export settings to Excel
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
Updated: December 30, 2025 - Added Excel export endpoints
"""

import os
from flask import Blueprint, jsonify, request, send_file, g, make_response, render_template
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
from .activity_logger import (
    get_activity_logs,
    get_activity_logs_grouped,
    get_activity_stats,
    get_suspicious_ips,
    cleanup_old_logs,
    log_logout,
    log_ctv_created,
    log_ctv_updated,
    log_ctv_deleted,
    log_commission_adjusted,
    log_data_export
)
from .export_excel import (
    create_xlsx_response,
    CTV_EXPORT_COLUMNS,
    COMMISSION_EXPORT_COLUMNS,
    COMMISSION_SUMMARY_COLUMNS,
    CLIENTS_EXPORT_COLUMNS,
    ACTIVITY_LOG_COLUMNS,
    COMMISSION_SETTINGS_COLUMNS
)

# Create Blueprint
admin_bp = Blueprint('admin', __name__)

# Get base directory for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use connection pool for better performance
from .db_pool import get_db_connection


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/admin89/login', methods=['POST'])
def login():
    """
    Admin login endpoint
    Body: {"username": "admin", "password": "admin123", "remember_me": true}
    Returns: {"token": "...", "admin": {...}}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password required'}), 400
    
    result = admin_login(username, password, remember_me=remember_me)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 401
    
    # Set cookie with token - longer expiry if remember me is checked
    # Default: 24 hours (86400 seconds), Remember me: 30 days (2592000 seconds)
    cookie_max_age = 2592000 if remember_me else 86400
    
    response = make_response(jsonify({
        'status': 'success',
        'token': result['token'],
        'admin': result['admin']
    }))
    response.set_cookie('session_token', result['token'], httponly=True, max_age=cookie_max_age)
    
    return response


@admin_bp.route('/admin89/logout', methods=['POST'])
def logout():
    """
    Admin logout endpoint
    Destroys session and clears cookie
    
    LOGGING: Logs logout event before destroying session
    """
    token = request.cookies.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    # Get user info before destroying session for logging
    user = get_current_user()
    if user:
        log_logout(user.get('user_type'), user.get('user_id'))
    
    if token:
        destroy_session(token)
    
    response = make_response(jsonify({'status': 'success', 'message': 'Logged out'}))
    response.delete_cookie('session_token')
    
    return response


@admin_bp.route('/admin89', methods=['GET'])
def dashboard():
    """Serve admin dashboard HTML using Jinja2 template"""
    try:
        return render_template('admin/base.html')
    except Exception as e:
        # Fallback to old method if new templates don't exist yet
        template_path = os.path.join(BASE_DIR, 'templates', 'admin.html')
        if os.path.exists(template_path):
            return send_file(template_path)
        return jsonify({'status': 'error', 'message': f'Admin dashboard not found: {str(e)}'}), 404


@admin_bp.route('/admin89/check-auth', methods=['GET'])
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
        
        # Log CTV creation
        admin_username = g.current_user.get('username', 'admin')
        log_ctv_created(admin_username, data['ma_ctv'], data['ten'])
        
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
        
        # Log CTV update
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
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/ctv/<ctv_code>', methods=['DELETE'])
@require_admin
def deactivate_ctv(ctv_code):
    """
    Deactivate CTV (soft delete)
    
    LOGGING: Logs ctv_deleted event
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
        
        # Log CTV deactivation
        admin_username = g.current_user.get('username', 'admin')
        log_ctv_deleted(admin_username, ctv_code)
        
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


@admin_bp.route('/api/admin/commissions/summary', methods=['GET'])
@require_admin
def list_commissions_summary():
    """
    Get commission summary grouped by CTV
    
    DOES: Aggregates all commissions by CTV showing total service price and total commission
    OUTPUTS: CTV code, CTV name, CTV phone, Total service price, Total commission
    
    Query params: ?month=2025-12
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        month = request.args.get('month')
        
        query = """
            SELECT 
                c.ctv_code,
                ctv.ten as ctv_name,
                ctv.sdt as ctv_phone,
                SUM(c.transaction_amount) as total_service_price,
                SUM(c.commission_amount) as total_commission
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if month:
            query += " AND DATE_FORMAT(c.created_at, '%Y-%m') = %s"
            params.append(month)
        
        query += """
            GROUP BY c.ctv_code, ctv.ten, ctv.sdt
            ORDER BY total_commission DESC
        """
        
        cursor.execute(query, params)
        summary = cursor.fetchall()
        
        # Convert decimals for JSON
        for s in summary:
            s['total_service_price'] = float(s['total_service_price'] or 0)
            s['total_commission'] = float(s['total_commission'] or 0)
        
        # Get grand total
        grand_total_commission = sum(s['total_commission'] for s in summary)
        grand_total_service = sum(s['total_service_price'] for s in summary)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'grand_total': {
                'total_service_price': grand_total_service,
                'total_commission': grand_total_commission
            },
            'total_ctv': len(summary)
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/<int:commission_id>', methods=['PUT'])
@require_admin
def adjust_commission(commission_id):
    """
    Manually adjust a commission record
    Body: {"commission_amount": 50000, "note": "Manual adjustment"}
    
    LOGGING: Logs commission_adjusted event with old and new values
    """
    data = request.get_json()
    
    if not data or 'commission_amount' not in data:
        return jsonify({'status': 'error', 'message': 'commission_amount required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get old value for logging
        cursor.execute("SELECT commission_amount FROM commissions WHERE id = %s;", (commission_id,))
        old_record = cursor.fetchone()
        
        if not old_record:
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'Commission record not found'}), 404
        
        old_amount = float(old_record['commission_amount'])
        new_amount = float(data['commission_amount'])
        
        cursor.execute("""
            UPDATE commissions SET commission_amount = %s WHERE id = %s;
        """, (new_amount, commission_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Log commission adjustment
        admin_username = g.current_user.get('username', 'admin')
        log_commission_adjusted(admin_username, commission_id, old_amount, new_amount)
        
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
        
        # Top earners this month (with total revenue and commission)
        cursor.execute("""
            SELECT 
                c.ctv_code,
                ctv.ten,
                SUM(c.transaction_amount) as total_revenue,
                SUM(c.commission_amount) as total_commission
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE DATE_FORMAT(c.created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')
            GROUP BY c.ctv_code, ctv.ten
            ORDER BY total_commission DESC
            LIMIT 5;
        """)
        top_earners = cursor.fetchall()
        for t in top_earners:
            t['total_revenue'] = float(t['total_revenue'])
            t['total_commission'] = float(t['total_commission'])
        
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
    Get all clients with their services grouped - OPTIMIZED VERSION (2-Query Approach)
    Groups khach_hang records by phone + name combination
    Returns up to 3 services per client
    
    OPTIMIZATION: Uses 2 queries instead of N+1:
    1. Get paginated client list
    2. Batch-fetch all services for those clients
    
    Query params:
    - search: Search by name or phone
    - nguoi_chot: Filter by CTV code
    - page: Page number (default 1)
    - per_page: Records per page (default 50, max 100)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 100)
        offset = (page - 1) * per_page
        
        # Build WHERE clause for base filtering
        base_where = "WHERE sdt IS NOT NULL AND sdt != ''"
        params = []
        
        if search:
            base_where += " AND (ten_khach LIKE %s OR sdt LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            base_where += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
        # QUERY 1: Get paginated client list (grouped by sdt + ten_khach)
        # Use subquery to avoid slow GROUP BY on full table
        client_query = f"""
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(ngay_nhap_don) as first_visit_date,
                MAX(ngay_nhap_don) as last_visit_date,
                MIN(nguoi_chot) as nguoi_chot,
                COUNT(*) as service_count
            FROM khach_hang
            {base_where}
            GROUP BY sdt, ten_khach
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(client_query, params + [per_page, offset])
        clients_raw = cursor.fetchall()
        
        # If no clients, return early
        if not clients_raw:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'success',
                'clients': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0
                }
            })
        
        # Build client lookup and collect keys for batch query
        clients_dict = {}
        client_keys = []
        for row in clients_raw:
            key = (row['sdt'], row['ten_khach'])
            client_keys.append(key)
            
            first_visit = row['first_visit_date']
            first_visit_str = first_visit.strftime('%d/%m/%Y') if first_visit else None
            
            clients_dict[key] = {
                'ten_khach': row['ten_khach'] or '',
                'sdt': row['sdt'] or '',
                'co_so': row['co_so'] or '',
                'first_visit_date': first_visit_str,
                'nguoi_chot': row['nguoi_chot'] or '',
                'service_count': row['service_count'],
                'overall_status': '',
                'overall_deposit': 'Chưa cọc',
                'services': [],
                '_order': len(client_keys)  # preserve order
            }
        
        # QUERY 2: Batch-fetch all services for these clients (top 3 per client using window function)
        # Build IN clause for the client keys
        placeholders = ', '.join(['(%s, %s)'] * len(client_keys))
        flat_keys = []
        for sdt, ten_khach in client_keys:
            flat_keys.extend([sdt, ten_khach])
        
        services_query = f"""
            SELECT * FROM (
                SELECT 
                    id,
                    sdt,
                    ten_khach,
                    dich_vu,
                    tong_tien,
                    tien_coc,
                    phai_dong,
                    ngay_hen_lam,
                    ngay_nhap_don,
                    trang_thai,
                    nguoi_chot,
                    ROW_NUMBER() OVER (PARTITION BY sdt, ten_khach ORDER BY ngay_nhap_don DESC) as rn
                FROM khach_hang
                WHERE (sdt, ten_khach) IN ({placeholders})
            ) ranked
            WHERE rn <= 3
            ORDER BY sdt, ten_khach, rn
        """
        
        cursor.execute(services_query, flat_keys)
        services_raw = cursor.fetchall()
        
        # Attach services to clients
        for svc in services_raw:
            key = (svc['sdt'], svc['ten_khach'])
            if key not in clients_dict:
                continue
            
            tien_coc = float(svc['tien_coc'] or 0)
            tong_tien = float(svc['tong_tien'] or 0)
            phai_dong = float(svc['phai_dong'] or 0)
            deposit_status = 'Đã cọc' if tien_coc > 0 else 'Chưa cọc'
            
            service = {
                'id': svc['id'],
                'service_number': svc['rn'],
                'dich_vu': svc['dich_vu'] or '',
                'tong_tien': tong_tien,
                'tien_coc': tien_coc,
                'phai_dong': phai_dong,
                'ngay_nhap_don': svc['ngay_nhap_don'].strftime('%d/%m/%Y') if svc['ngay_nhap_don'] else None,
                'ngay_hen_lam': svc['ngay_hen_lam'].strftime('%d/%m/%Y') if svc['ngay_hen_lam'] else None,
                'trang_thai': svc['trang_thai'] or '',
                'deposit_status': deposit_status
            }
            
            clients_dict[key]['services'].append(service)
            
            # Set overall status from first (most recent) service
            if svc['rn'] == 1:
                clients_dict[key]['overall_status'] = svc['trang_thai'] or ''
                clients_dict[key]['overall_deposit'] = deposit_status
        
        # OPTIMIZATION: Skip count query on first page if we got fewer results than per_page
        # This saves one database roundtrip (~0.4s)
        if len(clients_raw) < per_page:
            # We have all remaining results
            total = offset + len(clients_raw)
            total_pages = page
        else:
            # Need exact count for pagination - but cache it for subsequent pages
            # Use SQL_CALC_FOUND_ROWS alternative if available, otherwise do separate query
            count_query = f"""
                SELECT COUNT(*) as total FROM (
                    SELECT 1 FROM khach_hang
                    {base_where}
                    GROUP BY sdt, ten_khach
                ) as grouped_clients
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page
        
        # Convert to list maintaining original order
        clients = sorted(clients_dict.values(), key=lambda x: x.pop('_order'))
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'clients': clients,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOGS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/activity-logs', methods=['GET'])
@require_admin
def list_activity_logs():
    """
    Get activity logs with filtering and pagination
    
    Query params:
    - event_type: Filter by event type (login_success, login_failed, etc.)
    - user_type: Filter by user type (admin, ctv)
    - user_id: Filter by specific user
    - ip_address: Filter by IP address
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - search: Search across user_id, endpoint, IP
    - page: Page number (default 1)
    - per_page: Records per page (default 50)
    """
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 100)
        
        result = get_activity_logs(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'logs': result['logs'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result.get('total_pages', 1)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/stats', methods=['GET'])
@require_admin
def get_logs_stats():
    """
    Get activity log statistics
    
    Returns:
    - logins_today: Number of successful logins today
    - failed_logins_today: Number of failed login attempts today
    - unique_ips_today: Number of unique IP addresses today
    - total_logs: Total number of log entries
    - events_by_type: Breakdown of events by type (last 7 days)
    - top_ips: Most active IP addresses (last 7 days)
    - recent_failed_logins: Recent failed login attempts
    """
    try:
        stats = get_activity_stats()
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/export', methods=['GET'])
@require_admin
def export_activity_logs():
    """
    Export activity logs as CSV
    
    Query params: Same as list_activity_logs
    Returns: CSV file download
    """
    import csv
    import io
    
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        
        # Get all matching logs (up to 10000)
        result = get_activity_logs(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=1,
            per_page=10000
        )
        
        logs = result['logs']
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Timestamp', 'Event Type', 'User Type', 'User ID',
            'IP Address', 'Endpoint', 'Method', 'Status Code', 'Details'
        ])
        
        # Write data rows
        for log in logs:
            details_str = ''
            if log.get('details'):
                if isinstance(log['details'], dict):
                    details_str = str(log['details'])
                else:
                    details_str = str(log['details'])
            
            writer.writerow([
                log.get('id', ''),
                log.get('timestamp', ''),
                log.get('event_type', ''),
                log.get('user_type', ''),
                log.get('user_id', ''),
                log.get('ip_address', ''),
                log.get('endpoint', ''),
                log.get('method', ''),
                log.get('status_code', ''),
                details_str
            ])
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'activity_logs', len(logs))
        
        # Prepare response
        output.seek(0)
        from flask import Response
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=activity_logs_{date_from or "all"}_{date_to or "now"}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/cleanup', methods=['POST'])
@require_admin
def cleanup_logs():
    """
    Clean up old activity logs
    
    Body: {"days": 90} - Delete logs older than this many days
    """
    data = request.get_json() or {}
    days = data.get('days', 90)
    
    if days < 30:
        return jsonify({
            'status': 'error',
            'message': 'Minimum retention period is 30 days'
        }), 400
    
    try:
        deleted_count = cleanup_old_logs(days)
        
        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted_count} logs older than {days} days',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/event-types', methods=['GET'])
@require_admin
def get_event_types():
    """
    Get list of available event types for filtering
    """
    event_types = [
        {'value': 'login_success', 'label': 'Login Success', 'color': 'green'},
        {'value': 'login_failed', 'label': 'Login Failed', 'color': 'red'},
        {'value': 'logout', 'label': 'Logout', 'color': 'blue'},
        {'value': 'api_call', 'label': 'API Call', 'color': 'gray'},
        {'value': 'ctv_created', 'label': 'CTV Created', 'color': 'purple'},
        {'value': 'ctv_updated', 'label': 'CTV Updated', 'color': 'orange'},
        {'value': 'ctv_deleted', 'label': 'CTV Deleted', 'color': 'red'},
        {'value': 'commission_adjusted', 'label': 'Commission Adjusted', 'color': 'yellow'},
        {'value': 'data_export', 'label': 'Data Export', 'color': 'cyan'},
        {'value': 'settings_changed', 'label': 'Settings Changed', 'color': 'pink'}
    ]
    
    return jsonify({
        'status': 'success',
        'event_types': event_types
    })


@admin_bp.route('/api/admin/activity-logs/grouped', methods=['GET'])
@require_admin
def list_activity_logs_grouped():
    """
    Get activity logs grouped by user+IP combination
    
    Query params:
    - event_type: Filter by event type
    - user_type: Filter by user type (admin, ctv)
    - user_id: Filter by specific user
    - ip_address: Filter by IP address
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - search: Search term
    - page: Page number (default 1)
    - per_page: Items per page (default 50)
    
    Returns grouped logs and suspicious IPs
    """
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        per_page = min(per_page, 100)
        
        result = get_activity_logs_grouped(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'groups': result['groups'],
            'suspicious_ips': result['suspicious_ips'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result.get('total_pages', 1)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/suspicious-ips', methods=['GET'])
@require_admin
def get_suspicious_ips_endpoint():
    """
    Get IPs that are logged into multiple accounts
    
    Returns a dict of IP addresses with their associated user accounts
    """
    try:
        suspicious = get_suspicious_ips()
        
        return jsonify({
            'status': 'success',
            'suspicious_ips': suspicious,
            'count': len(suspicious)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/details', methods=['GET'])
@require_admin
def get_logs_by_user_ip():
    """
    Get detailed logs for a specific user+IP combination
    
    Query params:
    - user_id: User ID (required)
    - ip_address: IP address (required)
    - page: Page number (default 1)
    - per_page: Items per page (default 20)
    """
    try:
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not user_id and not ip_address:
            return jsonify({'status': 'error', 'message': 'user_id or ip_address required'}), 400
        
        result = get_activity_logs(
            user_id=user_id if user_id else None,
            ip_address=ip_address if ip_address else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'logs': result['logs'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result.get('total_pages', 1)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# EXCEL EXPORT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/ctv/export', methods=['GET'])
@require_admin
def export_ctv_excel():
    """
    Export all CTVs to Excel file
    
    Query params: ?search=term, ?active_only=true (same as list_ctv)
    Returns: XLSX file download
    
    LOGGING: Logs data_export event
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
                CASE WHEN c.is_active = TRUE OR c.is_active IS NULL THEN 'Active' ELSE 'Inactive' END as is_active,
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
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'ctv_list', len(ctv_list))
        
        return create_xlsx_response(
            data=ctv_list,
            columns=CTV_EXPORT_COLUMNS,
            filename='ctv_export',
            sheet_name='CTV List'
        )
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/export', methods=['GET'])
@require_admin
def export_commissions_excel():
    """
    Export commission records to Excel file
    
    Query params: ?ctv_code=CTV001, ?month=2025-12, ?level=1
    Returns: XLSX file download
    
    LOGGING: Logs data_export event
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        ctv_code = request.args.get('ctv_code')
        month = request.args.get('month')
        level = request.args.get('level')
        
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
        
        query += " ORDER BY c.created_at DESC LIMIT 10000;"
        
        cursor.execute(query, params)
        commissions = cursor.fetchall()
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commissions', len(commissions))
        
        return create_xlsx_response(
            data=commissions,
            columns=COMMISSION_EXPORT_COLUMNS,
            filename='commissions_export',
            sheet_name='Commissions'
        )
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/summary/export', methods=['GET'])
@require_admin
def export_commissions_summary_excel():
    """
    Export commission summary by CTV to Excel file
    
    Query params: ?month=2025-12
    Returns: XLSX file download
    
    LOGGING: Logs data_export event
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        month = request.args.get('month')
        
        query = """
            SELECT 
                c.ctv_code,
                ctv.ten as ctv_name,
                ctv.sdt as ctv_phone,
                SUM(c.transaction_amount) as total_service_price,
                SUM(c.commission_amount) as total_commission
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if month:
            query += " AND DATE_FORMAT(c.created_at, '%Y-%m') = %s"
            params.append(month)
        
        query += """
            GROUP BY c.ctv_code, ctv.ten, ctv.sdt
            ORDER BY total_commission DESC
        """
        
        cursor.execute(query, params)
        summary = cursor.fetchall()
        
        # Convert decimals for Excel
        for s in summary:
            s['total_service_price'] = float(s['total_service_price'] or 0)
            s['total_commission'] = float(s['total_commission'] or 0)
        
        cursor.close()
        connection.close()
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commission_summary', len(summary))
        
        return create_xlsx_response(
            data=summary,
            columns=COMMISSION_SUMMARY_COLUMNS,
            filename='commission_summary_export',
            sheet_name='Commission Summary'
        )
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/clients/export', methods=['GET'])
@require_admin
def export_clients_excel():
    """
    Export clients with services to Excel file
    
    Query params: ?search=term, ?nguoi_chot=CTV001
    Returns: XLSX file download
    
    LOGGING: Logs data_export event
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        
        # Build WHERE clause
        base_where = "WHERE sdt IS NOT NULL AND sdt != ''"
        params = []
        
        if search:
            base_where += " AND (ten_khach LIKE %s OR sdt LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            base_where += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
        # Get clients grouped by phone + name with aggregated data
        query = f"""
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(nguoi_chot) as nguoi_chot,
                COUNT(*) as service_count,
                MIN(ngay_nhap_don) as first_visit_date,
                MAX(trang_thai) as overall_status,
                CASE WHEN MAX(tien_coc) > 0 THEN 'Đã cọc' ELSE 'Chưa cọc' END as overall_deposit
            FROM khach_hang
            {base_where}
            GROUP BY sdt, ten_khach
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT 10000
        """
        
        cursor.execute(query, params)
        clients = cursor.fetchall()
        
        # Format dates
        for client in clients:
            if client.get('first_visit_date'):
                client['first_visit_date'] = client['first_visit_date'].strftime('%d/%m/%Y')
        
        cursor.close()
        connection.close()
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'clients', len(clients))
        
        return create_xlsx_response(
            data=clients,
            columns=CLIENTS_EXPORT_COLUMNS,
            filename='clients_export',
            sheet_name='Clients'
        )
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/export-xlsx', methods=['GET'])
@require_admin
def export_activity_logs_excel():
    """
    Export activity logs to Excel file
    
    Query params: Same as list_activity_logs
    Returns: XLSX file download
    
    LOGGING: Logs data_export event
    """
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        
        # Get all matching logs (up to 10000)
        result = get_activity_logs(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=1,
            per_page=10000
        )
        
        logs = result['logs']
        
        # Convert details dict to string for Excel
        for log in logs:
            if log.get('details'):
                if isinstance(log['details'], dict):
                    log['details'] = str(log['details'])
                else:
                    log['details'] = str(log['details'])
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'activity_logs', len(logs))
        
        return create_xlsx_response(
            data=logs,
            columns=ACTIVITY_LOG_COLUMNS,
            filename='activity_logs_export',
            sheet_name='Activity Logs'
        )
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commission-settings/export', methods=['GET'])
@require_admin
def export_commission_settings_excel():
    """
    Export commission settings to Excel file
    
    Returns: XLSX file download
    
    LOGGING: Logs data_export event
    """
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
        
        # Log the export
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commission_settings', len(settings))
        
        return create_xlsx_response(
            data=settings,
            columns=COMMISSION_SETTINGS_COLUMNS,
            filename='commission_settings_export',
            sheet_name='Commission Settings'
        )
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
