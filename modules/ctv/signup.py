"""
CTV Signup Routes
Handles new CTV registration requests with admin approval workflow
"""
from flask import jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from .blueprint import ctv_bp
from ..db_pool import get_db_connection, return_db_connection
from ..auth import hash_password
import base64
import json
import os
from datetime import datetime

# Google Gemini AI for ID OCR
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. ID scanning will be disabled.")

@ctv_bp.route('/signup', methods=['GET'])
def signup_page():
    """Serve the CTV signup page"""
    from flask import render_template
    return render_template('ctv_signup.html')


@ctv_bp.route('/api/ctv/scan-id', methods=['POST'])
def scan_id_card():
    """
    Scan Vietnamese ID card (CCCD/CMND) using Google Gemini Vision API
    Extracts: full_name, dob, id_number, address
    """
    if not GEMINI_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'ID scanning feature is not available. Please install google-generativeai.'
        }), 503
    
    data = request.get_json()
    
    if not data or not data.get('image'):
        return jsonify({
            'status': 'error',
            'message': 'No image provided'
        }), 400
    
    image_data = data['image']
    
    # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    try:
        # Decode base64 to verify it's valid
        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid image data: {str(e)}'
        }), 400
    
    # Get API key from environment or use provided key
    api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyCw1q1cUo7enX0S3NMAdPKkKNMr1yVFf9A')
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.0 Flash for fast processing
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create image part for the API
        image_part = {
            'mime_type': 'image/jpeg',
            'data': image_bytes
        }
        
        # Prompt for Vietnamese ID card extraction
        prompt = """Analyze this Vietnamese ID card (CCCD/CMND) image and extract the following information.
Return ONLY a JSON object with these fields (use null if not found):

{
    "full_name": "Full name as shown on the card",
    "last_name": "Family name (Họ)",
    "first_name": "Given name (Tên)",
    "dob": "Date of birth in YYYY-MM-DD format",
    "id_number": "12-digit ID number (Số CCCD) or 9-digit CMND number",
    "address": "Permanent address (Nơi thường trú)",
    "gender": "Nam or Nữ",
    "nationality": "Quốc tịch"
}

Important:
- For Vietnamese names, the last_name is usually the first word(s) before the final name
- Parse the date correctly to YYYY-MM-DD format
- Extract the full 12-digit CCCD number or 9-digit CMND number
- Return ONLY the JSON object, no other text"""

        # Generate response
        response = model.generate_content([prompt, image_part])
        
        # Parse the response
        response_text = response.text.strip()
        
        # Try to extract JSON from the response
        # Sometimes the model wraps it in markdown code blocks
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        extracted_data = json.loads(response_text)
        
        return jsonify({
            'status': 'success',
            'data': extracted_data
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error in ID Scanning: {str(e)}")
        print(f"Raw Response: {response_text if 'response_text' in locals() else 'None'}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to parse extracted data: {str(e)}',
            'raw_response': response_text if 'response_text' in locals() else None
        }), 500
    except Exception as e:
        print(f"ID Scanning Failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'ID scanning failed: {str(e)}'
        }), 500


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
    Handle CTV signup request - auto-approved (creates CTV account immediately)
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
    signature_image = data.get('signature_image')
    password = data['password']
    
    # Clean phone number
    phone_digits = ''.join(c for c in phone if c.isdigit())
    if len(phone_digits) < 9:
        return jsonify({
            'status': 'error',
            'message': 'Invalid phone number'
        }), 400
    
    # Hash password using proper hash_password function (salt:hash format)
    password_hash = hash_password(password)
    
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
                'error_code': 'ALREADY_REGISTERED',
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
                'error_code': 'PENDING_APPROVAL',
                'message': 'You already have a pending registration'
            }), 400
        
        # Verify referrer code if provided (now accepts phone number)
        referrer_id = None
        if referrer_code:
            cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (referrer_code,))
            referrer = cursor.fetchone()
            
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
        
        # ── Auto-generate CTV code ──
        # Only consider short numeric codes (not phone-number-like entries)
        cursor.execute("""
            SELECT ma_ctv FROM ctv 
            WHERE ma_ctv ~ '^[0-9]+$'
              AND LENGTH(ma_ctv) <= 6
            ORDER BY CAST(ma_ctv AS BIGINT) DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        ctv_code = str(int(result['ma_ctv']) + 1) if result else '1'
        
        # Ensure CTV code is unique (edge case safety)
        cursor.execute("SELECT ma_ctv FROM ctv WHERE ma_ctv = %s", (ctv_code,))
        if cursor.fetchone():
            ctv_code = str(int(ctv_code) + 1)
        
        # ── Insert registration record (for audit trail) ──
        cursor.execute("""
            INSERT INTO ctv_registrations 
            (full_name, phone, email, address, dob, id_number, referrer_code, password_hash, status, created_at, reviewed_at, reviewed_by, admin_notes, signature_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'approved', NOW(), NOW(), 'system', %s, %s)
            RETURNING id
        """, (full_name, phone_digits, email, address, dob, id_number, referrer_id, password_hash, 
              f'Auto-approved as {ctv_code}', signature_image))
        
        registration_id = cursor.fetchone()['id']
        
        # ── Create CTV account directly (auto-approved) ──
        cursor.execute("""
            INSERT INTO ctv 
            (ma_ctv, ten, sdt, email, cap_bac, nguoi_gioi_thieu, password_hash, is_active, created_at, signature_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), %s)
        """, (
            ctv_code,
            full_name,
            phone_digits,
            email,
            'Đồng',  # Default level
            referrer_id,
            password_hash,
            signature_image
        ))
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'message': f'Đăng ký thành công! Mã CTV của bạn là {ctv_code}. Đăng nhập bằng số điện thoại hoặc mã CTV.',
            'registration_id': registration_id,
            'ctv_code': ctv_code,
            'auto_approved': True
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
