"""
Public API endpoints - No authentication required
"""

import logging
from datetime import datetime
from flask import jsonify, request

from .blueprint import api_bp
from ..db_pool import get_db_connection, return_db_connection

logger = logging.getLogger(__name__)


def clean_phone(phone):
    """
    Clean phone number to digits only, preserving trailing zeros.
    This function extracts all digits from the phone number and preserves
    any trailing zeros that are part of the original number.
    
    Examples:
        "09720208810" -> "09720208810" (trailing zero preserved)
        "097202088100" -> "097202088100" (trailing zeros preserved)
        "097-202-0881" -> "0972020881" (non-digits removed, trailing zeros preserved)
    """
    if not phone:
        return None
    # Extract all digits, preserving trailing zeros
    cleaned = ''.join(c for c in str(phone).strip() if c.isdigit())
    return cleaned[:15] if cleaned else None


@api_bp.route('/api/public/booking', methods=['POST'])
def create_public_booking():
    """
    Create a new customer booking/referral from public form
    - No authentication required
    - Referrer phone is manually provided
    """
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
    referrer_phone = data.get('referrer_phone', '').strip()
    
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
    
    # Clean referrer phone if provided (preserves trailing zeros)
    cleaned_referrer = clean_phone(referrer_phone) if referrer_phone else ''
    
    # Save to database
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        today = datetime.now().date()
        
        # Insert into khach_hang table
        cursor.execute("""
            INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, dich_vu, ghi_chu, khu_vuc, nguoi_chot, source, trang_thai)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'gioi_thieu', 'Cho xac nhan')
            RETURNING id
        """, (
            today,
            customer_name[:100],
            cleaned_phone,
            service_interest[:500],
            notes[:1000] if notes else '',
            region[:50] if region else '',
            cleaned_referrer
        ))
        
        result = cursor.fetchone()
        booking_id = result[0] if result else None
        
        connection.commit()
        cursor.close()
        return_db_connection(connection)
        
        logger.info(f"Public booking created with ID: {booking_id}, referrer: {cleaned_referrer}")
        
        # Also try to sync to Google Sheets
        try:
            from ..ctv.booking import append_to_google_sheet
            booking_data = {
                'customer_name': customer_name,
                'customer_phone': cleaned_phone,
                'service_interest': service_interest,
                'notes': notes,
                'region': region
            }
            sheets_success, _ = append_to_google_sheet(booking_data, cleaned_referrer)
            if sheets_success:
                logger.info(f"Public booking synced to Google Sheets")
        except Exception as e:
            logger.warning(f"Failed to sync public booking to Google Sheets: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Booking created successfully',
            'booking_id': booking_id
        })
        
    except Exception as e:
        logger.error(f"Error creating public booking: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            return_db_connection(connection)
        return jsonify({'status': 'error', 'message': 'Failed to save booking'}), 500
