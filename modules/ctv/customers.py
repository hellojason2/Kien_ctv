import datetime
from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..auth import require_ctv
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import get_all_descendants, calculate_new_commissions_fast

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
        
        # Calculate lifetime stats by summing all commissions from network
        # This mirrors the logic in get_ctv_commission but without date filters
        
        cursor.execute("SELECT level, percent FROM hoa_hong_config ORDER BY level")
        rates_rows = cursor.fetchall()
        commission_rates = {row['level']: float(row['percent']) / 100 for row in rates_rows}
        
        # Level 0 (Personal Sales)
        level0_query_kh = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Đã đến làm')
        """
        cursor.execute(level0_query_kh, (ctv['ma_ctv'],))
        level0_kh = cursor.fetchone()
        
        level0_query_svc = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM services
            WHERE COALESCE(nguoi_chot, ctv_code) = %s
        """
        cursor.execute(level0_query_svc, (ctv['ma_ctv'],))
        level0_svc = cursor.fetchone()
        
        level0_revenue = float(level0_kh['total_revenue'] or 0) + float(level0_svc['total_revenue'] or 0)
        level0_count = int(level0_kh['transaction_count'] or 0) + int(level0_svc['transaction_count'] or 0)
        level0_commission = level0_revenue * commission_rates.get(0, 0.25)
        level0_rate = commission_rates.get(0, 0.25)
        
        total_commissions = level0_commission
        total_revenue = level0_revenue
        total_transactions = level0_count
        
        # Network Stats
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        network_size = len(my_network) if my_network else 0
        
        cursor.execute("""
            SELECT COUNT(*) as direct_count
            FROM ctv
            WHERE nguoi_gioi_thieu = %s AND (is_active = TRUE OR is_active IS NULL)
        """, (ctv['ma_ctv'],))
        direct_result = cursor.fetchone()
        direct_referrals = int(direct_result['direct_count']) if direct_result else 0
        
        # Calculate Downline Commissions
        my_network_excluding_self = [c for c in my_network if c != ctv['ma_ctv']]
        
        if my_network_excluding_self:
            # OPTIMIZED: Get descendants with levels in ONE query
            cursor.execute("""
                WITH RECURSIVE network AS (
                    SELECT ma_ctv, 0 as level 
                    FROM ctv 
                    WHERE ma_ctv = %s
                    
                    UNION ALL
                    
                    SELECT c.ma_ctv, n.level + 1
                    FROM ctv c
                    JOIN network n ON c.nguoi_gioi_thieu = n.ma_ctv
                    WHERE n.level < 4
                )
                SELECT ma_ctv, level FROM network WHERE level > 0
            """, (ctv['ma_ctv'],))
            
            network_with_levels = cursor.fetchall()
            
            ctvs_by_level = {1: [], 2: [], 3: [], 4: []}
            for row in network_with_levels:
                lvl = row['level']
                if lvl in ctvs_by_level:
                    ctvs_by_level[lvl].append(row['ma_ctv'])
            
            for level in range(1, 5):
                level_ctv_list = ctvs_by_level.get(level, [])
                
                if level_ctv_list:
                    placeholders = ','.join(['%s'] * len(level_ctv_list))
                    
                    level_query_kh = f"""
                        SELECT 
                            COALESCE(SUM(tong_tien), 0) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM khach_hang
                        WHERE nguoi_chot IN ({placeholders})
                        AND trang_thai IN ('Da den lam', 'Đã đến làm')
                    """
                    cursor.execute(level_query_kh, list(level_ctv_list))
                    level_data_kh = cursor.fetchone()
                    
                    level_query_svc = f"""
                        SELECT 
                            COALESCE(SUM(tong_tien), 0) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM services
                        WHERE COALESCE(nguoi_chot, ctv_code) IN ({placeholders})
                    """
                    cursor.execute(level_query_svc, list(level_ctv_list))
                    level_data_svc = cursor.fetchone()
                    
                    level_revenue = float(level_data_kh['total_revenue'] or 0) + float(level_data_svc['total_revenue'] or 0)
                    level_count = int(level_data_kh['transaction_count'] or 0) + int(level_data_svc['transaction_count'] or 0)
                    level_commission = level_revenue * commission_rates.get(level, 0)
                    
                    total_commissions += level_commission
                    total_revenue += level_revenue
                    total_transactions += level_count
        
        # Get total services count (completed) - same as total_transactions in this context
        total_services = total_transactions
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_commissions': total_commissions,
                'total_revenue': total_revenue,
                'total_transactions': total_transactions,
                'network_size': network_size,
                'direct_referrals': direct_referrals,
                'total_services': total_services,
                'level0_rate': level0_rate * 100,  # Return percentage
                'level0': {
                    'commission': level0_commission,
                    'revenue': level0_revenue,
                    'transactions': level0_count
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500


@ctv_bp.route('/api/ctv/customers', methods=['GET'])
@require_ctv
def get_ctv_customers():
    """Get all service transactions where CTV is the closer (from both khach_hang and services)"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        status = request.args.get('status')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        # Build date filters
        date_filter_kh = ""
        date_filter_svc = ""
        params_kh = [ctv['ma_ctv'], ctv['ma_ctv']]
        params_svc = [ctv['ma_ctv']]
        
        if status:
            date_filter_kh += " AND kh.trang_thai = %s"
            params_kh.append(status)
            # services table might not have the same status values
        
        if from_date:
            date_filter_kh += " AND kh.ngay_hen_lam >= %s"
            date_filter_svc += " AND s.date_entered >= %s"
            params_kh.append(from_date)
            params_svc.append(from_date)
        
        if to_date:
            date_filter_kh += " AND kh.ngay_hen_lam <= %s"
            date_filter_svc += " AND s.date_entered <= %s"
            params_kh.append(to_date)
            params_svc.append(to_date)
        
        # UNION query combining both tables
        query = f"""
            SELECT * FROM (
                SELECT 
                    kh.id,
                    kh.ngay_nhap_don,
                    kh.ten_khach,
                    kh.sdt,
                    kh.co_so,
                    kh.ngay_hen_lam,
                    kh.gio,
                    kh.dich_vu,
                    kh.tong_tien,
                    kh.tien_coc,
                    kh.phai_dong,
                    kh.nguoi_chot,
                    kh.ghi_chu,
                    kh.trang_thai,
                    kh.created_at,
                    COALESCE(c.commission_amount, 0) as commission_amount,
                    'tham_my' as source_type
                FROM khach_hang kh
                LEFT JOIN commissions c ON c.transaction_id = -ABS(kh.id) AND c.ctv_code = %s AND c.level = 0
                WHERE kh.nguoi_chot = %s
                {date_filter_kh}
                
                UNION ALL
                
                SELECT 
                    s.id,
                    s.date_entered as ngay_nhap_don,
                    cust.name as ten_khach,
                    cust.phone as sdt,
                    NULL as co_so,
                    s.date_scheduled as ngay_hen_lam,
                    NULL as gio,
                    s.service_name as dich_vu,
                    s.tong_tien,
                    0 as tien_coc,
                    s.tong_tien as phai_dong,
                    COALESCE(s.nguoi_chot, s.ctv_code) as nguoi_chot,
                    NULL as ghi_chu,
                    s.status as trang_thai,
                    s.created_at,
                    COALESCE(c.commission_amount, 0) as commission_amount,
                    'nha_khoa' as source_type
                FROM services s
                LEFT JOIN customers cust ON s.customer_id = cust.id
                LEFT JOIN commissions c ON c.transaction_id = s.id AND c.ctv_code = COALESCE(s.nguoi_chot, s.ctv_code) AND c.level = 0
                WHERE COALESCE(s.nguoi_chot, s.ctv_code) = %s
                {date_filter_svc}
            ) AS all_transactions
            ORDER BY ngay_hen_lam DESC, id DESC
            LIMIT 100
        """
        
        cursor.execute(query, params_kh + params_svc)
        customers = [dict(row) for row in cursor.fetchall()]
        
        for c in customers:
            if c.get('ngay_nhap_don'):
                c['ngay_nhap_don'] = c['ngay_nhap_don'].strftime('%Y-%m-%d') if hasattr(c['ngay_nhap_don'], 'strftime') else str(c['ngay_nhap_don'])
            if c.get('ngay_hen_lam'):
                c['ngay_hen_lam'] = c['ngay_hen_lam'].strftime('%Y-%m-%d') if hasattr(c['ngay_hen_lam'], 'strftime') else str(c['ngay_hen_lam'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(c['created_at'], 'strftime') else str(c['created_at'])
            c['tong_tien'] = float(c['tong_tien'] or 0)
            c['tien_coc'] = float(c['tien_coc'] or 0)
            c['phai_dong'] = float(c['phai_dong'] or 0)
            c['commission_amount'] = float(c.get('commission_amount') or 0)
        
        # Summary from both tables
        cursor.execute("""
            SELECT 
                COALESCE(kh.total_count, 0) + COALESCE(svc.total_count, 0) as total_count,
                COALESCE(kh.completed_count, 0) + COALESCE(svc.completed_count, 0) as completed_count,
                COALESCE(kh.total_revenue, 0) + COALESCE(svc.total_revenue, 0) as total_revenue,
                COALESCE(kh.pending_count, 0) as pending_count
            FROM (
                SELECT 
                    COUNT(*) as total_count,
                    SUM(CASE WHEN trang_thai IN ('Da den lam', 'Đã đến làm') THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN trang_thai IN ('Da den lam', 'Đã đến làm') THEN tong_tien ELSE 0 END) as total_revenue,
                    SUM(CASE WHEN trang_thai IN ('Da coc', 'Đã cọc') THEN 1 ELSE 0 END) as pending_count
                FROM khach_hang
                WHERE nguoi_chot = %s
            ) kh,
            (
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(*) as completed_count,
                    SUM(tong_tien) as total_revenue
                FROM services
                WHERE COALESCE(nguoi_chot, ctv_code) = %s
            ) svc
        """, (ctv['ma_ctv'], ctv['ma_ctv']))
        
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
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500


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
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500


@ctv_bp.route('/api/ctv/commission', methods=['GET'])
@require_ctv
def get_ctv_commission():
    """Get commission based on khach_hang table with date filter on ngay_hen_lam"""
    ctv = g.current_user

    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        # REMOVED calculate_new_commissions_fast(connection=connection)
        
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        from_date = request.args.get('from')
        to_date = request.args.get('to')
        month = request.args.get('month')
        day = request.args.get('day')

        if month and not from_date and not to_date:
            if day:
                from_date = day
                to_date = day
            else:
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
        
        level0_query_kh = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Đã đến làm')
        """
        level0_params_kh = [ctv['ma_ctv']]
        
        if from_date:
            level0_query_kh += " AND ngay_hen_lam >= %s"
            level0_params_kh.append(from_date)
        if to_date:
            level0_query_kh += " AND ngay_hen_lam <= %s"
            level0_params_kh.append(to_date)
        
        cursor.execute(level0_query_kh, level0_params_kh)
        level0_kh = cursor.fetchone()
        
        # Use COALESCE(nguoi_chot, ctv_code) to get closer (not referrer)
        level0_query_svc = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM services
            WHERE COALESCE(nguoi_chot, ctv_code) = %s
        """
        level0_params_svc = [ctv['ma_ctv']]
        
        if from_date:
            level0_query_svc += " AND date_entered >= %s"
            level0_params_svc.append(from_date)
        if to_date:
            level0_query_svc += " AND date_entered <= %s"
            level0_params_svc.append(to_date)
        
        cursor.execute(level0_query_svc, level0_params_svc)
        level0_svc = cursor.fetchone()
        
        level0_revenue = float(level0_kh['total_revenue'] or 0) + float(level0_svc['total_revenue'] or 0)
        level0_count = int(level0_kh['transaction_count'] or 0) + int(level0_svc['transaction_count'] or 0)
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
            # OPTIMIZED: Get descendants with levels in ONE query
            cursor.execute("""
                WITH RECURSIVE network AS (
                    SELECT ma_ctv, 0 as level 
                    FROM ctv 
                    WHERE ma_ctv = %s
                    
                    UNION ALL
                    
                    SELECT c.ma_ctv, n.level + 1
                    FROM ctv c
                    JOIN network n ON c.nguoi_gioi_thieu = n.ma_ctv
                    WHERE n.level < 4
                )
                SELECT ma_ctv, level FROM network WHERE level > 0
            """, (ctv['ma_ctv'],))
            
            network_with_levels = cursor.fetchall()
            
            # Group by level
            ctvs_by_level = {1: [], 2: [], 3: [], 4: []}
            for row in network_with_levels:
                lvl = row['level']
                if lvl in ctvs_by_level:
                    ctvs_by_level[lvl].append(row['ma_ctv'])
            
            for level in range(1, 5):
                level_ctv_list = ctvs_by_level.get(level, [])
                
                if level_ctv_list:
                    placeholders = ','.join(['%s'] * len(level_ctv_list))
                    
                    level_query_kh = f"""
                        SELECT 
                            COALESCE(SUM(tong_tien), 0) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM khach_hang
                        WHERE nguoi_chot IN ({placeholders})
                        AND trang_thai IN ('Da den lam', 'Đã đến làm')
                    """
                    level_params_kh = list(level_ctv_list)
                    
                    if from_date:
                        level_query_kh += " AND ngay_hen_lam >= %s"
                        level_params_kh.append(from_date)
                    if to_date:
                        level_query_kh += " AND ngay_hen_lam <= %s"
                        level_params_kh.append(to_date)
                    
                    cursor.execute(level_query_kh, level_params_kh)
                    level_data_kh = cursor.fetchone()
                    
                    # Use COALESCE(nguoi_chot, ctv_code) to get closer (not referrer)
                    level_query_svc = f"""
                        SELECT 
                            COALESCE(SUM(tong_tien), 0) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM services
                        WHERE COALESCE(nguoi_chot, ctv_code) IN ({placeholders})
                    """
                    level_params_svc = list(level_ctv_list)
                    
                    if from_date:
                        level_query_svc += " AND date_entered >= %s"
                        level_params_svc.append(from_date)
                    if to_date:
                        level_query_svc += " AND date_entered <= %s"
                        level_params_svc.append(to_date)
                    
                    cursor.execute(level_query_svc, level_params_svc)
                    level_data_svc = cursor.fetchone()
                    
                    level_revenue = float(level_data_kh['total_revenue'] or 0) + float(level_data_svc['total_revenue'] or 0)
                    level_count = int(level_data_kh['transaction_count'] or 0) + int(level_data_svc['transaction_count'] or 0)
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
        total_revenue = sum(lc['total_revenue'] for lc in level_commissions)
        
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
                'transactions': total_transactions,
                'revenue': total_revenue
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500


@ctv_bp.route('/api/ctv/date-ranges-with-data', methods=['GET'])
@require_ctv
def get_date_ranges_with_data():
    """Check which date range presets have data available"""
    ctv = g.current_user

    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        today = datetime.date.today()
        ranges_with_data = {}

        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        my_network_excluding_self = [c for c in my_network if c != ctv['ma_ctv']]
        all_ctvs = [ctv['ma_ctv']] + my_network_excluding_self
        placeholders = ','.join(['%s'] * len(all_ctvs))

        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - datetime.timedelta(days=days_since_sunday)
        
        # Calculate end of current month
        next_month = today.replace(day=28) + datetime.timedelta(days=4)
        last_day_of_month = next_month - datetime.timedelta(days=next_month.day)
        
        date_ranges = {
            'today': (today, today),
            '3days': (today - datetime.timedelta(days=3), today),
            'week': (week_start, today),
            'month': (today.replace(day=1), last_day_of_month), # Covers full month
            'lastmonth': (
                (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1),
                today.replace(day=1) - datetime.timedelta(days=1)
            ),
            '3months': (today.replace(day=1) - datetime.timedelta(days=60), today),
            'year': (today.replace(month=1, day=1), today.replace(month=12, day=31))
        }

        for preset, (from_date, to_date) in date_ranges.items():
            # Check for ANY records in date range (removed status filter)
            # This ensures the dot appears if there is any data, even if pending/unconfirmed
            query_kh = f"""
                SELECT COUNT(*) as count
                FROM khach_hang
                WHERE nguoi_chot IN ({placeholders})
                AND ngay_hen_lam >= %s
                AND ngay_hen_lam <= %s
            """
            cursor.execute(query_kh, all_ctvs + [from_date, to_date])
            kh_count = cursor.fetchone()['count']

            # Use COALESCE(nguoi_chot, ctv_code) to get closer (not referrer)
            query_svc = f"""
                SELECT COUNT(*) as count
                FROM services
                WHERE COALESCE(nguoi_chot, ctv_code) IN ({placeholders})
                AND date_entered >= %s
                AND date_entered <= %s
            """
            cursor.execute(query_svc, all_ctvs + [from_date, to_date])
            svc_count = cursor.fetchone()['count']

            ranges_with_data[preset] = (kh_count > 0) or (svc_count > 0)

        cursor.close()
        return_db_connection(connection)

        return jsonify({
            'status': 'success',
            'ranges_with_data': ranges_with_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500


def calculate_level_simple_v2(ancestor_code, descendant_code, cursor):
    """Efficient helper to calculate level between ancestor and descendant using shared cursor"""
    try:
        current = descendant_code
        level = 0
        visited = set()
        
        while current and level <= 4:
            if current in visited:
                return None
            visited.add(current)
            
            if current == ancestor_code:
                return level
            
            cursor.execute("SELECT nguoi_gioi_thieu FROM ctv WHERE ma_ctv = %s", (current,))
            result = cursor.fetchone()
            
            if not result or not result.get('nguoi_gioi_thieu'):
                return None
            
            current = result['nguoi_gioi_thieu']
            level += 1
        
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
    
    if len(phone) < 8:
        return jsonify({'status': 'error', 'message': 'Invalid phone number'}), 400
    
    # Extract last 8 digits for fuzzy matching (handles leading zero variations and 8-digit DB entries)
    phone_suffix = phone[-8:]
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Use LIKE with suffix pattern to match phone numbers regardless of leading zeros
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM khach_hang
                WHERE sdt LIKE %s
                  AND (
                    (trang_thai IN ('Đã đến làm', 'Đã cọc', 'Da den lam', 'Da coc')
                     AND ngay_hen_lam >= CURRENT_DATE - INTERVAL '360 days')
                    OR (ngay_hen_lam >= CURRENT_DATE 
                        AND ngay_hen_lam < CURRENT_DATE + INTERVAL '180 days')
                    OR ngay_nhap_don >= CURRENT_DATE - INTERVAL '60 days'
                  )
            ) AS is_duplicate
        """, ('%' + phone_suffix,))
        
        result = cursor.fetchone()
        is_duplicate = result[0] if result else False
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'is_duplicate': is_duplicate,
            'message': 'Trung' if is_duplicate else 'Khong trung'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500

