from .blueprint import api_bp
from flask import jsonify
import os
from pathlib import Path

@api_bp.route('/admin/check-google-creds', methods=['GET'])
def check_google_creds():
    has_env = bool(os.getenv('GOOGLE_CREDENTIALS_JSON'))
    has_file = (Path(os.getcwd()) / 'google_credentials.json').exists()
    return jsonify({'valid': has_env or has_file, 'source': 'env' if has_env else 'file' if has_file else None})
