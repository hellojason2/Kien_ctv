from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from ..db_pool import get_db_connection, return_db_connection
from ..redis_cache import (
    cache_hierarchy,
    get_cached_hierarchy
)

# Maximum level for commission calculations
MAX_LEVEL = 4

def get_parent(cursor, ctv_code):
    """
    DOES: Get the immediate referrer (parent) of a CTV
    """
    cursor.execute("SELECT nguoi_gioi_thieu FROM ctv WHERE ma_ctv = %s", (ctv_code,))
    result = cursor.fetchone()
    if not result:
        return None
    if isinstance(result, dict):
        return result.get('nguoi_gioi_thieu')
    return result[0] if result[0] else None

def calculate_level(cursor, ctv_code, ancestor_code):
    """
    DOES: Calculate the level distance between a CTV and a potential ancestor
    """
    if ctv_code == ancestor_code:
        return 0
    
    try:
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
    """
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
        from .commissions import get_commission_rates
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT ma_ctv, ten, sdt, email, cap_bac FROM ctv WHERE ma_ctv = %s", (root_ctv_code,))
        root = cursor.fetchone()
        
        if not root:
            cursor.close()
            if should_close:
                return_db_connection(connection)
            return None
        
        rates = get_commission_rates(connection)
        
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
        
        for node in all_nodes:
            if node['nguoi_gioi_thieu'] and node['nguoi_gioi_thieu'] in nodes_by_code:
                parent = nodes_by_code[node['nguoi_gioi_thieu']]
                parent['children'].append(nodes_by_code[node['ma_ctv']])
        
        tree = nodes_by_code.get(root_ctv_code)
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
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

def get_max_depth_below(ctv_code, connection=None):
    """
    DOES: Calculate the maximum depth/levels below a CTV
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            WITH RECURSIVE descendants AS (
                SELECT ma_ctv, 0 as level FROM ctv WHERE ma_ctv = %s
                
                UNION ALL
                
                SELECT c.ma_ctv, d.level + 1
                FROM ctv c
                INNER JOIN descendants d ON c.nguoi_gioi_thieu = d.ma_ctv
                WHERE d.level < %s
            )
            SELECT MAX(level) as max_depth
            FROM descendants
            WHERE level > 0
        """, (ctv_code, MAX_LEVEL))
        
        result = cursor.fetchone()
        max_depth = result[0] if result and result[0] is not None else 0
        
        cursor.close()
        if should_close:
            return_db_connection(connection)
        
        return max_depth
        
    except Error as e:
        print(f"Error getting max depth for CTV {ctv_code}: {e}")
        if should_close and connection:
            return_db_connection(connection)
        return 0

def get_network_stats(ctv_code, connection=None):
    """
    DOES: Get network statistics for a CTV
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return {'total': 0, 'by_level': {}}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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

