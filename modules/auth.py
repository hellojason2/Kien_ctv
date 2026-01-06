"""
Authentication Module
Handles password hashing, session management, and route protection.
Updated for PostgreSQL.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# FUNCTIONS:
# - hash_password(password) -> str
#     DOES: Hash password with salt using SHA256
#     OUTPUTS: "salt:hash" format string
#
# - verify_password(password, stored_hash) -> bool
#     DOES: Verify password against stored hash
#     OUTPUTS: True if match, False otherwise
#
# - create_session(user_type, user_id) -> str
#     DOES: Create new session in database
#     OUTPUTS: Session token (64-char hex string)
#
# - validate_session(token) -> dict | None
#     DOES: Check if session is valid and not expired
#     OUTPUTS: User info dict or None
#
# - destroy_session(token) -> bool
#     DOES: Delete session from database (logout)
#     OUTPUTS: Success status
#
# - get_current_user() -> dict | None
#     DOES: Get current user from request headers/cookies
#     OUTPUTS: User info or None
#
# - require_admin(func) -> decorator
#     DOES: Decorator to protect admin-only routes
#
# - require_ctv(func) -> decorator
#     DOES: Decorator to protect CTV-only routes
#
# ══════════════════════════════════════════════════════════════════════════════

Created: December 28, 2025
Updated: January 2, 2026 - Migrated to PostgreSQL
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

# Import activity logger (lazy import to avoid circular dependency)
_activity_logger = None

def _get_activity_logger():
    """Lazy import of activity logger to avoid circular imports"""
    global _activity_logger
    if _activity_logger is None:
        try:
            from . import activity_logger as al
            _activity_logger = al
        except ImportError:
            _activity_logger = False
    return _activity_logger if _activity_logger else None

# Session expiry time (24 hours)
SESSION_EXPIRY_HOURS = 24

# Use connection pool for better performance
from .db_pool import get_db_connection, return_db_connection


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(password):
    """
    DOES: Hash password using SHA256 with random salt
    INPUTS: password - plain text password
    OUTPUTS: "salt:hash" format string for storage
    
    Security: Uses 16-byte random salt to prevent rainbow table attacks
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password, stored_hash):
    """
    DOES: Verify password against stored hash
    INPUTS: password - plain text to verify, stored_hash - "salt:hash" from database
    OUTPUTS: True if password matches, False otherwise
    """
    if not stored_hash or ':' not in stored_hash:
        return False
    
    try:
        salt, expected_hash = stored_hash.split(':', 1)
        actual_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return actual_hash == expected_hash
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def create_session(user_type, user_id, remember_me=False):
    """
    DOES: Create new session token and store in database
    INPUTS: user_type ('admin' or 'ctv'), user_id (username or ma_ctv), remember_me (bool)
    OUTPUTS: Session token (64-char hex string) or None on failure
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Generate unique session token
        token = secrets.token_hex(32)
        
        # Calculate expiry time - 30 days if remember me, otherwise 24 hours
        expiry_hours = 720 if remember_me else SESSION_EXPIRY_HOURS
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        # Delete any existing sessions for this user (single session per user)
        cursor.execute(
            "DELETE FROM sessions WHERE user_type = %s AND user_id = %s",
            (user_type, user_id)
        )
        
        # Create new session
        cursor.execute("""
            INSERT INTO sessions (id, user_type, user_id, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (token, user_type, user_id, expires_at))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return token
        
    except Error as e:
        print(f"Error creating session: {e}")
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return None


def validate_session(token):
    """
    DOES: Check if session token is valid and not expired
    INPUTS: token - session token from client
    OUTPUTS: Dict with user info or None if invalid
    """
    if not token:
        return None
    
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get session and check expiry
        cursor.execute("""
            SELECT user_type, user_id, expires_at 
            FROM sessions 
            WHERE id = %s AND expires_at > CURRENT_TIMESTAMP
        """, (token,))
        
        session = cursor.fetchone()
        
        cursor.close()
        return_db_connection(connection)
        
        return dict(session) if session else None
        
    except Error as e:
        print(f"Error validating session: {e}")
        if connection:
            return_db_connection(connection)
        return None


def destroy_session(token):
    """
    DOES: Delete session from database (logout)
    INPUTS: token - session token to delete
    OUTPUTS: True if deleted, False otherwise
    """
    if not token:
        return False
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM sessions WHERE id = %s", (token,))
        deleted = cursor.rowcount > 0
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return deleted
        
    except Error as e:
        print(f"Error destroying session: {e}")
        if connection:
            return_db_connection(connection)
        return False


def cleanup_expired_sessions():
    """
    DOES: Remove all expired sessions from database
    """
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
        connection.commit()
        cursor.close()
        return_db_connection(connection)
    except Error:
        if connection:
            return_db_connection(connection)


# ══════════════════════════════════════════════════════════════════════════════
# USER RETRIEVAL
# ══════════════════════════════════════════════════════════════════════════════

def get_current_user():
    """
    DOES: Get current user from request Authorization header or cookie
    OUTPUTS: User info dict or None
    """
    token = None
    
    # Check Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    # Check X-Session-Token header if no token yet
    if not token:
        token = request.headers.get('X-Session-Token')
    
    # Check cookie if still no token
    if not token:
        token = request.cookies.get('session_token')
    
    # Validate once if we found a token
    if token:
        return validate_session(token)
    
    return None


def get_admin_info(username):
    """
    DOES: Get admin details by username
    OUTPUTS: Admin dict or None
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, username, name, created_at 
            FROM admins WHERE username = %s
        """, (username,))
        admin = cursor.fetchone()
        cursor.close()
        return_db_connection(connection)
        
        if admin:
            admin = dict(admin)
            if admin.get('created_at'):
                admin['created_at'] = admin['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return admin
    except Error:
        if connection:
            return_db_connection(connection)
        return None


def get_ctv_info(ma_ctv):
    """
    DOES: Get CTV details by ma_ctv
    OUTPUTS: CTV dict or None
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT ma_ctv, ten, sdt, email, cap_bac, nguoi_gioi_thieu, is_active
            FROM ctv WHERE ma_ctv = %s
        """, (ma_ctv,))
        ctv = cursor.fetchone()
        cursor.close()
        return_db_connection(connection)
        return dict(ctv) if ctv else None
    except Error:
        if connection:
            return_db_connection(connection)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE DECORATORS
# ══════════════════════════════════════════════════════════════════════════════

def require_admin(f):
    """
    DOES: Decorator to protect admin-only routes
    USAGE: @require_admin before route function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from request
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            token = request.headers.get('X-Session-Token')
        if not token:
            token = request.cookies.get('session_token')
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        # Combined query to validate session AND get admin info
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
        
        try:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    s.user_type,
                    s.user_id,
                    s.expires_at,
                    a.id as admin_id,
                    a.username,
                    a.name,
                    a.created_at
                FROM sessions s
                LEFT JOIN admins a ON s.user_type = 'admin' AND s.user_id = a.username
                WHERE s.id = %s AND s.expires_at > CURRENT_TIMESTAMP
            """, (token,))
            
            result = cursor.fetchone()
            cursor.close()
            return_db_connection(connection)
            
            if not result:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            
            if result.get('user_type') != 'admin':
                return jsonify({
                    'status': 'error',
                    'message': 'Admin access required'
                }), 403
            
            if not result.get('admin_id'):
                return jsonify({
                    'status': 'error',
                    'message': 'Admin account not found'
                }), 401
            
            admin_info = {
                'id': result['admin_id'],
                'username': result['username'],
                'name': result['name'],
                'created_at': result['created_at'].strftime('%Y-%m-%d %H:%M:%S') if result.get('created_at') else None
            }
            
            g.current_user = admin_info
            g.user_type = 'admin'
            
            return f(*args, **kwargs)
            
        except Exception as e:
            if connection:
                return_db_connection(connection)
            return jsonify({
                'status': 'error',
                'message': f'Authentication error: {str(e)}'
            }), 500
    
    return decorated_function


def require_ctv(f):
    """
    DOES: Decorator to protect CTV-only routes
    USAGE: @require_ctv before route function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        if user.get('user_type') != 'ctv':
            return jsonify({
                'status': 'error',
                'message': 'CTV access required'
            }), 403
        
        # Get full CTV info
        ctv_info = get_ctv_info(user['user_id'])
        if not ctv_info:
            return jsonify({
                'status': 'error',
                'message': 'CTV account not found'
            }), 401
        
        if not ctv_info.get('is_active', True):
            return jsonify({
                'status': 'error',
                'message': 'CTV account is deactivated'
            }), 403
        
        g.current_user = ctv_info
        g.user_type = 'ctv'
        
        return f(*args, **kwargs)
    
    return decorated_function


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def admin_login(username, password, remember_me=False):
    """
    DOES: Authenticate admin and create session
    INPUTS: username, password, remember_me (bool)
    OUTPUTS: {'token': str, 'admin': dict} or {'error': str}
    """
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        connection = get_db_connection()
        if not connection:
            last_error = 'Database connection failed'
            continue
        
        try:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, username, password_hash, name
                FROM admins WHERE username = %s
            """, (username,))
            admin = cursor.fetchone()
            
            cursor.close()
            return_db_connection(connection)
            
            if not admin:
                logger = _get_activity_logger()
                if logger:
                    logger.log_login_failed(username, 'admin')
                return {'error': 'Invalid username or password'}
            
            if not verify_password(password, admin.get('password_hash', '')):
                logger = _get_activity_logger()
                if logger:
                    logger.log_login_failed(username, 'admin')
                return {'error': 'Invalid username or password'}
            
            token = create_session('admin', username, remember_me=remember_me)
            if not token:
                return {'error': 'Failed to create session'}
            
            logger = _get_activity_logger()
            if logger:
                logger.log_login_success('admin', username)
            
            return {
                'token': token,
                'admin': {
                    'id': admin['id'],
                    'username': admin['username'],
                    'name': admin['name']
                }
            }
            
        except Error as e:
            error_str = str(e)
            print(f"Admin login attempt {attempt+1} failed: {error_str}")
            
            # Discard the bad connection
            if connection:
                try:
                    connection.rollback()
                    return_db_connection(connection, close=True)
                except:
                    pass
            
            last_error = f'Database error: {error_str}'
            
            # Only retry on connection/network errors
            if any(x in error_str for x in ["timed out", "closed", "connection", "SSL", "server closed"]):
                continue
            else:
                # Logic error or other fatal error
                break
                
    return {'error': last_error or 'Login failed'}


def ctv_login(ma_ctv, password):
    """
    DOES: Authenticate CTV by ma_ctv (case-insensitive) and create session
    INPUTS: ma_ctv (CTV code, case-insensitive), password
    OUTPUTS: {'token': str, 'ctv': dict} or {'error': str}
    """
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        connection = get_db_connection()
        if not connection:
            last_error = 'Database connection failed'
            continue
        
        try:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Case-insensitive lookup by ma_ctv
            cursor.execute("""
                SELECT ma_ctv, ten, email, sdt, cap_bac, password_hash, is_active
                FROM ctv WHERE LOWER(ma_ctv) = LOWER(%s)
            """, (ma_ctv,))
            ctv = cursor.fetchone()
            
            cursor.close()
            return_db_connection(connection)
            
            if not ctv:
                logger = _get_activity_logger()
                if logger:
                    logger.log_login_failed(ma_ctv, 'ctv')
                return {'error': 'Invalid CTV code or password'}
            
            if not ctv.get('is_active', True):
                logger = _get_activity_logger()
                if logger:
                    logger.log_login_failed(ma_ctv, 'ctv')
                return {'error': 'Account is deactivated'}
            
            if not verify_password(password, ctv.get('password_hash', '')):
                logger = _get_activity_logger()
                if logger:
                    logger.log_login_failed(ma_ctv, 'ctv')
                return {'error': 'Invalid CTV code or password'}
            
            token = create_session('ctv', ctv['ma_ctv'])
            if not token:
                return {'error': 'Failed to create session'}
            
            logger = _get_activity_logger()
            if logger:
                logger.log_login_success('ctv', ctv['ma_ctv'])
            
            return {
                'token': token,
                'ctv': {
                    'ma_ctv': ctv['ma_ctv'],
                    'ten': ctv['ten'],
                    'email': ctv['email'],
                    'sdt': ctv['sdt'],
                    'cap_bac': ctv['cap_bac']
                }
            }
            
        except Error as e:
            error_str = str(e)
            print(f"CTV login attempt {attempt+1} failed: {error_str}")
            
            # Discard the bad connection
            if connection:
                try:
                    connection.rollback()
                    return_db_connection(connection, close=True)
                except:
                    pass
            
            last_error = f'Database error: {error_str}'
            
            # Only retry on connection/network errors
            if any(x in error_str for x in ["timed out", "closed", "connection", "SSL", "server closed"]):
                continue
            else:
                # Logic error or other fatal error
                break
                
    return {'error': last_error or 'Login failed'}


def change_ctv_password(ma_ctv, current_password, new_password):
    """
    DOES: Change CTV password after verifying current password
    INPUTS: ma_ctv, current_password, new_password
    OUTPUTS: {'success': True} or {'error': str}
    """
    if not new_password or len(new_password) < 6:
        return {'error': 'New password must be at least 6 characters'}
    
    connection = get_db_connection()
    if not connection:
        return {'error': 'Database connection failed'}
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT ma_ctv, password_hash
            FROM ctv WHERE LOWER(ma_ctv) = LOWER(%s)
        """, (ma_ctv,))
        ctv = cursor.fetchone()
        
        if not ctv:
            cursor.close()
            return_db_connection(connection)
            return {'error': 'CTV not found'}
        
        if not verify_password(current_password, ctv.get('password_hash', '')):
            cursor.close()
            return_db_connection(connection)
            return {'error': 'Current password is incorrect'}
        
        new_password_hash = hash_password(new_password)
        cursor.execute("""
            UPDATE ctv SET password_hash = %s WHERE ma_ctv = %s
        """, (new_password_hash, ctv['ma_ctv']))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return {'success': True}
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return {'error': f'Database error: {str(e)}'}
