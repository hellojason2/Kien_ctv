"""
Activity Logger Module
Provides comprehensive activity logging for the CTV System.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# FUNCTIONS:
#
# Core Logging:
# - log_activity(event_type, user_type, user_id, details, ...)
#     DOES: Insert activity record into database
#     OUTPUTS: Log ID or None on failure
#
# - get_client_ip(request)
#     DOES: Extract real client IP (handles proxies/load balancers)
#     OUTPUTS: IP address string
#
# Specialized Loggers:
# - log_login_success(user_type, user_id)
# - log_login_failed(attempted_username, user_type)
# - log_logout(user_type, user_id)
# - log_api_call(user_type, user_id, endpoint, method, status_code)
#
# Flask Integration:
# - setup_request_logging(app)
#     DOES: Register before_request and after_request hooks
#
# Maintenance:
# - cleanup_old_logs(days=90)
#     DOES: Remove logs older than specified days
#
# Retrieval:
# - get_activity_logs(filters, page, per_page)
#     DOES: Query logs with filtering and pagination
#
# ══════════════════════════════════════════════════════════════════════════════
#
# EVENT TYPES:
# - login_success: Successful login
# - login_failed: Failed login attempt
# - logout: User logout
# - api_call: API endpoint accessed
# - ctv_created: New CTV account created
# - ctv_updated: CTV account modified
# - ctv_deleted: CTV account deactivated
# - commission_adjusted: Manual commission adjustment
# - data_export: Data exported (CSV, etc.)
# - settings_changed: System settings modified
#
# Created: December 29, 2025
# ══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g
import mysql.connector
from mysql.connector import Error

# Use connection pool for better performance
from .db_pool import get_db_connection

# Event types constants
EVENT_LOGIN_SUCCESS = 'login_success'
EVENT_LOGIN_FAILED = 'login_failed'
EVENT_LOGOUT = 'logout'
EVENT_API_CALL = 'api_call'
EVENT_CTV_CREATED = 'ctv_created'
EVENT_CTV_UPDATED = 'ctv_updated'
EVENT_CTV_DELETED = 'ctv_deleted'
EVENT_COMMISSION_ADJUSTED = 'commission_adjusted'
EVENT_DATA_EXPORT = 'data_export'
EVENT_SETTINGS_CHANGED = 'settings_changed'
EVENT_PAGE_VIEW = 'page_view'


# ══════════════════════════════════════════════════════════════════════════════
# IP ADDRESS UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def get_client_ip(req=None):
    """
    DOES: Extract the real client IP address from request
    Handles proxies, load balancers, and various header formats
    
    INPUTS: Flask request object (optional, uses global request if not provided)
    OUTPUTS: IP address string
    
    Priority:
    1. X-Forwarded-For header (first IP if multiple)
    2. X-Real-IP header
    3. CF-Connecting-IP (Cloudflare)
    4. Remote address
    """
    if req is None:
        req = request
    
    # Check X-Forwarded-For (may contain multiple IPs)
    forwarded_for = req.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        # Take the first IP (original client)
        ip = forwarded_for.split(',')[0].strip()
        if ip:
            return ip
    
    # Check X-Real-IP
    real_ip = req.headers.get('X-Real-IP', '')
    if real_ip:
        return real_ip.strip()
    
    # Check Cloudflare header
    cf_ip = req.headers.get('CF-Connecting-IP', '')
    if cf_ip:
        return cf_ip.strip()
    
    # Fall back to remote address
    return req.remote_addr or 'unknown'


def get_user_agent(req=None):
    """
    DOES: Extract user agent string from request
    OUTPUTS: User agent string or 'unknown'
    """
    if req is None:
        req = request
    return req.headers.get('User-Agent', 'unknown')


# ══════════════════════════════════════════════════════════════════════════════
# ASYNC LOGGING WITH QUEUE
# ══════════════════════════════════════════════════════════════════════════════

import threading
import queue

# Global log queue for async logging
_log_queue = queue.Queue()
_log_thread = None
_log_thread_stop = False


def _log_worker():
    """
    DOES: Background worker that processes log entries from the queue
    Runs in a separate thread to avoid blocking API responses
    """
    global _log_thread_stop
    while not _log_thread_stop:
        try:
            # Get log entry with timeout (allows checking stop flag)
            log_entry = _log_queue.get(timeout=1.0)
            if log_entry is None:  # Shutdown signal
                break
            
            # Process the log entry
            _sync_log_activity(**log_entry)
            _log_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Activity logger worker error: {e}")


def _start_log_thread():
    """Start the background logging thread if not already running"""
    global _log_thread
    if _log_thread is None or not _log_thread.is_alive():
        _log_thread = threading.Thread(target=_log_worker, daemon=True)
        _log_thread.start()


def _sync_log_activity(
    event_type,
    user_type=None,
    user_id=None,
    endpoint=None,
    method=None,
    status_code=None,
    details=None,
    ip_address=None,
    user_agent=None
):
    """
    DOES: Synchronously insert an activity log record (called by worker thread)
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        details_json = json.dumps(details) if details else None
        
        cursor.execute("""
            INSERT INTO activity_logs 
            (event_type, user_type, user_id, ip_address, user_agent, 
             endpoint, method, status_code, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            event_type, user_type, user_id, ip_address, user_agent,
            endpoint, method, status_code, details_json
        ))
        
        log_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()
        return log_id
    except Exception as e:
        print(f"Error logging activity: {e}")
        if connection:
            connection.close()
        return None


# ══════════════════════════════════════════════════════════════════════════════
# CORE LOGGING FUNCTION (ASYNC)
# ══════════════════════════════════════════════════════════════════════════════

def log_activity(
    event_type,
    user_type=None,
    user_id=None,
    endpoint=None,
    method=None,
    status_code=None,
    details=None,
    ip_address=None,
    user_agent=None
):
    """
    DOES: Queue an activity log record for async insertion
    
    OPTIMIZATION: Non-blocking - queues the log entry and returns immediately
    
    INPUTS:
    - event_type: Type of event (required)
    - user_type: 'admin' or 'ctv' (optional)
    - user_id: Username or ma_ctv (optional)
    - endpoint: API endpoint or page URL (optional)
    - method: HTTP method (optional)
    - status_code: HTTP response code (optional)
    - details: Dict with additional context (optional)
    - ip_address: Client IP (auto-detected if not provided)
    - user_agent: Browser info (auto-detected if not provided)
    
    OUTPUTS: True (queued successfully) or False
    """
    # Start background thread if needed
    _start_log_thread()
    
    # Auto-detect IP and user agent before queueing
    try:
        if ip_address is None:
            ip_address = get_client_ip()
        if user_agent is None:
            user_agent = get_user_agent()
    except RuntimeError:
        # Outside request context
        if ip_address is None:
            ip_address = 'system'
        if user_agent is None:
            user_agent = 'system'
    
    # Queue the log entry (non-blocking)
    try:
        _log_queue.put_nowait({
            'event_type': event_type,
            'user_type': user_type,
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'details': details,
            'ip_address': ip_address,
            'user_agent': user_agent
        })
        return True
    except queue.Full:
        # Queue is full, log synchronously as fallback
        return _sync_log_activity(
            event_type, user_type, user_id, endpoint, method,
            status_code, details, ip_address, user_agent
        )


# ══════════════════════════════════════════════════════════════════════════════
# SPECIALIZED LOGGING FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def log_login_success(user_type, user_id):
    """
    DOES: Log a successful login event
    CALLED BY: admin_login(), ctv_login() in auth.py
    """
    return log_activity(
        event_type=EVENT_LOGIN_SUCCESS,
        user_type=user_type,
        user_id=user_id,
        endpoint='/login',
        method='POST',
        status_code=200,
        details={'action': 'User logged in successfully'}
    )


def log_login_failed(attempted_username, user_type='unknown'):
    """
    DOES: Log a failed login attempt
    CALLED BY: admin_login(), ctv_login() in auth.py
    
    Security: Logs the attempted username for security monitoring
    """
    return log_activity(
        event_type=EVENT_LOGIN_FAILED,
        user_type=user_type,
        user_id=attempted_username,
        endpoint='/login',
        method='POST',
        status_code=401,
        details={'action': 'Failed login attempt', 'attempted_user': attempted_username}
    )


def log_logout(user_type, user_id):
    """
    DOES: Log a logout event
    CALLED BY: logout endpoints in admin_routes.py, ctv_routes.py
    """
    return log_activity(
        event_type=EVENT_LOGOUT,
        user_type=user_type,
        user_id=user_id,
        endpoint='/logout',
        method='POST',
        status_code=200,
        details={'action': 'User logged out'}
    )


def log_api_call(user_type, user_id, endpoint, method, status_code, details=None):
    """
    DOES: Log an API call
    CALLED BY: Flask after_request hook
    """
    return log_activity(
        event_type=EVENT_API_CALL,
        user_type=user_type,
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        details=details
    )


def log_ctv_created(admin_username, ctv_code, ctv_name):
    """
    DOES: Log when a new CTV is created
    CALLED BY: create_ctv() in admin_routes.py
    """
    return log_activity(
        event_type=EVENT_CTV_CREATED,
        user_type='admin',
        user_id=admin_username,
        endpoint='/api/admin/ctv',
        method='POST',
        status_code=201,
        details={
            'action': 'CTV created',
            'ctv_code': ctv_code,
            'ctv_name': ctv_name
        }
    )


def log_ctv_updated(admin_username, ctv_code, changes):
    """
    DOES: Log when a CTV is updated
    CALLED BY: update_ctv() in admin_routes.py
    """
    return log_activity(
        event_type=EVENT_CTV_UPDATED,
        user_type='admin',
        user_id=admin_username,
        endpoint=f'/api/admin/ctv/{ctv_code}',
        method='PUT',
        status_code=200,
        details={
            'action': 'CTV updated',
            'ctv_code': ctv_code,
            'changes': changes
        }
    )


def log_ctv_deleted(admin_username, ctv_code):
    """
    DOES: Log when a CTV is deactivated
    CALLED BY: deactivate_ctv() in admin_routes.py
    """
    return log_activity(
        event_type=EVENT_CTV_DELETED,
        user_type='admin',
        user_id=admin_username,
        endpoint=f'/api/admin/ctv/{ctv_code}',
        method='DELETE',
        status_code=200,
        details={
            'action': 'CTV deactivated',
            'ctv_code': ctv_code
        }
    )


def log_commission_adjusted(admin_username, commission_id, old_amount, new_amount):
    """
    DOES: Log when a commission is manually adjusted
    CALLED BY: adjust_commission() in admin_routes.py
    """
    return log_activity(
        event_type=EVENT_COMMISSION_ADJUSTED,
        user_type='admin',
        user_id=admin_username,
        endpoint=f'/api/admin/commissions/{commission_id}',
        method='PUT',
        status_code=200,
        details={
            'action': 'Commission adjusted',
            'commission_id': commission_id,
            'old_amount': old_amount,
            'new_amount': new_amount
        }
    )


def log_data_export(user_type, user_id, export_type, record_count):
    """
    DOES: Log when data is exported
    CALLED BY: export endpoints
    """
    return log_activity(
        event_type=EVENT_DATA_EXPORT,
        user_type=user_type,
        user_id=user_id,
        endpoint='/api/admin/export',
        method='GET',
        status_code=200,
        details={
            'action': 'Data exported',
            'export_type': export_type,
            'record_count': record_count
        }
    )


def log_settings_changed(admin_username, setting_name, old_value, new_value):
    """
    DOES: Log when system settings are changed
    CALLED BY: update_settings() in admin_routes.py
    """
    return log_activity(
        event_type=EVENT_SETTINGS_CHANGED,
        user_type='admin',
        user_id=admin_username,
        endpoint='/api/admin/settings',
        method='PUT',
        status_code=200,
        details={
            'action': 'Settings changed',
            'setting': setting_name,
            'old_value': old_value,
            'new_value': new_value
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
# FLASK MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

def setup_request_logging(app):
    """
    DOES: Register Flask before_request and after_request hooks for automatic logging
    CALLED BY: backend.py during app initialization
    
    Note: Only logs admin API calls (/api/admin/*) to avoid excessive logging
    """
    
    @app.before_request
    def before_request_logging():
        """Store request start time for duration calculation"""
        g.request_start_time = datetime.now()
    
    @app.after_request
    def after_request_logging(response):
        """Log API calls after request completion"""
        try:
            # Only log admin API calls
            if not request.path.startswith('/api/admin'):
                return response
            
            # Skip logging for activity logs endpoint to avoid infinite loop
            if '/activity-logs' in request.path:
                return response
            
            # Get user info from g (set by @require_admin decorator)
            user_type = getattr(g, 'user_type', None)
            user_id = None
            if hasattr(g, 'current_user'):
                if user_type == 'admin':
                    user_id = g.current_user.get('username')
                elif user_type == 'ctv':
                    user_id = g.current_user.get('ma_ctv')
            
            # Calculate request duration
            duration_ms = None
            if hasattr(g, 'request_start_time'):
                duration = datetime.now() - g.request_start_time
                duration_ms = int(duration.total_seconds() * 1000)
            
            # Log the API call
            log_api_call(
                user_type=user_type,
                user_id=user_id,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                details={'duration_ms': duration_ms} if duration_ms else None
            )
            
        except Exception as e:
            # Don't let logging errors affect the response
            print(f"Activity logging error: {e}")
        
        return response
    
    print("Activity logging middleware registered")


# ══════════════════════════════════════════════════════════════════════════════
# LOG RETRIEVAL
# ══════════════════════════════════════════════════════════════════════════════

def get_activity_logs(
    event_type=None,
    user_type=None,
    user_id=None,
    ip_address=None,
    date_from=None,
    date_to=None,
    search=None,
    page=1,
    per_page=50
):
    """
    DOES: Query activity logs with filtering and pagination
    
    INPUTS:
    - event_type: Filter by event type
    - user_type: Filter by user type (admin/ctv)
    - user_id: Filter by specific user
    - ip_address: Filter by IP address
    - date_from: Start date (datetime or string YYYY-MM-DD)
    - date_to: End date (datetime or string YYYY-MM-DD)
    - search: Search across user_id, endpoint, details
    - page: Page number (1-indexed)
    - per_page: Records per page
    
    OUTPUTS: Dict with logs, total count, and pagination info
    """
    connection = get_db_connection()
    if not connection:
        return {'logs': [], 'total': 0, 'page': page, 'per_page': per_page}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build query
        query = "SELECT * FROM activity_logs WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM activity_logs WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = %s"
            count_query += " AND event_type = %s"
            params.append(event_type)
        
        if user_type:
            query += " AND user_type = %s"
            count_query += " AND user_type = %s"
            params.append(user_type)
        
        if user_id:
            query += " AND user_id = %s"
            count_query += " AND user_id = %s"
            params.append(user_id)
        
        if ip_address:
            query += " AND ip_address = %s"
            count_query += " AND ip_address = %s"
            params.append(ip_address)
        
        if date_from:
            query += " AND timestamp >= %s"
            count_query += " AND timestamp >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND timestamp <= %s"
            count_query += " AND timestamp <= %s"
            # Add time to include the entire day
            if isinstance(date_to, str) and len(date_to) == 10:
                date_to = date_to + ' 23:59:59'
            params.append(date_to)
        
        if search:
            query += " AND (user_id LIKE %s OR endpoint LIKE %s OR ip_address LIKE %s)"
            count_query += " AND (user_id LIKE %s OR endpoint LIKE %s OR ip_address LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Add ordering and pagination
        query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        # Convert datetime objects and parse JSON details
        for log in logs:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            if log.get('details'):
                try:
                    if isinstance(log['details'], str):
                        log['details'] = json.loads(log['details'])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        cursor.close()
        connection.close()
        
        return {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
        
    except Error as e:
        print(f"Error retrieving activity logs: {e}")
        if connection:
            connection.close()
        return {'logs': [], 'total': 0, 'page': page, 'per_page': per_page}


def get_activity_stats():
    """
    DOES: Get summary statistics for activity logs
    
    OUTPUTS: Dict with various statistics
    """
    connection = get_db_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Logins today
        cursor.execute("""
            SELECT COUNT(*) as count FROM activity_logs 
            WHERE event_type = 'login_success' 
            AND DATE(timestamp) = %s;
        """, (today,))
        logins_today = cursor.fetchone()['count']
        
        # Failed logins today
        cursor.execute("""
            SELECT COUNT(*) as count FROM activity_logs 
            WHERE event_type = 'login_failed' 
            AND DATE(timestamp) = %s;
        """, (today,))
        failed_logins_today = cursor.fetchone()['count']
        
        # Unique IPs today
        cursor.execute("""
            SELECT COUNT(DISTINCT ip_address) as count FROM activity_logs 
            WHERE DATE(timestamp) = %s;
        """, (today,))
        unique_ips_today = cursor.fetchone()['count']
        
        # Total logs
        cursor.execute("SELECT COUNT(*) as count FROM activity_logs;")
        total_logs = cursor.fetchone()['count']
        
        # Events by type (last 7 days)
        cursor.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM activity_logs 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY event_type
            ORDER BY count DESC;
        """)
        events_by_type = cursor.fetchall()
        
        # Top IPs (last 7 days)
        cursor.execute("""
            SELECT ip_address, COUNT(*) as count 
            FROM activity_logs 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            AND ip_address IS NOT NULL AND ip_address != ''
            GROUP BY ip_address
            ORDER BY count DESC
            LIMIT 10;
        """)
        top_ips = cursor.fetchall()
        
        # Recent failed logins
        cursor.execute("""
            SELECT user_id, ip_address, timestamp 
            FROM activity_logs 
            WHERE event_type = 'login_failed'
            ORDER BY timestamp DESC
            LIMIT 10;
        """)
        recent_failed = cursor.fetchall()
        for log in recent_failed:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        return {
            'logins_today': logins_today,
            'failed_logins_today': failed_logins_today,
            'unique_ips_today': unique_ips_today,
            'total_logs': total_logs,
            'events_by_type': events_by_type,
            'top_ips': top_ips,
            'recent_failed_logins': recent_failed
        }
        
    except Error as e:
        print(f"Error getting activity stats: {e}")
        if connection:
            connection.close()
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# MAINTENANCE
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_old_logs(days=90):
    """
    DOES: Remove activity logs older than specified number of days
    CALLED BY: Scheduled maintenance task
    
    INPUTS: days - number of days to retain logs (default 90)
    OUTPUTS: Number of deleted records
    """
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            DELETE FROM activity_logs 
            WHERE timestamp < %s;
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Cleaned up {deleted_count} activity logs older than {days} days")
        return deleted_count
        
    except Error as e:
        print(f"Error cleaning up logs: {e}")
        if connection:
            connection.close()
        return 0


def get_suspicious_ips():
    """
    DOES: Find IPs that are logged into multiple different accounts
    
    OUTPUTS: Dict with IP addresses that have multiple user accounts
    Format: { 'ip_address': [{'user_id': ..., 'user_type': ..., 'last_login': ...}, ...] }
    """
    connection = get_db_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Find IPs with multiple accounts (last 7 days)
        cursor.execute("""
            SELECT ip_address, user_id, user_type, MAX(timestamp) as last_login
            FROM activity_logs 
            WHERE event_type IN ('login_success', 'api_call')
            AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            AND ip_address IS NOT NULL 
            AND ip_address != '' 
            AND ip_address != 'unknown'
            AND ip_address != 'system'
            AND user_id IS NOT NULL
            GROUP BY ip_address, user_id, user_type
            ORDER BY ip_address, last_login DESC;
        """)
        
        results = cursor.fetchall()
        
        # Group by IP
        ip_users = {}
        for row in results:
            ip = row['ip_address']
            if ip not in ip_users:
                ip_users[ip] = []
            ip_users[ip].append({
                'user_id': row['user_id'],
                'user_type': row['user_type'],
                'last_login': row['last_login'].strftime('%Y-%m-%d %H:%M:%S') if row['last_login'] else None
            })
        
        # Filter to only IPs with multiple users
        suspicious = {ip: users for ip, users in ip_users.items() if len(users) > 1}
        
        cursor.close()
        connection.close()
        
        return suspicious
        
    except Error as e:
        print(f"Error getting suspicious IPs: {e}")
        if connection:
            connection.close()
        return {}


def get_activity_logs_grouped(
    event_type=None,
    user_type=None,
    user_id=None,
    ip_address=None,
    date_from=None,
    date_to=None,
    search=None,
    page=1,
    per_page=50
):
    """
    DOES: Query activity logs grouped by user+IP combination
    
    OUTPUTS: Dict with grouped logs, suspicious IPs, and pagination info
    """
    connection = get_db_connection()
    if not connection:
        return {'groups': [], 'suspicious_ips': {}, 'total': 0, 'page': page, 'per_page': per_page}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build base query for grouping
        query = """
            SELECT 
                user_id, 
                user_type, 
                ip_address,
                COUNT(*) as log_count,
                MIN(timestamp) as first_activity,
                MAX(timestamp) as last_activity,
                GROUP_CONCAT(DISTINCT event_type) as event_types
            FROM activity_logs 
            WHERE 1=1
        """
        count_query = """
            SELECT COUNT(DISTINCT CONCAT(COALESCE(user_id, ''), '-', COALESCE(ip_address, ''))) as total 
            FROM activity_logs 
            WHERE 1=1
        """
        params = []
        
        if event_type:
            query += " AND event_type = %s"
            count_query += " AND event_type = %s"
            params.append(event_type)
        
        if user_type:
            query += " AND user_type = %s"
            count_query += " AND user_type = %s"
            params.append(user_type)
        
        if user_id:
            query += " AND user_id = %s"
            count_query += " AND user_id = %s"
            params.append(user_id)
        
        if ip_address:
            query += " AND ip_address = %s"
            count_query += " AND ip_address = %s"
            params.append(ip_address)
        
        if date_from:
            query += " AND timestamp >= %s"
            count_query += " AND timestamp >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND timestamp <= %s"
            count_query += " AND timestamp <= %s"
            if isinstance(date_to, str) and len(date_to) == 10:
                date_to = date_to + ' 23:59:59'
            params.append(date_to)
        
        if search:
            query += " AND (user_id LIKE %s OR endpoint LIKE %s OR ip_address LIKE %s)"
            count_query += " AND (user_id LIKE %s OR endpoint LIKE %s OR ip_address LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        # Get total count of groups
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Add grouping and pagination
        query += " GROUP BY user_id, user_type, ip_address ORDER BY last_activity DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        groups = cursor.fetchall()
        
        # Convert datetime objects
        for group in groups:
            if group.get('first_activity'):
                group['first_activity'] = group['first_activity'].strftime('%Y-%m-%d %H:%M:%S')
            if group.get('last_activity'):
                group['last_activity'] = group['last_activity'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        # Get suspicious IPs
        suspicious_ips = get_suspicious_ips()
        
        return {
            'groups': groups,
            'suspicious_ips': suspicious_ips,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
        
    except Error as e:
        print(f"Error retrieving grouped activity logs: {e}")
        if connection:
            connection.close()
        return {'groups': [], 'suspicious_ips': {}, 'total': 0, 'page': page, 'per_page': per_page}


def mask_old_ips(days=90):
    """
    DOES: Mask IP addresses in logs older than specified days for privacy
    Replaces last octet with 'xxx' (e.g., 192.168.1.xxx)
    
    INPUTS: days - logs older than this will have IPs masked
    OUTPUTS: Number of masked records
    """
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Mask IPv4 addresses
        cursor.execute("""
            UPDATE activity_logs 
            SET ip_address = CONCAT(
                SUBSTRING_INDEX(ip_address, '.', 3), 
                '.xxx'
            )
            WHERE timestamp < %s
            AND ip_address LIKE '%.%.%.%'
            AND ip_address NOT LIKE '%.xxx';
        """, (cutoff_date,))
        
        masked_count = cursor.rowcount
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Masked {masked_count} IP addresses older than {days} days")
        return masked_count
        
    except Error as e:
        print(f"Error masking IPs: {e}")
        if connection:
            connection.close()
        return 0

