"""
MLM Core Module
Contains all MLM hierarchy and commission calculation functions.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# CONSTANTS:
# - MAX_LEVEL = 4 (maximum commission depth)
#
# FUNCTIONS:
# 
# get_commission_rates()
#   DOES: Load commission rates from database
#   OUTPUTS: Dict {level: rate}
#
# get_parent(cursor, ctv_code)
#   DOES: Get immediate referrer of a CTV
#   OUTPUTS: Parent CTV code or None
#
# calculate_level(cursor, ctv_code, ancestor_code)
#   DOES: Find level distance between two CTVs
#   OUTPUTS: Level (0-4) or None if not in hierarchy
#
# build_ancestor_chain(cursor, ctv_code, max_levels)
#   DOES: Build list of all ancestors up to max_levels
#   OUTPUTS: List of (ancestor_code, level) tuples
#
# build_hierarchy_tree(root_ctv_code, connection)
#   DOES: Build complete hierarchy tree from a CTV
#   OUTPUTS: Nested dictionary structure
#
# get_all_descendants(ctv_code, connection)
#   DOES: Get all CTVs under a CTV (for access control)
#   OUTPUTS: Set of CTV codes
#
# calculate_commissions(transaction_id, ctv_code, amount, connection)
#   DOES: Calculate and store commissions for a transaction
#   OUTPUTS: List of commission records
#
# validate_ctv_data(ctv_list)
#   DOES: Validate CTV import data for circular references
#   OUTPUTS: (is_valid, error_message)
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
"""

from mysql.connector import Error

# Use connection pool for better performance
from .db_pool import get_db_connection

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


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION RATES
# ══════════════════════════════════════════════════════════════════════════════

def get_commission_rates(connection=None):
    """
    DOES: Load commission rates from database
    INPUTS: Optional connection (creates new if not provided)
    OUTPUTS: Dict {level: rate} or DEFAULT_COMMISSION_RATES on failure
    
    Loads rates from hoa_hong_config table (primary) or commission_settings (fallback).
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return DEFAULT_COMMISSION_RATES.copy()
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Try hoa_hong_config first (new table)
        cursor.execute("SHOW TABLES LIKE 'hoa_hong_config';")
        if cursor.fetchone():
            cursor.execute("SELECT level, percent FROM hoa_hong_config ORDER BY level;")
            rows = cursor.fetchall()
            
            if rows:
                rates = {}
                for row in rows:
                    # Convert percent to decimal (e.g., 25.0 -> 0.25)
                    rates[row['level']] = float(row['percent']) / 100
                cursor.close()
                if should_close:
                    connection.close()
                return rates
        
        # Fallback to commission_settings
        cursor.execute("SHOW TABLES LIKE 'commission_settings';")
        if cursor.fetchone():
            cursor.execute("SELECT level, rate FROM commission_settings ORDER BY level;")
            rows = cursor.fetchall()
            cursor.close()
            
            if should_close:
                connection.close()
            
            if rows:
                rates = {}
                for row in rows:
                    rates[row['level']] = float(row['rate'])
                return rates
        
        cursor.close()
        if should_close:
            connection.close()
        
        return DEFAULT_COMMISSION_RATES.copy()
        
    except Error:
        if should_close and connection:
            connection.close()
        return DEFAULT_COMMISSION_RATES.copy()


# ══════════════════════════════════════════════════════════════════════════════
# HIERARCHY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_parent(cursor, ctv_code):
    """
    DOES: Get the immediate referrer (parent) of a CTV
    CALLED BY: calculate_level(), build_ancestor_chain()
    INPUTS: cursor - database cursor, ctv_code - CTV to find parent for
    OUTPUTS: Parent CTV code or None
    """
    cursor.execute("SELECT nguoi_gioi_thieu FROM ctv WHERE ma_ctv = %s;", (ctv_code,))
    result = cursor.fetchone()
    if not result:
        return None
    # Handle both dictionary and tuple cursor results
    if isinstance(result, dict):
        return result.get('nguoi_gioi_thieu')
    return result[0] if result[0] else None


def calculate_level(cursor, ctv_code, ancestor_code):
    """
    DOES: Calculate the level distance between a CTV and a potential ancestor
    CALLED BY: build_hierarchy_tree(), calculate_commissions()
    INPUTS: cursor, ctv_code (descendant), ancestor_code (potential ancestor)
    OUTPUTS: level (0-4) or None if not in hierarchy or >4 levels
    
    Algorithm: Recursive tree traversal going up the parent chain
    Example: C -> B -> A means C is level 2 of A (2 steps up)
    """
    if ctv_code == ancestor_code:
        return 0
    
    level = 0
    current = ctv_code
    visited = set()
    
    while current and level <= MAX_LEVEL:
        if current in visited:
            return None  # Circular reference detected
        visited.add(current)
        
        parent = get_parent(cursor, current)
        if not parent:
            return None  # Reached root without finding ancestor
        
        level += 1
        if parent == ancestor_code:
            return level
        current = parent
    
    return None  # Level exceeds max (>4)


def build_ancestor_chain(cursor, ctv_code, max_levels=MAX_LEVEL):
    """
    DOES: Build list of all ancestors up to max_levels deep
    CALLED BY: calculate_commissions()
    INPUTS: cursor, ctv_code, max_levels
    OUTPUTS: List of (ancestor_code, level) tuples
    
    Example: For E with chain E->D->C->B->A:
    Returns: [(E, 0), (D, 1), (C, 2), (B, 3), (A, 4)]
    """
    ancestors = [(ctv_code, 0)]  # Self is level 0
    current = ctv_code
    visited = set([ctv_code])
    
    for level in range(1, max_levels + 1):
        parent = get_parent(cursor, current)
        if not parent or parent in visited:
            break
        visited.add(parent)
        ancestors.append((parent, level))
        current = parent
    
    return ancestors


def build_hierarchy_tree(root_ctv_code, connection=None):
    """
    DOES: Build complete hierarchy tree from a CTV's perspective
    CALLED BY: /api/ctv/<ctv_code>/hierarchy endpoint
    INPUTS: root_ctv_code - the CTV to build tree from
    OUTPUTS: Nested dictionary structure with descendants
    
    Structure: {
        'ma_ctv': 'CTV001',
        'ten': 'KienTT',
        'level': 0,
        'children': [
            {'ma_ctv': 'CTV002', 'ten': 'DungNTT', 'level': 1, 'children': [...]}
        ]
    }
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        commission_rates = get_commission_rates(connection)
        
        # Get root CTV info
        cursor.execute("""
            SELECT ma_ctv, ten, sdt, email, cap_bac 
            FROM ctv WHERE ma_ctv = %s;
        """, (root_ctv_code,))
        root = cursor.fetchone()
        
        if not root:
            cursor.close()
            if should_close:
                connection.close()
            return None
        
        def get_children(parent_code, current_level):
            """Recursively get all children up to level 4"""
            if current_level > MAX_LEVEL:
                return []
            
            cursor.execute("""
                SELECT ma_ctv, ten, sdt, email, cap_bac 
                FROM ctv 
                WHERE nguoi_gioi_thieu = %s AND (is_active = TRUE OR is_active IS NULL);
            """, (parent_code,))
            children = cursor.fetchall()
            
            result = []
            for child in children:
                child_node = {
                    'ma_ctv': child['ma_ctv'],
                    'ten': child['ten'],
                    'sdt': child['sdt'],
                    'email': child['email'],
                    'cap_bac': child['cap_bac'],
                    'level': current_level,
                    'commission_rate': commission_rates.get(current_level, 0),
                    'children': get_children(child['ma_ctv'], current_level + 1)
                }
                result.append(child_node)
            
            return result
        
        tree = {
            'ma_ctv': root['ma_ctv'],
            'ten': root['ten'],
            'sdt': root['sdt'],
            'email': root['email'],
            'cap_bac': root['cap_bac'],
            'level': 0,
            'commission_rate': commission_rates.get(0, 0.25),
            'children': get_children(root['ma_ctv'], 1)
        }
        
        cursor.close()
        if should_close:
            connection.close()
        
        return tree
        
    except Error as e:
        print(f"Error building hierarchy tree: {e}")
        if should_close and connection:
            connection.close()
        return None


def get_all_descendants(ctv_code, connection=None):
    """
    DOES: Get all CTVs under a CTV (including self) - used for access control
    CALLED BY: CTV routes for network filtering
    INPUTS: ctv_code
    OUTPUTS: Set of all CTV codes in the network
    
    OPTIMIZED: Loads all CTV relationships into memory once to avoid N+1 queries.
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {ctv_code}
    
    try:
        cursor = connection.cursor()
        
        # Fetch all active CTV relationships in one query
        cursor.execute("SELECT ma_ctv, nguoi_gioi_thieu FROM ctv WHERE is_active = TRUE OR is_active IS NULL")
        all_rows = cursor.fetchall()
        
        # Build adjacency list
        children_map = {}
        for row in all_rows:
            # Handle tuple result (ma_ctv, nguoi_gioi_thieu)
            child = row[0]
            parent = row[1]
            
            if parent:
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(child)
        
        # BFS traversal in memory
        descendants = {ctv_code}
        queue = [ctv_code]
        
        while queue:
            current = queue.pop(0)
            if current in children_map:
                for child in children_map[current]:
                    if child not in descendants:
                        descendants.add(child)
                        queue.append(child)
        
        cursor.close()
        if should_close:
            connection.close()
        
        return descendants
        
    except Error as e:
        print(f"Error getting descendants: {e}")
        if should_close and connection:
            connection.close()
        return {ctv_code}


# ══════════════════════════════════════════════════════════════════════════════
# COMMISSION CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

def calculate_commissions(transaction_id, ctv_code, amount, connection=None):
    """
    DOES: Calculate and store commission records for a transaction
    CALLED BY: POST /api/services endpoint (when creating transaction)
    INPUTS: transaction_id, ctv_code (who closed the deal), amount
    OUTPUTS: List of commission records created
    
    FLOW:
    1. Build ancestor chain from ctv_code up to 4 levels
    2. For each ancestor (including self):
       - Calculate commission based on level rate
       - Store commission record in database
    3. Return all created records
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        commission_rates = get_commission_rates(connection)
        
        # Build ancestor chain
        ancestors = build_ancestor_chain(cursor, ctv_code)
        
        commissions = []
        for ancestor_code, level in ancestors:
            rate = commission_rates.get(level, 0)
            commission_amount = float(amount) * rate
            
            # Insert commission record
            cursor.execute("""
                INSERT INTO commissions 
                (transaction_id, ctv_code, level, commission_rate, transaction_amount, commission_amount)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (transaction_id, ancestor_code, level, rate, amount, commission_amount))
            
            commissions.append({
                'ctv_code': ancestor_code,
                'level': level,
                'commission_rate': rate,
                'transaction_amount': float(amount),
                'commission_amount': commission_amount
            })
        
        connection.commit()
        cursor.close()
        
        if should_close:
            connection.close()
        
        return commissions
        
    except Error as e:
        print(f"Error calculating commissions: {e}")
        if should_close and connection:
            connection.close()
        return []


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_ctv_data(ctv_list):
    """
    DOES: Validate CTV import data for circular references and missing fields
    CALLED BY: POST /api/ctv/import endpoint
    INPUTS: List of CTV dictionaries
    OUTPUTS: (is_valid, error_message)
    """
    # Check for required fields
    for ctv in ctv_list:
        if not ctv.get('ma_ctv'):
            return False, "Missing required field: ma_ctv"
        if not ctv.get('ten'):
            return False, f"Missing required field: ten for CTV {ctv.get('ma_ctv')}"
    
    # Build reference map
    ctv_codes = {ctv['ma_ctv'] for ctv in ctv_list}
    
    # Check for circular references within the import data
    def has_cycle(start, visited, rec_stack, ref_map):
        visited.add(start)
        rec_stack.add(start)
        
        parent = ref_map.get(start)
        if parent:
            if parent in rec_stack:
                return True
            if parent not in visited:
                if has_cycle(parent, visited, rec_stack, ref_map):
                    return True
        
        rec_stack.remove(start)
        return False
    
    ref_map = {ctv['ma_ctv']: ctv.get('nguoi_gioi_thieu') for ctv in ctv_list}
    visited = set()
    
    for ctv_code in ctv_codes:
        if ctv_code not in visited:
            if has_cycle(ctv_code, visited, set(), ref_map):
                return False, f"Circular reference detected involving CTV {ctv_code}"
    
    return True, None


# ══════════════════════════════════════════════════════════════════════════════
# KHACH HANG COMMISSION CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

def calculate_khach_hang_commission(ctv_code, from_date=None, to_date=None, connection=None):
    """
    DOES: Calculate commission from khach_hang table with date filtering
    INPUTS: 
        - ctv_code: CTV to calculate for
        - from_date: Optional start date for ngay_hen_lam filter (YYYY-MM-DD)
        - to_date: Optional end date for ngay_hen_lam filter (YYYY-MM-DD)
    OUTPUTS: Dict with commission breakdown by level
    
    KEY CONDITIONS:
    - Only counts transactions where trang_thai = 'Da den lam'
    - Filters by ngay_hen_lam date range
    - Uses rates from hoa_hong_config table
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'error': 'Database connection failed'}
    
    try:
        cursor = connection.cursor(dictionary=True)
        commission_rates = get_commission_rates(connection)
        
        # Fetch all active CTV relationships in one query
        cursor.execute("SELECT ma_ctv, nguoi_gioi_thieu FROM ctv WHERE is_active = TRUE OR is_active IS NULL")
        all_rows = cursor.fetchall()
        
        # Build adjacency list
        children_map = {}
        for row in all_rows:
            child = row[0]
            parent = row[1]
            if parent:
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(child)
        
        # BFS to group descendants by level
        level_groups = {0: [], 1: [], 2: [], 3: [], 4: []}
        queue = [(ctv_code, 0)]
        visited = {ctv_code}
        
        while queue:
            current_code, current_level = queue.pop(0)
            
            if current_level <= MAX_LEVEL:
                level_groups[current_level].append(current_code)
                
                # Add children
                if current_code in children_map:
                    for child in children_map[current_code]:
                        if child not in visited:
                            visited.add(child)
                            queue.append((child, current_level + 1))

        result = {
            'by_level': [],
            'total_commission': 0,
            'total_transactions': 0
        }
        
        # Calculate for each level (0-4)
        for level in range(MAX_LEVEL + 1):
            level_ctv_list = level_groups[level]
            
            if not level_ctv_list:
                continue
            
            # Build query for this level
            placeholders = ','.join(['%s'] * len(level_ctv_list))
            query = f"""
                SELECT 
                    SUM(tong_tien) as total_revenue,
                    COUNT(*) as transaction_count
                FROM khach_hang
                WHERE nguoi_chot IN ({placeholders})
                AND trang_thai = 'Da den lam'
            """
            params = list(level_ctv_list)
            
            if from_date:
                query += " AND ngay_hen_lam >= %s"
                params.append(from_date)
            if to_date:
                query += " AND ngay_hen_lam <= %s"
                params.append(to_date)
            
            cursor.execute(query, params)
            level_data = cursor.fetchone()
            
            revenue = float(level_data['total_revenue'] or 0)
            count = int(level_data['transaction_count'] or 0)
            rate = commission_rates.get(level, 0)
            commission = revenue * rate
            
            if revenue > 0 or count > 0:
                result['by_level'].append({
                    'level': level,
                    'total_revenue': revenue,
                    'transaction_count': count,
                    'rate': rate * 100,  # Convert to percentage
                    'commission': commission
                })
                result['total_commission'] += commission
                result['total_transactions'] += count
        
        cursor.close()
        if should_close:
            connection.close()
        
        return result
        
    except Error as e:
        print(f"Error calculating khach_hang commission: {e}")
        if should_close and connection:
            connection.close()
        return {'error': str(e)}


def check_phone_duplicate(phone, connection=None):
    """
    DOES: Check if phone number is a duplicate based on business rules
    INPUTS: phone - phone number to check
    OUTPUTS: Dict with is_duplicate flag and message
    
    DUPLICATE CONDITIONS (ANY = duplicate):
    1. trang_thai IN ('Da den lam', 'Da coc')
    2. ngay_hen_lam >= TODAY AND < TODAY + 180 days
    3. ngay_nhap_don >= TODAY - 60 days
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'error': 'Database connection failed'}
    
    try:
        cursor = connection.cursor()
        
        # Normalize phone
        phone = ''.join(c for c in phone if c.isdigit())
        
        cursor.execute("""
            SELECT COUNT(*) > 0 AS is_duplicate
            FROM khach_hang
            WHERE sdt = %s
              AND (
                trang_thai IN ('Da den lam', 'Da coc')
                OR (ngay_hen_lam >= CURDATE() 
                    AND ngay_hen_lam < DATE_ADD(CURDATE(), INTERVAL 180 DAY))
                OR ngay_nhap_don >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
              );
        """, (phone,))
        
        result = cursor.fetchone()
        is_duplicate = bool(result[0]) if result else False
        
        cursor.close()
        if should_close:
            connection.close()
        
        return {
            'is_duplicate': is_duplicate,
            'message': 'Trung' if is_duplicate else 'Khong trung'
        }
        
    except Error as e:
        if should_close and connection:
            connection.close()
        return {'error': str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def count_network_members(ctv_code, connection=None):
    """
    DOES: Count total members in a CTV's network
    OUTPUTS: Integer count
    """
    descendants = get_all_descendants(ctv_code, connection)
    return len(descendants)


def get_network_stats(ctv_code, connection=None):
    """
    DOES: Get statistics for a CTV's network
    OUTPUTS: Dict with counts by level
    
    OPTIMIZED: Uses in-memory BFS to calculate levels and totals in one pass.
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'total': 0, 'by_level': {}}
    
    try:
        cursor = connection.cursor()
        
        # Fetch all active CTV relationships in one query
        cursor.execute("SELECT ma_ctv, nguoi_gioi_thieu FROM ctv WHERE is_active = TRUE OR is_active IS NULL")
        all_rows = cursor.fetchall()
        
        # Build adjacency list
        children_map = {}
        for row in all_rows:
            child = row[0]
            parent = row[1]
            
            if parent:
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(child)
        
        # BFS to calculate stats
        by_level = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        total_descendants = 0 # Excluding self
        
        # Queue stores (ctv_code, level)
        queue = [(ctv_code, 0)]
        visited = {ctv_code}
        
        while queue:
            current_code, current_level = queue.pop(0)
            
            # Update stats (skip level 0 for total count as it's self)
            if current_level > 0:
                total_descendants += 1
                if current_level <= MAX_LEVEL:
                    by_level[current_level] = by_level.get(current_level, 0) + 1
            elif current_level == 0:
                by_level[0] = 1 # Count self in level 0
            
            # Add children to queue
            if current_code in children_map:
                for child in children_map[current_code]:
                    if child not in visited:
                        visited.add(child)
                        queue.append((child, current_level + 1))
        
        cursor.close()
        if should_close:
            connection.close()
        
        return {
            'total': total_descendants + 1, # Include self in total to match original logic (len(descendants) included self)
            'by_level': by_level
        }
        
    except Error as e:
        print(f"Error getting network stats: {e}")
        if should_close and connection:
            connection.close()
        return {'total': 0, 'by_level': {}}

