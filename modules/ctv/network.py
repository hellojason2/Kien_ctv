from flask import jsonify, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..auth import require_ctv
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import build_hierarchy_tree, get_all_descendants, get_network_stats

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

