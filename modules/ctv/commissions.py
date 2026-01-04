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
                s.nguoi_chot as source_ctv_code,
                s.service_name,
                ctv_source.ten as source_ctv_name,
                cust.name as customer_name
            FROM commissions c
            LEFT JOIN services s ON c.transaction_id = s.id
            LEFT JOIN ctv ctv_source ON s.nguoi_chot = ctv_source.ma_ctv
            LEFT JOIN customers cust ON s.customer_id = cust.id
            WHERE c.ctv_code = %s
        """
        params = [ctv['ma_ctv']]
        
        if from_date and to_date:
            query += " AND DATE(c.created_at) >= %s AND DATE(c.created_at) <= %s"
            params.extend([from_date, to_date])
        elif month:
            query += " AND TO_CHAR(c.created_at, 'YYYY-MM') = %s"
            params.append(month)
        
        if level is not None and level != '':
            query += " AND c.level = %s"
            params.append(int(level))
        
        query += " ORDER BY c.created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
        commissions = [dict(row) for row in cursor.fetchall()]
        
        for c in commissions:
            c['commission_rate'] = float(c['commission_rate'])
            c['transaction_amount'] = float(c['transaction_amount'])
            c['commission_amount'] = float(c['commission_amount'])
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            c['source_ctv_name'] = c.get('source_ctv_name') or c.get('source_ctv_code') or 'N/A'
            c['source_ctv_code'] = c.get('source_ctv_code') or 'N/A'
            c['customer_name'] = c.get('customer_name') or 'N/A'
            c['service_name'] = c.get('service_name') or 'N/A'
        
        summary_query = """
            SELECT 
                level,
                COUNT(*) as count,
                SUM(commission_amount) as total
            FROM commissions
            WHERE ctv_code = %s
        """
        summary_params = [ctv['ma_ctv']]
        
        if from_date and to_date:
            summary_query += " AND DATE(created_at) >= %s AND DATE(created_at) <= %s"
            summary_params.extend([from_date, to_date])
        elif month:
            summary_query += " AND TO_CHAR(created_at, 'YYYY-MM') = %s"
            summary_params.append(month)
        
        summary_query += " GROUP BY level ORDER BY level"
        
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

