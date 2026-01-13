from .blueprint import ctv_bp

# Import sub-modules to register routes
from . import auth
from . import profile
from . import commissions
from . import network
from . import customers
from . import clients
from . import signup

# Export ctv_bp for backend.py
__all__ = ['ctv_bp']

