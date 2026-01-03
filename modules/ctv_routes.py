"""
CTV Routes Module
All API endpoints for the CTV Portal.
Updated for PostgreSQL.

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
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
Updated: January 2, 2026 - Migrated to PostgreSQL
"""

import os
import datetime
from flask import Blueprint, jsonify, request, send_file, g, make_response, render_template
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

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
from .db_pool import get_db_connection, return_db_connection


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/ctv/login', methods=['POST'])
def login():
    """CTV login endpoint"""
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
    
    response = make_response(jsonify({
        'status': 'success',
        'token': result['token'],
        'ctv': result['ctv']
    }))
    response.set_cookie('session_token', result['token'], httponly=True, max_age=86400)
    
    return response


@ctv_bp.route('/ctv/logout', methods=['POST'])
def logout():
    """CTV logout endpoint"""
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
    """Serve CTV portal HTML using Jinja2 template"""
    try:
        return render_template('ctv/base.html')
    except Exception as e:
        template_path = os.path.join(BASE_DIR, 'templates', 'ctv_portal.html')
        if os.path.exists(template_path):
            return send_file(template_path)
        return jsonify({'status': 'error', 'message': f'CTV portal not found: {str(e)}'}), 404


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
    """Change CTV password"""
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
    """Get logged-in CTV profile with network stats"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        stats = get_network_stats(ctv['ma_ctv'], connection)
        
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        if ctv.get('nguoi_gioi_thieu'):
            cursor.execute("""
                SELECT ma_ctv, ten FROM ctv WHERE ma_ctv = %s
            """, (ctv['nguoi_gioi_thieu'],))
            referrer = cursor.fetchone()
            if referrer:
                referrer = dict(referrer)
        else:
            referrer = None
        
        # Get commission rates from config
        cursor.execute("SELECT level, percent FROM hoa_hong_config ORDER BY level")
        rates_rows = cursor.fetchall()
        commission_rates = {row['level']: float(row['percent']) / 100 for row in rates_rows}
        level0_rate = commission_rates.get(0, 0.25)  # Default 25% for self
        
        # Calculate total earnings from khach_hang (all time)
        # Include both Vietnamese and non-Vietnamese status formats
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as total_revenue
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
        """, (ctv['ma_ctv'],))
        kh_revenue = float(cursor.fetchone()['total_revenue'])
        
        # Also check services table for CTVs with services
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as total_revenue
            FROM services
            WHERE ctv_code = %s
        """, (ctv['ma_ctv'],))
        svc_revenue = float(cursor.fetchone()['total_revenue'])
        
        total_revenue = kh_revenue + svc_revenue
        total_earnings = total_revenue * level0_rate
        
        # Date filtering for period stats
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        if from_date and to_date:
            start_date = from_date
            try:
                end_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)
                end_date = end_date_obj.strftime('%Y-%m-%d')
            except ValueError:
                end_date = to_date
        else:
            today = datetime.date.today()
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1)

        # Calculate period earnings from khach_hang
        # Include both Vietnamese and non-Vietnamese status formats
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as period_revenue
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
            AND ngay_hen_lam >= %s
            AND ngay_hen_lam < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        kh_period_revenue = float(cursor.fetchone()['period_revenue'])
        
        # Also check services table for period
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as period_revenue
            FROM services
            WHERE ctv_code = %s
            AND date_entered >= %s
            AND date_entered < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        svc_period_revenue = float(cursor.fetchone()['period_revenue'])
        
        period_revenue = kh_period_revenue + svc_period_revenue
        monthly_earnings = period_revenue * level0_rate
        
        # Count services from khach_hang
        # Include both Vietnamese and non-Vietnamese status formats
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
            AND ngay_hen_lam >= %s
            AND ngay_hen_lam < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        kh_count = int(cursor.fetchone()['count'])
        
        # Count services from services table
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM services
            WHERE ctv_code = %s
            AND date_entered >= %s
            AND date_entered < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        svc_count = int(cursor.fetchone()['count'])
        
        monthly_services_count = kh_count + svc_count
        
        cursor.close()
        return_db_connection(connection)
        
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
                'monthly_earnings': monthly_earnings,
                'monthly_services_count': monthly_services_count
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/my-commissions', methods=['GET'])
@require_ctv
def get_my_commissions():
    """Get own commission earnings with breakdown"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        month = request.args.get('month')
        level = request.args.get('level')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
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
        
        if from_date and to_date:
            query += " AND DATE(c.created_at) >= %s AND DATE(c.created_at) <= %s"
            params.extend([from_date, to_date])
        elif month:
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        
        if level is not None and level != '':
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += " ORDER BY c.created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            c['source_ctv_name'] = c.get('source_ctv_name') or c.get('source_ctv_code') or 'N/A'
            c['source_ctv_code'] = c.get('source_ctv_code') or 'N/A'
            c['customer_name'] = c.get('customer_name') or 'N/A'
            c['service_name'] = c.get('service_name') or 'N/A'
        
        summary_query = """
            SELECT 
                level,
                COUNT(*) as count,
                SUM(commission_amount) as total
            FROM commissions
            WHERE ctv_code = %s
        """
        summary_params = [ctv['ma_ctv']]
        
        if from_date and to_date:
            summary_query += " AND DATE(created_at) >= %s AND DATE(created_at) <= %s"
            summary_params.extend([from_date, to_date])
        elif month:
            summary_query += " AND TO_CHAR(created_at, 'YYYY-MM') = %s"
            summary_params.append(month)
        
        summary_query += " GROUP BY level ORDER BY level"
        
        cursor.execute(summary_query, summary_params)
        summary = [dict(row) for row in cursor.fetchall()]
        
        for s in summary:
            s['total'] = float(s['total'] or 0)
        
        total_commission = sum(s['total'] for s in summary)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'commissions': commissions,
            'summary': {
                'by_level': summary,
                'total': total_commission
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# NETWORK ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/my-downline', methods=['GET'])
@require_ctv
def get_my_downline():
    """Get all CTVs directly under me (Level 1 only)"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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
            ORDER BY created_at DESC
        """, (ctv['ma_ctv'],))
        
        downline = [dict(row) for row in cursor.fetchall()]
        
        for d in downline:
            if d.get('created_at'):
                d['created_at'] = d['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'downline': downline,
            'total': len(downline)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/my-hierarchy', methods=['GET'])
@require_ctv
def get_my_hierarchy():
    """Get my hierarchy tree (all descendants)"""
    ctv = g.current_user
    
    tree = build_hierarchy_tree(ctv['ma_ctv'])
    
    if not tree:
        return jsonify({'status': 'error', 'message': 'Failed to build hierarchy'}), 500
    
    return jsonify({
        'status': 'success',
        'hierarchy': tree
    })


@ctv_bp.route('/api/ctv/my-network/customers', methods=['GET'])
@require_ctv
def get_my_customers():
    """Get all customers in my network"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        
        if not my_network:
            return jsonify({
                'status': 'success',
                'customers': [],
                'total': 0
            })
        
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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
            LIMIT 100
        """, list(my_network))
        
        customers = [dict(row) for row in cursor.fetchall()]
        
        for c in customers:
            if c.get('last_service_date'):
                c['last_service_date'] = c['last_service_date'].strftime('%Y-%m-%d')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'customers': customers,
            'total': len(customers)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/my-stats', methods=['GET'])
@require_ctv
def get_my_stats():
    """Get detailed statistics for my network"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        stats = get_network_stats(ctv['ma_ctv'], connection)
        
        cursor.execute("""
            SELECT 
                level,
                SUM(commission_amount) as total,
                COUNT(*) as count
            FROM commissions
            WHERE ctv_code = %s
            GROUP BY level
            ORDER BY level
        """, (ctv['ma_ctv'],))
        commission_by_level = [dict(row) for row in cursor.fetchall()]
        
        for c in commission_by_level:
            c['total'] = float(c['total'] or 0)
        
        cursor.execute("""
            SELECT 
                TO_CHAR(created_at, 'YYYY-MM') as month,
                SUM(commission_amount) as total
            FROM commissions
            WHERE ctv_code = %s
            AND created_at >= CURRENT_TIMESTAMP - INTERVAL '6 months'
            GROUP BY TO_CHAR(created_at, 'YYYY-MM')
            ORDER BY month
        """, (ctv['ma_ctv'],))
        monthly_trend = [dict(row) for row in cursor.fetchall()]
        
        for m in monthly_trend:
            m['total'] = float(m['total'] or 0)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'stats': {
                'network': stats,
                'commission_by_level': commission_by_level,
                'monthly_trend': monthly_trend
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# KHACH HANG (CUSTOMER) ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/lifetime-stats', methods=['GET'])
@require_ctv
def get_lifetime_stats():
    """Get lifetime statistics for the CTV - all-time cumulative data"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get commission rate for Level 0 (self)
        cursor.execute("SELECT percent FROM hoa_hong_config WHERE level = 0")
        rate_row = cursor.fetchone()
        level0_rate = float(rate_row['percent']) / 100 if rate_row else 0.25
        
        # Total commissions earned (all time) - calculated from khach_hang
        # Include both Vietnamese and non-Vietnamese status formats
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as total_revenue,
                   COUNT(*) as total_transactions
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
        """, (ctv['ma_ctv'],))
        commission_stats = cursor.fetchone()
        
        # Also check services table
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as total_revenue,
                   COUNT(*) as total_transactions
            FROM services
            WHERE ctv_code = %s
        """, (ctv['ma_ctv'],))
        svc_stats = cursor.fetchone()
        
        total_revenue = float(commission_stats['total_revenue'] or 0) + float(svc_stats['total_revenue'] or 0)
        total_transactions = int(commission_stats['total_transactions'] or 0) + int(svc_stats['total_transactions'] or 0)
        total_commissions = total_revenue * level0_rate
        
        # Network size (all descendants)
        from .mlm_core import get_all_descendants
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        network_size = len(my_network) if my_network else 0
        
        # Direct referrals (Level 1)
        cursor.execute("""
            SELECT COUNT(*) as direct_count
            FROM ctv
            WHERE nguoi_gioi_thieu = %s AND (is_active = TRUE OR is_active IS NULL)
        """, (ctv['ma_ctv'],))
        direct_result = cursor.fetchone()
        direct_referrals = int(direct_result['direct_count']) if direct_result else 0
        
        # Total services completed (all time)
        # Include both Vietnamese and non-Vietnamese status formats
        cursor.execute("""
            SELECT COUNT(*) as total_services,
                   COALESCE(SUM(tong_tien), 0) as total_revenue
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
        """, (ctv['ma_ctv'],))
        kh_service_stats = cursor.fetchone()
        
        # Also check services table
        cursor.execute("""
            SELECT COUNT(*) as total_services,
                   COALESCE(SUM(tong_tien), 0) as total_revenue
            FROM services
            WHERE ctv_code = %s
        """, (ctv['ma_ctv'],))
        svc_service_stats = cursor.fetchone()
        
        total_services = int(kh_service_stats['total_services'] or 0) + int(svc_service_stats['total_services'] or 0)
        service_revenue = float(kh_service_stats['total_revenue'] or 0) + float(svc_service_stats['total_revenue'] or 0)
        
        service_stats = {
            'total_services': total_services,
            'total_revenue': service_revenue
        }
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_commissions': total_commissions,
                'total_transactions': total_transactions,
                'network_size': network_size,
                'direct_referrals': direct_referrals,
                'total_services': int(service_stats['total_services'] or 0),
                'total_revenue': service_revenue
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/customers', methods=['GET'])
@require_ctv
def get_ctv_customers():
    """Get all customers where nguoi_chot = logged-in CTV"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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
        
        status = request.args.get('status')
        if status:
            query += " AND trang_thai = %s"
            params.append(status)
        
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        if from_date:
            query += " AND ngay_hen_lam >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND ngay_hen_lam <= %s"
            params.append(to_date)
        
        query += " ORDER BY ngay_hen_lam DESC, id DESC LIMIT 100"
        
        cursor.execute(query, params)
        customers = [dict(row) for row in cursor.fetchall()]
        
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
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN trang_thai IN ('Da den lam', 'Da coc') THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN trang_thai IN ('Da den lam', 'Da coc') THEN tong_tien ELSE 0 END) as total_revenue,
                SUM(CASE WHEN trang_thai IN ('Da coc') THEN 1 ELSE 0 END) as pending_count
            FROM khach_hang
            WHERE nguoi_chot = %s
        """, (ctv['ma_ctv'],))
        
        summary = cursor.fetchone()
        
        cursor.close()
        return_db_connection(connection)
        
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
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/earliest-date', methods=['GET'])
@require_ctv
def get_ctv_earliest_date():
    """Get the earliest customer date for the CTV and their network"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        
        if not my_network:
            my_network = [ctv['ma_ctv']]
        
        placeholders = ','.join(['%s'] * len(my_network))
        query = f"""
            SELECT MIN(ngay_hen_lam) as earliest_date
            FROM khach_hang
            WHERE nguoi_chot IN ({placeholders})
            AND ngay_hen_lam IS NOT NULL
        """
        
        cursor.execute(query, list(my_network))
        result = cursor.fetchone()
        
        earliest_date = None
        if result and result['earliest_date']:
            earliest_date = result['earliest_date'].strftime('%Y-%m-%d')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'earliest_date': earliest_date
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@ctv_bp.route('/api/ctv/commission', methods=['GET'])
@require_ctv
def get_ctv_commission():
    """Get commission based on khach_hang table with date filter on ngay_hen_lam"""
    ctv = g.current_user

    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Support both old from/to and new month/day parameters
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        month = request.args.get('month')
        day = request.args.get('day')

        # If month/day provided, convert to from/to dates
        if month and not from_date and not to_date:
            if day:
                # Specific day
                from_date = day
                to_date = day
            else:
                # Month range
                try:
                    year, month_num = map(int, month.split('-'))
                    from_date = f"{year}-{month_num:02d}-01"
                    if month_num == 12:
                        to_date = f"{year+1}-01-01"
                    else:
                        to_date = f"{year}-{month_num+1:02d}-01"
                except ValueError:
                    return jsonify({'status': 'error', 'message': 'Invalid month format'}), 400
        
        cursor.execute("SELECT level, percent FROM hoa_hong_config ORDER BY level")
        rates_rows = cursor.fetchall()
        commission_rates = {row['level']: float(row['percent']) / 100 for row in rates_rows}
        
        level0_query = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc')
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
        
        if my_network_excluding_self:
            for level in range(1, 5):
                level_ctv_list = []
                
                for descendant_code in my_network_excluding_self:
                    desc_level = calculate_level_simple(ctv['ma_ctv'], descendant_code, connection)
                    if desc_level == level:
                        level_ctv_list.append(descendant_code)
                
                if level_ctv_list:
                    placeholders = ','.join(['%s'] * len(level_ctv_list))
                    level_query = f"""
                        SELECT 
                            SUM(tong_tien) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM khach_hang
                        WHERE nguoi_chot IN ({placeholders})
                        AND trang_thai IN ('Da den lam', 'Da coc')
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
        
        total_commission = sum(lc['commission'] for lc in level_commissions)
        total_transactions = sum(lc['transaction_count'] for lc in level_commissions)
        
        cursor.close()
        return_db_connection(connection)
        
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
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


def calculate_level_simple(ancestor_code, descendant_code, connection):
    """Simple helper to calculate level between ancestor and descendant"""
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        current = descendant_code
        level = 0
        visited = set()
        
        while current and level <= 4:
            if current in visited:
                cursor.close()
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
    """CTV can check phone duplicate"""
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
            SELECT EXISTS(
                SELECT 1 FROM khach_hang
                WHERE sdt = %s
                  AND (
                    trang_thai IN ('Da den lam', 'Da coc')
                    OR (ngay_hen_lam >= CURRENT_DATE 
                        AND ngay_hen_lam < CURRENT_DATE + INTERVAL '180 days')
                    OR ngay_nhap_don >= CURRENT_DATE - INTERVAL '60 days'
                  )
            ) AS is_duplicate
        """, (phone,))
        
        result = cursor.fetchone()
        is_duplicate = result[0] if result else False
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'is_duplicate': is_duplicate,
            'message': 'Trung' if is_duplicate else 'Khong trung'
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# CLIENT SERVICES ENDPOINT (Card View)
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/api/ctv/clients-with-services', methods=['GET'])
@require_ctv
def get_ctv_clients_with_services():
    """Get clients with their services grouped - filtered by CTV"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
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
            client_query += " AND (ten_khach ILIKE %s OR sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        client_query += f"""
            GROUP BY sdt, ten_khach, nguoi_chot
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(client_query, params)
        clients_raw = [dict(row) for row in cursor.fetchall()]
        
        clients = []
        for client_row in clients_raw:
            sdt = client_row['sdt']
            ten_khach = client_row['ten_khach']
            
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
                LIMIT 3
            """, (sdt, ten_khach, ctv['ma_ctv']))
            
            services_raw = [dict(row) for row in cursor.fetchall()]
            
            services = []
            for idx, svc in enumerate(services_raw):
                tien_coc = float(svc['tien_coc'] or 0)
                tong_tien = float(svc['tong_tien'] or 0)
                phai_dong = float(svc['phai_dong'] or 0)
                
                deposit_status = 'Da coc' if tien_coc > 0 else 'Chua coc'
                
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
            
            overall_status = services[0]['trang_thai'] if services else ''
            overall_deposit = services[0]['deposit_status'] if services else 'Chua coc'
            
            first_visit = client_row['first_visit_date']
            first_visit_str = first_visit.strftime('%d/%m/%Y') if first_visit else None
            
            referrer_ctv_code = None
            client_level = None
            
            if client_row['nguoi_chot']:
                cursor.execute("""
                    SELECT nguoi_gioi_thieu, cap_bac FROM ctv WHERE ma_ctv = %s
                """, (client_row['nguoi_chot'],))
                ctv_info = cursor.fetchone()
                if ctv_info:
                    referrer_ctv_code = ctv_info.get('nguoi_gioi_thieu')
                    client_level = ctv_info.get('cap_bac') or 'Cong tac vien'
            
            email = ''
            try:
                cursor.execute("""
                    SELECT email FROM customers WHERE phone = %s LIMIT 1
                """, (sdt,))
                email_row = cursor.fetchone()
                if email_row and email_row.get('email'):
                    email = email_row['email']
            except Error:
                pass
            
            clients.append({
                'ten_khach': ten_khach or '',
                'sdt': sdt or '',
                'email': email,
                'co_so': client_row['co_so'] or '',
                'first_visit_date': first_visit_str,
                'nguoi_chot': client_row['nguoi_chot'] or '',
                'referrer_ctv_code': referrer_ctv_code or '',
                'level': client_level or 'Cong tac vien',
                'service_count': client_row['service_count'],
                'overall_status': overall_status,
                'overall_deposit': overall_deposit,
                'services': services
            })
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'clients': clients,
            'total': len(clients)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500
