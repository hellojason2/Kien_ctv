from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin
from ..db_pool import get_db_connection, return_db_connection
from ..mlm_core import (
    recalculate_all_commissions,
    calculate_new_commissions_fast,
    get_commission_cache_status
)
from ..redis_cache import invalidate_commission_cache
from ..activity_logger import log_commission_adjusted

@admin_bp.route('/api/admin/commission-settings', methods=['GET'])
@require_admin
def get_settings():
    """Get all commission rate settings"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT level, rate, description, updated_at, updated_by, is_active
            FROM commission_settings ORDER BY level
        """)
        settings = [dict(row) for row in cursor.fetchall()]
        
        for s in settings:
            s['rate'] = float(s['rate'])
            s['is_active'] = s.get('is_active', True)  # Default to True if not set
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'settings': settings
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commission-settings', methods=['PUT'])
@require_admin
def update_settings():
    """Update commission rate settings"""
    data = request.get_json()
    
    if not data or 'settings' not in data:
        return jsonify({'status': 'error', 'message': 'Settings array required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        admin_username = g.current_user.get('username', 'admin')
        
        for setting in data['settings']:
            level = setting.get('level')
            rate = setting.get('rate')
            description = setting.get('description')
            is_active = setting.get('is_active', True)  # Default to True if not provided
            
            if level is None or rate is None:
                continue
            
            if level < 0 or level > 4:
                continue
            
            cursor.execute("""
                UPDATE commission_settings 
                SET rate = %s, description = %s, updated_by = %s, is_active = %s
                WHERE level = %s
            """, (rate, description, admin_username, is_active, level))
            
            # Also update legacy table hoa_hong_config if it exists to keep them in sync
            # Note: hoa_hong_config stores percentage (e.g. 25.0) not rate (0.25)
            try:
                percent = float(rate) * 100
                cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'hoa_hong_config')")
                if cursor.fetchone()[0]:
                    cursor.execute("""
                        UPDATE hoa_hong_config 
                        SET percent = %s, description = %s, is_active = %s
                        WHERE level = %s
                    """, (percent, description, is_active, level))
            except Exception as e:
                print(f"Warning: Could not update legacy hoa_hong_config: {e}")
        
        connection.commit()
        cursor.close()
        
        # Invalidate cache to ensure new rates are used
        invalidate_commission_cache()
        
        # Recalculate all commissions with new settings
        stats = recalculate_all_commissions(connection)
        
        return_db_connection(connection)
        
        if 'error' in stats:
            return jsonify({
                'status': 'warning',
                'message': f'Commission settings updated but recalculation failed: {stats["error"]}'
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Commission settings updated and commissions recalculated',
            'recalculation_stats': stats
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions', methods=['GET'])
@require_admin
def list_commissions():
    """Get all commission records with filtering"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        ctv_code = request.args.get('ctv_code')
        month = request.args.get('month')
        level = request.args.get('level')
        limit = request.args.get('limit', 100, type=int)
        
        query = """
            SELECT
                c.id,
                c.transaction_id,
                c.ctv_code,
                ctv.ten as ctv_name,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam
                    ELSE s.date_entered
                END as transaction_date
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            WHERE 1=1
        """
        params = []
        
        if ctv_code:
            query += " AND c.ctv_code = %s"
            params.append(ctv_code)
        
        if month:
            query += """ AND (
                (c.transaction_id < 0 AND TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = %s)
                OR
                (c.transaction_id > 0 AND TO_CHAR(s.date_entered, 'YYYY-MM') = %s)
            )"""
            params.extend([month, month])
        
        if level is not None:
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += f""" ORDER BY (
            CASE
                WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam
                ELSE s.date_entered
            END
        ) DESC LIMIT %s"""
        params.append(limit)
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(commission_amount), 0) as total_commission,
                COUNT(*) as total_records,
                COUNT(DISTINCT ctv_code) as unique_ctv
            FROM commissions
        """)
        summary = cursor.fetchone()
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'data': commissions,
            'summary': {
                'total_commission': float(summary['total_commission'] or 0),
                'total_records': summary['total_records'],
                'unique_ctv': summary['unique_ctv']
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/summary', methods=['GET'])
@require_admin
def list_commissions_summary():
    """Get commission summary grouped by CTV, including services even if no commissions"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        month = request.args.get('month')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build date conditions and parameters for different tables
        comm_params = []
        kh_params = []
        svc_params = []
        
        if month:
            comm_where = """(
                (c.transaction_id < 0 AND TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = %s)
                OR
                (c.transaction_id > 0 AND TO_CHAR(s.date_entered, 'YYYY-MM') = %s)
            )"""
            comm_params.extend([month, month])
            kh_where = "TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = %s"
            kh_params.append(month)
            svc_where = "TO_CHAR(s.date_entered, 'YYYY-MM') = %s"
            svc_params.append(month)
        elif date_from and date_to:
            comm_where = """(
                (c.transaction_id < 0 AND DATE(kh.ngay_hen_lam) >= %s AND DATE(kh.ngay_hen_lam) <= %s)
                OR
                (c.transaction_id > 0 AND DATE(s.date_entered) >= %s AND DATE(s.date_entered) <= %s)
            )"""
            comm_params.extend([date_from, date_to, date_from, date_to])
            kh_where = "DATE(kh.ngay_hen_lam) >= %s AND DATE(kh.ngay_hen_lam) <= %s"
            kh_params.extend([date_from, date_to])
            svc_where = "DATE(s.date_entered) >= %s AND DATE(s.date_entered) <= %s"
            svc_params.extend([date_from, date_to])
        elif date_from:
            comm_where = """(
                (c.transaction_id < 0 AND DATE(kh.ngay_hen_lam) >= %s)
                OR
                (c.transaction_id > 0 AND DATE(s.date_entered) >= %s)
            )"""
            comm_params.extend([date_from, date_from])
            kh_where = "DATE(kh.ngay_hen_lam) >= %s"
            kh_params.append(date_from)
            svc_where = "DATE(s.date_entered) >= %s"
            svc_params.append(date_from)
        elif date_to:
            comm_where = """(
                (c.transaction_id < 0 AND DATE(kh.ngay_hen_lam) <= %s)
                OR
                (c.transaction_id > 0 AND DATE(s.date_entered) <= %s)
            )"""
            comm_params.extend([date_to, date_to])
            kh_where = "DATE(kh.ngay_hen_lam) <= %s"
            kh_params.append(date_to)
            svc_where = "DATE(s.date_entered) <= %s"
            svc_params.append(date_to)
        else:
            comm_where = """(
                (c.transaction_id < 0 AND TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM'))
                OR
                (c.transaction_id > 0 AND TO_CHAR(s.date_entered, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM'))
            )"""
            kh_where = "TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
            svc_where = "TO_CHAR(s.date_entered, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')"
        
        # Get commissions data
        comm_query = """
            SELECT
                c.ctv_code,
                SUM(c.transaction_amount) as total_service_price,
                SUM(c.commission_amount) as total_commission,
                COUNT(*) as commission_count
            FROM commissions c
            LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            WHERE """ + comm_where + """
            GROUP BY c.ctv_code
        """
        cursor.execute(comm_query, comm_params)
        commissions_data = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # Get services from khach_hang table
        kh_query = """
            SELECT
                kh.nguoi_chot as ctv_code,
                COUNT(*) as service_count,
                SUM(kh.tong_tien) as total_revenue
            FROM khach_hang kh
            WHERE kh.nguoi_chot IS NOT NULL
            AND kh.nguoi_chot != ''
            AND (kh.trang_thai = 'Đã đến làm' OR kh.trang_thai = 'Da den lam')
            AND """ + kh_where + """
            GROUP BY kh.nguoi_chot
        """
        cursor.execute(kh_query, kh_params)
        kh_services = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # Get services from services table
        svc_query = """
            SELECT 
                s.ctv_code,
                COUNT(*) as service_count,
                SUM(s.tong_tien) as total_revenue
            FROM services s
            WHERE s.ctv_code IS NOT NULL 
            AND s.ctv_code != ''
            AND """ + svc_where + """
            GROUP BY s.ctv_code
        """
        cursor.execute(svc_query, svc_params)
        svc_services = {row['ctv_code']: row for row in cursor.fetchall()}
        
        # FAST: Calculate only new commissions using cached max IDs
        # fast_stats = calculate_new_commissions_fast(connection=connection)
        
        # if fast_stats.get('total', 0) > 0:
        #     cursor.execute(comm_query, comm_params)
        #     commissions_data = {row['ctv_code']: row for row in cursor.fetchall()}
        
        all_ctv_codes = set()
        all_ctv_codes.update(commissions_data.keys())
        all_ctv_codes.update(kh_services.keys())
        all_ctv_codes.update(svc_services.keys())
        
        summary = []
        total_service_count = 0
        total_service_revenue = 0
        
        for ctv_code in all_ctv_codes:
            cursor.execute("SELECT ma_ctv, ten, sdt FROM ctv WHERE ma_ctv = %s", (ctv_code,))
            ctv_info = cursor.fetchone()
            if not ctv_info:
                continue
            
            comm_data = commissions_data.get(ctv_code, {})
            comm_total = float(comm_data.get('total_commission', 0) or 0)
            comm_service_price = float(comm_data.get('total_service_price', 0) or 0)
            
            kh_data = kh_services.get(ctv_code, {})
            kh_count = int(kh_data.get('service_count', 0) or 0)
            kh_revenue = float(kh_data.get('total_revenue', 0) or 0)
            
            svc_data = svc_services.get(ctv_code, {})
            svc_count = int(svc_data.get('service_count', 0) or 0)
            svc_revenue = float(svc_data.get('total_revenue', 0) or 0)
            
            total_services = kh_count + svc_count
            total_revenue = kh_revenue + svc_revenue
            
            service_price = comm_service_price if comm_service_price > 0 else total_revenue
            
            summary.append({
                'ctv_code': ctv_code,
                'ctv_name': ctv_info['ten'],
                'ctv_phone': ctv_info['sdt'],
                'total_service_price': service_price,
                'total_commission': comm_total,
                'service_count': total_services,
                'has_services_no_commission': total_services > 0 and comm_total == 0
            })
            
            total_service_count += total_services
            total_service_revenue += service_price
        
        summary.sort(key=lambda x: (x['total_commission'], x['service_count']), reverse=True)
        
        grand_total_commission = sum(s['total_commission'] for s in summary)
        grand_total_service = sum(s['total_service_price'] for s in summary)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'grand_total': {
                'total_service_price': grand_total_service,
                'total_commission': grand_total_commission,
                'total_service_count': total_service_count
            },
            'total_ctv': len(summary)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/recalculate', methods=['POST'])
@require_admin
def recalculate_commissions():
    """Recalculate all commissions from khach_hang and services tables (admin only)"""
    try:
        stats = recalculate_all_commissions()
        return jsonify({
            'status': 'success',
            'message': 'Commissions recalculated successfully',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/<int:commission_id>', methods=['PUT'])
@require_admin
def adjust_commission(commission_id):
    """Manually adjust a commission record"""
    data = request.get_json()
    
    if not data or 'commission_amount' not in data:
        return jsonify({'status': 'error', 'message': 'commission_amount required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT commission_amount FROM commissions WHERE id = %s", (commission_id,))
        old_record = cursor.fetchone()
        
        if not old_record:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Commission record not found'}), 404
        
        old_amount = float(old_record['commission_amount'])
        new_amount = float(data['commission_amount'])
        
        cursor.execute("""
            UPDATE commissions SET commission_amount = %s WHERE id = %s
        """, (new_amount, commission_id))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_commission_adjusted(admin_username, commission_id, old_amount, new_amount)
        
        return jsonify({
            'status': 'success',
            'message': 'Commission adjusted successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/admin/commission-cache/status', methods=['GET'])
@require_admin
def commission_cache_status():
    """Get status of commission calculation cache"""
    try:
        status = get_commission_cache_status()
        return jsonify({
            'status': 'success',
            'cache_status': status
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

