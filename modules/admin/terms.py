"""
Admin Routes - Signup Terms Management
Handles CRUD operations for signup agreement terms
"""
from flask import jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import admin_bp
from ..db_pool import get_db_connection, return_db_connection
from ..auth import require_admin

@admin_bp.route('/api/admin/signup-terms', methods=['GET'])
@require_admin
def get_signup_terms(admin_session):
    """Get all signup terms (for admin panel)"""
    language = request.args.get('language', 'vi')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get all terms for the language
        cursor.execute("""
            SELECT id, language, title, content, is_active, version, 
                   created_at, updated_at, updated_by
            FROM signup_terms
            WHERE language = %s
            ORDER BY version DESC
        """, (language,))
        
        terms = cursor.fetchall()
        
        cursor.close()
        return_db_connection(connection)
        
        # Convert datetime to string
        for term in terms:
            if term.get('created_at'):
                term['created_at'] = term['created_at'].isoformat()
            if term.get('updated_at'):
                term['updated_at'] = term['updated_at'].isoformat()
        
        return jsonify({
            'status': 'success',
            'terms': terms
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


@admin_bp.route('/api/admin/signup-terms/active', methods=['GET'])
def get_active_signup_terms():
    """Get active signup terms (public endpoint for signup page)"""
    language = request.args.get('language', 'vi')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get the active term for the language
        cursor.execute("""
            SELECT id, language, title, content, version
            FROM signup_terms
            WHERE language = %s AND is_active = TRUE
            ORDER BY version DESC
            LIMIT 1
        """, (language,))
        
        term = cursor.fetchone()
        
        cursor.close()
        return_db_connection(connection)
        
        if not term:
            return jsonify({
                'status': 'error',
                'message': 'No active terms found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'term': {
                'id': term['id'],
                'language': term['language'],
                'title': term['title'],
                'content': term['content'],
                'version': term['version']
            }
        })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


@admin_bp.route('/api/admin/signup-terms', methods=['POST'])
@require_admin
def create_signup_terms(admin_session):
    """Create new version of signup terms"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    language = data.get('language', 'vi')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'status': 'error', 'message': 'Title and content are required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get the max version for this language
        cursor.execute("""
            SELECT COALESCE(MAX(version), 0) + 1 as next_version
            FROM signup_terms
            WHERE language = %s
        """, (language,))
        
        next_version = cursor.fetchone()['next_version']
        
        # Deactivate all previous versions
        cursor.execute("""
            UPDATE signup_terms
            SET is_active = FALSE
            WHERE language = %s
        """, (language,))
        
        # Insert new version
        cursor.execute("""
            INSERT INTO signup_terms 
            (language, title, content, is_active, version, updated_by)
            VALUES (%s, %s, %s, TRUE, %s, %s)
            RETURNING id
        """, (language, title, content, next_version, admin_session['username']))
        
        new_id = cursor.fetchone()['id']
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Terms created successfully',
            'id': new_id,
            'version': next_version
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


@admin_bp.route('/api/admin/signup-terms/<int:term_id>', methods=['PUT'])
@require_admin
def update_signup_terms(admin_session, term_id):
    """Update existing signup terms"""
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'status': 'error', 'message': 'Title and content are required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Update the term
        cursor.execute("""
            UPDATE signup_terms
            SET title = %s, content = %s, updated_at = NOW(), updated_by = %s
            WHERE id = %s
            RETURNING id
        """, (title, content, admin_session['username'], term_id))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Term not found'}), 404
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Terms updated successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


@admin_bp.route('/api/admin/signup-terms/<int:term_id>/activate', methods=['PUT'])
@require_admin
def activate_signup_terms(admin_session, term_id):
    """Activate a specific version of signup terms"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get the language of the term to activate
        cursor.execute("""
            SELECT language FROM signup_terms WHERE id = %s
        """, (term_id,))
        
        term = cursor.fetchone()
        if not term:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Term not found'}), 404
        
        language = term['language']
        
        # Deactivate all terms for this language
        cursor.execute("""
            UPDATE signup_terms
            SET is_active = FALSE
            WHERE language = %s
        """, (language,))
        
        # Activate the selected term
        cursor.execute("""
            UPDATE signup_terms
            SET is_active = TRUE, updated_at = NOW(), updated_by = %s
            WHERE id = %s
        """, (admin_session['username'], term_id))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Terms activated successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


@admin_bp.route('/api/admin/signup-terms/<int:term_id>', methods=['DELETE'])
@require_admin
def delete_signup_terms(admin_session, term_id):
    """Delete a version of signup terms (only if not active)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Check if the term is active
        cursor.execute("""
            SELECT is_active FROM signup_terms WHERE id = %s
        """, (term_id,))
        
        term = cursor.fetchone()
        if not term:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Term not found'}), 404
        
        if term['is_active']:
            cursor.close()
            return_db_connection(connection)
            return jsonify({'status': 'error', 'message': 'Cannot delete active terms'}), 400
        
        # Delete the term
        cursor.execute("""
            DELETE FROM signup_terms WHERE id = %s
        """, (term_id,))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Terms deleted successfully'
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500
