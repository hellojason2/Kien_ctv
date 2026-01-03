"""
Admin Routes Module
All API endpoints for the Admin Dashboard.
Updated for PostgreSQL.

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
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
Updated: January 2, 2026 - Migrated to PostgreSQL
"""

import os
from flask import Blueprint, jsonify, request, send_file, g, make_response, render_template
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

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
    get_all_descendants,
    get_max_depth_below,
    build_ancestor_chain,
    recalculate_all_commissions,
    calculate_missing_commissions,
    calculate_new_commissions_fast,
    get_commission_cache_status
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

# Create Blueprint with template folder
BASE_DIR_FOR_TEMPLATES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
admin_bp = Blueprint('admin', __name__, template_folder=os.path.join(BASE_DIR_FOR_TEMPLATES, 'templates'))

# Get base directory for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use connection pool for better performance
from .db_pool import get_db_connection, return_db_connection


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/admin89/login', methods=['POST'])
def login():
    """Admin login endpoint"""
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
    """Admin logout endpoint"""
    token = request.cookies.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    user = get_current_user()
    if user:
        log_logout(user.get('user_type'), user.get('user_id'))
    
    if token:
        destroy_session(token)
    
    response = make_response(jsonify({'status': 'success', 'message': 'Logged out'}))
    response.delete_cookie('session_token')
    
    return response


@admin_bp.route('/admin89/test', methods=['GET'])
def test_route():
    """Test route to verify blueprint is working"""
    return jsonify({'status': 'success', 'message': 'Admin blueprint is working!'})


@admin_bp.route('/admin89/simple', methods=['GET'])
def simple_test():
    """Simple HTML test route"""
    return '<html><body><h1>Admin Route Works!</h1><p>If you see this, the route is working.</p></body></html>'


@admin_bp.route('/admin89', methods=['GET'])
def dashboard():
    """Serve admin dashboard HTML using Jinja2 template"""
    try:
        # Try rendering the template
        return render_template('admin/base.html')
    except Exception as e:
        # Fallback: try sending the file directly
        import traceback
        error_details = traceback.format_exc()
        print(f"Error rendering admin template: {e}")
        print(f"Traceback: {error_details}")
        
        # Try fallback template file
        template_path = os.path.join(BASE_DIR, 'templates', 'admin.html')
        if os.path.exists(template_path):
            try:
                return send_file(template_path)
            except Exception as e2:
                print(f"Error sending fallback file: {e2}")
        
        # Return HTML error page instead of JSON (browser expects HTML)
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Admin Dashboard Error</title></head>
        <body>
            <h1>Admin Dashboard Error</h1>
            <p>Error: {str(e)}</p>
            <p>Template path checked: {template_path}</p>
            <p>Template exists: {os.path.exists(template_path) if template_path else 'N/A'}</p>
            <pre>{error_details}</pre>
        </body>
        </html>
        """
        return error_html, 500


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
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT level, rate, description, updated_at, updated_by
            FROM commission_settings ORDER BY level
        """)
        settings = [dict(row) for row in cursor.fetchall()]
        
        for s in settings:
            s['rate'] = float(s['rate'])
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'settings': settings
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commission-settings', methods=['PUT'])
@require_admin
def update_settings():
    """Update commission rate settings"""
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
                WHERE level = %s
            """, (rate, description, admin_username, level))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Commission settings updated'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION MANAGEMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/commissions', methods=['GET'])
@require_admin
def list_commissions():
    """Get all commission records with filtering"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        
        if level is not None:
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += f" ORDER BY c.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(commission_amount), 0) as total_commission,
                COUNT(*) as total_records,
                COUNT(DISTINCT ctv_code) as unique_ctv
            FROM commissions
        """)
        summary = cursor.fetchone()
        
        cursor.close()
        return_db_connection(connection)
        
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
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/summary', methods=['GET'])
@require_admin
def list_commissions_summary():
    """Get commission summary grouped by CTV, including services even if no commissions"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        month = request.args.get('month')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build date conditions and parameters for different tables
        comm_params = []
        kh_params = []
        svc_params = []
        
        if month:
            comm_where = "TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            comm_params.append(month)
            kh_where = "TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = %s"
            kh_params.append(month)
            svc_where = "TO_CHAR(s.date_entered, 'YYYY-MM') = %s"
            svc_params.append(month)
        elif date_from and date_to:
            comm_where = "DATE(c.created_at) >= %s AND DATE(c.created_at) <= %s"
            comm_params.extend([date_from, date_to])
            kh_where = "DATE(kh.ngay_hen_lam) >= %s AND DATE(kh.ngay_hen_lam) <= %s"
            kh_params.extend([date_from, date_to])
            svc_where = "DATE(s.date_entered) >= %s AND DATE(s.date_entered) <= %s"
            svc_params.extend([date_from, date_to])
        elif date_from:
            comm_where = "DATE(c.created_at) >= %s"
            comm_params.append(date_from)
            kh_where = "DATE(kh.ngay_hen_lam) >= %s"
            kh_params.append(date_from)
            svc_where = "DATE(s.date_entered) >= %s"
            svc_params.append(date_from)
        elif date_to:
            comm_where = "DATE(c.created_at) <= %s"
            comm_params.append(date_to)
            kh_where = "DATE(kh.ngay_hen_lam) <= %s"
            kh_params.append(date_to)
            svc_where = "DATE(s.date_entered) <= %s"
            svc_params.append(date_to)
        else:
            comm_where = "TO_CHAR(c.created_at, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            kh_where = "TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            svc_where = "TO_CHAR(s.date_entered, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
        
        # Get commissions data
        comm_query = """
            SELECT 
                c.ctv_code,
                SUM(c.transaction_amount) as total_service_price,
                SUM(c.commission_amount) as total_commission,
                COUNT(*) as commission_count
            FROM commissions c
            WHERE """ + comm_where + """
            GROUP BY c.ctv_code
        """
        cursor.execute(comm_query, comm_params)
        commissions_data = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # Get services from khach_hang table
        kh_query = """
            SELECT 
                kh.nguoi_chot as ctv_code,
                COUNT(*) as service_count,
                SUM(kh.tong_tien) as total_revenue
            FROM khach_hang kh
            WHERE kh.nguoi_chot IS NOT NULL 
            AND kh.nguoi_chot != ''
            AND kh.trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
            AND """ + kh_where + """
            GROUP BY kh.nguoi_chot
        """
        cursor.execute(kh_query, kh_params)
        kh_services = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # Get services from services table
        svc_query = """
            SELECT 
                s.ctv_code,
                COUNT(*) as service_count,
                SUM(s.tong_tien) as total_revenue
            FROM services s
            WHERE s.ctv_code IS NOT NULL 
            AND s.ctv_code != ''
            AND """ + svc_where + """
            GROUP BY s.ctv_code
        """
        cursor.execute(svc_query, svc_params)
        svc_services = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # FAST: Calculate only new commissions using cached max IDs
        # This only processes records added since last calculation (delta)
        fast_stats = calculate_new_commissions_fast(connection=connection)
        
        # If any new commissions were calculated, refresh the commissions data
        if fast_stats.get('total', 0) > 0:
            cursor.execute(comm_query, comm_params)
            commissions_data = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # Combine all CTV codes
        all_ctv_codes = set()
        all_ctv_codes.update(commissions_data.keys())
        all_ctv_codes.update(kh_services.keys())
        all_ctv_codes.update(svc_services.keys())
        
        # Build summary (FAST - uses stored commissions)
        summary = []
        total_service_count = 0
        total_service_revenue = 0
        
        for ctv_code in all_ctv_codes:
            # Get CTV info
            cursor.execute("SELECT ma_ctv, ten, sdt FROM ctv WHERE ma_ctv = %s", (ctv_code,))
            ctv_info = cursor.fetchone()
            if not ctv_info:
                continue
            
            # Get commission from stored table (FAST - always use stored data)
            comm_data = commissions_data.get(ctv_code, {})
            comm_total = float(comm_data.get('total_commission', 0) or 0)
            comm_service_price = float(comm_data.get('total_service_price', 0) or 0)
            
            # Get revenue from services tables (for display)
            kh_data = kh_services.get(ctv_code, {})
            kh_count = int(kh_data.get('service_count', 0) or 0)
            kh_revenue = float(kh_data.get('total_revenue', 0) or 0)
            
            svc_data = svc_services.get(ctv_code, {})
            svc_count = int(svc_data.get('service_count', 0) or 0)
            svc_revenue = float(svc_data.get('total_revenue', 0) or 0)
            
            total_services = kh_count + svc_count
            total_revenue = kh_revenue + svc_revenue
            
            # Use stored transaction_amount sum, or revenue from services tables
            service_price = comm_service_price if comm_service_price > 0 else total_revenue
            
            summary.append({
                'ctv_code': ctv_code,
                'ctv_name': ctv_info['ten'],
                'ctv_phone': ctv_info['sdt'],
                'total_service_price': service_price,
                'total_commission': comm_total,
                'service_count': total_services,
                'has_services_no_commission': total_services > 0 and comm_total == 0
            })
            
            total_service_count += total_services
            total_service_revenue += service_price
        
        # Sort by commission descending, then by service count
        summary.sort(key=lambda x: (x['total_commission'], x['service_count']), reverse=True)
        
        grand_total_commission = sum(s['total_commission'] for s in summary)
        grand_total_service = sum(s['total_service_price'] for s in summary)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'grand_total': {
                'total_service_price': grand_total_service,
                'total_commission': grand_total_commission,
                'total_service_count': total_service_count
            },
            'total_ctv': len(summary)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/recalculate', methods=['POST'])
@require_admin
def recalculate_commissions():
    """Recalculate all commissions from khach_hang and services tables (admin only)"""
    try:
        stats = recalculate_all_commissions()
        return jsonify({
            'status': 'success',
            'message': 'Commissions recalculated successfully',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/<int:commission_id>', methods=['PUT'])
@require_admin
def adjust_commission(commission_id):
    """Manually adjust a commission record"""
    data = request.get_json()
    
    if not data or 'commission_amount' not in data:
        return jsonify({'status': 'error', 'message': 'commission_amount required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT commission_amount FROM commissions WHERE id = %s", (commission_id,))
        old_record = cursor.fetchone()
        
        if not old_record:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Commission record not found'}), 404
        
        old_amount = float(old_record['commission_amount'])
        new_amount = float(data['commission_amount'])
        
        cursor.execute("""
            UPDATE commissions SET commission_amount = %s WHERE id = %s
        """, (new_amount, commission_id))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_commission_adjusted(admin_username, commission_id, old_amount, new_amount)
        
        return jsonify({
            'status': 'success',
            'message': 'Commission adjusted successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION CACHE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/commission-cache/status', methods=['GET'])
@require_admin
def get_cache_status():
    """Get commission cache status for debugging/monitoring"""
    status = get_commission_cache_status()
    if status:
        return jsonify({'status': 'success', 'data': status})
    return jsonify({'status': 'error', 'message': 'Could not get cache status'}), 500


# ══════════════════════════════════════════════════════════════════════════════
# STATISTICS ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/stats', methods=['GET'])
@require_admin
def get_stats():
    """Get dashboard statistics with optional date filters (month, day, or from_date/to_date)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        month_filter = request.args.get('month', None)
        day_filter = request.args.get('day', None)
        from_date = request.args.get('from_date', None)
        to_date = request.args.get('to_date', None)
        
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) as count FROM ctv WHERE is_active = TRUE OR is_active IS NULL")
        total_ctv = cursor.fetchone()['count']
        
        # Build date filter conditions for PostgreSQL
        if from_date and to_date:
            date_condition = f"DATE(created_at) >= '{from_date}' AND DATE(created_at) <= '{to_date}'"
            date_condition_services = f"DATE(date_entered) >= '{from_date}' AND DATE(date_entered) <= '{to_date}'"
        elif day_filter:
            date_condition = f"DATE(created_at) = '{day_filter}'"
            date_condition_services = f"DATE(date_entered) = '{day_filter}'"
        elif month_filter:
            date_condition = f"TO_CHAR(created_at, 'YYYY-MM') = '{month_filter}'"
            date_condition_services = f"TO_CHAR(date_entered, 'YYYY-MM') = '{month_filter}'"
        else:
            date_condition = "TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            date_condition_services = "TO_CHAR(date_entered, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
        
        # Calculate missing commissions incrementally (fast - only calculates new ones)
        # This ensures data is always up-to-date without recalculating everything
        # FAST: Calculate only new commissions using cached max IDs
        # This only processes records added since last calculation (delta)
        calculate_new_commissions_fast(connection=connection)
        
        # Get monthly commission from stored commissions table (FAST)
        cursor.execute(f"""
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM commissions
            WHERE {date_condition}
        """)
        monthly_commission = float(cursor.fetchone()['total'])
        
        # Get transaction count from both khach_hang and services tables (matching CTV dashboard logic)
        # Include both Vietnamese and non-Vietnamese status formats
        kh_transactions = 0
        svc_transactions = 0
        
        try:
            if from_date and to_date:
                kh_date_condition = f"DATE(ngay_hen_lam) >= '{from_date}' AND DATE(ngay_hen_lam) <= '{to_date}'"
            elif day_filter:
                kh_date_condition = f"DATE(ngay_hen_lam) = '{day_filter}'"
            elif month_filter:
                kh_date_condition = f"TO_CHAR(ngay_hen_lam, 'YYYY-MM') = '{month_filter}'"
            else:
                kh_date_condition = "TO_CHAR(ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM khach_hang
                WHERE {kh_date_condition}
                AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
            """)
            kh_transactions = cursor.fetchone()['count']
        except Error:
            pass
        
        try:
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM services
                WHERE {date_condition_services}
            """)
            svc_transactions = cursor.fetchone()['count']
        except Error:
            pass
        
        monthly_transactions = kh_transactions + svc_transactions
        
        # Calculate monthly revenue from both khach_hang and services tables (matching CTV dashboard logic)
        # First try commissions table
        cursor.execute(f"""
            SELECT COALESCE(SUM(transaction_amount), 0) as total
            FROM (
                SELECT DISTINCT transaction_id, transaction_amount
                FROM commissions
                WHERE {date_condition}
            ) as distinct_transactions
        """)
        result = cursor.fetchone()
        monthly_revenue = float(result['total']) if result['total'] else 0.0
        
        # If no revenue from commissions, check khach_hang and services tables
        if monthly_revenue == 0:
            kh_revenue = 0
            svc_revenue = 0
            
            try:
                if from_date and to_date:
                    kh_date_condition = f"DATE(ngay_hen_lam) >= '{from_date}' AND DATE(ngay_hen_lam) <= '{to_date}'"
                elif day_filter:
                    kh_date_condition = f"DATE(ngay_hen_lam) = '{day_filter}'"
                elif month_filter:
                    kh_date_condition = f"TO_CHAR(ngay_hen_lam, 'YYYY-MM') = '{month_filter}'"
                else:
                    kh_date_condition = "TO_CHAR(ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
                
                cursor.execute(f"""
                    SELECT COALESCE(SUM(tong_tien), 0) as total
                    FROM khach_hang
                    WHERE {kh_date_condition}
                    AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
                """)
                kh_revenue = float(cursor.fetchone()['total'] or 0)
            except Error:
                pass
            
            try:
                cursor.execute(f"""
                    SELECT COALESCE(SUM(tong_tien), 0) as total
                    FROM services
                    WHERE {date_condition_services}
                """)
                svc_revenue = float(cursor.fetchone()['total'] or 0)
            except Error:
                pass
            
            monthly_revenue = kh_revenue + svc_revenue
        
        cursor.execute("""
            SELECT cap_bac, COUNT(*) as count
            FROM ctv
            WHERE is_active = TRUE OR is_active IS NULL
            GROUP BY cap_bac
        """)
        ctv_by_level = {row['cap_bac']: row['count'] for row in cursor.fetchall()}
        
        # Get top earners - initialize as empty list
        top_earners = []
        try:
            cursor.execute(f"""
                SELECT 
                    c.ctv_code,
                    ctv.ten,
                    COALESCE(SUM(c.transaction_amount), 0) as total_revenue,
                    COALESCE(SUM(c.commission_amount), 0) as total_commission
                FROM commissions c
                JOIN ctv ON c.ctv_code = ctv.ma_ctv
                WHERE {date_condition}
                GROUP BY c.ctv_code, ctv.ten
                HAVING COALESCE(SUM(c.commission_amount), 0) > 0
                ORDER BY total_commission DESC
                LIMIT 5
            """)
            top_earners_raw = cursor.fetchall()
            top_earners = []
            for row in top_earners_raw:
                try:
                    top_earners.append({
                        'ctv_code': row['ctv_code'],
                        'ten': row['ten'],
                        'total_revenue': float(row['total_revenue'] or 0),
                        'total_commission': float(row['total_commission'] or 0)
                    })
                except (ValueError, TypeError) as e:
                    print(f"Error processing top earner row: {e}, row: {row}")
                    continue
        except Error as e:
            print(f"Error fetching top earners: {e}")
            import traceback
            traceback.print_exc()
            top_earners = []
        
        cursor.close()
        return_db_connection(connection)
        
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
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/date-ranges-with-data', methods=['GET'])
@require_admin
def get_date_ranges_with_data():
    """Check which date range presets have data available"""
    import datetime
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        today = datetime.date.today()
        ranges_with_data = {}

        # Define all date ranges (matching frontend logic)
        days_since_sunday = (today.weekday() + 1) % 7  # Convert to Sunday-based (0=Sunday)
        week_start = today - datetime.timedelta(days=days_since_sunday)
        
        date_ranges = {
            'today': (today, today),
            '3days': (today - datetime.timedelta(days=2), today),  # Last 3 days (including today)
            'week': (week_start, today),  # Start of week (Sunday)
            'month': (today.replace(day=1), today),
            'lastmonth': (
                (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1),
                today.replace(day=1) - datetime.timedelta(days=1)
            ),
            '3months': (today.replace(day=1) - datetime.timedelta(days=60), today),
            'year': (today.replace(month=1, day=1), today)
        }

        # Check each date range for data
        for preset, (from_date, to_date) in date_ranges.items():
            # Check khach_hang table
            query_kh = """
                SELECT COUNT(*) as count
                FROM khach_hang
                WHERE trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
                AND ngay_hen_lam >= %s
                AND ngay_hen_lam <= %s
            """
            cursor.execute(query_kh, [from_date, to_date])
            kh_count = cursor.fetchone()['count']

            # Check services table
            query_svc = """
                SELECT COUNT(*) as count
                FROM services
                WHERE date_entered >= %s
                AND date_entered <= %s
            """
            cursor.execute(query_svc, [from_date, to_date])
            svc_count = cursor.fetchone()['count']

            # Check commissions table
            query_comm = """
                SELECT COUNT(*) as count
                FROM commissions
                WHERE DATE(created_at) >= %s
                AND DATE(created_at) <= %s
            """
            cursor.execute(query_comm, [from_date, to_date])
            comm_count = cursor.fetchone()['count']

            # Has data if any table has records
            ranges_with_data[preset] = (kh_count > 0) or (svc_count > 0) or (comm_count > 0)

        cursor.close()
        return_db_connection(connection)

        return jsonify({
            'status': 'success',
            'ranges_with_data': ranges_with_data
        })

    except Error as e:
        if connection:
            return_db_connection(connection)
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


# ══════════════════════════════════════════════════════════════════════════════
# CLIENT SERVICES ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/clients-with-services', methods=['GET'])
@require_admin
def get_clients_with_services():
    """Get all clients with their services grouped - OPTIMIZED VERSION"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        per_page = min(per_page, 100)
        offset = (page - 1) * per_page
        
        base_where = "WHERE sdt IS NOT NULL AND sdt != ''"
        params = []
        
        if search:
            base_where += " AND (ten_khach ILIKE %s OR sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            base_where += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
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
        clients_raw = [dict(row) for row in cursor.fetchall()]
        
        if not clients_raw:
            cursor.close()
            return_db_connection(connection)
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
                'overall_deposit': 'Chua coc',
                'services': [],
                '_order': len(client_keys)
            }
        
        if client_keys:
            or_conditions = []
            flat_keys = []
            for sdt, ten_khach in client_keys:
                or_conditions.append('(sdt = %s AND ten_khach = %s)')
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
                    WHERE {' OR '.join(or_conditions)}
                ) ranked
                WHERE rn <= 3
                ORDER BY sdt, ten_khach, rn
            """
            
            cursor.execute(services_query, flat_keys)
            services_raw = [dict(row) for row in cursor.fetchall()]
            
            for svc in services_raw:
                key = (svc['sdt'], svc['ten_khach'])
                if key not in clients_dict:
                    continue
                
                tien_coc = float(svc['tien_coc'] or 0)
                tong_tien = float(svc['tong_tien'] or 0)
                phai_dong = float(svc['phai_dong'] or 0)
                deposit_status = 'Da coc' if tien_coc > 0 else 'Chua coc'
                
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
                
                if svc['rn'] == 1:
                    clients_dict[key]['overall_status'] = svc['trang_thai'] or ''
                    clients_dict[key]['overall_deposit'] = deposit_status
        
        if len(clients_raw) < per_page:
            total = offset + len(clients_raw)
            total_pages = page
        else:
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
        
        clients = sorted(clients_dict.values(), key=lambda x: x.pop('_order'))
        
        cursor.close()
        return_db_connection(connection)
        
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
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOGS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/activity-logs', methods=['GET'])
@require_admin
def list_activity_logs():
    """Get activity logs with filtering and pagination"""
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
    """Get activity log statistics"""
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
    """Export activity logs as CSV"""
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
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'ID', 'Timestamp', 'Event Type', 'User Type', 'User ID',
            'IP Address', 'Endpoint', 'Method', 'Status Code', 'Details'
        ])
        
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
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'activity_logs', len(logs))
        
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
    """Clean up old activity logs"""
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
    """Get list of available event types for filtering"""
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
    """Get activity logs grouped by user+IP combination"""
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
    """Get IPs that are logged into multiple accounts"""
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
    """Get detailed logs for a specific user+IP combination"""
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
    """Export all CTVs to Excel file"""
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
                CASE WHEN c.is_active = TRUE OR c.is_active IS NULL THEN 'Active' ELSE 'Inactive' END as is_active,
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
        
        for ctv in ctv_list:
            if ctv.get('created_at'):
                ctv['created_at'] = ctv['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'ctv_list', len(ctv_list))
        
        return create_xlsx_response(
            data=ctv_list,
            columns=CTV_EXPORT_COLUMNS,
            filename='ctv_export',
            sheet_name='CTV List'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/export', methods=['GET'])
@require_admin
def export_commissions_excel():
    """Export commission records to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        
        if level is not None:
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += " ORDER BY c.created_at DESC LIMIT 10000"
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commissions', len(commissions))
        
        return create_xlsx_response(
            data=commissions,
            columns=COMMISSION_EXPORT_COLUMNS,
            filename='commissions_export',
            sheet_name='Commissions'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/summary/export', methods=['GET'])
@require_admin
def export_commissions_summary_excel():
    """Export commission summary by CTV to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        month = request.args.get('month')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
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
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        elif date_from and date_to:
            query += " AND DATE(c.created_at) >= %s AND DATE(c.created_at) <= %s"
            params.extend([date_from, date_to])
        elif date_from:
            query += " AND DATE(c.created_at) >= %s"
            params.append(date_from)
        elif date_to:
            query += " AND DATE(c.created_at) <= %s"
            params.append(date_to)
        
        query += """
            GROUP BY c.ctv_code, ctv.ten, ctv.sdt
            ORDER BY total_commission DESC
        """
        
        cursor.execute(query, params)
        summary = [dict(row) for row in cursor.fetchall()]
        
        for s in summary:
            s['total_service_price'] = float(s['total_service_price'] or 0)
            s['total_commission'] = float(s['total_commission'] or 0)
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commission_summary', len(summary))
        
        return create_xlsx_response(
            data=summary,
            columns=COMMISSION_SUMMARY_COLUMNS,
            filename='commission_summary_export',
            sheet_name='Commission Summary'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/clients/export', methods=['GET'])
@require_admin
def export_clients_excel():
    """Export clients with services to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        
        base_where = "WHERE sdt IS NOT NULL AND sdt != ''"
        params = []
        
        if search:
            base_where += " AND (ten_khach ILIKE %s OR sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            base_where += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
        query = f"""
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(nguoi_chot) as nguoi_chot,
                COUNT(*) as service_count,
                MIN(ngay_nhap_don) as first_visit_date,
                MAX(trang_thai) as overall_status,
                CASE WHEN MAX(tien_coc) > 0 THEN 'Da coc' ELSE 'Chua coc' END as overall_deposit
            FROM khach_hang
            {base_where}
            GROUP BY sdt, ten_khach
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT 10000
        """
        
        cursor.execute(query, params)
        clients = [dict(row) for row in cursor.fetchall()]
        
        for client in clients:
            if client.get('first_visit_date'):
                client['first_visit_date'] = client['first_visit_date'].strftime('%d/%m/%Y')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'clients', len(clients))
        
        return create_xlsx_response(
            data=clients,
            columns=CLIENTS_EXPORT_COLUMNS,
            filename='clients_export',
            sheet_name='Clients'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/export-xlsx', methods=['GET'])
@require_admin
def export_activity_logs_excel():
    """Export activity logs to Excel file"""
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        
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
        
        for log in logs:
            if log.get('details'):
                if isinstance(log['details'], dict):
                    log['details'] = str(log['details'])
                else:
                    log['details'] = str(log['details'])
        
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
    """Export commission settings to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT level, rate, description, updated_at, updated_by
            FROM commission_settings ORDER BY level
        """)
        settings = [dict(row) for row in cursor.fetchall()]
        
        for s in settings:
            s['rate'] = float(s['rate'])
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commission_settings', len(settings))
        
        return create_xlsx_response(
            data=settings,
            columns=COMMISSION_SETTINGS_COLUMNS,
            filename='commission_settings_export',
            sheet_name='Commission Settings'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500
