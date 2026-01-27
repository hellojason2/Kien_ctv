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

# ══════════════════════════════════════════════════════════════════════════════
# EMBEDDED BACKGROUND SYNC WORKER (for platforms without separate worker dyno)
# ══════════════════════════════════════════════════════════════════════════════

def start_embedded_sync_worker():
    """
    Start the sync worker as a background thread inside the main web process.
    This is triggered when gunicorn starts (via gunicorn hooks or first request).
    """
    import threading
    import os
    
    # Only start in production (gunicorn) - not in Flask debug mode
    if os.environ.get('FLASK_DEBUG') == '1' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("[SYNC] Skipping embedded worker in debug mode")
        return
    
    # Check if already started (avoid duplicate threads)
    if hasattr(app, '_sync_worker_started') and app._sync_worker_started:
        return
    
    def run_sync_loop():
        """Background sync loop - runs every 30 seconds"""
        import time
        import logging
        from datetime import datetime
        
        logger = logging.getLogger('sync_worker_embedded')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('[SYNC] %(asctime)s - %(message)s'))
            logger.addHandler(handler)
        
        logger.info("=" * 50)
        logger.info("Embedded Sync Worker Started")
        logger.info("=" * 50)
        
        # Wait for app to fully initialize
        time.sleep(10)
        
        cycle = 0
        consecutive_failures = 0
        SYNC_INTERVAL = 30
        MAX_FAILURES = 10
        
        def log_to_db(conn, level, message):
            """Helper to log to worker_logs table"""
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO worker_logs (level, message, created_at, source) VALUES (%s, %s, %s, 'sync_worker')",
                        (level, message, datetime.now())
                    )
                conn.commit()
            except Exception:
                pass
        
        while True:
            cycle += 1
            try:
                from modules.google_sync import GoogleSheetSync
                from modules.mlm_core import calculate_new_commissions_fast
                
                GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ')
                
                syncer = GoogleSheetSync()
                client = syncer.get_google_client()
                spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
                conn = syncer.get_db_connection()
                
                # Start cycle log
                log_to_db(conn, 'INFO', f'🔄 Cycle #{cycle} started')
                
                # Sync all tabs with detailed logging
                total_processed = 0
                total_new = 0
                total_skipped = 0
                tab_names = {'tham_my': 'Thẩm Mỹ', 'nha_khoa': 'Nha Khoa', 'gioi_thieu': 'Giới Thiệu'}
                
                for tab in ['tham_my', 'nha_khoa', 'gioi_thieu']:
                    try:
                        # Get sheet row count before sync
                        tab_display = tab_names.get(tab, tab)
                        
                        p, e = syncer.sync_tab_by_phone_matching(spreadsheet, conn, tab)
                        total_processed += p
                        
                        if p > 0:
                            total_new += p
                            log_to_db(conn, 'INFO', f'✅ {tab_display}: +{p} new rows synced')
                        else:
                            total_skipped += 1
                            log_to_db(conn, 'INFO', f'⏭️ {tab_display}: No new data, skipped')
                            
                    except Exception as tab_e:
                        log_to_db(conn, 'ERROR', f'❌ {tab_display}: Error - {str(tab_e)[:50]}')
                        logger.error(f"Tab {tab} error: {tab_e}")
                
                # Calculate commissions if new records
                if total_new > 0:
                    try:
                        calculate_new_commissions_fast(connection=conn)
                        log_to_db(conn, 'INFO', f'💰 Commissions recalculated for {total_new} new records')
                    except Exception as ce:
                        log_to_db(conn, 'WARNING', f'⚠️ Commission calc skipped: {str(ce)[:30]}')
                
                # Update heartbeat
                syncer.update_heartbeat(conn, total_processed)
                
                # Summary log
                if total_new > 0:
                    log_to_db(conn, 'INFO', f'✨ Cycle #{cycle} done: {total_new} new, {total_skipped} skipped')
                else:
                    log_to_db(conn, 'INFO', f'💤 Cycle #{cycle} done: All tabs up-to-date')
                
                conn.close()
                consecutive_failures = 0
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Cycle #{cycle} error: {e}")
                
                # Try to log error to DB
                try:
                    from modules.db_pool import get_db_connection as pool_conn
                    err_conn = pool_conn()
                    if err_conn:
                        log_to_db(err_conn, 'ERROR', f'❌ Cycle #{cycle} failed: {str(e)[:50]}')
                        err_conn.close()
                except:
                    pass
                
                if consecutive_failures >= MAX_FAILURES:
                    wait_time = 300
                else:
                    wait_time = min(SYNC_INTERVAL * (2 ** consecutive_failures), 300)
                
                time.sleep(wait_time)
                continue
            
            time.sleep(SYNC_INTERVAL)
    
    # Start the background thread
    thread = threading.Thread(target=run_sync_loop, daemon=True)
    thread.start()
    app._sync_worker_started = True
    print("[SYNC] Embedded sync worker thread started")

# Start worker when app is ready (gunicorn)
# Uses before_first_request equivalent for Flask
@app.before_request
def _start_sync_worker_once():
    """Start embedded sync worker on first request (gunicorn warmup)"""
    if not hasattr(app, '_sync_first_request_done'):
        app._sync_first_request_done = True
        start_embedded_sync_worker()

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
