"""
CTV Dashboard Modules Package

This package contains modular components for the CTV Dashboard application:
- auth.py: Authentication and session management
- mlm_core.py: MLM hierarchy and commission calculations
- admin_routes.py: Admin dashboard API endpoints
- ctv_routes.py: CTV portal API endpoints

Created: December 28, 2025
"""

from .auth import (
    hash_password,
    verify_password,
    create_session,
    validate_session,
    destroy_session,
    require_admin,
    require_ctv,
    get_current_user
)

from .mlm_core import (
    get_commission_rates,
    get_parent,
    calculate_level,
    build_ancestor_chain,
    build_hierarchy_tree,
    calculate_commissions,
    validate_ctv_data,
    get_all_descendants
)

__all__ = [
    # Auth functions
    'hash_password',
    'verify_password', 
    'create_session',
    'validate_session',
    'destroy_session',
    'require_admin',
    'require_ctv',
    'get_current_user',
    # MLM functions
    'get_commission_rates',
    'get_parent',
    'calculate_level',
    'build_ancestor_chain',
    'build_hierarchy_tree',
    'calculate_commissions',
    'validate_ctv_data',
    'get_all_descendants'
]

