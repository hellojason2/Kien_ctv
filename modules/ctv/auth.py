import os
from flask import jsonify, request, make_response, render_template, send_file, g
from .blueprint import ctv_bp, BASE_DIR
from ..auth import (
    ctv_login,
    destroy_session,
    get_current_user,
    require_ctv,
    change_ctv_password
)

@ctv_bp.route('/ctv/login', methods=['POST'])
def login():
    """CTV login endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    ma_ctv = data.get('ma_ctv', '').strip()
    password = data.get('password', '')
    
    if not ma_ctv or not password:
        return jsonify({'status': 'error', 'message': 'CTV code and password required'}), 400
    
    result = ctv_login(ma_ctv, password)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 401
    
    response = make_response(jsonify({
        'status': 'success',
        'token': result['token'],
        'ctv': result['ctv']
    }))
    response.set_cookie('session_token', result['token'], httponly=True, max_age=86400)
    
    return response


@ctv_bp.route('/ctv/logout', methods=['POST'])
def logout():
    """CTV logout endpoint"""
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


@ctv_bp.route('/ctv/portal', methods=['GET'])
def portal():
    """Serve CTV portal HTML using Jinja2 template with no-cache headers"""
    try:
        response = make_response(render_template('ctv/base.html'))
        # Prevent browser caching - always fetch fresh content
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        template_path = os.path.join(BASE_DIR, 'templates', 'ctv_portal.html')
        if os.path.exists(template_path):
            response = make_response(send_file(template_path))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        return jsonify({'status': 'error', 'message': f'CTV portal not found: {str(e)}'}), 404


@ctv_bp.route('/ctv/check-auth', methods=['GET'])
def check_auth():
    """Check if current user is authenticated as CTV"""
    user = get_current_user()
    if user and user.get('user_type') == 'ctv':
        return jsonify({'status': 'success', 'authenticated': True, 'user': user})
    return jsonify({'status': 'error', 'authenticated': False}), 401


@ctv_bp.route('/api/ctv/change-password', methods=['POST'])
@require_ctv
def change_password():
    """Change CTV password"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'status': 'error', 'message': 'Current and new password required'}), 400
    
    ctv = g.current_user
    result = change_ctv_password(ctv['ma_ctv'], current_password, new_password)
    
    if 'error' in result:
        return jsonify({'status': 'error', 'message': result['error']}), 400
    
    return jsonify({'status': 'success', 'message': 'Password changed successfully'})

