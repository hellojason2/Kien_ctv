"""
Activity Logger Module
Provides comprehensive activity logging for the CTV System.
Updated for PostgreSQL.

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

Created: December 29, 2025
Updated: January 2, 2026 - Migrated to PostgreSQL
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g
from psycopg2 import Error
from psycopg2.extras import RealDictCursor, Json

# Use connection pool for better performance
from .db_pool import get_db_connection, return_db_connection

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
    """
    if req is None:
        req = request
    
    forwarded_for = req.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        ip = forwarded_for.split(',')[0].strip()
        if ip:
            return ip
    
    real_ip = req.headers.get('X-Real-IP', '')
    if real_ip:
        return real_ip.strip()
    
    cf_ip = req.headers.get('CF-Connecting-IP', '')
    if cf_ip:
        return cf_ip.strip()
    
    return req.remote_addr or 'unknown'


def get_user_agent(req=None):
    """
    DOES: Extract user agent string from request
    """
    if req is None:
        req = request
    return req.headers.get('User-Agent', 'unknown')


# ══════════════════════════════════════════════════════════════════════════════
# ASYNC LOGGING WITH QUEUE
# ══════════════════════════════════════════════════════════════════════════════

import threading
import queue

_log_queue = queue.Queue()
_log_thread = None
_log_thread_stop = False


def _log_worker():
    """Background worker that processes log entries from the queue"""
    global _log_thread_stop
    while not _log_thread_stop:
        try:
            log_entry = _log_queue.get(timeout=1.0)
            if log_entry is None:
                break
            
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
    """Synchronously insert an activity log record"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO activity_logs 
            (event_type, user_type, user_id, ip_address, user_agent, 
             endpoint, method, status_code, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            event_type, user_type, user_id, ip_address, user_agent,
            endpoint, method, status_code, Json(details) if details else None
        ))
        
        result = cursor.fetchone()
        log_id = result[0] if result else None
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        return log_id
    except Exception as e:
        print(f"Error logging activity: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
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
    """Queue an activity log record for async insertion"""
    _start_log_thread()
    
    try:
        if ip_address is None:
            ip_address = get_client_ip()
        if user_agent is None:
            user_agent = get_user_agent()
    except RuntimeError:
        if ip_address is None:
            ip_address = 'system'
        if user_agent is None:
            user_agent = 'system'
    
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
        return _sync_log_activity(
            event_type, user_type, user_id, endpoint, method,
            status_code, details, ip_address, user_agent
        )


# ══════════════════════════════════════════════════════════════════════════════
# SPECIALIZED LOGGING FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def log_login_success(user_type, user_id):
    """Log a successful login event"""
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
    """Log a failed login attempt"""
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
    """Log a logout event"""
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
    """Log an API call"""
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
    """Log when a new CTV is created"""
    return log_activity(
        event_type=EVENT_CTV_CREATED,
        user_type='admin',
        user_id=admin_username,
        endpoint='/api/admin/ctv',
        method='POST',
        status_code=201,
        details={'action': 'CTV created', 'ctv_code': ctv_code, 'ctv_name': ctv_name}
    )


def log_ctv_updated(admin_username, ctv_code, changes):
    """Log when a CTV is updated"""
    return log_activity(
        event_type=EVENT_CTV_UPDATED,
        user_type='admin',
        user_id=admin_username,
        endpoint=f'/api/admin/ctv/{ctv_code}',
        method='PUT',
        status_code=200,
        details={'action': 'CTV updated', 'ctv_code': ctv_code, 'changes': changes}
    )


def log_ctv_deleted(admin_username, ctv_code):
    """Log when a CTV is deactivated"""
    return log_activity(
        event_type=EVENT_CTV_DELETED,
        user_type='admin',
        user_id=admin_username,
        endpoint=f'/api/admin/ctv/{ctv_code}',
        method='DELETE',
        status_code=200,
        details={'action': 'CTV deactivated', 'ctv_code': ctv_code}
    )


def log_commission_adjusted(admin_username, commission_id, old_amount, new_amount):
    """Log when a commission is manually adjusted"""
    return log_activity(
        event_type=EVENT_COMMISSION_ADJUSTED,
        user_type='admin',
        user_id=admin_username,
        endpoint=f'/api/admin/commissions/{commission_id}',
        method='PUT',
        status_code=200,
        details={'action': 'Commission adjusted', 'commission_id': commission_id, 'old_amount': old_amount, 'new_amount': new_amount}
    )


def log_data_export(user_type, user_id, export_type, record_count):
    """Log when data is exported"""
    return log_activity(
        event_type=EVENT_DATA_EXPORT,
        user_type=user_type,
        user_id=user_id,
        endpoint='/api/admin/export',
        method='GET',
        status_code=200,
        details={'action': 'Data exported', 'export_type': export_type, 'record_count': record_count}
    )


def log_settings_changed(admin_username, setting_name, old_value, new_value):
    """Log when system settings are changed"""
    return log_activity(
        event_type=EVENT_SETTINGS_CHANGED,
        user_type='admin',
        user_id=admin_username,
        endpoint='/api/admin/settings',
        method='PUT',
        status_code=200,
        details={'action': 'Settings changed', 'setting': setting_name, 'old_value': old_value, 'new_value': new_value}
    )


# ══════════════════════════════════════════════════════════════════════════════
# FLASK MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

def setup_request_logging(app):
    """Register Flask request logging hooks"""
    
    @app.before_request
    def before_request_logging():
        g.request_start_time = datetime.now()
    
    @app.after_request
    def after_request_logging(response):
        try:
            if not request.path.startswith('/api/admin'):
                return response
            
            if '/activity-logs' in request.path:
                return response
            
            user_type = getattr(g, 'user_type', None)
            user_id = None
            if hasattr(g, 'current_user'):
                if user_type == 'admin':
                    user_id = g.current_user.get('username')
                elif user_type == 'ctv':
                    user_id = g.current_user.get('ma_ctv')
            
            duration_ms = None
            if hasattr(g, 'request_start_time'):
                duration = datetime.now() - g.request_start_time
                duration_ms = int(duration.total_seconds() * 1000)
            
            log_api_call(
                user_type=user_type,
                user_id=user_id,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                details={'duration_ms': duration_ms} if duration_ms else None
            )
            
        except Exception as e:
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
    """Query activity logs with filtering and pagination"""
    connection = get_db_connection()
    if not connection:
        return {'logs': [], 'total': 0, 'page': page, 'per_page': per_page}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
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
            if isinstance(date_to, str) and len(date_to) == 10:
                date_to = date_to + ' 23:59:59'
            params.append(date_to)
        
        if search:
            query += " AND (user_id ILIKE %s OR endpoint ILIKE %s OR ip_address ILIKE %s)"
            count_query += " AND (user_id ILIKE %s OR endpoint ILIKE %s OR ip_address ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Add pagination
        query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        # Convert to list of dicts
        logs = [dict(log) for log in logs]
        for log in logs:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
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
            return_db_connection(connection)
        return {'logs': [], 'total': 0, 'page': page, 'per_page': per_page}


def get_activity_stats():
    """Get summary statistics for activity logs"""
    connection = get_db_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM activity_logs 
            WHERE event_type = 'login_success' 
            AND DATE(timestamp) = %s
        """, (today,))
        logins_today = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM activity_logs 
            WHERE event_type = 'login_failed' 
            AND DATE(timestamp) = %s
        """, (today,))
        failed_logins_today = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(DISTINCT ip_address) as count FROM activity_logs 
            WHERE DATE(timestamp) = %s
        """, (today,))
        unique_ips_today = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM activity_logs")
        total_logs = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM activity_logs 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            GROUP BY event_type
            ORDER BY count DESC
        """)
        events_by_type = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT ip_address, COUNT(*) as count 
            FROM activity_logs 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            AND ip_address IS NOT NULL AND ip_address != ''
            GROUP BY ip_address
            ORDER BY count DESC
            LIMIT 10
        """)
        top_ips = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT user_id, ip_address, timestamp 
            FROM activity_logs 
            WHERE event_type = 'login_failed'
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent_failed = [dict(row) for row in cursor.fetchall()]
        for log in recent_failed:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
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
            return_db_connection(connection)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# MAINTENANCE
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_old_logs(days=90):
    """Remove activity logs older than specified number of days"""
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM activity_logs 
            WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """, (days,))
        
        deleted_count = cursor.rowcount
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        print(f"Cleaned up {deleted_count} activity logs older than {days} days")
        return deleted_count
        
    except Error as e:
        print(f"Error cleaning up logs: {e}")
        if connection:
            return_db_connection(connection)
        return 0


def get_suspicious_ips():
    """Find IPs that are logged into multiple different accounts"""
    connection = get_db_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT ip_address, user_id, user_type, MAX(timestamp) as last_login
            FROM activity_logs 
            WHERE event_type IN ('login_success', 'api_call')
            AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            AND ip_address IS NOT NULL 
            AND ip_address != '' 
            AND ip_address != 'unknown'
            AND ip_address != 'system'
            AND user_id IS NOT NULL
            GROUP BY ip_address, user_id, user_type
            ORDER BY ip_address, last_login DESC
        """)
        
        results = cursor.fetchall()
        
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
        
        suspicious = {ip: users for ip, users in ip_users.items() if len(users) > 1}
        
        cursor.close()
        return_db_connection(connection)
        
        return suspicious
        
    except Error as e:
        print(f"Error getting suspicious IPs: {e}")
        if connection:
            return_db_connection(connection)
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
    """Query activity logs grouped by user+IP combination"""
    connection = get_db_connection()
    if not connection:
        return {'groups': [], 'suspicious_ips': {}, 'total': 0, 'page': page, 'per_page': per_page}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                user_id, 
                user_type, 
                ip_address,
                COUNT(*) as log_count,
                MIN(timestamp) as first_activity,
                MAX(timestamp) as last_activity,
                STRING_AGG(DISTINCT event_type, ',') as event_types
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
            query += " AND (user_id ILIKE %s OR endpoint ILIKE %s OR ip_address ILIKE %s)"
            count_query += " AND (user_id ILIKE %s OR endpoint ILIKE %s OR ip_address ILIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        query += " GROUP BY user_id, user_type, ip_address ORDER BY last_activity DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        groups = [dict(row) for row in cursor.fetchall()]
        
        for group in groups:
            if group.get('first_activity'):
                group['first_activity'] = group['first_activity'].strftime('%Y-%m-%d %H:%M:%S')
            if group.get('last_activity'):
                group['last_activity'] = group['last_activity'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return_db_connection(connection)
        
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
            return_db_connection(connection)
        return {'groups': [], 'suspicious_ips': {}, 'total': 0, 'page': page, 'per_page': per_page}


def mask_old_ips(days=90):
    """Mask IP addresses in logs older than specified days for privacy"""
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE activity_logs 
            SET ip_address = CONCAT(
                (STRING_TO_ARRAY(ip_address, '.'))[1], '.',
                (STRING_TO_ARRAY(ip_address, '.'))[2], '.',
                (STRING_TO_ARRAY(ip_address, '.'))[3], '.xxx'
            )
            WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
            AND ip_address LIKE '%%.%%.%%.%%'
            AND ip_address NOT LIKE '%%.xxx'
        """, (days,))
        
        masked_count = cursor.rowcount
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        print(f"Masked {masked_count} IP addresses older than {days} days")
        return masked_count
        
    except Error as e:
        print(f"Error masking IPs: {e}")
        if connection:
            return_db_connection(connection)
        return 0
