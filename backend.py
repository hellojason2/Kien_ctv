import os
import sys
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 45433,
    'user': 'root',
    'password': 'hMNdGtasqTqqLLocTYtzZtKxxEKaIhAg',
    'database': 'railway'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(BASE_DIR, 'dashboard.html')
    return send_file(dashboard_path)

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test database connection"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'success',
                'message': 'Database connected successfully',
                'database': db_name[0]
            })
        except Error as e:
            return jsonify({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to database'
        }), 500

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of all tables in the database"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        connection.close()
        return jsonify({
            'status': 'success',
            'tables': tables
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching tables: {str(e)}'
        }), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """Fetch customer data (id, name, email, phone)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check if customers table exists
        cursor.execute("SHOW TABLES LIKE 'customers';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            return jsonify({
                'status': 'success',
                'data': [],
                'message': 'Customers table not found. Run migrate_database.py first.'
            })
        
        # Fetch id, name, email, and phone from customers table
        cursor.execute("SELECT id, name, email, phone FROM customers ORDER BY id;")
        data = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'table': 'customers',
            'data': data
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching data: {str(e)}'
        }), 500

@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get full customer details by ID"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Fetch customer details
        cursor.execute("SELECT * FROM customers WHERE id = %s;", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'customer': customer
        })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching customer: {str(e)}'
        }), 500

@app.route('/api/customer/<int:customer_id>/services', methods=['GET'])
def get_customer_services(customer_id):
    """Get all services for a customer with CTV info"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # First get the customer details
        cursor.execute("SELECT * FROM customers WHERE id = %s;", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
        
        # Get all services for this customer with CTV name
        cursor.execute("""
            SELECT 
                s.id,
                s.service_name,
                s.date_entered,
                s.date_scheduled,
                s.amount,
                s.status,
                s.ctv_code,
                c.name as ctv_name,
                c.level as ctv_level
            FROM services s
            LEFT JOIN ctv_accounts c ON s.ctv_code = c.ctv_code
            WHERE s.customer_id = %s
            ORDER BY s.date_entered DESC;
        """, (customer_id,))
        services = cursor.fetchall()
        
        # Convert date objects to strings for JSON serialization
        for service in services:
            if service['date_entered']:
                service['date_entered'] = service['date_entered'].strftime('%Y-%m-%d')
            if service['date_scheduled']:
                service['date_scheduled'] = service['date_scheduled'].strftime('%Y-%m-%d')
        
        cursor.close()
        connection.close()
        
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

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask server on http://localhost:4000")
    print("=" * 50)
    print("\nTesting database connection...")
    
    # Test connection on startup
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            print(f"SUCCESS: Connected to database '{db_name[0]}'")
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            if tables:
                print(f"Found {len(tables)} table(s):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("No tables found in database")
            cursor.close()
            connection.close()
        except Error as e:
            print(f"ERROR: {e}")
    else:
        print("ERROR: Failed to connect to database")
    
    print("\n" + "=" * 50)
    print("Server running. Access dashboard at:")
    print("http://localhost:4000")
    print("=" * 50 + "\n")
    
    port = int(os.environ.get('PORT', 4000))
    debug = os.environ.get('RAILWAY_ENVIRONMENT') is None
    app.run(host='0.0.0.0', port=port, debug=debug)

