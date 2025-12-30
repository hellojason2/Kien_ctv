"""
CTV Routes Module
All API endpoints for the CTV Portal.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# ENDPOINTS:
#
# Authentication:
# - POST /ctv/login          -> CTV login (email + password)
# - POST /ctv/logout         -> CTV logout
# - GET  /ctv/portal         -> Serve CTV portal HTML
#
# Profile:
# - GET /api/ctv/me          -> Get logged-in CTV profile
#
# Commissions:
# - GET /api/ctv/my-commissions -> Get own commission earnings
#
# Network:
# - GET /api/ctv/my-downline    -> Get all CTVs under me
# - GET /api/ctv/my-hierarchy   -> Get my hierarchy tree
# - GET /api/ctv/my-network/search -> Search customers in my network
#
# KEY SECURITY:
# All endpoints filter data to only show records within CTV's network
# Uses get_all_descendants() to determine accessible CTV codes
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
"""

import os
from flask import Blueprint, jsonify, request, send_file, g, make_response
import mysql.connector
from mysql.connector import Error

from .auth import (
    require_ctv,
    ctv_login,
    destroy_session,
    get_current_user,
    change_ctv_password
)
from .mlm_core import (
    build_hierarchy_tree,
    get_all_descendants,
    get_commission_rates,
    calculate_level,
    get_network_stats
)

# Create Blueprint
ctv_bp = Blueprint('ctv', __name__)

# Get base directory for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use connection pool for better performance
from .db_pool import get_db_connection


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/ctv/login', methods=['POST'])
def login():
    """
    CTV login endpoint
    Body: {"ma_ctv": "BsDieu", "password": "123456"}
    Login is case-insensitive (can enter "BSDIEU" or "bsdieu")
    Returns: {"token": "...", "ctv": {...}}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    ma_ctv = data.get('ma_ctv', '').strip()
    password = data.get('password', '')
    
    if not ma_ctv or not password:
        return jsonify({'status': 'error', 'message': 'CTV code and password required'}), 400
    
    result = ctv_login(ma_ctv, password)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 401
    
    # Set cookie with token
    response = make_response(jsonify({
        'status': 'success',
        'token': result['token'],
        'ctv': result['ctv']
    }))
    response.set_cookie('session_token', result['token'], httponly=True, max_age=86400)
    
    return response


@ctv_bp.route('/ctv/logout', methods=['POST'])
def logout():
    """
    CTV logout endpoint
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


@ctv_bp.route('/ctv/portal', methods=['GET'])
def portal():
    """Serve CTV portal HTML"""
    template_path = os.path.join(BASE_DIR, 'templates', 'ctv_portal.html')
    if os.path.exists(template_path):
        return send_file(template_path)
    return jsonify({'status': 'error', 'message': 'CTV portal not found'}), 404


@ctv_bp.route('/ctv/check-auth', methods=['GET'])
def check_auth():
    """Check if current user is authenticated as CTV"""
    user = get_current_user()
    if user and user.get('user_type') == 'ctv':
        return jsonify({'status': 'success', 'authenticated': True, 'user': user})
    return jsonify({'status': 'error', 'authenticated': False}), 401


@ctv_bp.route('/api/ctv/change-password', methods=['POST'])
@require_ctv
def change_password():
    """
    Change CTV password
    Body: {"current_password": "123456", "new_password": "newpass123"}
    Requires authentication
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'status': 'error', 'message': 'Current and new password required'}), 400
    
    ctv = g.current_user
    result = change_ctv_password(ctv['ma_ctv'], current_password, new_password)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 400
    
    return jsonify({'status': 'success', 'message': 'Password changed successfully'})


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/me', methods=['GET'])
@require_ctv
def get_profile():
    """
    Get logged-in CTV profile with network stats
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        # Get network stats
        stats = get_network_stats(ctv['ma_ctv'], connection)
        
        # Get referrer info
        cursor = connection.cursor(dictionary=True)
        if ctv.get('nguoi_gioi_thieu'):
            cursor.execute("""
                SELECT ma_ctv, ten FROM ctv WHERE ma_ctv = %s;
            """, (ctv['nguoi_gioi_thieu'],))
            referrer = cursor.fetchone()
        else:
            referrer = None
        
        # Get total earnings
        cursor.execute("""
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM commissions WHERE ctv_code = %s;
        """, (ctv['ma_ctv'],))
        total_earnings = float(cursor.fetchone()['total'])
        
        # Get this month's earnings
        cursor.execute("""
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM commissions 
            WHERE ctv_code = %s 
            AND DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
        """, (ctv['ma_ctv'],))
        monthly_earnings = float(cursor.fetchone()['total'])
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'profile': {
                'ma_ctv': ctv['ma_ctv'],
                'ten': ctv['ten'],
                'email': ctv['email'],
                'sdt': ctv['sdt'],
                'cap_bac': ctv['cap_bac'],
                'referrer': referrer
            },
            'stats': {
                'network_size': stats['total'],
                'network_by_level': stats['by_level'],
                'total_earnings': total_earnings,
                'monthly_earnings': monthly_earnings
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/my-commissions', methods=['GET'])
@require_ctv
def get_my_commissions():
    """
    Get own commission earnings with breakdown
    Query params: ?month=2025-12, ?level=1
    
    Returns commission records with:
    - source_ctv_name: Name of the CTV who made the sale (nguoi_chot)
    - source_ctv_code: Code of the CTV who made the sale
    - customer_name: Name of the customer
    - service_name: Name of the service
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        month = request.args.get('month')
        level = request.args.get('level')
        
        # Build query with JOINs to get source CTV, customer, and service info
        query = """
            SELECT 
                c.id,
                c.transaction_id,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at,
                s.nguoi_chot as source_ctv_code,
                s.service_name,
                ctv_source.ten as source_ctv_name,
                cust.name as customer_name
            FROM commissions c
            LEFT JOIN services s ON c.transaction_id = s.id
            LEFT JOIN ctv ctv_source ON s.nguoi_chot = ctv_source.ma_ctv
            LEFT JOIN customers cust ON s.customer_id = cust.id
            WHERE c.ctv_code = %s
        """
        params = [ctv['ma_ctv']]
        
        if month:
            query += " AND DATE_FORMAT(c.created_at, '%Y-%m') = %s"
            params.append(month)
        
        if level is not None:
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += " ORDER BY c.created_at DESC LIMIT 100;"
        
        cursor.execute(query, params)
        commissions = cursor.fetchall()
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            # Provide fallback values if JOINs returned NULL
            c['source_ctv_name'] = c.get('source_ctv_name') or c.get('source_ctv_code') or 'N/A'
            c['source_ctv_code'] = c.get('source_ctv_code') or 'N/A'
            c['customer_name'] = c.get('customer_name') or 'N/A'
            c['service_name'] = c.get('service_name') or 'N/A'
        
        # Get summary by level
        summary_query = """
            SELECT 
                level,
                COUNT(*) as count,
                SUM(commission_amount) as total
            FROM commissions
            WHERE ctv_code = %s
        """
        summary_params = [ctv['ma_ctv']]
        
        if month:
            summary_query += " AND DATE_FORMAT(created_at, '%Y-%m') = %s"
            summary_params.append(month)
        
        summary_query += " GROUP BY level ORDER BY level;"
        
        cursor.execute(summary_query, summary_params)
        summary = cursor.fetchall()
        
        for s in summary:
            s['total'] = float(s['total'] or 0)
        
        total_commission = sum(s['total'] for s in summary)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'commissions': commissions,
            'summary': {
                'by_level': summary,
                'total': total_commission
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# NETWORK ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/my-downline', methods=['GET'])
@require_ctv
def get_my_downline():
    """
    Get all CTVs directly under me (Level 1 only)
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                ma_ctv,
                ten,
                sdt,
                email,
                cap_bac,
                created_at
            FROM ctv
            WHERE nguoi_gioi_thieu = %s AND (is_active = TRUE OR is_active IS NULL)
            ORDER BY created_at DESC;
        """, (ctv['ma_ctv'],))
        
        downline = cursor.fetchall()
        
        for d in downline:
            if d.get('created_at'):
                d['created_at'] = d['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'downline': downline,
            'total': len(downline)
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/my-hierarchy', methods=['GET'])
@require_ctv
def get_my_hierarchy():
    """
    Get my hierarchy tree (all descendants)
    """
    ctv = g.current_user
    
    tree = build_hierarchy_tree(ctv['ma_ctv'])
    
    if not tree:
        return jsonify({'status': 'error', 'message': 'Failed to build hierarchy'}), 500
    
    return jsonify({
        'status': 'success',
        'hierarchy': tree
    })


@ctv_bp.route('/api/ctv/my-network/search', methods=['GET'])
@require_ctv
def search_my_network():
    """
    Search customers/phone numbers within my network only
    Query params: ?q=search_term
    
    SECURITY: Only returns results where nguoi_chot is in CTV's network
    """
    ctv = g.current_user
    search_term = request.args.get('q', '').strip()
    
    if not search_term or len(search_term) < 2:
        return jsonify({
            'status': 'error',
            'message': 'Search term must be at least 2 characters'
        }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        # Get all CTVs in my network
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        
        if not my_network:
            return jsonify({
                'status': 'success',
                'customers': [],
                'ctv_members': [],
                'total': 0
            })
        
        cursor = connection.cursor(dictionary=True)
        
        # Search customers where nguoi_chot is in my network
        placeholders = ','.join(['%s'] * len(my_network))
        search_like = f"%{search_term}%"
        
        # Search customers
        customer_query = f"""
            SELECT DISTINCT
                c.id,
                c.name,
                c.phone,
                c.email
            FROM customers c
            JOIN services s ON c.id = s.customer_id
            WHERE s.nguoi_chot IN ({placeholders})
            AND (c.name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s)
            LIMIT 20;
        """
        params = list(my_network) + [search_like, search_like, search_like]
        
        cursor.execute(customer_query, params)
        customers = cursor.fetchall()
        
        # Search CTV members in my network
        ctv_query = f"""
            SELECT 
                ma_ctv,
                ten,
                sdt,
                email,
                cap_bac
            FROM ctv
            WHERE ma_ctv IN ({placeholders})
            AND (ten LIKE %s OR sdt LIKE %s OR email LIKE %s OR ma_ctv LIKE %s)
            AND (is_active = TRUE OR is_active IS NULL)
            LIMIT 20;
        """
        ctv_params = list(my_network) + [search_like, search_like, search_like, search_like]
        
        cursor.execute(ctv_query, ctv_params)
        ctv_members = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'customers': customers,
            'ctv_members': ctv_members,
            'total': len(customers) + len(ctv_members)
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/my-network/customers', methods=['GET'])
@require_ctv
def get_my_customers():
    """
    Get all customers in my network
    
    SECURITY: Only returns customers where nguoi_chot is in CTV's network
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        # Get all CTVs in my network
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        
        if not my_network:
            return jsonify({
                'status': 'success',
                'customers': [],
                'total': 0
            })
        
        cursor = connection.cursor(dictionary=True)
        
        placeholders = ','.join(['%s'] * len(my_network))
        
        cursor.execute(f"""
            SELECT DISTINCT
                c.id,
                c.name,
                c.phone,
                c.email,
                s.service_name as last_service,
                s.date_entered as last_service_date,
                s.nguoi_chot as served_by
            FROM customers c
            JOIN services s ON c.id = s.customer_id
            WHERE s.nguoi_chot IN ({placeholders})
            ORDER BY s.date_entered DESC
            LIMIT 100;
        """, list(my_network))
        
        customers = cursor.fetchall()
        
        for c in customers:
            if c.get('last_service_date'):
                c['last_service_date'] = c['last_service_date'].strftime('%Y-%m-%d')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'customers': customers,
            'total': len(customers)
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/my-stats', methods=['GET'])
@require_ctv
def get_my_stats():
    """
    Get detailed statistics for my network
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get network stats
        stats = get_network_stats(ctv['ma_ctv'], connection)
        
        # Get commission breakdown by level (all time)
        cursor.execute("""
            SELECT 
                level,
                SUM(commission_amount) as total,
                COUNT(*) as count
            FROM commissions
            WHERE ctv_code = %s
            GROUP BY level
            ORDER BY level;
        """, (ctv['ma_ctv'],))
        commission_by_level = cursor.fetchall()
        
        for c in commission_by_level:
            c['total'] = float(c['total'] or 0)
        
        # Get monthly trend (last 6 months)
        cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m') as month,
                SUM(commission_amount) as total
            FROM commissions
            WHERE ctv_code = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month;
        """, (ctv['ma_ctv'],))
        monthly_trend = cursor.fetchall()
        
        for m in monthly_trend:
            m['total'] = float(m['total'] or 0)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'network': stats,
                'commission_by_level': commission_by_level,
                'monthly_trend': monthly_trend
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# KHACH HANG (CUSTOMER) ENDPOINTS - Based on new khach_hang table
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/customers', methods=['GET'])
@require_ctv
def get_ctv_customers():
    """
    Get all customers where nguoi_chot = logged-in CTV
    Uses the new khach_hang table
    
    Query params:
    - status: Filter by trang_thai (Da den lam, Da coc, Huy lich, Cho xac nhan)
    - from: Filter ngay_hen_lam >= from date (YYYY-MM-DD)
    - to: Filter ngay_hen_lam <= to date (YYYY-MM-DD)
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build query with optional filters
        query = """
            SELECT 
                id,
                ngay_nhap_don,
                ten_khach,
                sdt,
                co_so,
                ngay_hen_lam,
                gio,
                dich_vu,
                tong_tien,
                tien_coc,
                phai_dong,
                nguoi_chot,
                ghi_chu,
                trang_thai,
                created_at
            FROM khach_hang
            WHERE nguoi_chot = %s
        """
        params = [ctv['ma_ctv']]
        
        # Filter by status
        status = request.args.get('status')
        if status:
            query += " AND trang_thai = %s"
            params.append(status)
        
        # Filter by date range (on ngay_hen_lam)
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        if from_date:
            query += " AND ngay_hen_lam >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND ngay_hen_lam <= %s"
            params.append(to_date)
        
        query += " ORDER BY ngay_hen_lam DESC, id DESC LIMIT 100;"
        
        cursor.execute(query, params)
        customers = cursor.fetchall()
        
        # Convert dates and decimals for JSON
        for c in customers:
            if c.get('ngay_nhap_don'):
                c['ngay_nhap_don'] = c['ngay_nhap_don'].strftime('%Y-%m-%d')
            if c.get('ngay_hen_lam'):
                c['ngay_hen_lam'] = c['ngay_hen_lam'].strftime('%Y-%m-%d')
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            c['tong_tien'] = float(c['tong_tien'] or 0)
            c['tien_coc'] = float(c['tien_coc'] or 0)
            c['phai_dong'] = float(c['phai_dong'] or 0)
        
        # Get summary stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN trang_thai = 'Da den lam' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN trang_thai = 'Da den lam' THEN tong_tien ELSE 0 END) as total_revenue,
                SUM(CASE WHEN trang_thai = 'Da coc' THEN 1 ELSE 0 END) as pending_count
            FROM khach_hang
            WHERE nguoi_chot = %s
        """, (ctv['ma_ctv'],))
        
        summary = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'customers': customers,
            'summary': {
                'total': int(summary['total_count'] or 0),
                'completed': int(summary['completed_count'] or 0),
                'pending': int(summary['pending_count'] or 0),
                'total_revenue': float(summary['total_revenue'] or 0)
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/earliest-date', methods=['GET'])
@require_ctv
def get_ctv_earliest_date():
    """
    Get the earliest customer date for the CTV and their network.
    Returns the minimum ngay_hen_lam from khach_hang table.
    This is used to set default start date in date filters.
    
    Returns:
    - earliest_date: The first date when CTV received a customer (YYYY-MM-DD)
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all CTV codes in network (self + descendants)
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        
        if not my_network:
            my_network = [ctv['ma_ctv']]
        
        # Find the earliest ngay_hen_lam across the network
        placeholders = ','.join(['%s'] * len(my_network))
        query = f"""
            SELECT MIN(ngay_hen_lam) as earliest_date
            FROM khach_hang
            WHERE nguoi_chot IN ({placeholders})
            AND ngay_hen_lam IS NOT NULL
        """
        
        cursor.execute(query, my_network)
        result = cursor.fetchone()
        
        earliest_date = None
        if result and result['earliest_date']:
            earliest_date = result['earliest_date'].strftime('%Y-%m-%d')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'earliest_date': earliest_date
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/commission', methods=['GET'])
@require_ctv
def get_ctv_commission():
    """
    Get commission based on khach_hang table with date filter on ngay_hen_lam
    Only counts transactions where trang_thai = 'Da den lam'
    
    Query params:
    - from: Start date (YYYY-MM-DD) for ngay_hen_lam
    - to: End date (YYYY-MM-DD) for ngay_hen_lam
    
    Commission calculation:
    - Level 0 (self): 25% of tong_tien where trang_thai = 'Da den lam'
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get date filters
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        # Get commission rates from config
        cursor.execute("SELECT level, percent FROM hoa_hong_config ORDER BY level")
        rates_rows = cursor.fetchall()
        commission_rates = {row['level']: float(row['percent']) / 100 for row in rates_rows}
        
        # Level 0: Own revenue (nguoi_chot = me, trang_thai = 'Da den lam')
        level0_query = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai = 'Da den lam'
        """
        level0_params = [ctv['ma_ctv']]
        
        if from_date:
            level0_query += " AND ngay_hen_lam >= %s"
            level0_params.append(from_date)
        if to_date:
            level0_query += " AND ngay_hen_lam <= %s"
            level0_params.append(to_date)
        
        cursor.execute(level0_query, level0_params)
        level0 = cursor.fetchone()
        
        level0_revenue = float(level0['total_revenue'] or 0)
        level0_count = int(level0['transaction_count'] or 0)
        level0_commission = level0_revenue * commission_rates.get(0, 0.25)
        
        # Get all descendants for level 1-4 commissions
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        my_network_excluding_self = [c for c in my_network if c != ctv['ma_ctv']]
        
        level_commissions = [{
            'level': 0,
            'description': 'Doanh so ban than',
            'total_revenue': level0_revenue,
            'transaction_count': level0_count,
            'rate': commission_rates.get(0, 0.25) * 100,
            'commission': level0_commission
        }]
        
        # Calculate commissions for each level (1-4)
        if my_network_excluding_self:
            for level in range(1, 5):
                # Get CTVs at this level
                cursor_check = connection.cursor(dictionary=True)
                level_ctv_list = []
                
                for descendant_code in my_network_excluding_self:
                    # Calculate level of this descendant relative to me
                    desc_level = calculate_level_simple(ctv['ma_ctv'], descendant_code, connection)
                    if desc_level == level:
                        level_ctv_list.append(descendant_code)
                
                cursor_check.close()
                
                if level_ctv_list:
                    placeholders = ','.join(['%s'] * len(level_ctv_list))
                    level_query = f"""
                        SELECT 
                            SUM(tong_tien) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM khach_hang
                        WHERE nguoi_chot IN ({placeholders})
                        AND trang_thai = 'Da den lam'
                    """
                    level_params = list(level_ctv_list)
                    
                    if from_date:
                        level_query += " AND ngay_hen_lam >= %s"
                        level_params.append(from_date)
                    if to_date:
                        level_query += " AND ngay_hen_lam <= %s"
                        level_params.append(to_date)
                    
                    cursor.execute(level_query, level_params)
                    level_data = cursor.fetchone()
                    
                    level_revenue = float(level_data['total_revenue'] or 0)
                    level_count = int(level_data['transaction_count'] or 0)
                    level_commission = level_revenue * commission_rates.get(level, 0)
                    
                    level_commissions.append({
                        'level': level,
                        'description': f'Doanh so Level {level}',
                        'total_revenue': level_revenue,
                        'transaction_count': level_count,
                        'rate': commission_rates.get(level, 0) * 100,
                        'commission': level_commission
                    })
        
        # Calculate totals
        total_commission = sum(lc['commission'] for lc in level_commissions)
        total_transactions = sum(lc['transaction_count'] for lc in level_commissions)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'filter': {
                'from': from_date,
                'to': to_date
            },
            'by_level': level_commissions,
            'total': {
                'commission': total_commission,
                'transactions': total_transactions
            }
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def calculate_level_simple(ancestor_code, descendant_code, connection):
    """
    Simple helper to calculate level between ancestor and descendant
    Returns the level (1-4) or None if not in hierarchy
    """
    try:
        cursor = connection.cursor(dictionary=True)
        
        current = descendant_code
        level = 0
        visited = set()
        
        while current and level <= 4:
            if current in visited:
                return None
            visited.add(current)
            
            if current == ancestor_code:
                cursor.close()
                return level
            
            cursor.execute("SELECT nguoi_gioi_thieu FROM ctv WHERE ma_ctv = %s", (current,))
            result = cursor.fetchone()
            
            if not result or not result.get('nguoi_gioi_thieu'):
                cursor.close()
                return None
            
            current = result['nguoi_gioi_thieu']
            level += 1
        
        cursor.close()
        return None
        
    except Error:
        return None


@ctv_bp.route('/api/ctv/check-phone', methods=['POST'])
@require_ctv
def check_phone():
    """
    CTV can check phone duplicate (same logic as public endpoint but requires auth)
    
    Body: { "phone": "0979832523" }
    """
    data = request.get_json()
    
    if not data or not data.get('phone'):
        return jsonify({'status': 'error', 'message': 'Phone number required'}), 400
    
    phone = data['phone'].strip()
    phone = ''.join(c for c in phone if c.isdigit())
    
    if len(phone) < 9:
        return jsonify({'status': 'error', 'message': 'Invalid phone number'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) > 0 AS is_duplicate
            FROM khach_hang
            WHERE sdt = %s
              AND (
                trang_thai IN ('Da den lam', 'Da coc')
                OR (ngay_hen_lam >= CURDATE() 
                    AND ngay_hen_lam < DATE_ADD(CURDATE(), INTERVAL 180 DAY))
                OR ngay_nhap_don >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
              );
        """, (phone,))
        
        result = cursor.fetchone()
        is_duplicate = bool(result[0]) if result else False
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'is_duplicate': is_duplicate,
            'message': 'Trung' if is_duplicate else 'Khong trung'
        })
        
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# CLIENT SERVICES ENDPOINT (Card View)
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/clients-with-services', methods=['GET'])
@require_ctv
def get_ctv_clients_with_services():
    """
    Get clients with their services grouped - filtered by CTV
    Only shows clients where nguoi_chot = logged-in CTV code
    Groups khach_hang records by phone + name combination
    Returns up to 3 services per client
    
    Query params:
    - search: Search by name or phone
    - limit: Max number of clients (default 50)
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        search = request.args.get('search', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
        # First, get unique clients (grouped by phone + name) for this CTV
        # MIN(ngay_nhap_don) = first time visiting (earliest date they entered the system)
        client_query = """
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(ngay_nhap_don) as first_visit_date,
                nguoi_chot,
                COUNT(*) as service_count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND sdt IS NOT NULL AND sdt != ''
        """
        params = [ctv['ma_ctv']]
        
        if search:
            client_query += " AND (ten_khach LIKE %s OR sdt LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        client_query += f"""
            GROUP BY sdt, ten_khach, nguoi_chot
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
            
            # Get services for this client (only those belonging to this CTV)
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
                WHERE sdt = %s AND ten_khach = %s AND nguoi_chot = %s
                ORDER BY ngay_nhap_don DESC
                LIMIT 3;
            """, (sdt, ten_khach, ctv['ma_ctv']))
            
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

