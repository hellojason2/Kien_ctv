import os
import sys
from datetime import datetime
from flask import Flask, jsonify, send_file, request, render_template
from flask_cors import CORS
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# App version for cache busting (update on each deploy)
APP_VERSION = "2026.01.04.3"

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Inject version into all templates for cache busting
@app.context_processor
def inject_version():
    return {'version': APP_VERSION}

# ══════════════════════════════════════════════════════════════════════════════
# REGISTER MODULAR BLUEPRINTS
# ══════════════════════════════════════════════════════════════════════════════

try:
    from modules.admin import admin_bp
    from modules.ctv import ctv_bp
    from modules.api import api_bp
    from modules.activity_logger import setup_request_logging
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(ctv_bp)
    app.register_blueprint(api_bp)
    
    # Setup activity logging middleware
    setup_request_logging(app)
    
    print("Modules loaded: admin, ctv, api, activity_logger")
except ImportError as e:
    print(f"WARNING: Could not load modules: {e}")
    print("Some features will be unavailable.")

# Database connection pool
from modules.db_pool import get_db_connection, return_db_connection

# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(BASE_DIR, 'dashboard.html')
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    return render_template('dashboard.html')

@app.route('/api/check-duplicate', methods=['POST'])
def check_duplicate():
    """
    PUBLIC: Check if a phone number already exists in the system
    """
    data = request.get_json()
    
    if not data or not data.get('phone'):
        return jsonify({'status': 'error', 'message': 'Phone number is required'}), 400
    
    phone = data['phone'].strip()
    phone = ''.join(c for c in phone if c.isdigit())
    phone = phone.lstrip('0')
    
    if len(phone) < 9:
        return jsonify({'status': 'error', 'message': 'Invalid phone number'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM khach_hang
                WHERE sdt = %s
                  AND (
                    (trang_thai IN ('Đã đến làm', 'Đã cọc', 'Da den lam', 'Da coc')
                     AND ngay_hen_lam >= CURRENT_DATE - INTERVAL '360 days')
                    OR (ngay_hen_lam >= CURRENT_DATE 
                        AND ngay_hen_lam < CURRENT_DATE + INTERVAL '180 days')
                    OR ngay_nhap_don >= CURRENT_DATE - INTERVAL '60 days'
                  )
            ) AS is_duplicate;
        """, (phone,))
        
        result = cursor.fetchone()
        is_duplicate = bool(result[0]) if result else False
        
        cursor.close()
        return_db_connection(connection)
        
        if is_duplicate:
            return jsonify({
                'status': 'success',
                'is_duplicate': True,
                'message': 'Trùng - Số điện thoại này đã có trong hệ thống'
            })
        else:
            return jsonify({
                'status': 'success',
                'is_duplicate': False,
                'message': 'Không trùng - Số điện thoại này chưa có trong hệ thống'
            })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Error checking duplicate: {str(e)}'}), 500

# ══════════════════════════════════════════════════════════════════════════════
# MAIN STARTUP
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask server on http://localhost:4000")
    print("=" * 50)
    print("\nTesting database connection...")
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"SUCCESS: Connected to database '{db_name[0]}'")
            
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()
            if tables:
                print(f"Found {len(tables)} table(s):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("No tables found in database")
            
            cursor.close()
            return_db_connection(connection)
        except Error as e:
            print(f"ERROR: {e}")
            if connection:
                return_db_connection(connection)
    else:
        print("ERROR: Failed to connect to database")
    
    print("\n" + "=" * 50)
    print("Server running. Access dashboard at:")
    print("http://localhost:4000")
    print("=" * 50 + "\n")
    
    port = int(os.environ.get('PORT', 4000))
    debug = os.environ.get('RAILWAY_ENVIRONMENT') is None
    app.run(host='0.0.0.0', port=port, debug=debug)
