from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..auth import require_ctv
from ..db_pool import get_db_connection, return_db_connection

@ctv_bp.route('/api/ctv/my-commissions', methods=['GET'])
@require_ctv
def get_my_commissions():
    """Get own commission earnings with breakdown"""
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        month = request.args.get('month')
        level = request.args.get('level')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        query = """
            SELECT
                c.id,
                c.transaction_id,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.nguoi_chot
                    ELSE s.nguoi_chot
                END as source_ctv_code,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.dich_vu
                    ELSE s.service_name
                END as service_name,
                CASE
                    WHEN c.transaction_id < 0 THEN ctv_kh.ten
                    ELSE ctv_s.ten
                END as source_ctv_name,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.ten_khach
                    ELSE cust.name
                END as customer_name,
                CASE
                    WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam
                    ELSE s.date_entered
                END as transaction_date
            FROM commissions c
            LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            LEFT JOIN ctv ctv_kh ON (
                kh.nguoi_chot = ctv_kh.ma_ctv
                OR RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(ctv_kh.ma_ctv, '[^0-9]', '', 'g'), 9)
            )
            LEFT JOIN ctv ctv_s ON (
                s.nguoi_chot = ctv_s.ma_ctv
                OR RIGHT(REGEXP_REPLACE(s.nguoi_chot, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(ctv_s.ma_ctv, '[^0-9]', '', 'g'), 9)
            )
            LEFT JOIN customers cust ON s.customer_id = cust.id
            WHERE c.ctv_code = %s
        """
        params = [ctv['ma_ctv']]
        
        if from_date and to_date:
            query += """ AND (
                (c.transaction_id < 0 AND DATE(kh.ngay_hen_lam) >= %s AND DATE(kh.ngay_hen_lam) <= %s)
                OR
                (c.transaction_id > 0 AND DATE(s.date_entered) >= %s AND DATE(s.date_entered) <= %s)
            )"""
            params.extend([from_date, to_date, from_date, to_date])
        elif month:
            query += """ AND (
                (c.transaction_id < 0 AND TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = %s)
                OR
                (c.transaction_id > 0 AND TO_CHAR(s.date_entered, 'YYYY-MM') = %s)
            )"""
            params.extend([month, month])
        
        if level is not None and level != '':
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += """ ORDER BY (
            CASE
                WHEN c.transaction_id < 0 THEN kh.ngay_hen_lam
                ELSE s.date_entered
            END
        ) DESC LIMIT 100"""
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if c.get('transaction_date'):
                c['transaction_date'] = str(c['transaction_date'])
            c['source_ctv_name'] = c.get('source_ctv_name') or c.get('source_ctv_code') or 'N/A'
            c['source_ctv_code'] = c.get('source_ctv_code') or 'N/A'
            c['customer_name'] = c.get('customer_name') or 'N/A'
            c['service_name'] = c.get('service_name') or 'N/A'
        
        summary_query = """
            SELECT
                c.level,
                COUNT(*) as count,
                SUM(c.commission_amount) as total
            FROM commissions c
            LEFT JOIN khach_hang kh ON c.transaction_id = -ABS(kh.id)
            LEFT JOIN services s ON c.transaction_id = s.id AND c.transaction_id > 0
            WHERE c.ctv_code = %s
        """
        summary_params = [ctv['ma_ctv']]
        
        if from_date and to_date:
            summary_query += """ AND (
                (c.transaction_id < 0 AND DATE(kh.ngay_hen_lam) >= %s AND DATE(kh.ngay_hen_lam) <= %s)
                OR
                (c.transaction_id > 0 AND DATE(s.date_entered) >= %s AND DATE(s.date_entered) <= %s)
            )"""
            summary_params.extend([from_date, to_date, from_date, to_date])
        elif month:
            summary_query += """ AND (
                (c.transaction_id < 0 AND TO_CHAR(kh.ngay_hen_lam, 'YYYY-MM') = %s)
                OR
                (c.transaction_id > 0 AND TO_CHAR(s.date_entered, 'YYYY-MM') = %s)
            )"""
            summary_params.extend([month, month])
        
        summary_query += " GROUP BY c.level ORDER BY c.level"
        
        cursor.execute(summary_query, summary_params)
        summary = [dict(row) for row in cursor.fetchall()]
        
        for s in summary:
            s['total'] = float(s['total'] or 0)
        
        total_commission = sum(s['total'] for s in summary)
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'commissions': commissions,
            'summary': {
                'by_level': summary,
                'total': total_commission
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500

