"""
CTV Signup Routes
Handles new CTV registration requests with admin approval workflow
"""
from flask import jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..db_pool import get_db_connection, return_db_connection
import hashlib
from datetime import datetime

@ctv_bp.route('/signup', methods=['GET'])
def signup_page():
    """Serve the CTV signup page"""
    from flask import render_template
    return render_template('ctv_signup.html')

@ctv_bp.route('/api/ctv/check-referrer-phone', methods=['POST'])
def check_referrer_phone():
    """
    Check if a referrer CTV exists by phone number
    Returns: {'exists': True/False, 'name': 'CTV Name', 'ma_ctv': 'code' (if exists)}
    """
    data = request.get_json()
    
    if not data or not data.get('phone'):
        return jsonify({
            'status': 'error',
            'message': 'Phone number required'
        }), 400
    
    phone = data['phone'].strip()
    
    # Clean phone number
    phone_digits = ''.join(c for c in phone if c.isdigit())
    
    if not phone_digits:
        return jsonify({
            'status': 'success',
            'exists': None,
            'message': 'No phone number provided'
        })
    
    if len(phone_digits) < 8:
        return jsonify({
            'status': 'success',
            'exists': False,
            'message': 'Phone number too short'
        })
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Search for CTV by phone number - try multiple matching strategies
        # 1. Exact match
        # 2. Match without leading zero (0989... vs 989...)
        # 3. Match last 8 digits (flexible matching)
        # 4. Strip leading zeros from both sides for comparison
        phone_suffix = phone_digits[-8:]
        phone_without_zero = phone_digits.lstrip('0')
        
        cursor.execute("""
            SELECT ma_ctv, ten, sdt 
            FROM ctv 
            WHERE sdt = %s
               OR sdt = %s
               OR REPLACE(sdt, ' ', '') = %s
               OR REPLACE(sdt, ' ', '') = %s
               OR sdt LIKE %s
               OR REPLACE(sdt, ' ', '') LIKE %s
               OR LTRIM(sdt, '0') = %s
               OR LTRIM(REPLACE(sdt, ' ', ''), '0') = %s
               OR LTRIM(sdt, '0') = %s
               OR LTRIM(REPLACE(sdt, ' ', ''), '0') = %s
            LIMIT 1
        """, (phone_digits, phone_without_zero, phone_digits, phone_without_zero, 
              '%' + phone_suffix, '%' + phone_suffix,
              phone_without_zero, phone_without_zero, phone_digits, phone_digits))
        
        referrer = cursor.fetchone()
        
        cursor.close()
        return_db_connection(connection)
        
        if referrer:
            return jsonify({
                'status': 'success',
                'exists': True,
                'name': referrer['ten'],
                'ma_ctv': referrer['ma_ctv'],
                'phone': referrer['sdt']
            })
        else:
            return jsonify({
                'status': 'success',
                'exists': False,
                'message': 'CTV with this phone number not found'
            })
        
    except Error as e:
        if connection:
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@ctv_bp.route('/api/ctv/signup', methods=['POST'])
def ctv_signup():
    """
    Handle CTV signup request - creates pending registration
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['full_name', 'phone', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    full_name = data['full_name'].strip()
    phone = data['phone'].strip()
    email = data.get('email', '').strip() if data.get('email') else None
    address = data.get('address', '').strip() if data.get('address') else None
    dob = data.get('dob') if data.get('dob') else None
    id_number = data.get('id_number', '').strip() if data.get('id_number') else None
    referrer_code = data.get('referrer_code', '').strip() if data.get('referrer_code') else None
    password = data['password']
    
    # Clean phone number
    phone_digits = ''.join(c for c in phone if c.isdigit())
    if len(phone_digits) < 9:
        return jsonify({
            'status': 'error',
            'message': 'Invalid phone number'
        }), 400
    
    # Hash password (using sha256 for compatibility)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Check if phone already exists in ctv table
        cursor.execute("SELECT ma_ctv FROM ctv WHERE sdt = %s", (phone_digits,))
        existing_ctv = cursor.fetchone()
        if existing_ctv:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'error',
                'message': 'Phone number already registered'
            }), 400
        
        # Check if phone already has pending registration
        cursor.execute("SELECT id FROM ctv_registrations WHERE phone = %s AND status = 'pending'", (phone_digits,))
        pending = cursor.fetchone()
        if pending:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'error',
                'message': 'You already have a pending registration'
            }), 400
        
        # Verify referrer code if provided (now accepts phone number)
        referrer_id = None
        if referrer_code:
            # First try as CTV code
            cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (referrer_code,))
            referrer = cursor.fetchone()
            
            # If not found, try as phone number
            if not referrer:
                referrer_digits = ''.join(c for c in referrer_code if c.isdigit())
                if len(referrer_digits) >= 8:
                    phone_suffix = referrer_digits[-8:]
                    cursor.execute("SELECT ma_ctv FROM ctv WHERE sdt LIKE %s LIMIT 1", ('%' + phone_suffix,))
                    referrer = cursor.fetchone()
            
            if not referrer:
                cursor.close()
                return_db_connection(connection)
                return jsonify({
                    'status': 'error',
                    'message': f'Referrer not found with code/phone: {referrer_code}'
                }), 400
            referrer_id = referrer['ma_ctv']
        
        # Insert registration request
        cursor.execute("""
            INSERT INTO ctv_registrations 
            (full_name, phone, email, address, dob, id_number, referrer_code, password_hash, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
            RETURNING id
        """, (full_name, phone_digits, email, address, dob, id_number, referrer_id, password_hash))
        
        registration_id = cursor.fetchone()['id']
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': 'Registration submitted successfully. Awaiting admin approval.',
            'registration_id': registration_id
        })
        
    except Error as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500
