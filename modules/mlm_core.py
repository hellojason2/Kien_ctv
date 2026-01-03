"""
MLM Core Module
Contains all MLM hierarchy and commission calculation functions.
Optimized for PostgreSQL with recursive CTEs and Redis caching.

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
#   DOES: Load commission rates from database (with caching)
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
#   DOES: Build complete hierarchy tree from a CTV (with caching)
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
Updated: January 2, 2026 - Migrated to PostgreSQL with recursive CTEs and caching
"""

from psycopg2 import Error
from psycopg2.extras import RealDictCursor

# Use connection pool for better performance
from .db_pool import get_db_connection, return_db_connection

# Use Redis caching
from .redis_cache import (
    cache_hierarchy,
    get_cached_hierarchy,
    invalidate_hierarchy,
    cache_commission_rates,
    get_cached_commission_rates,
    invalidate_commission_cache
)

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
    DOES: Load commission rates from database (with Redis caching)
    INPUTS: Optional connection (creates new if not provided)
    OUTPUTS: Dict {level: rate} or DEFAULT_COMMISSION_RATES on failure
    
    OPTIMIZATION: Uses Redis cache with 1 hour TTL
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
        
        # Try hoa_hong_config first (new table)
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'hoa_hong_config')")
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT level, percent FROM hoa_hong_config ORDER BY level")
            rows = cursor.fetchall()
            
            if rows:
                rates = {}
                for row in rows:
                    level = int(row['level'])
                    # percent is stored as percentage (e.g., 25.0 for 25%)
                    rate = float(row['percent']) / 100
                    rates[level] = rate
                
                cursor.close()
                if should_close:
                    return_db_connection(connection)
                
                # Cache the rates
                cache_commission_rates(rates)
                return rates
        
        # Try commission_settings as fallback
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'commission_settings')")
        if cursor.fetchone()['exists']:
            cursor.execute("SELECT level, rate FROM commission_settings ORDER BY level")
            rows = cursor.fetchall()
            
            if rows:
                rates = {}
                for row in rows:
                    level = int(row['level'])
                    rate = float(row['rate'])
                    rates[level] = rate
                
                cursor.close()
                if should_close:
                    return_db_connection(connection)
                
                # Cache the rates
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


# ══════════════════════════════════════════════════════════════════════════════
# HIERARCHY FUNCTIONS (PostgreSQL Recursive CTEs)
# ══════════════════════════════════════════════════════════════════════════════

def get_parent(cursor, ctv_code):
    """
    DOES: Get the immediate referrer (parent) of a CTV
    CALLED BY: calculate_level(), build_ancestor_chain()
    INPUTS: cursor - database cursor, ctv_code - CTV to find parent for
    OUTPUTS: Parent CTV code or None
    """
    cursor.execute("SELECT nguoi_gioi_thieu FROM ctv WHERE ma_ctv = %s", (ctv_code,))
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
    
    OPTIMIZATION: Uses PostgreSQL recursive CTE instead of multiple queries
    """
    if ctv_code == ancestor_code:
        return 0
    
    try:
        # Use PostgreSQL recursive CTE for efficient hierarchy traversal
        cursor.execute("""
            WITH RECURSIVE chain AS (
                SELECT ma_ctv, nguoi_gioi_thieu, 0 as level
                FROM ctv
                WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, c.nguoi_gioi_thieu, chain.level + 1
                FROM ctv c
                INNER JOIN chain ON c.ma_ctv = chain.nguoi_gioi_thieu
                WHERE chain.level < %s
            )
            SELECT level FROM chain WHERE ma_ctv = %s
        """, (ctv_code, MAX_LEVEL + 1, ancestor_code))
        
        result = cursor.fetchone()
        if result:
            level = result[0] if isinstance(result, tuple) else result.get('level')
            return level if level <= MAX_LEVEL else None
        return None
        
    except Error:
        # Fallback to iterative approach
        level = 0
        current = ctv_code
        visited = set()
        
        while current and level <= MAX_LEVEL:
            if current in visited:
                return None
            visited.add(current)
            
            parent = get_parent(cursor, current)
            if not parent:
                return None
            
            level += 1
            if parent == ancestor_code:
                return level
            current = parent
        
        return None


def build_ancestor_chain(cursor, ctv_code, max_levels=MAX_LEVEL):
    """
    DOES: Build list of all ancestors up to max_levels deep
    CALLED BY: calculate_commissions()
    INPUTS: cursor, ctv_code, max_levels
    OUTPUTS: List of (ancestor_code, level) tuples
    
    OPTIMIZATION: Uses PostgreSQL recursive CTE
    """
    try:
        cursor.execute("""
            WITH RECURSIVE ancestors AS (
                SELECT ma_ctv, nguoi_gioi_thieu, 0 as level
                FROM ctv
                WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, c.nguoi_gioi_thieu, a.level + 1
                FROM ctv c
                INNER JOIN ancestors a ON c.ma_ctv = a.nguoi_gioi_thieu
                WHERE a.level < %s AND a.nguoi_gioi_thieu IS NOT NULL
            )
            SELECT ma_ctv, level FROM ancestors ORDER BY level
        """, (ctv_code, max_levels))
        
        results = cursor.fetchall()
        
        if results:
            ancestors = []
            for row in results:
                if isinstance(row, dict):
                    ancestors.append((row['ma_ctv'], row['level']))
                else:
                    ancestors.append((row[0], row[1]))
            return ancestors
        
        return [(ctv_code, 0)]
        
    except Error:
        # Fallback to iterative approach
        ancestors = [(ctv_code, 0)]
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
    
    OPTIMIZATION: 
    - Uses Redis cache with 15 min TTL
    - Uses PostgreSQL recursive CTE for descendants
    """
    # Check cache first
    cached_tree = get_cached_hierarchy(root_ctv_code)
    if cached_tree:
        return cached_tree
    
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get root CTV info
        cursor.execute("SELECT ma_ctv, ten, sdt, email, cap_bac FROM ctv WHERE ma_ctv = %s", (root_ctv_code,))
        root = cursor.fetchone()
        
        if not root:
            cursor.close()
            if should_close:
                return_db_connection(connection)
            return None
        
        # Get commission rates
        rates = get_commission_rates(connection)
        
        # Use recursive CTE to get all descendants with their levels
        cursor.execute("""
            WITH RECURSIVE hierarchy AS (
                SELECT ma_ctv, ten, sdt, email, cap_bac, nguoi_gioi_thieu, 0 as level
                FROM ctv
                WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, c.ten, c.sdt, c.email, c.cap_bac, c.nguoi_gioi_thieu, h.level + 1
                FROM ctv c
                INNER JOIN hierarchy h ON c.nguoi_gioi_thieu = h.ma_ctv
                WHERE h.level < %s
            )
            SELECT * FROM hierarchy ORDER BY level, ma_ctv
        """, (root_ctv_code, MAX_LEVEL))
        
        all_nodes = cursor.fetchall()
        
        # Build tree structure
        nodes_by_code = {}
        for node in all_nodes:
            node_data = {
                'ma_ctv': node['ma_ctv'],
                'ten': node['ten'],
                'sdt': node['sdt'],
                'email': node['email'],
                'cap_bac': node['cap_bac'],
                'level': node['level'],
                'commission_rate': rates.get(node['level'], 0),
                'children': []
            }
            nodes_by_code[node['ma_ctv']] = node_data
        
        # Link children to parents
        for node in all_nodes:
            if node['nguoi_gioi_thieu'] and node['nguoi_gioi_thieu'] in nodes_by_code:
                parent = nodes_by_code[node['nguoi_gioi_thieu']]
                parent['children'].append(nodes_by_code[node['ma_ctv']])
        
        # Get root tree
        tree = nodes_by_code.get(root_ctv_code)
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        # Cache the result
        if tree:
            cache_hierarchy(root_ctv_code, tree)
        
        return tree
        
    except Error as e:
        print(f"Error building hierarchy tree: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return None


def get_all_descendants(ctv_code, connection=None):
    """
    DOES: Get all CTV codes under a CTV (including self)
    CALLED BY: Access control in CTV routes
    INPUTS: ctv_code, optional connection
    OUTPUTS: Set of CTV codes
    
    OPTIMIZATION: Uses PostgreSQL recursive CTE
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {ctv_code}
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            WITH RECURSIVE descendants AS (
                SELECT ma_ctv FROM ctv WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv
                FROM ctv c
                INNER JOIN descendants d ON c.nguoi_gioi_thieu = d.ma_ctv
            )
            SELECT ma_ctv FROM descendants
        """, (ctv_code,))
        
        results = cursor.fetchall()
        descendants = {row[0] for row in results}
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        return descendants
        
    except Error as e:
        print(f"Error getting descendants: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return {ctv_code}


def get_network_stats(ctv_code, connection=None):
    """
    DOES: Get network statistics for a CTV
    INPUTS: ctv_code, optional connection
    OUTPUTS: Dict with network stats
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'total': 0, 'by_level': {}}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get descendant count by level using recursive CTE
        cursor.execute("""
            WITH RECURSIVE descendants AS (
                SELECT ma_ctv, 0 as level FROM ctv WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, d.level + 1
                FROM ctv c
                INNER JOIN descendants d ON c.nguoi_gioi_thieu = d.ma_ctv
                WHERE d.level < %s
            )
            SELECT level, COUNT(*) as count
            FROM descendants
            WHERE level > 0
            GROUP BY level
            ORDER BY level
        """, (ctv_code, MAX_LEVEL))
        
        results = cursor.fetchall()
        
        by_level = {}
        total = 0
        for row in results:
            level = row['level']
            count = row['count']
            by_level[level] = count
            total += count
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        return {
            'total': total,
            'by_level': by_level
        }
        
    except Error as e:
        print(f"Error getting network stats: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return {'total': 0, 'by_level': {}}


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
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get commission rates
        rates = get_commission_rates(connection)
        
        # Build ancestor chain
        ancestors = build_ancestor_chain(cursor, ctv_code)
        
        commissions = []
        for ancestor_code, level in ancestors:
            rate = rates.get(level, 0)
            commission_amount = float(amount) * rate
            
            # Insert commission record
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
        
        connection.commit()
        cursor.close()
        
        if should_close:
            return_db_connection(connection)
        
        # Invalidate commission cache
        invalidate_commission_cache()
        
        return commissions
        
    except Error as e:
        print(f"Error calculating commissions: {e}")
        if connection:
            connection.rollback()
        if should_close and connection:
            return_db_connection(connection)
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
