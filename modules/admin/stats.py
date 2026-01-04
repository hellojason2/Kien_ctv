import datetime
from flask import jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import calculate_new_commissions_fast

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
        
        # Calculate missing commissions incrementally
        calculate_new_commissions_fast(connection=connection)
        
        # Build date conditions for source tables
        if from_date and to_date:
            kh_date_condition = f"DATE(kh.ngay_hen_lam) >= '{from_date}' AND DATE(kh.ngay_hen_lam) <= '{to_date}'"
            svc_date_condition = f"DATE(svc.date_entered) >= '{from_date}' AND DATE(svc.date_entered) <= '{to_date}'"
        elif day_filter:
            kh_date_condition = f"DATE(kh.ngay_hen_lam) = '{day_filter}'"
            svc_date_condition = f"DATE(svc.date_entered) = '{day_filter}'"
        elif month_filter:
            kh_date_condition = f"TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = '{month_filter}'"
            svc_date_condition = f"TO_CHAR(svc.date_entered, 'YYYY-MM') = '{month_filter}'"
        else:
            kh_date_condition = "TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            svc_date_condition = "TO_CHAR(svc.date_entered, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
        
        # Get monthly commission from stored commissions table
        cursor.execute(f"""
            SELECT COALESCE(SUM(c.commission_amount), 0) as total
            FROM commissions c
            LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
            LEFT JOIN services svc ON c.transaction_id = svc.id AND c.transaction_id > 0
            WHERE ({kh_date_condition} AND c.transaction_id < 0) 
               OR ({svc_date_condition} AND c.transaction_id > 0)
        """)
        monthly_commission = float(cursor.fetchone()['total'])
        
        kh_transactions = 0
        svc_transactions = 0
        
        try:
            if from_date and to_date:
                kh_date_cond = f"DATE(ngay_hen_lam) >= '{from_date}' AND DATE(ngay_hen_lam) <= '{to_date}'"
            elif day_filter:
                kh_date_cond = f"DATE(ngay_hen_lam) = '{day_filter}'"
            elif month_filter:
                kh_date_cond = f"TO_CHAR(ngay_hen_lam, 'YYYY-MM') = '{month_filter}'"
            else:
                kh_date_cond = "TO_CHAR(ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM khach_hang
                WHERE {kh_date_cond}
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
        
        # Calculate monthly revenue
        cursor.execute(f"""
            SELECT COALESCE(SUM(transaction_amount), 0) as total
            FROM (
                SELECT DISTINCT c.transaction_id, c.transaction_amount
                FROM commissions c
                LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
                LEFT JOIN services svc ON c.transaction_id = svc.id AND c.transaction_id > 0
                WHERE ({kh_date_condition} AND c.transaction_id < 0) 
                   OR ({svc_date_condition} AND c.transaction_id > 0)
            ) as distinct_transactions
        """)
        result = cursor.fetchone()
        monthly_revenue = float(result['total']) if result['total'] else 0.0
        
        if monthly_revenue == 0:
            kh_revenue = 0
            svc_revenue = 0
            
            try:
                if from_date and to_date:
                    kh_date_cond = f"DATE(ngay_hen_lam) >= '{from_date}' AND DATE(ngay_hen_lam) <= '{to_date}'"
                elif day_filter:
                    kh_date_cond = f"DATE(ngay_hen_lam) = '{day_filter}'"
                elif month_filter:
                    kh_date_cond = f"TO_CHAR(ngay_hen_lam, 'YYYY-MM') = '{month_filter}'"
                else:
                    kh_date_cond = "TO_CHAR(ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
                
                cursor.execute(f"""
                    SELECT COALESCE(SUM(tong_tien), 0) as total
                    FROM khach_hang
                    WHERE {kh_date_cond}
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
        
        # Get top earners
        top_earners = []
        try:
            if from_date and to_date:
                kh_date_cond = f"DATE(kh.ngay_hen_lam) >= '{from_date}' AND DATE(kh.ngay_hen_lam) <= '{to_date}'"
                svc_date_cond = f"DATE(svc.date_entered) >= '{from_date}' AND DATE(svc.date_entered) <= '{to_date}'"
            elif day_filter:
                kh_date_cond = f"DATE(kh.ngay_hen_lam) = '{day_filter}'"
                svc_date_cond = f"DATE(svc.date_entered) = '{day_filter}'"
            elif month_filter:
                kh_date_cond = f"TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = '{month_filter}'"
                svc_date_cond = f"TO_CHAR(svc.date_entered, 'YYYY-MM') = '{month_filter}'"
            else:
                kh_date_cond = "TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
                svc_date_cond = "TO_CHAR(svc.date_entered, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            
            cursor.execute(f"""
                SELECT 
                    c.ctv_code,
                    ctv.ten,
                    COALESCE(SUM(c.transaction_amount), 0) as total_revenue,
                    COALESCE(SUM(c.commission_amount), 0) as total_commission
                FROM commissions c
                JOIN ctv ON c.ctv_code = ctv.ma_ctv
                LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
                LEFT JOIN services svc ON c.transaction_id = svc.id AND c.transaction_id > 0
                WHERE ({kh_date_cond} AND c.transaction_id < 0) 
                   OR ({svc_date_cond} AND c.transaction_id > 0)
                GROUP BY c.ctv_code, ctv.ten
                HAVING COALESCE(SUM(c.commission_amount), 0) > 0
                ORDER BY total_commission DESC
                LIMIT 5
            """)
            top_earners_raw = cursor.fetchall()
            for row in top_earners_raw:
                top_earners.append({
                    'ctv_code': row['ctv_code'],
                    'ten': row['ten'],
                    'total_revenue': float(row['total_revenue'] or 0),
                    'total_commission': float(row['total_commission'] or 0)
                })
        except Error:
            pass
        
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
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        today = datetime.date.today()
        ranges_with_data = {}

        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - datetime.timedelta(days=days_since_sunday)
        
        date_ranges = {
            'today': (today, today),
            '3days': (today - datetime.timedelta(days=2), today),
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
            query_kh = """
                SELECT COUNT(*) as count
                FROM khach_hang
                WHERE trang_thai IN ('Da den lam', 'Da coc', 'Đã đến làm', 'Đã cọc', 'Cho xac nhan', 'Chờ xác nhận')
                AND ngay_hen_lam >= %s
                AND ngay_hen_lam <= %s
            """
            cursor.execute(query_kh, [from_date, to_date])
            kh_count = cursor.fetchone()['count']

            query_svc = """
                SELECT COUNT(*) as count
                FROM services
                WHERE date_entered >= %s
                AND date_entered <= %s
            """
            cursor.execute(query_svc, [from_date, to_date])
            svc_count = cursor.fetchone()['count']

            query_comm = """
                SELECT COUNT(*) as count
                FROM commissions
                WHERE DATE(created_at) >= %s
                AND DATE(created_at) <= %s
            """
            cursor.execute(query_comm, [from_date, to_date])
            comm_count = cursor.fetchone()['count']

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

