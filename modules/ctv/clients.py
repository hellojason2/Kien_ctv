from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..auth import require_ctv
from ..db_pool import get_db_connection, return_db_connection
from .customers import normalize_phone

@ctv_bp.route('/api/ctv/clients-with-services', methods=['GET'])
@require_ctv
def get_ctv_clients_with_services():
    """Get clients with their services grouped - filtered by CTV (closer)
    
    This includes both khach_hang (Beauty) and services (Dental) tables,
    using nguoi_chot as the closer for both.
    """
    ctv = g.current_user
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        limit = request.args.get('limit', 50, type=int)
        
        # Normalize CTV code for matching (handles 0972020908 vs 972020908)
        ctv_code = ctv['ma_ctv']
        ctv_code_normalized = normalize_phone(ctv_code)
        ctv_code_with_zero = '0' + ctv_code_normalized if ctv_code_normalized else ctv_code
        
        # Get distinct clients from BOTH khach_hang and services where CTV is the closer
        # Use normalized phone matching for nguoi_chot
        client_query = """
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(first_date) as first_visit_date,
                COUNT(*) as service_count
            FROM (
                SELECT 
                    sdt,
                    ten_khach,
                    co_so,
                    ngay_nhap_don as first_date,
                    source
                FROM khach_hang
                WHERE (nguoi_chot = %s OR nguoi_chot = %s OR nguoi_chot = %s
                       OR RIGHT(REGEXP_REPLACE(nguoi_chot, '[^0-9]', '', 'g'), 9) = %s)
                AND sdt IS NOT NULL AND sdt != ''
                
                UNION ALL
                
                SELECT 
                    c.phone as sdt,
                    c.name as ten_khach,
                    NULL as co_so,
                    s.date_entered as first_date,
                    'nha_khoa' as source
                FROM services s
                JOIN customers c ON s.customer_id = c.id
                WHERE (COALESCE(s.nguoi_chot, s.ctv_code) = %s 
                       OR COALESCE(s.nguoi_chot, s.ctv_code) = %s 
                       OR COALESCE(s.nguoi_chot, s.ctv_code) = %s
                       OR RIGHT(REGEXP_REPLACE(COALESCE(s.nguoi_chot, s.ctv_code), '[^0-9]', '', 'g'), 9) = %s)
                AND c.phone IS NOT NULL AND c.phone != ''
            ) AS all_services
            WHERE sdt IS NOT NULL AND sdt != ''
        """
        params = [ctv_code, ctv_code_normalized, ctv_code_with_zero, ctv_code_normalized,
                  ctv_code, ctv_code_normalized, ctv_code_with_zero, ctv_code_normalized]
        
        if search:
            client_query += " AND (ten_khach ILIKE %s OR sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Sort by date
        client_query += """
            GROUP BY sdt, ten_khach
            ORDER BY 
                MAX(first_date) DESC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(client_query, params)
        clients_raw = [dict(row) for row in cursor.fetchall()]
        
        clients = []
        for client_row in clients_raw:
            sdt = client_row['sdt']
            ten_khach = client_row['ten_khach']
            
            # Get services from BOTH tables for this client where CTV is the closer
            # Use normalized phone matching for nguoi_chot
            cursor.execute("""
                SELECT 
                    id,
                    dich_vu,
                    tong_tien,
                    tien_coc,
                    phai_dong,
                    ngay_hen_lam,
                    ngay_nhap_don,
                    trang_thai,
                    nguoi_chot,
                    source_type
                FROM (
                    SELECT 
                        id,
                        dich_vu,
                        tong_tien,
                        tien_coc,
                        phai_dong,
                        ngay_hen_lam,
                        ngay_nhap_don,
                        trang_thai,
                        nguoi_chot,
                        source as source_type
                    FROM khach_hang
                    WHERE sdt = %s AND (nguoi_chot = %s OR nguoi_chot = %s OR nguoi_chot = %s
                           OR RIGHT(REGEXP_REPLACE(nguoi_chot, '[^0-9]', '', 'g'), 9) = %s)
                    
                    UNION ALL
                    
                    SELECT 
                        s.id,
                        s.service_name as dich_vu,
                        s.tong_tien,
                        0 as tien_coc,
                        s.tong_tien as phai_dong,
                        s.date_scheduled as ngay_hen_lam,
                        s.date_entered as ngay_nhap_don,
                        s.status as trang_thai,
                        COALESCE(s.nguoi_chot, s.ctv_code) as nguoi_chot,
                        'nha_khoa' as source_type
                    FROM services s
                    JOIN customers c ON s.customer_id = c.id
                    WHERE c.phone = %s AND (COALESCE(s.nguoi_chot, s.ctv_code) = %s 
                           OR COALESCE(s.nguoi_chot, s.ctv_code) = %s 
                           OR COALESCE(s.nguoi_chot, s.ctv_code) = %s
                           OR RIGHT(REGEXP_REPLACE(COALESCE(s.nguoi_chot, s.ctv_code), '[^0-9]', '', 'g'), 9) = %s)
                ) AS all_svc
                ORDER BY 
                    ngay_nhap_don DESC
                LIMIT 5
            """, (sdt, ctv_code, ctv_code_normalized, ctv_code_with_zero, ctv_code_normalized,
                  sdt, ctv_code, ctv_code_normalized, ctv_code_with_zero, ctv_code_normalized))
            
            services_raw = [dict(row) for row in cursor.fetchall()]
            
            services = []
            for idx, svc in enumerate(services_raw):
                tien_coc = float(svc['tien_coc'] or 0)
                tong_tien = float(svc['tong_tien'] or 0)
                phai_dong = float(svc['phai_dong'] or 0)
                
                deposit_status = 'Da coc' if tien_coc > 0 else 'Chua coc'
                source_type = svc.get('source_type', 'tham_my')
                
                services.append({
                    'id': svc['id'],
                    'service_number': idx + 1,
                    'dich_vu': svc['dich_vu'] or '',
                    'tong_tien': tong_tien,
                    'tien_coc': tien_coc,
                    'phai_dong': phai_dong,
                    'ngay_nhap_don': svc['ngay_nhap_don'].strftime('%d/%m/%Y') if svc['ngay_nhap_don'] else None,
                    'ngay_hen_lam': svc['ngay_hen_lam'].strftime('%d/%m/%Y') if svc['ngay_hen_lam'] else None,
                    'trang_thai': svc['trang_thai'] or '',
                    'deposit_status': deposit_status,
                    'source_type': source_type,
                    'source': source_type
                })
            
            overall_status = services[0]['trang_thai'] if services else ''
            overall_deposit = services[0]['deposit_status'] if services else 'Chua coc'
            
            first_visit = client_row['first_visit_date']
            first_visit_str = first_visit.strftime('%d/%m/%Y') if first_visit else None
            
            referrer_ctv_code = None
            client_level = None
            
            cursor.execute("""
                SELECT nguoi_gioi_thieu, cap_bac FROM ctv WHERE ma_ctv = %s
            """, (ctv['ma_ctv'],))
            ctv_info = cursor.fetchone()
            if ctv_info:
                referrer_ctv_code = ctv_info.get('nguoi_gioi_thieu')
                client_level = ctv_info.get('cap_bac') or 'Cong tac vien'
            
            email = ''
            try:
                cursor.execute("""
                    SELECT email FROM customers WHERE phone = %s LIMIT 1
                """, (sdt,))
                email_row = cursor.fetchone()
                if email_row and email_row.get('email'):
                    email = email_row['email']
            except Error:
                pass
            
            clients.append({
                'ten_khach': ten_khach or '',
                'sdt': sdt or '',
                'email': email,
                'co_so': client_row['co_so'] or '',
                'first_visit_date': first_visit_str,
                'nguoi_chot': ctv['ma_ctv'],
                'referrer_ctv_code': referrer_ctv_code or '',
                'level': client_level or 'Cong tac vien',
                'service_count': client_row['service_count'],
                'overall_status': overall_status,
                'overall_deposit': overall_deposit,
                'services': services
            })
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'clients': clients,
            'total': len(clients)
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500
