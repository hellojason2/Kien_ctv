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
        
        cursor.execute("SELECT percent FROM hoa_hong_config WHERE level = 0")
        rate_row = cursor.fetchone()
        level0_rate = float(rate_row['percent']) / 100 if rate_row else 0.25
        
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as total_revenue,
                   COUNT(*) as total_transactions
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
        """, (ctv['ma_ctv'],))
        commission_stats = cursor.fetchone()
        
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
        
        my_network = get_all_descendants(ctv['ma_ctv'], connection)
        network_size = len(my_network) if my_network else 0
        
        cursor.execute("""
            SELECT COUNT(*) as direct_count
            FROM ctv
            WHERE nguoi_gioi_thieu = %s AND (is_active = TRUE OR is_active IS NULL)
        """, (ctv['ma_ctv'],))
        direct_result = cursor.fetchone()
        direct_referrals = int(direct_result['direct_count']) if direct_result else 0
        
        cursor.execute("""
            SELECT COUNT(*) as total_services,
                   COALESCE(SUM(tong_tien), 0) as total_revenue
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
        """, (ctv['ma_ctv'],))
        kh_service_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) as total_services,
                   COALESCE(SUM(tong_tien), 0) as total_revenue
            FROM services
            WHERE ctv_code = %s
        """, (ctv['ma_ctv'],))
        svc_service_stats = cursor.fetchone()
        
        total_services = int(kh_service_stats['total_services'] or 0) + int(svc_service_stats['total_services'] or 0)
        service_revenue = float(kh_service_stats['total_revenue'] or 0) + float(svc_service_stats['total_revenue'] or 0)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_commissions': total_commissions,
                'total_transactions': total_transactions,
                'network_size': network_size,
                'direct_referrals': direct_referrals,
                'total_services': total_services,
                'total_revenue': service_revenue
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
    """Get all customers where nguoi_chot = logged-in CTV"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        # REMOVED calculate_new_commissions_fast(connection=connection)
        
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        query = """
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
                COALESCE(c.commission_amount, 0) as commission_amount
            FROM khach_hang kh
            LEFT JOIN commissions c ON c.transaction_id = -ABS(kh.id) AND c.ctv_code = %s AND c.level = 0
            WHERE kh.nguoi_chot = %s
        """
        params = [ctv['ma_ctv'], ctv['ma_ctv']]
        
        status = request.args.get('status')
        if status:
            query += " AND kh.trang_thai = %s"
            params.append(status)
        
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        if from_date:
            query += " AND kh.ngay_hen_lam >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND kh.ngay_hen_lam <= %s"
            params.append(to_date)
        
        query += " ORDER BY kh.ngay_hen_lam DESC, kh.id DESC LIMIT 100"
        
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
            c['commission_amount'] = float(c.get('commission_amount') or 0)
        
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
            AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
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
        
        level0_query_svc = """
            SELECT 
                SUM(tong_tien) as total_revenue,
                COUNT(*) as transaction_count
            FROM services
            WHERE ctv_code = %s
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
            # Get common cursor for all level calculations
            level_cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            for level in range(1, 5):
                level_ctv_list = []
                
                for descendant_code in my_network_excluding_self:
                    desc_level = calculate_level_simple_v2(ctv['ma_ctv'], descendant_code, level_cursor)
                    if desc_level == level:
                        level_ctv_list.append(descendant_code)
                
                if level_ctv_list:
                    placeholders = ','.join(['%s'] * len(level_ctv_list))
                    
                    level_query_kh = f"""
                        SELECT 
                            COALESCE(SUM(tong_tien), 0) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM khach_hang
                        WHERE nguoi_chot IN ({placeholders})
                        AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
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
                    
                    level_query_svc = f"""
                        SELECT 
                            COALESCE(SUM(tong_tien), 0) as total_revenue,
                            COUNT(*) as transaction_count
                        FROM services
                        WHERE ctv_code IN ({placeholders})
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
            level_cursor.close()
        
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
        
        date_ranges = {
            'today': (today, today),
            '3days': (today - datetime.timedelta(days=3), today),
            'week': (week_start, today),
            'month': (today.replace(day=1), today),
            'lastmonth': (
                (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1),
                today.replace(day=1) - datetime.timedelta(days=1)
            ),
            '3months': (today.replace(day=1) - datetime.timedelta(days=60), today),
            'year': (today.replace(month=1, day=1), today)
        }

        for preset, (from_date, to_date) in date_ranges.items():
            query_kh = f"""
                SELECT COUNT(*) as count
                FROM khach_hang
                WHERE nguoi_chot IN ({placeholders})
                AND trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
                AND ngay_hen_lam >= %s
                AND ngay_hen_lam <= %s
            """
            cursor.execute(query_kh, all_ctvs + [from_date, to_date])
            kh_count = cursor.fetchone()['count']

            query_svc = f"""
                SELECT COUNT(*) as count
                FROM services
                WHERE ctv_code IN ({placeholders})
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
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500

