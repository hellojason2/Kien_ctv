import os
import sys
from datetime import datetime
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# ══════════════════════════════════════════════════════════════════════════════
# REGISTER MODULAR BLUEPRINTS
# ══════════════════════════════════════════════════════════════════════════════
# 
# STRUCTURE MAP:
# - modules/admin_routes.py -> Admin Dashboard API endpoints
# - modules/ctv_routes.py -> CTV Portal API endpoints  
# - modules/auth.py -> Authentication & session management
# - modules/mlm_core.py -> MLM hierarchy & commission functions
# - modules/activity_logger.py -> Activity logging & tracking
#
# ══════════════════════════════════════════════════════════════════════════════

try:
    from modules.admin_routes import admin_bp
    from modules.ctv_routes import ctv_bp
    from modules.activity_logger import setup_request_logging
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(ctv_bp)
    
    # Setup activity logging middleware
    setup_request_logging(app)
    
    print("Modules loaded: admin_routes, ctv_routes, activity_logger")
except ImportError as e:
    print(f"WARNING: Could not load modules: {e}")
    print("Admin and CTV portal features will be unavailable.")

# Database configuration
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MLM CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
# 
# STRUCTURE MAP:
# 
# calculate_level(ctv_code, ancestor_code)
#   DOES: Find level distance between two CTVs in the referral hierarchy
#   INPUTS: ctv_code (descendant), ancestor_code (potential ancestor)
#   OUTPUTS: level (0-4) or None if not in hierarchy or >4 levels
#   FLOW: Traverse parent chain until ancestor is found or max level reached
#
# get_parent(cursor, ctv_code)
#   DOES: Get the immediate referrer of a CTV
#   INPUTS: cursor, ctv_code
#   OUTPUTS: nguoi_gioi_thieu (parent CTV code) or None
#
# build_hierarchy_tree(root_ctv_code)
#   DOES: Build complete hierarchy tree from a root CTV
#   INPUTS: root_ctv_code
#   OUTPUTS: Nested dictionary with all descendants up to level 4
#
# calculate_commissions(transaction_id, ctv_code, amount)
#   DOES: Calculate and store commissions for a transaction
#   INPUTS: transaction_id, ctv_code (who closed the deal), amount
#   OUTPUTS: List of commission records created
#   FLOW: Find ancestors -> Calculate each level's commission -> Store in DB
#
# ══════════════════════════════════════════════════════════════════════════════

# Commission rates by level (from the MLM diagram)
COMMISSION_RATES = {
    0: 0.25,      # 25% - self (doanh so ban than)
    1: 0.05,      # 5% - direct referral
    2: 0.025,     # 2.5% - level 2
    3: 0.0125,    # 1.25% - level 3
    4: 0.00625    # 0.625% - level 4 (max)
}

MAX_LEVEL = 4


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
        
        # Get root CTV info
        cursor.execute("SELECT ma_ctv, ten, sdt, email, cap_bac FROM ctv WHERE ma_ctv = %s;", (root_ctv_code,))
        root = cursor.fetchone()
        
        if not root:
            return None
        
        def get_children(parent_code, current_level):
            """Recursively get all children up to level 4"""
            if current_level > MAX_LEVEL:
                return []
            
            cursor.execute("""
                SELECT ma_ctv, ten, sdt, email, cap_bac 
                FROM ctv 
                WHERE nguoi_gioi_thieu = %s;
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
                    'commission_rate': COMMISSION_RATES.get(current_level, 0),
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
            'commission_rate': COMMISSION_RATES[0],
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
    
    Commission Rates:
    - Level 0 (self): 25%
    - Level 1: 5%
    - Level 2: 2.5%
    - Level 3: 1.25%
    - Level 4: 0.625%
    """
    should_close = False
    if connection is None:
        connection = get_db_connection()
        should_close = True
    
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build ancestor chain
        ancestors = build_ancestor_chain(cursor, ctv_code)
        
        commissions = []
        for ancestor_code, level in ancestors:
            rate = COMMISSION_RATES.get(level, 0)
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
    
    # Check for invalid referrers (referencing non-existent CTVs)
    for ctv in ctv_list:
        referrer = ctv.get('nguoi_gioi_thieu')
        if referrer and referrer not in ctv_codes:
            # Referrer might already exist in database - this is OK
            pass
    
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
# PUBLIC API ENDPOINTS (No authentication required)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/check-duplicate', methods=['POST'])
def check_duplicate():
    """
    PUBLIC: Check if a phone number already exists in the system
    
    DOES: Check phone against khach_hang table with specific duplicate conditions
    INPUTS: JSON with "phone" field
    OUTPUTS: { "is_duplicate": true/false, "message": "..." }
    
    Duplicate conditions (ANY = duplicate):
    1. trang_thai IN ('Da den lam', 'Da coc') AND ngay_hen_lam within last 360 days
    2. ngay_hen_lam >= TODAY AND < TODAY + 180 days
    3. ngay_nhap_don >= TODAY - 60 days
    
    IMPORTANT: Only returns "Trung" or "Khong trung" - NO customer details!
    """
    data = request.get_json()
    
    if not data or not data.get('phone'):
        return jsonify({
            'status': 'error',
            'message': 'Phone number is required'
        }), 400
    
    phone = data['phone'].strip()
    
    # Normalize phone number (remove spaces, dashes)
    phone = ''.join(c for c in phone if c.isdigit())
    
    # Strip leading zeros to match database format
    # Database stores: 988942155, User inputs: 0988942155
    phone = phone.lstrip('0')
    
    if len(phone) < 9:
        return jsonify({
            'status': 'error',
            'message': 'Invalid phone number'
        }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Check for duplicates using the three conditions from specification
        # Condition 1: trang_thai IN ('Da den lam', 'Da coc') AND within last 360 days
        # Condition 2: ngay_hen_lam >= TODAY AND < TODAY + 180 days
        # Condition 3: ngay_nhap_don >= TODAY - 60 days
        cursor.execute("""
            SELECT COUNT(*) > 0 AS is_duplicate
            FROM khach_hang
            WHERE sdt = %s
              AND (
                -- Condition 1: Status is completed or deposited AND within last 360 days
                (trang_thai IN ('Da den lam', 'Da coc')
                 AND ngay_hen_lam >= DATE_SUB(CURDATE(), INTERVAL 360 DAY))
                
                -- Condition 2: Future appointment within 180 days
                OR (ngay_hen_lam >= CURDATE() 
                    AND ngay_hen_lam < DATE_ADD(CURDATE(), INTERVAL 180 DAY))
                
                -- Condition 3: Order entry within last 60 days
                OR ngay_nhap_don >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
              );
        """, (phone,))
        
        result = cursor.fetchone()
        is_duplicate = bool(result[0]) if result else False
        
        cursor.close()
        connection.close()
        
        if is_duplicate:
            return jsonify({
                'status': 'success',
                'is_duplicate': True,
                'message': 'Trung - So dien thoai nay da co trong he thong'
            })
        else:
            return jsonify({
                'status': 'success',
                'is_duplicate': False,
                'message': 'Khong trung - So dien thoai nay chua co trong he thong'
            })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking duplicate: {str(e)}'
        }), 500


@app.route('/')
def index():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(BASE_DIR, 'dashboard.html')
    return send_file(dashboard_path)

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test database connection"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'success',
                'message': 'Database connected successfully',
                'database': db_name[0]
            })
        except Error as e:
            return jsonify({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to database'
        }), 500

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of all tables in the database"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        connection.close()
        return jsonify({
            'status': 'success',
            'tables': tables
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching tables: {str(e)}'
        }), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """Fetch customer data (id, name, email, phone)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check if customers table exists
        cursor.execute("SHOW TABLES LIKE 'customers';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            return jsonify({
                'status': 'success',
                'data': [],
                'message': 'Customers table not found. Run migrate_database.py first.'
            })
        
        # Fetch id, name, email, and phone from customers table
        cursor.execute("SELECT id, name, email, phone FROM customers ORDER BY id;")
        data = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'table': 'customers',
            'data': data
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching data: {str(e)}'
        }), 500

@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get full customer details by ID"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Fetch customer details
        cursor.execute("SELECT * FROM customers WHERE id = %s;", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'customer': customer
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching customer: {str(e)}'
        }), 500

@app.route('/api/customer/<int:customer_id>/services', methods=['GET'])
def get_customer_services(customer_id):
    """Get all services for a customer with CTV info"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # First get the customer details
        cursor.execute("SELECT * FROM customers WHERE id = %s;", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
        
        # Get all services for this customer with CTV name
        cursor.execute("""
            SELECT 
                s.id,
                s.service_name,
                s.date_entered,
                s.date_scheduled,
                s.amount,
                s.status,
                s.ctv_code,
                c.name as ctv_name,
                c.level as ctv_level
            FROM services s
            LEFT JOIN ctv_accounts c ON s.ctv_code = c.ctv_code
            WHERE s.customer_id = %s
            ORDER BY s.date_entered DESC;
        """, (customer_id,))
        services = cursor.fetchall()
        
        # Convert date objects to strings for JSON serialization
        for service in services:
            if service['date_entered']:
                service['date_entered'] = service['date_entered'].strftime('%Y-%m-%d')
            if service['date_scheduled']:
                service['date_scheduled'] = service['date_scheduled'].strftime('%Y-%m-%d')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'customer': customer,
            'services': services
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching services: {str(e)}'
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
# MLM API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/ctv/import', methods=['POST'])
def import_ctv():
    """
    Import CTV data with referral relationships
    
    DOES: Bulk import/update CTV records with nguoi_gioi_thieu relationships
    INPUTS: JSON array of CTV objects
    OUTPUTS: Success status with imported count
    
    Body: [
        {"ma_ctv": "CTV001", "ten": "Kien", "nguoi_gioi_thieu": null},
        {"ma_ctv": "CTV002", "ten": "Dung", "nguoi_gioi_thieu": "CTV001"}
    ]
    """
    data = request.get_json()
    
    if not data or not isinstance(data, list):
        return jsonify({
            'status': 'error',
            'message': 'Request body must be a JSON array of CTV objects'
        }), 400
    
    # Validate data
    is_valid, error_message = validate_ctv_data(data)
    if not is_valid:
        return jsonify({
            'status': 'error',
            'message': error_message
        }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        imported = 0
        updated = 0
        
        # Sort CTVs so that referrers are inserted before their referrals
        # This handles the foreign key constraint
        sorted_data = sorted(data, key=lambda x: 0 if not x.get('nguoi_gioi_thieu') else 1)
        
        for ctv in sorted_data:
            ma_ctv = ctv.get('ma_ctv')
            ten = ctv.get('ten')
            sdt = ctv.get('sdt')
            email = ctv.get('email')
            nguoi_gioi_thieu = ctv.get('nguoi_gioi_thieu')
            cap_bac = ctv.get('cap_bac', 'Bronze')
            
            # Check if CTV exists
            cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s;", (ma_ctv,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute("""
                    UPDATE ctv SET ten = %s, sdt = %s, email = %s, 
                    nguoi_gioi_thieu = %s, cap_bac = %s
                    WHERE ma_ctv = %s;
                """, (ten, sdt, email, nguoi_gioi_thieu, cap_bac, ma_ctv))
                updated += 1
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO ctv (ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac))
                imported += 1
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Imported {imported} new CTVs, updated {updated} existing CTVs',
            'imported': imported,
            'updated': updated
        })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error importing CTV data: {str(e)}'
        }), 500


@app.route('/api/ctv/<ctv_code>/hierarchy', methods=['GET'])
def get_ctv_hierarchy(ctv_code):
    """
    Get hierarchy tree from a CTV's perspective
    
    DOES: Build and return the referral tree showing all descendants
    INPUTS: ctv_code - the root CTV to build tree from
    OUTPUTS: Nested hierarchy structure with levels 0-4
    """
    tree = build_hierarchy_tree(ctv_code)
    
    if tree is None:
        return jsonify({
            'status': 'error',
            'message': f'CTV {ctv_code} not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'ctv_code': ctv_code,
        'hierarchy': tree
    })


@app.route('/api/ctv/<ctv_code>/levels', methods=['GET'])
def get_ctv_levels(ctv_code):
    """
    Get level matrix showing each CTV's level relative to the specified CTV
    
    DOES: Calculate level for all CTVs relative to the specified root
    INPUTS: ctv_code - the root CTV to calculate levels from
    OUTPUTS: Table of CTVs with their level relative to root
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verify CTV exists
        cursor.execute("SELECT ma_ctv, ten FROM ctv WHERE ma_ctv = %s;", (ctv_code,))
        root = cursor.fetchone()
        
        if not root:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': f'CTV {ctv_code} not found'
            }), 404
        
        # Get all CTVs
        cursor.execute("SELECT ma_ctv, ten, nguoi_gioi_thieu, cap_bac FROM ctv;")
        all_ctv = cursor.fetchall()
        
        # Calculate level for each CTV relative to root
        levels = []
        for ctv in all_ctv:
            level = calculate_level(cursor, ctv['ma_ctv'], ctv_code)
            if level is not None:
                levels.append({
                    'ma_ctv': ctv['ma_ctv'],
                    'ten': ctv['ten'],
                    'cap_bac': ctv['cap_bac'],
                    'level': level,
                    'commission_rate': COMMISSION_RATES.get(level, 0),
                    'commission_rate_percent': f"{COMMISSION_RATES.get(level, 0) * 100}%"
                })
        
        # Sort by level
        levels.sort(key=lambda x: x['level'])
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'root_ctv': {
                'ma_ctv': root['ma_ctv'],
                'ten': root['ten']
            },
            'levels': levels,
            'total_in_network': len(levels)
        })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error calculating levels: {str(e)}'
        }), 500


@app.route('/api/ctv/<ctv_code>/commissions', methods=['GET'])
def get_ctv_commissions(ctv_code):
    """
    Get commission report for a CTV
    
    DOES: Retrieve and summarize all commissions earned by a CTV
    INPUTS: ctv_code, optional query params: month (YYYY-MM), year (YYYY)
    OUTPUTS: Commission breakdown by level with totals
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verify CTV exists
        cursor.execute("SELECT ma_ctv, ten, cap_bac FROM ctv WHERE ma_ctv = %s;", (ctv_code,))
        ctv = cursor.fetchone()
        
        if not ctv:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': f'CTV {ctv_code} not found'
            }), 404
        
        # Build date filter
        month = request.args.get('month')  # YYYY-MM format
        year = request.args.get('year')    # YYYY format
        
        date_filter = ""
        params = [ctv_code]
        
        if month:
            date_filter = " AND DATE_FORMAT(c.created_at, '%Y-%m') = %s"
            params.append(month)
        elif year:
            date_filter = " AND YEAR(c.created_at) = %s"
            params.append(year)
        
        # Get commission summary by level
        cursor.execute(f"""
            SELECT 
                level,
                commission_rate,
                COUNT(*) as transaction_count,
                SUM(transaction_amount) as total_transaction_amount,
                SUM(commission_amount) as total_commission
            FROM commissions c
            WHERE ctv_code = %s {date_filter}
            GROUP BY level, commission_rate
            ORDER BY level;
        """, params)
        
        level_summary = cursor.fetchall()
        
        # Get detailed commission records
        cursor.execute(f"""
            SELECT 
                c.id,
                c.transaction_id,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at
            FROM commissions c
            WHERE ctv_code = %s {date_filter}
            ORDER BY c.created_at DESC
            LIMIT 100;
        """, params)
        
        details = cursor.fetchall()
        
        # Convert datetime objects
        for detail in details:
            if detail['created_at']:
                detail['created_at'] = detail['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate totals
        total_commission = sum(float(l['total_commission'] or 0) for l in level_summary)
        total_transactions = sum(int(l['transaction_count'] or 0) for l in level_summary)
        
        # Convert decimals for JSON
        for l in level_summary:
            l['commission_rate'] = float(l['commission_rate'])
            l['total_transaction_amount'] = float(l['total_transaction_amount'] or 0)
            l['total_commission'] = float(l['total_commission'] or 0)
        
        for d in details:
            d['commission_rate'] = float(d['commission_rate'])
            d['transaction_amount'] = float(d['transaction_amount'])
            d['commission_amount'] = float(d['commission_amount'])
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'ctv': {
                'ma_ctv': ctv['ma_ctv'],
                'ten': ctv['ten'],
                'cap_bac': ctv['cap_bac']
            },
            'filter': {
                'month': month,
                'year': year
            },
            'summary': {
                'total_commission': total_commission,
                'total_transactions': total_transactions,
                'by_level': level_summary
            },
            'recent_commissions': details
        })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching commissions: {str(e)}'
        }), 500


@app.route('/api/services', methods=['POST'])
def create_service():
    """
    Create a new service transaction with automatic commission calculation
    
    DOES: Create service record and calculate commissions for the CTV hierarchy
    INPUTS: JSON with customer_id, service_name, amount, ctv_code, etc.
    OUTPUTS: Created service with commission breakdown
    
    Body: {
        "customer_id": 1,
        "service_name": "Massage",
        "amount": 1000000,
        "ctv_code": "CTV005",
        "date_scheduled": "2025-01-15",
        "status": "Da coc"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Request body is required'
        }), 400
    
    # Validate required fields
    required = ['customer_id', 'service_name', 'amount', 'ctv_code']
    for field in required:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verify customer exists
        cursor.execute("SELECT id FROM customers WHERE id = %s;", (data['customer_id'],))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': f"Customer {data['customer_id']} not found"
            }), 404
        
        # Verify CTV exists
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s;", (data['ctv_code'],))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': f"CTV {data['ctv_code']} not found"
            }), 404
        
        # Insert service record
        cursor.execute("""
            INSERT INTO services 
            (customer_id, service_name, date_entered, date_scheduled, amount, status, ctv_code, nguoi_chot, tong_tien)
            VALUES (%s, %s, CURDATE(), %s, %s, %s, %s, %s, %s);
        """, (
            data['customer_id'],
            data['service_name'],
            data.get('date_scheduled'),
            data['amount'],
            data.get('status', 'Cho xu ly'),
            data['ctv_code'],
            data['ctv_code'],  # nguoi_chot is same as ctv_code
            data['amount']     # tong_tien
        ))
        
        service_id = cursor.lastrowid
        connection.commit()
        
        # Calculate commissions
        commissions = calculate_commissions(
            transaction_id=service_id,
            ctv_code=data['ctv_code'],
            amount=data['amount'],
            connection=connection
        )
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Service created and commissions calculated',
            'service': {
                'id': service_id,
                'customer_id': data['customer_id'],
                'service_name': data['service_name'],
                'amount': data['amount'],
                'ctv_code': data['ctv_code'],
                'status': data.get('status', 'Cho xu ly')
            },
            'commissions': commissions
        }), 201
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error creating service: {str(e)}'
        }), 500


@app.route('/api/commissions/transaction/<int:transaction_id>', methods=['GET'])
def get_transaction_commissions(transaction_id):
    """
    Get all commission records for a specific transaction
    
    DOES: Retrieve commission breakdown for a single transaction
    INPUTS: transaction_id
    OUTPUTS: List of all CTVs who earned commission from this transaction
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get commission records with CTV names
        cursor.execute("""
            SELECT 
                c.id,
                c.ctv_code,
                ctv.ten as ctv_name,
                c.level,
                c.commission_rate,
                c.transaction_amount,
                c.commission_amount,
                c.created_at
            FROM commissions c
            JOIN ctv ON c.ctv_code = ctv.ma_ctv
            WHERE c.transaction_id = %s
            ORDER BY c.level;
        """, (transaction_id,))
        
        commissions = cursor.fetchall()
        
        if not commissions:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': f'No commissions found for transaction {transaction_id}'
            }), 404
        
        # Convert for JSON
        for comm in commissions:
            comm['commission_rate'] = float(comm['commission_rate'])
            comm['transaction_amount'] = float(comm['transaction_amount'])
            comm['commission_amount'] = float(comm['commission_amount'])
            if comm['created_at']:
                comm['created_at'] = comm['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        total_commission = sum(c['commission_amount'] for c in commissions)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'transaction_id': transaction_id,
            'commissions': commissions,
            'total_commission': total_commission,
            'total_beneficiaries': len(commissions)
        })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching commissions: {str(e)}'
        }), 500


@app.route('/api/ctv', methods=['GET'])
def get_all_ctv():
    """
    Get all CTV accounts
    
    DOES: Retrieve list of all CTVs with their referral info
    OUTPUTS: List of CTV records
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                c.ma_ctv,
                c.ten,
                c.sdt,
                c.email,
                c.nguoi_gioi_thieu,
                p.ten as nguoi_gioi_thieu_name,
                c.cap_bac,
                c.created_at
            FROM ctv c
            LEFT JOIN ctv p ON c.nguoi_gioi_thieu = p.ma_ctv
            ORDER BY c.ma_ctv;
        """)
        
        ctv_list = cursor.fetchall()
        
        # Convert datetime
        for ctv in ctv_list:
            if ctv['created_at']:
                ctv['created_at'] = ctv['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'data': ctv_list,
            'total': len(ctv_list)
        })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching CTVs: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask server on http://localhost:4000")
    print("=" * 50)
    print("\nTesting database connection...")
    
    # Test connection on startup
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            print(f"SUCCESS: Connected to database '{db_name[0]}'")
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            if tables:
                print(f"Found {len(tables)} table(s):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("No tables found in database")
            cursor.close()
            connection.close()
        except Error as e:
            print(f"ERROR: {e}")
    else:
        print("ERROR: Failed to connect to database")
    
    print("\n" + "=" * 50)
    print("Server running. Access dashboard at:")
    print("http://localhost:4000")
    print("=" * 50 + "\n")
    
    port = int(os.environ.get('PORT', 4000))
    debug = os.environ.get('RAILWAY_ENVIRONMENT') is None
    app.run(host='0.0.0.0', port=port, debug=debug)

