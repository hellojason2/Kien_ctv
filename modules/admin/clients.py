from flask import jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..auth import require_admin
from ..db_pool import get_db_connection, return_db_connection

@admin_bp.route('/api/admin/clients-with-services', methods=['GET'])
@require_admin
def get_clients_with_services():
    """Get all clients with their services grouped - OPTIMIZED VERSION"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        search = request.args.get('search', '').strip()
        nguoi_chot = request.args.get('nguoi_chot', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        per_page = min(per_page, 100)
        offset = (page - 1) * per_page
        
        base_where = "WHERE sdt IS NOT NULL AND sdt != ''"
        params = []
        
        if search:
            base_where += " AND (ten_khach ILIKE %s OR sdt ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if nguoi_chot:
            base_where += " AND nguoi_chot = %s"
            params.append(nguoi_chot)
        
        client_query = f"""
            SELECT 
                sdt,
                ten_khach,
                MIN(co_so) as co_so,
                MIN(ngay_nhap_don) as first_visit_date,
                MAX(ngay_nhap_don) as last_visit_date,
                MIN(nguoi_chot) as nguoi_chot,
                COUNT(*) as service_count
            FROM khach_hang
            {base_where}
            GROUP BY sdt, ten_khach
            ORDER BY MAX(ngay_nhap_don) DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(client_query, params + [per_page, offset])
        clients_raw = [dict(row) for row in cursor.fetchall()]
        
        if not clients_raw:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'success',
                'clients': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0
                }
            })
        
        clients_dict = {}
        client_keys = []
        for row in clients_raw:
            key = (row['sdt'], row['ten_khach'])
            client_keys.append(key)
            
            first_visit = row['first_visit_date']
            first_visit_str = first_visit.strftime('%d/%m/%Y') if first_visit else None
            
            clients_dict[key] = {
                'ten_khach': row['ten_khach'] or '',
                'sdt': row['sdt'] or '',
                'co_so': row['co_so'] or '',
                'first_visit_date': first_visit_str,
                'nguoi_chot': row['nguoi_chot'] or '',
                'service_count': row['service_count'],
                'overall_status': '',
                'overall_deposit': 'Chua coc',
                'services': [],
                '_order': len(client_keys)
            }
        
        if client_keys:
            or_conditions = []
            flat_keys = []
            for sdt, ten_khach in client_keys:
                or_conditions.append('(sdt = %s AND ten_khach = %s)')
                flat_keys.extend([sdt, ten_khach])
            
            services_query = f"""
                SELECT * FROM (
                    SELECT 
                        id,
                        sdt,
                        ten_khach,
                        dich_vu,
                        tong_tien,
                        tien_coc,
                        phai_dong,
                        ngay_hen_lam,
                        ngay_nhap_don,
                        trang_thai,
                        nguoi_chot,
                        ROW_NUMBER() OVER (PARTITION BY sdt, ten_khach ORDER BY ngay_nhap_don DESC) as rn
                    FROM khach_hang
                    WHERE {' OR '.join(or_conditions)}
                ) ranked
                WHERE rn <= 3
                ORDER BY sdt, ten_khach, rn
            """
            
            cursor.execute(services_query, flat_keys)
            services_raw = [dict(row) for row in cursor.fetchall()]
            
            for svc in services_raw:
                key = (svc['sdt'], svc['ten_khach'])
                if key not in clients_dict:
                    continue
                
                tien_coc = float(svc['tien_coc'] or 0)
                tong_tien = float(svc['tong_tien'] or 0)
                phai_dong = float(svc['phai_dong'] or 0)
                deposit_status = 'Da coc' if tien_coc > 0 else 'Chua coc'
                
                service = {
                    'id': svc['id'],
                    'service_number': svc['rn'],
                    'dich_vu': svc['dich_vu'] or '',
                    'tong_tien': tong_tien,
                    'tien_coc': tien_coc,
                    'phai_dong': phai_dong,
                    'ngay_nhap_don': svc['ngay_nhap_don'].strftime('%d/%m/%Y') if svc['ngay_nhap_don'] else None,
                    'ngay_hen_lam': svc['ngay_hen_lam'].strftime('%d/%m/%Y') if svc['ngay_hen_lam'] else None,
                    'trang_thai': svc['trang_thai'] or '',
                    'deposit_status': deposit_status
                }
                
                clients_dict[key]['services'].append(service)
                
                if svc['rn'] == 1:
                    clients_dict[key]['overall_status'] = svc['trang_thai'] or ''
                    clients_dict[key]['overall_deposit'] = deposit_status
        
        if len(clients_raw) < per_page:
            total = offset + len(clients_raw)
            total_pages = page
        else:
            count_query = f"""
                SELECT COUNT(*) as total FROM (
                    SELECT 1 FROM khach_hang
                    {base_where}
                    GROUP BY sdt, ten_khach
                ) as grouped_clients
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page
        
        clients = sorted(clients_dict.values(), key=lambda x: x.pop('_order'))
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'clients': clients,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

