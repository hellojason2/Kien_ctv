# ══════════════════════════════════════
# PROJECT STRUCTURE MAP
# ══════════════════════════════════════
#
# ENTRY POINT: backend.py
#
# FLOW:
# backend.py
#   ├── app.register_blueprint(admin_bp) -> modules/admin/
#   ├── app.register_blueprint(ctv_bp)   -> modules/ctv/
#   └── app.register_blueprint(api_bp)   -> modules/api/
#
# MODULES:
# - backend.py          : App entry, landing page routes, public API
# - sync_worker.py      : Google Sheets live sync worker
#
# - modules/admin/      : Admin Dashboard logic (split into sub-modules)
#   ├── auth.py         : Admin login/logout
#   ├── ctv.py          : CTV account management
#   ├── commissions.py  : Commission reports and settings
#   ├── stats.py        : Dashboard statistics
#   ├── admins.py       : Admin account management
#   ├── clients.py      : Client services management
#   ├── logs.py         : Activity logs
#   └── export.py       : Excel/CSV export functions
#
# - modules/ctv/        : CTV Portal logic (split into sub-modules)
#   ├── auth.py         : CTV login/logout
#   ├── profile.py      : Profile and personal stats
#   ├── commissions.py  : Personal earnings
#   ├── network.py      : Referral hierarchy and downline
#   ├── customers.py    : Customer list and commissions
#   └── clients.py      : Card view for clients
#
# - modules/api/        : Core system API (Legacy/Utility)
#   ├── database.py     : DB connection, table info, schema validation
#   ├── customers.py    : Generic customer data
#   ├── ctv.py          : Generic CTV data and hierarchy
#   └── commissions.py  : Generic commission data
#
# - static/js/admin/    : Admin Dashboard JavaScript
#   ├── db-validator.js : Database schema validation (NEW)
#   └── (other modules) : Auth, API, Navigation, etc.
#
# - static/js/ctv/      : CTV Portal JavaScript
#   ├── db-validator.js : Database schema validation (NEW)
#   └── (other modules) : Auth, API, Navigation, etc.
#
# - modules/mlm/        : Core MLM Business Logic
#   ├── commissions.py  : Calculation algorithms
#   ├── hierarchy.py    : Referral chain traversal
#   └── validation.py   : Data integrity checks
#
# - modules/            : Shared Utility Modules
#   ├── auth.py         : Auth decorators and session management
#   ├── db_pool.py      : Connection pooling
#   ├── activity_logger.py : Tracking and logging
#   ├── redis_cache.py  : Caching layer
#   └── export_excel.py : Excel generation utilities
# ══════════════════════════════════════

