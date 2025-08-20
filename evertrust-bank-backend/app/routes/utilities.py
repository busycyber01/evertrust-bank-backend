from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app import db
import json
import os

utilities_bp = Blueprint('utilities', __name__)

@utilities_bp.route('/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    }), 200

@utilities_bp.route('/atms', methods=['GET'])
@jwt_required()
def get_atms():
    # Load static ATM data
    try:
        # In a real application, this would come from a database or external API
        # For demo purposes, we'll use static data
        atms = [
            {
                'id': 1,
                'name': 'Main Branch ATM',
                'address': '123 Financial District, San Francisco, CA 94105',
                'lat': 37.7749,
                'lng': -122.4194,
                'hours': '24/7',
                'features': ['Cash Withdrawal', 'Deposit', 'Balance Inquiry']
            },
            {
                'id': 2,
                'name': 'Downtown ATM',
                'address': '456 Market Street, San Francisco, CA 94103',
                'lat': 37.7849,
                'lng': -122.4094,
                'hours': '5:00 AM - 11:00 PM',
                'features': ['Cash Withdrawal', 'Balance Inquiry']
            },
            {
                'id': 3,
                'name': 'Westside ATM',
                'address': '789 Sunset Boulevard, San Francisco, CA 94118',
                'lat': 37.7649,
                'lng': -122.4294,
                'hours': '24/7',
                'features': ['Cash Withdrawal', 'Deposit', 'Balance Inquiry', 'Check Deposit']
            }
        ]
        return jsonify(atms), 200
    except Exception as e:
        return jsonify({'message': 'Failed to load ATM data', 'error': str(e)}), 500