from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from ..db_pool import get_db_connection, return_db_connection
from ..redis_cache import (
    cache_commission_rates,
    get_cached_commission_rates,
    invalidate_commission_cache
)
from .hierarchy import build_ancestor_chain

# Maximum level for commission calculations
MAX_LEVEL = 4

# Default commission rates (fallback if database is empty)
DEFAULT_COMMISSION_RATES = {
    0: 0.25,      # 25% - self
    1: 0.05,      # 5% - direct referral
    2: 0.025,     # 2.5% - level 2
    3: 0.0125,    # 1.25% - level 3
    4: 0.00625    # 0.625% - level 4
}

def get_commission_rates(connection=None):
    """
    DOES: Load commission rates from database (with Redis caching)
    INPUTS: Optional connection (creates new if not provided)
    OUTPUTS: Dict {level: rate} or DEFAULT_COMMISSION_RATES on failure
    """
    # Try cache first
    cached_rates = get_cached_commission_rates()
    if cached_rates:
        return cached_rates
    
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return DEFAULT_COMMISSION_RATES.copy()
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Try hoa_hong_config first
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'hoa_hong_config')")
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT level, percent, is_active FROM hoa_hong_config ORDER BY level")
            rows = cursor.fetchall()
            
            if rows:
                rates = {}
                for row in rows:
                    level = int(row['level'])
                    is_active = row.get('is_active', True)
                    # If level is inactive, set rate to 0 (no commission generated)
                    rate = float(row['percent']) / 100 if is_active else 0
                    rates[level] = rate
                
                cursor.close()
                if should_close:
                    return_db_connection(connection)
                
                cache_commission_rates(rates)
                return rates
        
        # Try commission_settings fallback
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'commission_settings')")
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT level, rate, is_active FROM commission_settings ORDER BY level")
            rows = cursor.fetchall()
            
            if rows:
                rates = {}
                for row in rows:
                    level = int(row['level'])
                    is_active = row.get('is_active', True)
                    # If level is inactive, set rate to 0 (no commission generated)
                    rate = float(row['rate']) if is_active else 0
                    rates[level] = rate
                
                cursor.close()
                if should_close:
                    return_db_connection(connection)
                
                cache_commission_rates(rates)
                return rates
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        return DEFAULT_COMMISSION_RATES.copy()
        
    except Error as e:
        print(f"Error loading commission rates: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return DEFAULT_COMMISSION_RATES.copy()

def calculate_commissions(transaction_id, ctv_code, amount, connection=None, commit=True):
    """
    DOES: Calculate and store commission records for a transaction
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Ensure idempotency by removing existing commissions for this transaction
        cursor.execute("DELETE FROM commissions WHERE transaction_id = %s", (transaction_id,))
        
        rates = get_commission_rates(connection)
        ancestors = build_ancestor_chain(cursor, ctv_code)
        
        commissions = []
        for ancestor_code, level in ancestors:
            rate = rates.get(level, 0)
            commission_amount = float(amount) * rate
            
            cursor.execute("""
                INSERT INTO commissions
                (transaction_id, ctv_code, level, commission_rate, transaction_amount, commission_amount)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (transaction_id, ancestor_code, level, rate, amount, commission_amount))
            
            result = cursor.fetchone()
            
            commissions.append({
                'id': result['id'] if result else None,
                'ctv_code': ancestor_code,
                'level': level,
                'commission_rate': rate,
                'transaction_amount': float(amount),
                'commission_amount': commission_amount
            })
        
        if commit:
            connection.commit()
            invalidate_commission_cache()
            
        cursor.close()
        
        if should_close:
            return_db_connection(connection)
        
        return commissions
    # ... (rest of function)
        
    except Error as e:
        print(f"Error calculating commissions: {e}")
        if connection:
            connection.rollback()
        if should_close and connection:
            return_db_connection(connection)
        return []

def calculate_commission_for_khach_hang(khach_hang_id, ctv_code, amount, connection=None, commit=True):
    """
    DOES: Calculate and store commission records for a khach_hang transaction
    """
    return calculate_commissions(-abs(khach_hang_id), ctv_code, amount, connection, commit=commit)

def calculate_commission_for_service(service_id, ctv_code, amount, connection=None, commit=True):
    """
    DOES: Calculate and store commission records for a service transaction
    """
    return calculate_commissions(service_id, ctv_code, amount, connection, commit=commit)

def recalculate_commissions_for_record(record_id, source_type, connection=None):
    """
    DOES: Recalculate commissions for a single record (khach_hang or service)
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        if source_type == 'khach_hang':
            transaction_id = -abs(record_id)
            cursor.execute("SELECT tong_tien, nguoi_chot FROM khach_hang WHERE id = %s", (record_id,))
        elif source_type == 'service':
            transaction_id = record_id
            cursor.execute("SELECT tong_tien, COALESCE(nguoi_chot, ctv_code) as ctv_code FROM services WHERE id = %s", (record_id,))
        else:
            return 0
        
        record = cursor.fetchone()
        if not record:
            return 0
        
        tong_tien = float(record.get('tong_tien') or 0)
        ctv_code = record.get('ctv_code') or record.get('nguoi_chot')
        
        if tong_tien <= 0 or not ctv_code:
            cursor.execute("DELETE FROM commissions WHERE transaction_id = %s", (transaction_id,))
            connection.commit()
            return 0
        
        cursor.execute("DELETE FROM commissions WHERE transaction_id = %s", (transaction_id,))
        calculate_commissions(transaction_id, ctv_code, tong_tien, connection)
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        return 1
        
    except Error as e:
        print(f"Error recalculating commissions for {source_type} {record_id}: {e}")
        if connection:
            connection.rollback()
        if should_close and connection:
            return_db_connection(connection)
        return 0

def recalculate_all_commissions(connection=None, batch_size=100):
    """
    DOES: Recalculate all commissions from khach_hang and services tables
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'khach_hang': 0, 'services': 0, 'errors': 0}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("DELETE FROM commissions")
        connection.commit()
        
        stats = {'khach_hang': 0, 'services': 0, 'errors': 0}
        
        cursor.execute("""
            SELECT id, tong_tien, nguoi_chot
            FROM khach_hang
            WHERE nguoi_chot IS NOT NULL 
            AND nguoi_chot != ''
            AND tong_tien > 0
            AND (trang_thai = 'Đã đến làm' OR trang_thai = 'Da den lam')
        """)
        kh_records = cursor.fetchall()
        
        for kh in kh_records:
            try:
                calculate_commission_for_khach_hang(kh['id'], kh['nguoi_chot'], kh['tong_tien'], connection)
                stats['khach_hang'] += 1
            except Exception:
                stats['errors'] += 1
        
        cursor.execute("""
            SELECT id, tong_tien, COALESCE(nguoi_chot, ctv_code) as ctv_code
            FROM services
            WHERE (nguoi_chot IS NOT NULL AND nguoi_chot != '')
            OR (ctv_code IS NOT NULL AND ctv_code != '')
            AND tong_tien > 0
        """)
        svc_records = cursor.fetchall()
        
        for svc in svc_records:
            try:
                calculate_commission_for_service(svc['id'], svc['ctv_code'], svc['tong_tien'], connection)
                stats['services'] += 1
            except Exception:
                stats['errors'] += 1
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        return stats
        
    except Error as e:
        print(f"Error recalculating all commissions: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return {'error': str(e)}

def calculate_missing_commissions(connection=None):
    """
    DOES: Find transactions that don't have commissions and calculate them
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'total': 0}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT kh.id, kh.tong_tien, kh.nguoi_chot
            FROM khach_hang kh
            LEFT JOIN commissions c ON c.transaction_id = -abs(kh.id)
            WHERE kh.nguoi_chot IS NOT NULL 
            AND kh.nguoi_chot != ''
            AND kh.tong_tien > 0
            AND (kh.trang_thai = 'Đã đến làm' OR kh.trang_thai = 'Da den lam')
            AND c.id IS NULL
        """)
        kh_missing = cursor.fetchall()
        
        count = 0
        for kh in kh_missing:
            calculate_commission_for_khach_hang(kh['id'], kh['nguoi_chot'], kh['tong_tien'], connection)
            count += 1
            
        cursor.execute("""
            SELECT s.id, s.tong_tien, COALESCE(s.nguoi_chot, s.ctv_code) as ctv_code
            FROM services s
            LEFT JOIN commissions c ON c.transaction_id = s.id AND s.id > 0
            WHERE (s.nguoi_chot IS NOT NULL AND s.nguoi_chot != '' OR s.ctv_code IS NOT NULL AND s.ctv_code != '')
            AND s.tong_tien > 0
            AND c.id IS NULL
        """)
        svc_missing = cursor.fetchall()
        
        for svc in svc_missing:
            calculate_commission_for_service(svc['id'], svc['ctv_code'], svc['tong_tien'], connection)
            count += 1
            
        cursor.close()
        if should_close:
            return_db_connection(connection)
            
        return {'total': count}
        
    except Error as e:
        print(f"Error calculating missing commissions: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return {'error': str(e)}

def calculate_new_commissions_fast(connection=None):
    """
    DOES: Incrementally calculate commissions only for new records since last run
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'total': 0}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Use commission_cache table
        cursor.execute("SELECT last_kh_max_id, last_svc_max_id FROM commission_cache WHERE cache_key = 'global'")
        cache_row = cursor.fetchone()
        
        if not cache_row:
            # Initialize if missing
            cursor.execute("INSERT INTO commission_cache (cache_key, last_kh_max_id, last_svc_max_id) VALUES ('global', 0, 0) RETURNING last_kh_max_id, last_svc_max_id")
            cache_row = cursor.fetchone()
            connection.commit()
            
        max_kh_id = cache_row['last_kh_max_id']
        max_svc_id = cache_row['last_svc_max_id']
        
        # New khach_hang records - ONLY where nguoi_chot exists in ctv table
        # Use phone normalization to handle leading zero variations (972020881 vs 0972020881)
        cursor.execute("""
            SELECT kh.id, kh.tong_tien, c.ma_ctv as nguoi_chot
            FROM khach_hang kh
            JOIN ctv c ON (
                LOWER(kh.nguoi_chot) = LOWER(c.ma_ctv)
                OR RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(c.ma_ctv, '[^0-9]', '', 'g'), 9)
            )
            WHERE kh.id > %s
            AND kh.tong_tien > 0
            AND (kh.trang_thai = 'Đã đến làm' OR kh.trang_thai = 'Da den lam')
            ORDER BY kh.id ASC
        """, (max_kh_id,))
        new_kh = cursor.fetchall()
        
        count = 0
        new_max_kh = max_kh_id
        for kh in new_kh:
            try:
                calculate_commission_for_khach_hang(kh['id'], kh['nguoi_chot'], kh['tong_tien'], connection, commit=False)
                new_max_kh = max(new_max_kh, kh['id'])
                count += 1
            except Exception as e:
                print(f"Error processing khach_hang {kh['id']}: {e}")
            
        # New service records - ONLY where ctv_code exists in ctv table
        # Use phone normalization to handle leading zero variations (972020881 vs 0972020881)
        cursor.execute("""
            SELECT s.id, s.tong_tien, c.ma_ctv as ctv_code
            FROM services s
            JOIN ctv c ON (
                LOWER(COALESCE(s.nguoi_chot, s.ctv_code)) = LOWER(c.ma_ctv)
                OR RIGHT(REGEXP_REPLACE(COALESCE(s.nguoi_chot, s.ctv_code), '[^0-9]', '', 'g'), 9) = RIGHT(REGEXP_REPLACE(c.ma_ctv, '[^0-9]', '', 'g'), 9)
            )
            WHERE s.id > %s
            AND s.tong_tien > 0
            ORDER BY s.id ASC
        """, (max_svc_id,))
        new_svc = cursor.fetchall()
        
        new_max_svc = max_svc_id
        for svc in new_svc:
            try:
                calculate_commission_for_service(svc['id'], svc['ctv_code'], svc['tong_tien'], connection, commit=False)
                new_max_svc = max(new_max_svc, svc['id'])
                count += 1
            except Exception as e:
                print(f"Error processing service {svc['id']}: {e}")
            
        # Update commission_cache
        if new_max_kh > max_kh_id or new_max_svc > max_svc_id:
            cursor.execute("""
                UPDATE commission_cache
                SET last_kh_max_id = %s, last_svc_max_id = %s, last_updated = CURRENT_TIMESTAMP
                WHERE cache_key = 'global'
            """, (new_max_kh, new_max_svc))
            
        connection.commit()
        invalidate_commission_cache()
        cursor.close()
        
        if should_close:
            return_db_connection(connection)
            
        return {'total': count}
        
    except Error as e:
        print(f"Error in fast commission calculation: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return {'error': str(e)}

def get_commission_cache_status():
    """
    DOES: Check how many transactions are missing from commissions table
    """
    connection = get_db_connection()
    if not connection: return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT COUNT(*) as count FROM commissions")
        comm_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM khach_hang WHERE nguoi_chot IS NOT NULL AND tong_tien > 0")
        kh_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM services WHERE tong_tien > 0")
        svc_count = cursor.fetchone()['count']
        
        cursor.close()
        return_db_connection(connection)
        
        return {
            'commissions_stored': comm_count,
            'total_source_records': kh_count + svc_count,
            'status': 'up_to_date' if comm_count >= (kh_count + svc_count) else 'needs_sync'
        }
    except Exception:
        return None

def get_active_levels(connection=None):
    """
    DOES: Get list of active commission levels from database
    INPUTS: Optional connection (creates new if not provided)
    OUTPUTS: List of active level numbers [0, 1, 2, ...]
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return list(range(MAX_LEVEL + 1))  # Return all levels as fallback
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Try hoa_hong_config first
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'hoa_hong_config')")
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT DISTINCT level FROM hoa_hong_config WHERE is_active = TRUE ORDER BY level")
            rows = cursor.fetchall()
            if rows:
                levels = [int(row['level']) for row in rows]
                cursor.close()
                if should_close:
                    return_db_connection(connection)
                return levels
        
        # Try commission_settings fallback
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'commission_settings')")
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT DISTINCT level FROM commission_settings WHERE is_active = TRUE ORDER BY level")
            rows = cursor.fetchall()
            if rows:
                levels = [int(row['level']) for row in rows]
                cursor.close()
                if should_close:
                    return_db_connection(connection)
                return levels
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        # Fallback: return all levels up to MAX_LEVEL
        return list(range(MAX_LEVEL + 1))
        
    except Error as e:
        print(f"Error getting active levels: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return list(range(MAX_LEVEL + 1))  # Return all levels as fallback

def remove_commissions_for_levels(levels, connection=None):
    """
    DOES: Remove commission records for specific levels (used when levels are disabled)
    INPUTS: List of level integers to remove
    OUTPUTS: Dict with count of deleted records
    """
    if not levels:
        return {'deleted': 0}
    
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'deleted': 0, 'error': 'Database connection failed'}
    
    try:
        cursor = connection.cursor()
        
        # Delete commissions for the specified levels
        cursor.execute(
            "DELETE FROM commissions WHERE level = ANY(%s)",
            (levels,)
        )
        deleted_count = cursor.rowcount
        
        connection.commit()
        cursor.close()
        
        if should_close:
            return_db_connection(connection)
        
        invalidate_commission_cache()
        
        return {'deleted': deleted_count}
        
    except Error as e:
        print(f"Error removing commissions for levels {levels}: {e}")
        if connection:
            connection.rollback()
        if should_close and connection:
            return_db_connection(connection)
        return {'deleted': 0, 'error': str(e)}