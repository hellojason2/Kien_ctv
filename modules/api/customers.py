from flask import jsonify
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from .blueprint import api_bp
from ..db_pool import get_db_connection, return_db_connection

@api_bp.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get full customer details by ID"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM customers WHERE id = %s;", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'customer': customer
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching customer: {str(e)}'
        }), 500

@api_bp.route('/api/customer/<int:customer_id>/services', methods=['GET'])
def get_customer_services(customer_id):
    """Get all services for a customer with CTV info"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM customers WHERE id = %s;", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            return_db_connection(connection)
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
        
        cursor.execute("""
            SELECT 
                s.id,
                s.service_name,
                s.date_entered,
                s.date_scheduled,
                s.amount,
                s.status,
                s.ctv_code,
                c.ten as ctv_name,
                c.cap_bac as ctv_level
            FROM services s
            LEFT JOIN ctv c ON s.ctv_code = c.ma_ctv
            WHERE s.customer_id = %s
            ORDER BY s.date_entered DESC;
        """, (customer_id,))
        services = cursor.fetchall()
        
        for service in services:
            if service['date_entered']:
                service['date_entered'] = service['date_entered'].strftime('%Y-%m-%d')
            if service['date_scheduled']:
                service['date_scheduled'] = service['date_scheduled'].strftime('%Y-%m-%d')
        
        cursor.close()
        return_db_connection(connection)
        
        return jsonify({
            'status': 'success',
            'customer': customer,
            'services': services
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching services: {str(e)}'
        }), 500

