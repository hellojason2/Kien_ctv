"""
CTV Portal - Booking Appointments Module
Handles creation of customer bookings/referrals from CTVs
Saves to both database and Google Sheets
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import jsonify, request, g
from psycopg2.extras import RealDictCursor

import gspread
from google.oauth2.service_account import Credentials

from .blueprint import ctv_bp
from ..auth import require_ctv
from ..db_pool import get_db_connection, return_db_connection

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.absolute()
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '12YrAEGiOKLoqzj4tE-VLZNQNIda7S5hdMaQJO5UEsnQ')
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'
# Environment variable for credentials (JSON string) - used in production
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')

logger = logging.getLogger(__name__)


def clean_phone(phone):
    """Clean phone number to digits only"""
    if not phone:
        return None
    cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
    return cleaned[:15] if cleaned else None


def get_google_client():
    """Get authenticated Google Sheets client - supports both file and env variable"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Try environment variable first (for production/Railway)
    if GOOGLE_CREDENTIALS_JSON:
        try:
            creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            logger.info("Using Google credentials from environment variable")
            return gspread.authorize(credentials)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get Google client from env: {e}")
            return None
    
    # Fall back to file (for local development)
    try:
        if CREDENTIALS_FILE.exists():
            credentials = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
            logger.info("Using Google credentials from file")
            return gspread.authorize(credentials)
        else:
            logger.error(f"Google credentials file not found: {CREDENTIALS_FILE}")
            return None
    except Exception as e:
        logger.error(f"Failed to get Google client from file: {e}")
        return None


def normalize_header(header):
    """Normalize Vietnamese header to ASCII for comparison"""
    import unicodedata
    if not header:
        return ''
    vn_map = {
        '\u0111': 'd', '\u0110': 'D', '\u0103': 'a', '\u0102': 'A', '\u00e2': 'a', '\u00c2': 'A',
        '\u00ea': 'e', '\u00ca': 'E', '\u00f4': 'o', '\u00d4': 'O', '\u01a1': 'o', '\u01a0': 'O',
        '\u01b0': 'u', '\u01af': 'U',
    }
    text = str(header)
    for vn_char, ascii_char in vn_map.items():
        text = text.replace(vn_char, ascii_char)
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').strip()


def find_worksheet(spreadsheet, tab_variations):
    """Find worksheet by trying multiple name variations"""
    worksheets = spreadsheet.worksheets()
    for variation in tab_variations:
        for ws in worksheets:
            if ws.title == variation:
                return ws
            if ws.title.lower() == variation.lower():
                return ws
            if normalize_header(ws.title) == normalize_header(variation):
                return ws
    return None


def append_to_google_sheet(booking_data, referrer_phone):
    """Append booking data to Google Sheets 'Khách giới thiệu' tab"""
    try:
        client = get_google_client()
        if not client:
            logger.error("Failed to get Google client for booking")
            return False, "Could not connect to Google Sheets"
        
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Find the Khách giới thiệu worksheet
        variations = ['Khách giới thiệu', 'Khach gioi thieu', 'Gioi Thieu', 'Referral']
        worksheet = find_worksheet(spreadsheet, variations)
        
        if not worksheet:
            logger.error("Could not find 'Khách giới thiệu' worksheet")
            return False, "Could not find the referral worksheet"
        
        # Format date as DD/MM/YYYY for Google Sheets
        today = datetime.now().strftime('%d/%m/%Y')
        
        # Build the row to append
        # Columns: Ngày nhập đơn, Tên khách hàng, Số điện thoại, Dịch vụ Quan tâm, Ghi chú, Khu vực của khách hàng, SDT người giới thiệu
        row = [
            today,                                      # Ngày nhập đơn
            booking_data['customer_name'],              # Tên khách hàng
            booking_data['customer_phone'],             # Số điện thoại
            booking_data['service_interest'],           # Dịch vụ Quan tâm
            booking_data.get('notes', ''),              # Ghi chú
            booking_data.get('region', ''),             # Khu vực của khách hàng
            referrer_phone                              # SDT người giới thiệu
        ]
        
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        logger.info(f"Successfully appended booking to Google Sheets for customer: {booking_data['customer_name']}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error appending to Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def save_to_database(booking_data, referrer_phone):
    """Save booking to khach_hang table in database"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Get today's date
        today = datetime.now().date()
        
        # Clean phone number
        customer_phone = clean_phone(booking_data['customer_phone'])
        if not customer_phone:
            cursor.close()
            return_db_connection(connection)
            return False, "Invalid customer phone number"
        
        # Insert into khach_hang table
        cursor.execute("""
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, dich_vu, ghi_chu, khu_vuc, nguoi_chot, source, trang_thai)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'gioi_thieu', 'Cho xac nhan')
            RETURNING id
        """, (
            today,
            booking_data['customer_name'][:100],
            customer_phone,
            booking_data['service_interest'][:500],
            booking_data.get('notes', '')[:1000] if booking_data.get('notes') else '',
            booking_data.get('region', '')[:50] if booking_data.get('region') else '',
            referrer_phone
        ))
        
        result = cursor.fetchone()
        booking_id = result[0] if result else None
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        logger.info(f"Successfully saved booking to database with ID: {booking_id}")
        return True, booking_id
        
    except Exception as e:
        logger.error(f"Error saving booking to database: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return False, str(e)


@ctv_bp.route('/api/ctv/booking', methods=['POST'])
@require_ctv
def create_booking():
    """
    Create a new customer booking/referral
    - Saves to database (khach_hang table)
    - Appends to Google Sheets (Khách giới thiệu tab)
    """
    ctv = g.current_user
    
    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body required'}), 400
    
    # Validate required fields
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    service_interest = data.get('service_interest', '').strip()
    notes = data.get('notes', '').strip()
    region = data.get('region', '').strip()
    
    if not customer_name:
        return jsonify({'status': 'error', 'message': 'Customer name is required'}), 400
    
    if not customer_phone:
        return jsonify({'status': 'error', 'message': 'Customer phone is required'}), 400
    
    if not service_interest:
        return jsonify({'status': 'error', 'message': 'Service interest is required'}), 400
    
    # Clean customer phone
    cleaned_phone = clean_phone(customer_phone)
    if not cleaned_phone or len(cleaned_phone) < 8:
        return jsonify({'status': 'error', 'message': 'Invalid customer phone number'}), 400
    
    # Get referrer phone (CTV's ma_ctv, which is typically their phone number)
    referrer_phone = ctv.get('ma_ctv', '')
    if not referrer_phone:
        referrer_phone = ctv.get('sdt', '')
    
    # Build booking data
    booking_data = {
        'customer_name': customer_name,
        'customer_phone': cleaned_phone,
        'service_interest': service_interest,
        'notes': notes,
        'region': region
    }
    
    # Save to database
    db_success, db_result = save_to_database(booking_data, referrer_phone)
    if not db_success:
        return jsonify({
            'status': 'error',
            'message': f'Failed to save booking: {db_result}'
        }), 500
    
    # Append to Google Sheets
    sheets_success, sheets_error = append_to_google_sheet(booking_data, referrer_phone)
    if not sheets_success:
        # Log the error but don't fail the request since DB was successful
        logger.warning(f"Google Sheets append failed: {sheets_error}")
    
    return jsonify({
        'status': 'success',
        'message': 'Booking created successfully',
        'booking_id': db_result,
        'sheets_synced': sheets_success
    })
