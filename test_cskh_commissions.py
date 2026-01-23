"""
Test script for CSKH (Customer Care) Commission Logic

Tests the returning customer commission attribution:
1. First visit by staff - No commission
2. First visit by CTV - Normal commission
3. Return visit by staff - CSKH commission to original CTV
4. Return visit by different CTV - Normal commission to new CTV
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from psycopg2.extras import RealDictCursor
from modules.db_pool import get_db_connection, return_db_connection
from modules.mlm.commissions import (
    find_original_ctv_for_customer,
    count_customer_visits,
    calculate_cskh_commissions,
    calculate_cskh_commission_for_khach_hang,
    get_commission_rates
)


def test_find_original_ctv():
    """Test finding the original CTV for a customer"""
    print("\n" + "=" * 60)
    print("TEST: find_original_ctv_for_customer()")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        print("ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Find a customer with multiple visits and a CTV closer
        cursor.execute("""
            SELECT kh.sdt, kh.nguoi_chot, kh.ngay_hen_lam, kh.trang_thai,
                   c.ma_ctv IS NOT NULL as is_ctv
            FROM khach_hang kh
            LEFT JOIN ctv c ON (
                LOWER(kh.nguoi_chot) = LOWER(c.ma_ctv)
                OR RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9) = 
                   RIGHT(REGEXP_REPLACE(c.ma_ctv, '[^0-9]', '', 'g'), 9)
            )
            WHERE kh.sdt IS NOT NULL
            AND kh.trang_thai IN ('Đã đến làm', 'Da den lam')
            ORDER BY kh.ngay_hen_lam DESC
            LIMIT 10
        """)
        
        recent_visits = cursor.fetchall()
        print(f"\nRecent visits found: {len(recent_visits)}")
        
        for visit in recent_visits[:5]:
            print(f"  Phone: {visit['sdt']}, Closer: {visit['nguoi_chot']}, Is CTV: {visit['is_ctv']}, Date: {visit['ngay_hen_lam']}")
        
        # Test with a known phone
        if recent_visits:
            test_phone = recent_visits[0]['sdt']
            print(f"\nTesting with phone: {test_phone}")
            
            original_ctv = find_original_ctv_for_customer(cursor, test_phone)
            print(f"Original CTV found: {original_ctv}")
            
            visit_count = count_customer_visits(cursor, test_phone)
            print(f"Visit count (365 days): {visit_count}")
        
        cursor.close()
        return_db_connection(connection)
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return False


def test_staff_closed_records():
    """Find staff-closed records that could be CSKH candidates"""
    print("\n" + "=" * 60)
    print("TEST: Staff-closed records analysis")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        print("ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Find staff-closed records (nguoi_chot not in ctv table)
        cursor.execute("""
            SELECT kh.id, kh.sdt, kh.nguoi_chot, kh.tong_tien, kh.ngay_hen_lam
            FROM khach_hang kh
            LEFT JOIN ctv c ON (
                LOWER(kh.nguoi_chot) = LOWER(c.ma_ctv)
                OR RIGHT(REGEXP_REPLACE(kh.nguoi_chot, '[^0-9]', '', 'g'), 9) = 
                   RIGHT(REGEXP_REPLACE(c.ma_ctv, '[^0-9]', '', 'g'), 9)
            )
            WHERE c.ma_ctv IS NULL  -- Staff closed
            AND kh.tong_tien > 0
            AND kh.sdt IS NOT NULL
            AND kh.trang_thai IN ('Đã đến làm', 'Da den lam')
            ORDER BY kh.ngay_hen_lam DESC
            LIMIT 10
        """)
        
        staff_closed = cursor.fetchall()
        print(f"\nStaff-closed records found: {len(staff_closed)}")
        
        cskh_candidates = []
        for record in staff_closed:
            visit_count = count_customer_visits(cursor, record['sdt'])
            original_ctv = find_original_ctv_for_customer(cursor, record['sdt']) if visit_count >= 2 else None
            
            is_cskh = visit_count >= 2 and original_ctv is not None
            
            print(f"\n  ID: {record['id']}")
            print(f"  Phone: {record['sdt']}")
            print(f"  Closer: {record['nguoi_chot']} (STAFF)")
            print(f"  Amount: {record['tong_tien']:,.0f}")
            print(f"  Visit count: {visit_count}")
            print(f"  Original CTV: {original_ctv}")
            print(f"  CSKH eligible: {'YES' if is_cskh else 'NO'}")
            
            if is_cskh:
                cskh_candidates.append({
                    'id': record['id'],
                    'phone': record['sdt'],
                    'amount': record['tong_tien'],
                    'original_ctv': original_ctv
                })
        
        print(f"\n\nCSKH candidates found: {len(cskh_candidates)}")
        
        cursor.close()
        return_db_connection(connection)
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            return_db_connection(connection)
        return False


def test_commission_rates():
    """Check current commission rates"""
    print("\n" + "=" * 60)
    print("TEST: Commission rates")
    print("=" * 60)
    
    rates = get_commission_rates()
    print("\nCurrent commission rates:")
    for level, rate in sorted(rates.items()):
        print(f"  Level {level}: {rate*100:.2f}%")
    
    print("\nCSKH commission flow:")
    print(f"  Original CTV gets Level 1 rate: {rates.get(1, 0.04)*100:.2f}%")
    print(f"  Original CTV's upline gets Level 2 rate: {rates.get(2, 0.02)*100:.2f}%")
    print(f"  Chain STOPS after 2 levels")
    
    return True


def show_commission_summary():
    """Show summary of commissions by type"""
    print("\n" + "=" * 60)
    print("Commission Summary by Type")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        print("ERROR: Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COALESCE(commission_type, 'direct') as type,
                COUNT(*) as count,
                SUM(commission_amount) as total_amount
            FROM commissions
            GROUP BY commission_type
            ORDER BY commission_type
        """)
        
        results = cursor.fetchall()
        print("\nCommission breakdown:")
        for row in results:
            print(f"  {row['type']}: {row['count']} records, {row['total_amount']:,.0f} VND")
        
        cursor.close()
        return_db_connection(connection)
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        if connection:
            return_db_connection(connection)
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("CSKH COMMISSION LOGIC TEST SUITE")
    print("=" * 60)
    
    # Run tests
    test_commission_rates()
    test_find_original_ctv()
    test_staff_closed_records()
    show_commission_summary()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)
