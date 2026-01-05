from .blueprint import admin_bp

# Import all sub-modules to register routes with admin_bp
from . import auth
from . import ctv
from . import commissions
from . import stats
from . import admins
from . import clients
from . import logs
from . import export
from . import debug  # TEMPORARY - DELETE WHEN DONE

# Export admin_bp for backend.py
__all__ = ['admin_bp']

