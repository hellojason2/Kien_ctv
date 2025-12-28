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
    get_current_user
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
        print(f"CTV Routes - Error connecting to MySQL: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@ctv_bp.route('/ctv/login', methods=['POST'])
def login():
    """
    CTV login endpoint
    Body: {"email": "kien@example.com", "password": "ctv123"}
    Returns: {"token": "...", "ctv": {...}}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
    
    result = ctv_login(email, password)
    
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
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        month = request.args.get('month')
        level = request.args.get('level')
        
        # Build query
        query = """
            SELECT 
                c.id,
                c.transaction_id,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at
            FROM commissions c
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

