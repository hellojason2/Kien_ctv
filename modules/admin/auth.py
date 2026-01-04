import os
from flask import jsonify, request, make_response, render_template, send_file
from .blueprint import admin_bp, BASE_DIR
from ..auth import (
    admin_login,
    destroy_session,
    get_current_user
)

@admin_bp.route('/admin89/login', methods=['POST'])
def login():
    """Admin login endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password required'}), 400
    
    result = admin_login(username, password, remember_me=remember_me)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 401
    
    cookie_max_age = 2592000 if remember_me else 86400
    
    response = make_response(jsonify({
        'status': 'success',
        'token': result['token'],
        'admin': result['admin']
    }))
    response.set_cookie('session_token', result['token'], httponly=True, max_age=cookie_max_age)
    
    return response


@admin_bp.route('/admin89/logout', methods=['POST'])
def logout():
    """Admin logout endpoint"""
    token = request.cookies.get('session_token')
    if not token:
        token = request.headers.get('X-Session-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if token:
        destroy_session(token)
    
    response = make_response(jsonify({'status': 'success', 'message': 'Logged out'}))
    response.delete_cookie('session_token')
    
    return response


@admin_bp.route('/admin89', methods=['GET'])
def dashboard():
    """Serve admin dashboard HTML using Jinja2 template"""
    try:
        # Try rendering the template
        return render_template('admin/base.html')
    except Exception as e:
        # Fallback: try sending the file directly
        import traceback
        error_details = traceback.format_exc()
        print(f"Error rendering admin template: {e}")
        print(f"Traceback: {error_details}")
        
        # Try fallback template file
        template_path = os.path.join(BASE_DIR, 'templates', 'admin.html')
        if os.path.exists(template_path):
            try:
                return send_file(template_path)
            except Exception as e2:
                print(f"Error sending fallback file: {e2}")
        
        # Return HTML error page instead of JSON (browser expects HTML)
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Admin Dashboard Error</title></head>
        <body>
            <h1>Admin Dashboard Error</h1>
            <p>Error: {str(e)}</p>
            <p>Template path checked: {template_path}</p>
            <p>Template exists: {os.path.exists(template_path) if template_path else 'N/A'}</p>
            <pre>{error_details}</pre>
        </body>
        </html>
        """
        return error_html, 500


@admin_bp.route('/admin89/check-auth', methods=['GET'])
def check_auth():
    """Check if current user is authenticated as admin"""
    user = get_current_user()
    if user and user.get('user_type') == 'admin':
        return jsonify({'status': 'success', 'authenticated': True, 'user': user})
    return jsonify({'status': 'error', 'authenticated': False}), 401

