"""
TEMPORARY DEBUG MODULE - DELETE WHEN DONE
Commission verification debug page with bidirectional sync
"""
from flask import jsonify, render_template
from psycopg2.extras import RealDictCursor
from .blueprint import admin_bp
from ..db_pool import get_db_connection, return_db_connection
from ..auth import require_admin


@admin_bp.route('/admin/debug/commission-verify')
@require_admin
def debug_commission_page():
    """Serve the commission verification debug page"""
    return render_template('admin/pages/debug-commission.html')


@admin_bp.route('/api/admin/debug/hierarchy-full')
@require_admin
def get_full_hierarchy():
    """Get complete CTV hierarchy tree with all data"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all CTVs with their data
        cursor.execute("""
            SELECT 
                c.ma_ctv,
                c.ten,
                c.sdt,
                c.nguoi_gioi_thieu,
                c.cap_bac,
                COALESCE(client_stats.client_count, 0) as client_count,
                COALESCE(client_stats.total_revenue, 0) as total_revenue,
                COALESCE(comm_stats.total_commission, 0) as total_commission
            FROM ctv c
            LEFT JOIN (
                SELECT 
                    nguoi_chot,
                    COUNT(*) as client_count,
                    SUM(tong_tien) as total_revenue
                FROM khach_hang
                WHERE nguoi_chot IS NOT NULL
                GROUP BY nguoi_chot
            ) client_stats ON client_stats.nguoi_chot = c.ma_ctv
            LEFT JOIN (
                SELECT 
                    ctv_code,
                    SUM(commission_amount) as total_commission
                FROM commissions
                WHERE level = 0
                GROUP BY ctv_code
            ) comm_stats ON comm_stats.ctv_code = c.ma_ctv
            ORDER BY c.ma_ctv
        """)
        all_ctvs = cursor.fetchall()
        
        # Get commission rates
        cursor.execute("SELECT level, rate FROM commission_settings ORDER BY level")
        rates = {row['level']: float(row['rate']) for row in cursor.fetchall()}
        
        # Build tree structure
        nodes_by_code = {}
        roots = []
        
        for ctv in all_ctvs:
            node = {
                'ma_ctv': ctv['ma_ctv'],
                'ten': ctv['ten'],
                'sdt': ctv['sdt'],
                'cap_bac': ctv['cap_bac'],
                'nguoi_gioi_thieu': ctv['nguoi_gioi_thieu'],
                'client_count': ctv['client_count'],
                'total_revenue': float(ctv['total_revenue'] or 0),
                'total_commission': float(ctv['total_commission'] or 0),
                'commission_rate': rates.get(0, 0.25),
                'children': []
            }
            nodes_by_code[ctv['ma_ctv']] = node
        
        # Build parent-child relationships
        for ctv in all_ctvs:
            parent_code = ctv['nguoi_gioi_thieu']
            if parent_code and parent_code in nodes_by_code:
                nodes_by_code[parent_code]['children'].append(nodes_by_code[ctv['ma_ctv']])
            else:
                roots.append(nodes_by_code[ctv['ma_ctv']])
        
        cursor.close()
        return_db_connection(conn)
        
        return jsonify({
            'hierarchy': roots,
            'rates': rates,
            'total_ctvs': len(all_ctvs)
        })
        
    except Exception as e:
        if conn:
            return_db_connection(conn)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/debug/ctv-detail/<ctv_code>')
@require_admin
def get_ctv_detail(ctv_code):
    """Get detailed report for a specific CTV"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get CTV info
        cursor.execute("SELECT * FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        ctv = cursor.fetchone()
        if not ctv:
            cursor.close()
            return_db_connection(conn)
            return jsonify({'error': 'CTV not found'}), 404
        
        # Get clients for this CTV
        cursor.execute("""
            SELECT 
                id, ten_khach as ho_ten, sdt, tong_tien, ngay_hen_lam,
                dich_vu, nguoi_chot
            FROM khach_hang
            WHERE nguoi_chot = %s
            ORDER BY ngay_hen_lam DESC
        """, (ctv_code,))
        clients = cursor.fetchall()
        
        # Get commissions earned by this CTV
        cursor.execute("""
            SELECT 
                c.id, c.transaction_id, c.level, c.commission_amount,
                c.created_at as calculated_at,
                CASE 
                    WHEN c.transaction_id < 0 THEN kh.ten_khach
                    ELSE 'Service'
                END as source_name,
                CASE 
                    WHEN c.transaction_id < 0 THEN kh.tong_tien
                    ELSE s.tong_tien
                END as source_amount
            FROM commissions c
            LEFT JOIN khach_hang kh ON c.transaction_id = -kh.id
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            WHERE c.ctv_code = %s
            ORDER BY c.level, c.created_at DESC
        """, (ctv_code,))
        commissions = cursor.fetchall()
        
        # Get downline CTVs
        cursor.execute("""
            WITH RECURSIVE downline AS (
                SELECT ma_ctv, ten, nguoi_gioi_thieu, 1 as level
                FROM ctv WHERE nguoi_gioi_thieu = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, c.ten, c.nguoi_gioi_thieu, d.level + 1
                FROM ctv c
                JOIN downline d ON c.nguoi_gioi_thieu = d.ma_ctv
                WHERE d.level < 4
            )
            SELECT * FROM downline ORDER BY level, ma_ctv
        """, (ctv_code,))
        downline = cursor.fetchall()
        
        # Calculate totals
        total_revenue = sum(float(c['tong_tien'] or 0) for c in clients)
        total_commission = sum(float(c['commission_amount'] or 0) for c in commissions)
        
        cursor.close()
        return_db_connection(conn)
        
        # Convert dates to strings
        for c in clients:
            if c.get('ngay_hen_lam'):
                c['ngay_hen_lam'] = str(c['ngay_hen_lam'])
        for c in commissions:
            if c.get('calculated_at'):
                c['calculated_at'] = str(c['calculated_at'])
        
        return jsonify({
            'ctv': dict(ctv),
            'clients': [dict(c) for c in clients],
            'commissions': [dict(c) for c in commissions],
            'downline': [dict(d) for d in downline],
            'summary': {
                'total_clients': len(clients),
                'total_revenue': total_revenue,
                'total_commission': total_commission,
                'downline_count': len(downline)
            }
        })
        
    except Exception as e:
        if conn:
            return_db_connection(conn)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/debug/raw-data')
# @require_admin  # TEMPORARY: Removed for debugging
def get_raw_data():
    """Get raw database dump grouped by CTV for easy comparison"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all clients grouped by CTV, with their services
        cursor.execute("""
            SELECT 
                kh.id,
                kh.ten_khach as ho_ten,
                kh.sdt,
                kh.tong_tien,
                kh.ngay_hen_lam,
                kh.dich_vu,
                kh.nguoi_chot,
                ctv.ten as ctv_name
            FROM khach_hang kh
            LEFT JOIN ctv ON ctv.ma_ctv = kh.nguoi_chot
            ORDER BY kh.nguoi_chot, kh.ten_khach, kh.id
        """)
        clients = cursor.fetchall()
        
        # Get all commissions
        cursor.execute("""
            SELECT 
                c.id,
                c.ctv_code,
                c.transaction_id,
                c.level,
                c.commission_amount,
                c.created_at as calculated_at,
                ctv.ten as ctv_name,
                CASE 
                    WHEN c.transaction_id < 0 THEN kh.ten_khach
                    ELSE 'Service #' || c.transaction_id
                END as source_name,
                CASE 
                    WHEN c.transaction_id < 0 THEN kh.tong_tien
                    ELSE s.tong_tien
                END as source_amount,
                CASE 
                    WHEN c.transaction_id < 0 THEN kh.nguoi_chot
                    ELSE s.nguoi_chot
                END as closer_ctv
            FROM commissions c
            LEFT JOIN ctv ON ctv.ma_ctv = c.ctv_code
            LEFT JOIN khach_hang kh ON c.transaction_id = -kh.id
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            ORDER BY c.ctv_code, c.level, c.id
        """)
        commissions = cursor.fetchall()
        
        # Get commission rates
        cursor.execute("SELECT level, rate, description FROM commission_settings ORDER BY level")
        rates = cursor.fetchall()
        
        # Get all CTVs for reference
        cursor.execute("""
            SELECT ma_ctv, ten, sdt, nguoi_gioi_thieu, cap_bac
            FROM ctv ORDER BY ma_ctv
        """)
        ctvs = cursor.fetchall()
        
        cursor.close()
        return_db_connection(conn)
        
        # Convert dates to strings
        for c in clients:
            if c.get('ngay_hen_lam'):
                c['ngay_hen_lam'] = str(c['ngay_hen_lam'])
        for c in commissions:
            if c.get('calculated_at'):
                c['calculated_at'] = str(c['calculated_at'])
        
        return jsonify({
            'clients': [dict(c) for c in clients],
            'commissions': [dict(c) for c in commissions],
            'rates': [dict(r) for r in rates],
            'ctvs': [dict(c) for c in ctvs],
            'counts': {
                'clients': len(clients),
                'commissions': len(commissions),
                'ctvs': len(ctvs)
            }
        })
        
    except Exception as e:
        if conn:
            return_db_connection(conn)
        return jsonify({'error': str(e)}), 500

