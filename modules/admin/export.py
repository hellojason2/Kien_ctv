from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin
from ..db_pool import get_db_connection, return_db_connection
from ..activity_logger import get_activity_logs, log_data_export
from ..export_excel import (
    create_xlsx_response,
    CTV_EXPORT_COLUMNS,
    COMMISSION_EXPORT_COLUMNS,
    COMMISSION_SUMMARY_COLUMNS,
    CLIENTS_EXPORT_COLUMNS,
    ACTIVITY_LOG_COLUMNS,
    COMMISSION_SETTINGS_COLUMNS
)

@admin_bp.route('/api/admin/ctv/export', methods=['GET'])
@require_admin
def export_ctv_excel():
    """Export all CTVs to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = """
            SELECT 
                c.ma_ctv,
                c.ten,
                c.sdt,
                c.email,
                c.nguoi_gioi_thieu,
                c.nguoi_gioi_thieu as nguoi_gioi_thieu_code,
                c.cap_bac,
                CASE WHEN c.is_active = TRUE OR c.is_active IS NULL THEN 'Active' ELSE 'Inactive' END as is_active,
                c.created_at
            FROM ctv c
            LEFT JOIN ctv p ON c.nguoi_gioi_thieu = p.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (c.ma_ctv ILIKE %s OR c.ten ILIKE %s OR c.email ILIKE %s OR c.sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        if active_only:
            query += " AND (c.is_active = TRUE OR c.is_active IS NULL)"
        
        query += " ORDER BY c.created_at DESC"
        
        cursor.execute(query, params)
        ctv_list = [dict(row) for row in cursor.fetchall()]
        
        for ctv in ctv_list:
            if ctv.get('created_at'):
                ctv['created_at'] = ctv['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'ctv_list', len(ctv_list))
        
        return create_xlsx_response(
            data=ctv_list,
            columns=CTV_EXPORT_COLUMNS,
            filename='ctv_export',
            sheet_name='CTV List'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/export', methods=['GET'])
@require_admin
def export_commissions_excel():
    """Export commission records to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        ctv_code = request.args.get('ctv_code')
        month = request.args.get('month')
        level = request.args.get('level')
        
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
                c.created_at
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if ctv_code:
            query += " AND c.ctv_code = %s"
            params.append(ctv_code)
        
        if month:
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        
        if level is not None:
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += " ORDER BY c.created_at DESC LIMIT 10000"
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commissions', len(commissions))
        
        return create_xlsx_response(
            data=commissions,
            columns=COMMISSION_EXPORT_COLUMNS,
            filename='commissions_export',
            sheet_name='Commissions'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commissions/summary/export', methods=['GET'])
@require_admin
def export_commissions_summary_excel():
    """Export commission summary by CTV to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        month = request.args.get('month')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = """
            SELECT 
                c.ctv_code,
                ctv.ten as ctv_name,
                ctv.sdt as ctv_phone,
                SUM(c.transaction_amount) as total_service_price,
                SUM(c.commission_amount) as total_commission
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE 1=1
        """
        params = []
        
        if month:
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        elif date_from and date_to:
            query += " AND DATE(c.created_at) >= %s AND DATE(c.created_at) <= %s"
            params.extend([date_from, date_to])
        elif date_from:
            query += " AND DATE(c.created_at) >= %s"
            params.append(date_from)
        elif date_to:
            query += " AND DATE(c.created_at) <= %s"
            params.append(date_to)
        
        query += """
            GROUP BY c.ctv_code, ctv.ten, ctv.sdt
            ORDER BY total_commission DESC
        """
        
        cursor.execute(query, params)
        summary = [dict(row) for row in cursor.fetchall()]
        
        for s in summary:
            s['total_service_price'] = float(s['total_service_price'] or 0)
            s['total_commission'] = float(s['total_commission'] or 0)
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commission_summary', len(summary))
        
        return create_xlsx_response(
            data=summary,
            columns=COMMISSION_SUMMARY_COLUMNS,
            filename='commission_summary_export',
            sheet_name='Commission Summary'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/clients/export', methods=['GET'])
@require_admin
def export_clients_excel():
    """Export clients with services to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        
        base_where = "WHERE sdt IS NOT NULL AND sdt != ''"
        params = []
        
        if search:
            base_where += " AND (ten_khach ILIKE %s OR sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            base_where += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
        query = f"""
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(nguoi_chot) as nguoi_chot,
                COUNT(*) as service_count,
                MIN(ngay_nhap_don) as first_visit_date,
                MAX(trang_thai) as overall_status,
                CASE WHEN MAX(tien_coc) > 0 THEN 'Da coc' ELSE 'Chua coc' END as overall_deposit
            FROM khach_hang
            {base_where}
            GROUP BY sdt, ten_khach
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT 10000
        """
        
        cursor.execute(query, params)
        clients = [dict(row) for row in cursor.fetchall()]
        
        for client in clients:
            if client.get('first_visit_date'):
                client['first_visit_date'] = client['first_visit_date'].strftime('%d/%m/%Y')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'clients', len(clients))
        
        return create_xlsx_response(
            data=clients,
            columns=CLIENTS_EXPORT_COLUMNS,
            filename='clients_export',
            sheet_name='Clients'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/export-xlsx', methods=['GET'])
@require_admin
def export_activity_logs_excel():
    """Export activity logs to Excel file"""
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        
        result = get_activity_logs(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=1,
            per_page=10000
        )
        
        logs = result['logs']
        
        for log in logs:
            if log.get('details'):
                if isinstance(log['details'], dict):
                    log['details'] = str(log['details'])
                else:
                    log['details'] = str(log['details'])
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'activity_logs', len(logs))
        
        return create_xlsx_response(
            data=logs,
            columns=ACTIVITY_LOG_COLUMNS,
            filename='activity_logs_export',
            sheet_name='Activity Logs'
        )
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/commission-settings/export', methods=['GET'])
@require_admin
def export_commission_settings_excel():
    """Export commission settings to Excel file"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT level, rate, description, updated_at, updated_by
            FROM commission_settings ORDER BY level
        """)
        settings = [dict(row) for row in cursor.fetchall()]
        
        for s in settings:
            s['rate'] = float(s['rate'])
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'commission_settings', len(settings))
        
        return create_xlsx_response(
            data=settings,
            columns=COMMISSION_SETTINGS_COLUMNS,
            filename='commission_settings_export',
            sheet_name='Commission Settings'
        )
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500

