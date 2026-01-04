import os
from flask import Blueprint

# Get base directory for templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR_FOR_TEMPLATES = os.path.join(BASE_DIR, 'templates')

# Create Blueprint with template folder
admin_bp = Blueprint('admin', __name__, template_folder=BASE_DIR_FOR_TEMPLATES)

