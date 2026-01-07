import datetime
from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..auth import require_ctv
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import get_network_stats, calculate_new_commissions_fast

@ctv_bp.route('/api/ctv/me', methods=['GET'])
@require_ctv
def get_profile():
    """Get logged-in CTV profile with network stats"""
    ctv = g.current_user
    print(f"DEBUG: get_profile for {ctv['ma_ctv']}")
    
    connection = get_db_connection()
    if not connection:
        print("DEBUG: connection failed")
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        print(f"DEBUG: get_profile for {ctv['ma_ctv']} - getting network stats")
        try:
            stats = get_network_stats(ctv['ma_ctv'], connection)
        except Exception as e:
            print(f"DEBUG: Error in get_network_stats: {e}")
            stats = {'total': 0, 'by_level': {}}
            
        print(f"DEBUG: get_profile for {ctv['ma_ctv']} - getting referrer and rates")
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
        
        # REMOVED calculate_new_commissions_fast(connection=connection) from sync path
        # It's better to run this in a background task or at specific intervals
        
        # ... (rest of the earnings queries)

        
        print(f"DEBUG: get_profile for {ctv['ma_ctv']} - getting total earnings")
        # Get total earnings from commissions table (all time, Level 0 only)
        cursor.execute("""
            SELECT COALESCE(SUM(commission_amount), 0) as total_earnings
            FROM commissions
            WHERE ctv_code = %s AND level = 0
        """, (ctv['ma_ctv'],))
        total_earnings = float(cursor.fetchone()['total_earnings'])
        
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

        print(f"DEBUG: getting monthly earnings for {start_date} to {end_date}")
        # Calculate monthly earnings from source data (same as /api/ctv/commission endpoint)
        # This avoids potential data corruption issues in the commissions table
        
        # Get commission rate for level 0
        cursor.execute("SELECT percent FROM hoa_hong_config WHERE level = 0")
        rate_row = cursor.fetchone()
        level0_rate = float(rate_row['percent']) / 100 if rate_row else 0.25
        
        # Get period revenue from khach_hang where this CTV is the nguoi_chot (closer)
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as revenue
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND (trang_thai = 'Đã đến làm' OR trang_thai = 'Da den lam')
            AND ngay_hen_lam >= %s AND ngay_hen_lam < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        kh_revenue = float(cursor.fetchone()['revenue'])
        
        # Get period revenue from services where this CTV is the ctv_code
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as revenue
            FROM services
            WHERE ctv_code = %s
            AND date_entered >= %s AND date_entered < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        svc_revenue = float(cursor.fetchone()['revenue'])
        
        # Calculate commission: (revenue from khach_hang + services) × rate
        monthly_earnings = (kh_revenue + svc_revenue) * level0_rate
        
        print("DEBUG: calculating period revenue")
        # Calculate period revenue for services count
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as period_revenue
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND (trang_thai = 'Đã đến làm' OR trang_thai = 'Da den lam')
            AND ngay_hen_lam >= %s
            AND ngay_hen_lam < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        kh_period_revenue = float(cursor.fetchone()['period_revenue'])
        
        cursor.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as period_revenue
            FROM services
            WHERE ctv_code = %s
            AND date_entered >= %s
            AND date_entered < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        svc_period_revenue = float(cursor.fetchone()['period_revenue'])
        
        period_revenue = kh_period_revenue + svc_period_revenue
        
        print("DEBUG: counting services")
        # Count services
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM khach_hang
            WHERE nguoi_chot = %s
            AND (trang_thai = 'Đã đến làm' OR trang_thai = 'Da den lam')
            AND ngay_hen_lam >= %s
            AND ngay_hen_lam < %s
        """, (ctv['ma_ctv'], start_date, end_date))
        kh_count = int(cursor.fetchone()['count'])
        
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
        
        print("DEBUG: get_profile success")
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
                'monthly_services_count': monthly_services_count,
                'period_revenue': period_revenue
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500

