import os
import sys
from datetime import datetime
from flask import Flask, jsonify, send_file, request, render_template, url_for
from flask_cors import CORS
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# App version for cache busting (update on each deploy)
APP_VERSION = "2026.01.25"

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ══════════════════════════════════════════════════════════════════════════════
# CACHE BUSTING CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    """
    Automatically append a version parameter to all static file URLs 
    for cache busting. Uses file modification time.
    """
    if endpoint == 'static' or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if app.static_folder:
                 if os.path.isabs(app.static_folder):
                     static_folder = app.static_folder
                 else:
                     static_folder = os.path.join(app.root_path, app.static_folder)
            
            file_path = os.path.join(static_folder, filename)
            if os.path.isfile(file_path):
                # Use file modification time as version
                values['v'] = int(os.stat(file_path).st_mtime)
            else:
                # Fallback to app version if file not found
                values['v'] = APP_VERSION

@app.context_processor
def inject_version():
    """Inject version into templates for manual usage if needed"""
    return dict(version=APP_VERSION)

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

@app.route('/favicon.ico')
def favicon():
    """Serve favicon with no-cache headers to force update"""
    print("Serving favicon.ico with no-cache headers")
    response = send_file(os.path.join(BASE_DIR, 'static', 'images', 'favicon.ico'), mimetype='image/vnd.microsoft.icon')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    """Serve the dashboard HTML with no-cache headers to prevent stale content"""
    from flask import make_response
    response = make_response(render_template('dashboard.html'))
    # Prevent browser caching of HTML - always fetch fresh content
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/ctv/signup')
def ctv_signup_page():
    """Serve the CTV signup page with no-cache headers"""
    from flask import make_response
    response = make_response(render_template('ctv_signup.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/booking')
def booking_page():
    """Serve the public booking/appointment page with no-cache headers"""
    from flask import make_response
    response = make_response(render_template('booking.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/test-login')
def test_login_page():
    """Serve the test login page for troubleshooting"""
    return render_template('test_login.html')

@app.route('/catalogue')
def catalogue_page():
    """Serve the service catalogue page (TMV + NK) with no-cache headers"""
    response = send_file(os.path.join(BASE_DIR, 'static', 'catalogue', 'index.html'))
    # Prevent browser caching - always fetch fresh content
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/bang-gia')
def pricing_page():
    """Serve the TMV pricing page with dynamic data from JSON"""
    import json
    pricing_data = {"categories": [], "updated_at": ""}
    try:
        data_path = os.path.join(app.static_folder, 'data', 'pricing.json')
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                pricing_data = json.load(f)
    except Exception as e:
        print(f"Error loading pricing data: {e}")
        
    return render_template('pricing.html', categories=pricing_data.get('categories', []), updated_at=pricing_data.get('updated_at'))

# Catalogue asset routes - serve pages and images for the React catalogue app
@app.route('/pages/<path:filename>')
def catalogue_pages(filename):
    """Serve catalogue page images"""
    return send_file(os.path.join(BASE_DIR, 'static', 'catalogue', 'pages', filename))

@app.route('/images/<path:filename>')
def catalogue_images(filename):
    """Serve catalogue images"""
    return send_file(os.path.join(BASE_DIR, 'static', 'catalogue', 'images', filename))

@app.route('/assets/<path:filename>')
def catalogue_assets(filename):
    """Serve catalogue JS/CSS assets"""
    return send_file(os.path.join(BASE_DIR, 'static', 'catalogue', 'assets', filename))

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
    
    if len(phone) < 8:
        return jsonify({'status': 'error', 'message': 'Invalid phone number'}), 400
    
    # Extract last 8 digits for fuzzy matching (handles leading zero variations)
    phone_suffix = phone[-8:]
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM khach_hang
                WHERE sdt LIKE %s
                  AND (
                    (trang_thai IN ('Đã đến làm', 'Đã cọc', 'Da den lam', 'Da coc')
                     AND ngay_hen_lam >= CURRENT_DATE - INTERVAL '360 days')
                    OR (ngay_hen_lam >= CURRENT_DATE 
                        AND ngay_hen_lam < CURRENT_DATE + INTERVAL '180 days')
                    OR ngay_nhap_don >= CURRENT_DATE - INTERVAL '60 days'
                  )
            ) AS is_duplicate;
        """, ('%' + phone_suffix,))
        
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
# ADMIN UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

import json
import time
from flask import Response, stream_with_context

@app.route('/api/admin/remove-duplicates', methods=['POST'])
def api_admin_remove_duplicates():
    # Helper to clean phone numbers for log safety
    def safe_phone(ph):
        if not ph: return "N/A"
        return f"{ph[:3]}***{ph[-3:]}" if len(ph) > 6 else ph

    def generate_logs():
        conn = None
        try:
            yield f"data: {json.dumps({'message': 'Initializing duplicate scan...', 'type': 'info'})}\n\n"
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Count duplicates based on User criteria: Phone, Date, Service, Time, Name, Source
            yield f"data: {json.dumps({'message': 'Scanning database for duplicates (Phone + Date + Time + Name + Service)...', 'type': 'info'})}\n\n"
            time.sleep(0.5)
            
            # Find duplicates
            cur.execute("""
                SELECT sdt, ngay_nhap_don, gio, dich_vu, ten_khach, source, COUNT(*) 
                FROM khach_hang 
                GROUP BY sdt, ngay_nhap_don, gio, dich_vu, ten_khach, source
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
            
            rows = cur.fetchall()
            duplicate_groups = len(rows)
            yield f"data: {json.dumps({'message': f'Found {duplicate_groups} groups of duplicates matching criteria.', 'type': 'warning' if duplicate_groups > 0 else 'success'})}\n\n"
            
            total_deleted = 0
            
            if duplicate_groups > 0:
                yield f"data: {json.dumps({'message': 'Starting cleanup process...', 'type': 'info'})}\n\n"
                
                # Delete logic: Keep the one with MIN(id) (oldest imported)
                cur.execute("""
                    DELETE FROM khach_hang a USING (
                        SELECT MIN(id) as id, sdt, ngay_nhap_don, gio, dich_vu, ten_khach, source
                        FROM khach_hang 
                        GROUP BY sdt, ngay_nhap_don, gio, dich_vu, ten_khach, source
                        HAVING COUNT(*) > 1
                    ) b
                    WHERE a.sdt = b.sdt 
                    AND (a.ngay_nhap_don = b.ngay_nhap_don OR (a.ngay_nhap_don IS NULL AND b.ngay_nhap_don IS NULL))
                    AND (a.gio = b.gio OR (a.gio IS NULL AND b.gio IS NULL))
                    AND (a.dich_vu = b.dich_vu OR (a.dich_vu IS NULL AND b.dich_vu IS NULL))
                    AND (a.ten_khach = b.ten_khach OR (a.ten_khach IS NULL AND b.ten_khach IS NULL))
                    AND a.source = b.source 
                    AND a.id <> b.id;
                """)
                
                total_deleted = cur.rowcount
                conn.commit()
                
                yield f"data: {json.dumps({'message': f'Successfully removed {total_deleted} redundant rows.', 'type': 'success'})}\n\n"
            else:
                yield f"data: {json.dumps({'message': 'No duplicates found. Database is clean.', 'type': 'success'})}\n\n"
            
            # Final integrity check
            yield f"data: {json.dumps({'message': 'Clean up process finished.', 'type': 'success', 'done': True, 'count': total_deleted})}\n\n"
            
        except Exception as e:
            if conn: conn.rollback()
            yield f"data: {json.dumps({'message': f'Error: {str(e)}', 'type': 'error'})}\n\n"
        finally:
            if conn: conn.close()
            
    return Response(stream_with_context(generate_logs()), mimetype='text/event-stream')

# ══════════════════════════════════════════════════════════════════════════════
# MAIN STARTUP
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 2002))
    print("=" * 50)
    print(f"Starting Flask server on http://localhost:{port}")
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
    print(f"http://localhost:{port}")
    print("=" * 50 + "\n")
    debug = os.environ.get('RAILWAY_ENVIRONMENT') is None
    
    # On macOS, port 5000 is often used by AirPlay Receiver (ControlCenter)
    # Try to kill it multiple times if we're using port 5000
    if port == 5000:
        import subprocess
        import time
        # Kill ControlCenter multiple times to ensure it stays dead
        for _ in range(3):
            try:
                subprocess.run(['killall', '-9', 'ControlCenter'], 
                             capture_output=True, timeout=1, check=False)
                time.sleep(0.3)
            except Exception:
                pass
        time.sleep(0.5)  # Final delay to let port be released
    
    app.run(host='0.0.0.0', port=port, debug=debug)
