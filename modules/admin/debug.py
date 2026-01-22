"""
TEMPORARY DEBUG MODULE - DELETE WHEN DONE
Commission verification debug page with bidirectional sync
"""
from flask import jsonify, render_template, request
from psycopg2.extras import RealDictCursor
from .blueprint import admin_bp
from ..db_pool import get_db_connection, return_db_connection
from ..auth import require_admin


@admin_bp.route('/admin/debug/commission-verify')
# @require_admin  # TEMPORARY: Removed for debugging
def debug_commission_page():
    """Serve the commission verification debug page"""
    return render_template('admin/pages/debug-commission.html')


@admin_bp.route('/api/admin/debug/hierarchy-full')
# @require_admin  # TEMPORARY: Removed for debugging
def get_full_hierarchy():
    """Get complete CTV hierarchy tree with all data"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all CTVs with their data (from both khach_hang and services)
        cursor.execute("""
            SELECT 
                c.ma_ctv,
                c.ten,
                c.sdt,
                c.nguoi_gioi_thieu,
                c.cap_bac,
                COALESCE(kh_stats.client_count, 0) + COALESCE(svc_stats.client_count, 0) as client_count,
                COALESCE(kh_stats.total_revenue, 0) + COALESCE(svc_stats.total_revenue, 0) as total_revenue,
                COALESCE(comm_stats.total_commission, 0) as total_commission
            FROM ctv c
            LEFT JOIN (
                SELECT
                    nguoi_chot,
                    COUNT(*) as client_count,
                    SUM(tong_tien) as total_revenue
                FROM khach_hang
                WHERE nguoi_chot IS NOT NULL
                AND (trang_thai = 'Đã đến làm' OR trang_thai = 'Da den lam')
                GROUP BY nguoi_chot
            ) kh_stats ON kh_stats.nguoi_chot = c.ma_ctv
            LEFT JOIN (
                SELECT
                    COALESCE(nguoi_chot, ctv_code) as closer,
                    COUNT(*) as client_count,
                    SUM(tong_tien) as total_revenue
                FROM services
                WHERE COALESCE(nguoi_chot, ctv_code) IS NOT NULL
                GROUP BY COALESCE(nguoi_chot, ctv_code)
            ) svc_stats ON svc_stats.closer = c.ma_ctv
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
# @require_admin  # TEMPORARY: Removed for debugging
def get_ctv_detail(ctv_code):
    """Get detailed report for a specific CTV AND their entire downline hierarchy"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
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
        
        # Get the entire downline hierarchy (including the selected CTV at level 0)
        cursor.execute("""
            WITH RECURSIVE network AS (
                SELECT ma_ctv, ten, nguoi_gioi_thieu, 0 as level
                FROM ctv WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, c.ten, c.nguoi_gioi_thieu, n.level + 1
                FROM ctv c
                JOIN network n ON c.nguoi_gioi_thieu = n.ma_ctv
                WHERE n.level < 4
            )
            SELECT * FROM network ORDER BY level, ma_ctv
        """, (ctv_code,))
        network_ctvs = cursor.fetchall()
        
        # Get list of all CTV codes in the network
        network_codes = [n['ma_ctv'] for n in network_ctvs]
        
        if not network_codes:
            network_codes = [ctv_code]
        
        placeholders = ','.join(['%s'] * len(network_codes))
        
        # Build date filter clauses
        date_filter_kh = ""
        date_filter_svc = ""
        date_params = []
        
        if start_date:
            date_filter_kh = " AND kh.ngay_hen_lam >= %s"
            date_filter_svc = " AND s.date_entered >= %s"
            date_params.append(start_date)
            
        if end_date:
            date_filter_kh += " AND kh.ngay_hen_lam <= %s"
            date_filter_svc += " AND s.date_entered <= %s"
            date_params.append(end_date)
        
        # Get ALL service transactions for the ENTIRE network (UNION of khach_hang and services)
        query = f"""
            SELECT
                id,
                ho_ten,
                sdt,
                tong_tien,
                transaction_date,
                dich_vu,
                nguoi_chot,
                closer_name,
                closer_level,
                source_type
            FROM (
                SELECT
                    kh.id,
                    kh.ten_khach as ho_ten,
                    kh.sdt,
                    kh.tong_tien,
                    kh.ngay_hen_lam as transaction_date,
                    kh.dich_vu,
                    kh.nguoi_chot,
                    ctv.ten as closer_name,
                    network.level as closer_level,
                    'tham_my' as source_type
                FROM khach_hang kh
                JOIN (
                    WITH RECURSIVE net AS (
                        SELECT ma_ctv, 0 as level FROM ctv WHERE ma_ctv = %s
                        UNION ALL
                        SELECT c.ma_ctv, n.level + 1 FROM ctv c JOIN net n ON c.nguoi_gioi_thieu = n.ma_ctv WHERE n.level < 4
                    )
                    SELECT * FROM net
                ) network ON (
                    kh.nguoi_chot = network.ma_ctv
                    OR RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(network.ma_ctv, '[^0-9]', '', 'g'), 9)
                )
                LEFT JOIN ctv ON (
                    ctv.ma_ctv = kh.nguoi_chot
                    OR RIGHT(REGEXP_REPLACE(ctv.ma_ctv, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9)
                )
                WHERE (kh.trang_thai = 'Đã đến làm' OR kh.trang_thai = 'Da den lam')
                {date_filter_kh}
                
                UNION ALL
                
                SELECT
                    s.id,
                    c.name as ho_ten,
                    c.phone as sdt,
                    s.tong_tien,
                    s.date_entered as transaction_date,
                    s.service_name as dich_vu,
                    COALESCE(s.nguoi_chot, s.ctv_code) as nguoi_chot,
                    ctv.ten as closer_name,
                    network.level as closer_level,
                    'nha_khoa' as source_type
                FROM services s
                LEFT JOIN customers c ON s.customer_id = c.id
                JOIN (
                    WITH RECURSIVE net AS (
                        SELECT ma_ctv, 0 as level FROM ctv WHERE ma_ctv = %s
                        UNION ALL
                        SELECT c.ma_ctv, n.level + 1 FROM ctv c JOIN net n ON c.nguoi_gioi_thieu = n.ma_ctv WHERE n.level < 4
                    )
                    SELECT * FROM net
                ) network ON (
                    COALESCE(s.nguoi_chot, s.ctv_code) = network.ma_ctv
                    OR RIGHT(REGEXP_REPLACE(COALESCE(s.nguoi_chot, s.ctv_code), '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(network.ma_ctv, '[^0-9]', '', 'g'), 9)
                )
                LEFT JOIN ctv ON (
                    ctv.ma_ctv = COALESCE(s.nguoi_chot, s.ctv_code)
                    OR RIGHT(REGEXP_REPLACE(ctv.ma_ctv, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(COALESCE(s.nguoi_chot, s.ctv_code), '[^0-9]', '', 'g'), 9)
                )
                WHERE 1=1
                {date_filter_svc}
            ) AS all_transactions
            ORDER BY closer_level, nguoi_chot, transaction_date DESC
        """
        
        # Build params: ctv_code for first CTE, date params, ctv_code for second CTE, date params
        query_params = [ctv_code] + date_params + [ctv_code] + date_params
        
        cursor.execute(query, tuple(query_params))
        all_transactions = cursor.fetchall()
        
        # Group transactions by closer for the breakdown
        transactions_by_closer = {}
        for t in all_transactions:
            closer = t['nguoi_chot']
            if closer not in transactions_by_closer:
                transactions_by_closer[closer] = {
                    'closer_code': closer,
                    'closer_name': t['closer_name'],
                    'closer_level': t['closer_level'],
                    'transactions': [],
                    'total_revenue': 0,
                    'count': 0
                }
            transactions_by_closer[closer]['transactions'].append(dict(t))
            transactions_by_closer[closer]['total_revenue'] += float(t['tong_tien'] or 0)
            transactions_by_closer[closer]['count'] += 1
        
        # Convert to list sorted by level
        breakdown = sorted(transactions_by_closer.values(), key=lambda x: (x['closer_level'], x['closer_code']))
        
        # Get commissions earned by this CTV
        date_filter_comm = ""
        params_comm = [ctv_code]
        if start_date:
            date_filter_comm += " AND (CASE WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam ELSE s.date_entered END) >= %s"
            params_comm.append(start_date)
        if end_date:
            date_filter_comm += " AND (CASE WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam ELSE s.date_entered END) <= %s"
            params_comm.append(end_date)
            
        cursor.execute(f"""
            SELECT
                c.id, c.transaction_id, c.level, c.commission_amount,
                c.created_at as calculated_at,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.ten_khach
                    ELSE cust.name
                END as source_name,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.sdt
                    ELSE cust.phone
                END as source_phone,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.dich_vu
                    ELSE s.service_name
                END as source_service,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.tong_tien
                    ELSE s.tong_tien
                END as source_amount,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.nguoi_chot
                    ELSE s.nguoi_chot
                END as closer_code,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam
                    ELSE s.date_entered
                END as transaction_date
            FROM commissions c
            LEFT JOIN khach_hang kh ON c.transaction_id = -kh.id
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            LEFT JOIN customers cust ON s.customer_id = cust.id
            WHERE c.ctv_code = %s
            {date_filter_comm}
            ORDER BY c.level, c.created_at DESC
        """, tuple(params_comm))
        commissions = cursor.fetchall()
        
        # Calculate totals
        total_revenue = sum(float(t['tong_tien'] or 0) for t in all_transactions)
        total_transactions = len(all_transactions)
        total_commission = sum(float(c['commission_amount'] or 0) for c in commissions)
        
        # Personal transactions (level 0 - the selected CTV's own closes)
        personal_transactions = [t for t in all_transactions if t['nguoi_chot'] == ctv_code]
        personal_revenue = sum(float(t['tong_tien'] or 0) for t in personal_transactions)
        
        # Network transactions (levels 1-4)
        network_transactions = [t for t in all_transactions if t['nguoi_chot'] != ctv_code]
        network_revenue = sum(float(t['tong_tien'] or 0) for t in network_transactions)
        
        cursor.close()
        return_db_connection(conn)
        
        # Convert dates to strings
        for t in all_transactions:
            if t.get('transaction_date'):
                t['transaction_date'] = str(t['transaction_date'])
            t['ngay_hen_lam'] = t.get('transaction_date')
        
        for b in breakdown:
            for t in b['transactions']:
                if t.get('transaction_date'):
                    t['transaction_date'] = str(t['transaction_date'])
                t['ngay_hen_lam'] = t.get('transaction_date')
        
        for c in commissions:
            if c.get('calculated_at'):
                c['calculated_at'] = str(c['calculated_at'])
        
        return jsonify({
            'ctv': dict(ctv),
            'clients': [dict(t) for t in all_transactions],
            'breakdown': breakdown,
            'commissions': [dict(c) for c in commissions],
            'downline': [dict(n) for n in network_ctvs if n['ma_ctv'] != ctv_code],
            'summary': {
                'total_transactions': total_transactions,
                'total_revenue': total_revenue,
                'personal_revenue': personal_revenue,
                'network_revenue': network_revenue,
                'total_commission': total_commission,
                'network_size': len(network_ctvs) - 1,
                'total_clients': total_transactions
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
            LEFT JOIN ctv ON (
                ctv.ma_ctv = kh.nguoi_chot
                OR RIGHT(REGEXP_REPLACE(ctv.ma_ctv, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9)
            )
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

