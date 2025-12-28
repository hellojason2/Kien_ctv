# Release Notes - CTV Dashboard

## Version 1.2.0 - December 28, 2025

### Admin & CTV Portal System Implementation

**Time:** 15:37 (GMT+7)

---

### New Features Added

#### Modular Architecture

Refactored the entire backend into modular components for better maintainability:

```
Ctv/
├── backend.py              # Main Flask app (imports modules)
├── modules/
│   ├── __init__.py         # Package initialization
│   ├── auth.py             # Authentication & session management
│   ├── admin_routes.py     # Admin API endpoints
│   ├── ctv_routes.py       # CTV Portal API endpoints
│   └── mlm_core.py         # MLM functions (commission, hierarchy)
├── templates/
│   ├── admin.html          # Admin dashboard UI
│   └── ctv_portal.html     # CTV portal UI
└── migrate_auth.py         # Auth tables migration
```

#### Authentication System (`modules/auth.py`)

- **Password Hashing:** SHA256 with random salt
- **Session Management:** 64-char hex tokens, 24-hour expiry
- **Route Protection:** `@require_admin` and `@require_ctv` decorators

Functions:
- `hash_password(password)` - Hash with salt
- `verify_password(password, stored_hash)` - Verify credentials
- `create_session(user_type, user_id)` - Create session token
- `validate_session(token)` - Check session validity
- `destroy_session(token)` - Logout
- `get_current_user()` - Get user from request headers/cookies

#### Database Schema Changes

**New Table: `admins`**
- `id` INT PRIMARY KEY AUTO_INCREMENT
- `username` VARCHAR(50) UNIQUE
- `password_hash` VARCHAR(255)
- `name` VARCHAR(100)
- `created_at`, `updated_at` DATETIME

**New Table: `sessions`**
- `id` VARCHAR(64) PRIMARY KEY - Session token
- `user_type` ENUM('admin', 'ctv')
- `user_id` VARCHAR(50)
- `created_at`, `expires_at` DATETIME

**New Table: `commission_settings`**
- `level` INT PRIMARY KEY (0-4)
- `rate` DECIMAL(5,4)
- `description` VARCHAR(100)
- `updated_at`, `updated_by`

**Updated Table: `ctv`**
- Added `password_hash` VARCHAR(255)
- Added `is_active` BOOLEAN DEFAULT TRUE

#### Admin Dashboard (`/admin/dashboard`)

Features:
1. **Dashboard Overview** - Stats cards (total CTVs, monthly commission, transactions, revenue)
2. **Top Earners** - Monthly leaderboard
3. **CTV Management** - Create, update, deactivate CTVs with search
4. **Hierarchy Visualizer** - Interactive tree view with level colors
5. **Commission Settings** - Edit rates for levels 0-4
6. **Commission Reports** - Filter by CTV, month, level

Admin API Endpoints:
- `POST /admin/login` - Admin login
- `POST /admin/logout` - Admin logout
- `GET /admin/check-auth` - Check authentication
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/ctv` - List all CTVs
- `POST /api/admin/ctv` - Create new CTV
- `PUT /api/admin/ctv/<code>` - Update CTV
- `DELETE /api/admin/ctv/<code>` - Deactivate CTV
- `GET /api/admin/hierarchy/<code>` - Get hierarchy tree
- `GET /api/admin/commission-settings` - Get commission rates
- `PUT /api/admin/commission-settings` - Update rates
- `GET /api/admin/commissions` - Commission reports
- `PUT /api/admin/commissions/<id>` - Adjust commission

#### CTV Portal (`/ctv/portal`)

Features:
1. **Login Page** - Email + password authentication
2. **My Dashboard** - Personal stats, network size, recent commissions
3. **My Earnings** - Commission breakdown by level, filterable
4. **My Network** - Hierarchy tree of all descendants
5. **Search** - Search customers/CTVs within own network ONLY

**Security:** CTVs can ONLY access data within their network (descendants)

CTV API Endpoints:
- `POST /ctv/login` - CTV login (email + password)
- `POST /ctv/logout` - CTV logout
- `GET /ctv/check-auth` - Check authentication
- `GET /api/ctv/me` - Get own profile with stats
- `GET /api/ctv/my-commissions` - Own commission earnings
- `GET /api/ctv/my-downline` - Direct referrals (Level 1)
- `GET /api/ctv/my-hierarchy` - Full descendant tree
- `GET /api/ctv/my-network/search` - Search within network
- `GET /api/ctv/my-network/customers` - Customers in network
- `GET /api/ctv/my-stats` - Detailed statistics

#### Default Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**CTVs:**
- Email: `<ctv_email>` (e.g., kien@example.com)
- Password: `ctv123`

> WARNING: Change these in production!

#### Migration Script

**New File: `migrate_auth.py`**
- Creates admins, sessions, commission_settings tables
- Adds password fields to ctv table
- Inserts default admin account
- Sets default CTV passwords

Run: `python3 migrate_auth.py passwords`

---

## Version 1.1.0 - December 28, 2025

### MLM Referral System Implementation

**Time:** Earlier today (GMT+7)

---

### New Features Added

#### MLM Multi-Level Commission System

Based on the MLM hierarchy diagram requirements, implemented a complete referral tracking and commission calculation system.

##### Database Changes
- **New Table: `ctv`** - CTV accounts with referral relationships
  - `ma_ctv` (VARCHAR(20) PRIMARY KEY) - CTV code
  - `ten` (VARCHAR(100)) - Name
  - `sdt` (VARCHAR(15)) - Phone
  - `email` (VARCHAR(100)) - Email
  - `nguoi_gioi_thieu` (VARCHAR(20) FK) - Referrer code (parent CTV)
  - `cap_bac` (VARCHAR(50)) - Rank/level badge
  - `created_at`, `updated_at` - Timestamps

- **New Table: `commissions`** - Commission records for each transaction
  - `id` (INT PRIMARY KEY AUTO_INCREMENT)
  - `transaction_id` (INT FK) - Links to services.id
  - `ctv_code` (VARCHAR(20) FK) - CTV receiving commission
  - `level` (INT 0-4) - Level in hierarchy
  - `commission_rate` (DECIMAL) - Rate applied
  - `transaction_amount` (DECIMAL) - Original amount
  - `commission_amount` (DECIMAL) - Calculated commission
  - `created_at` - Timestamp

- **Updated Table: `services`**
  - Added `nguoi_chot` column - CTV who closed the deal
  - Added `tong_tien` column - Total amount

##### Core Functions (backend.py)

1. **`calculate_level(cursor, ctv_code, ancestor_code)`**
   - Recursive tree traversal to find level distance between CTVs
   - Returns level (0-4) or None if not in hierarchy or >4 levels
   - Detects circular references

2. **`build_ancestor_chain(cursor, ctv_code, max_levels=4)`**
   - Builds list of all ancestors up to max_levels deep
   - Returns list of (ancestor_code, level) tuples

3. **`build_hierarchy_tree(root_ctv_code)`**
   - Builds complete hierarchy tree from a CTV's perspective
   - Returns nested structure with all descendants up to level 4

4. **`calculate_commissions(transaction_id, ctv_code, amount)`**
   - Automatically calculates and stores commissions when transactions created
   - Commission rates:
     - Level 0 (self): 25%
     - Level 1: 5%
     - Level 2: 2.5%
     - Level 3: 1.25%
     - Level 4: 0.625%

5. **`validate_ctv_data(ctv_list)`**
   - Validates CTV import data for circular references and missing fields

##### New API Endpoints

1. **`POST /api/ctv/import`**
   - Import CTV data with referral relationships
   - Body: `[{ma_ctv, ten, sdt, email, nguoi_gioi_thieu, cap_bac}, ...]`
   - Validates circular references before import

2. **`GET /api/ctv`**
   - Get all CTV accounts with referral info

3. **`GET /api/ctv/<ctv_code>/hierarchy`**
   - Get hierarchy tree from a CTV's perspective
   - Returns nested structure with all descendants

4. **`GET /api/ctv/<ctv_code>/levels`**
   - Get level matrix showing each CTV's level relative to root
   - Returns commission rates per level

5. **`GET /api/ctv/<ctv_code>/commissions`**
   - Get commission report for a CTV
   - Query params: `?month=YYYY-MM` or `?year=YYYY`
   - Returns breakdown by level with totals

6. **`POST /api/services`**
   - Create service transaction with auto commission calculation
   - Automatically triggers commission calculation for entire hierarchy
   - Body: `{customer_id, service_name, amount, ctv_code, date_scheduled, status}`

7. **`GET /api/commissions/transaction/<transaction_id>`**
   - Get all commission records for a specific transaction
   - Shows all CTVs who earned commission

##### Migration Script

- **New File: `migrate_mlm.py`**
  - Creates ctv and commissions tables
  - Migrates existing ctv_accounts data
  - Adds nguoi_chot and tong_tien columns to services
  - Run with: `python3 migrate_mlm.py` or `python3 migrate_mlm.py sample`

##### Sample Data

The migration script can insert sample MLM hierarchy:
```
CTV001 (KienTT) - Root
  |- CTV002 (DungNTT) - Level 1
  |    |- CTV005 (TuTT) - Level 2
  |    |    |- CTV008 (TungPT) - Level 3
  |    |    |    |- CTV011 (HanhNT) - Level 4
  |    |    |- CTV009 (VuNL) - Level 3
  |    |- CTV006 (LinhVT) - Level 2
  |         |- CTV010 (TrangNTT) - Level 3
  |- CTV003 (TungHV) - Level 1
  |    |- CTV007 (AnhNT) - Level 2
  |- CTV004 (LinhNP) - Level 1
```

---

## Version 1.0.0 - December 27, 2025

### Initial Release

**Time:** 09:38 AM (GMT+7)

---

### Features Added

#### Database Structure
- Created multi-table MySQL database schema:
  - `customers` - Customer personal information (id, name, phone, email, created_at)
  - `services` - Service records linked to customers (id, customer_id, service_name, date_entered, date_scheduled, amount, status, ctv_code)
  - `ctv_accounts` - CTV employee accounts (id, ctv_code, name, password, level)

#### Backend API (Flask)
- `GET /` - Serve dashboard HTML
- `GET /api/data` - Get customer list (id, name, email, phone) for search
- `GET /api/customer/<id>` - Get full customer details
- `GET /api/customer/<id>/services` - Get customer with all their services and CTV info

#### Frontend Dashboard
- Clean, minimal UI matching the original design
- Search functionality:
  - Search by name, email, or phone
  - Real-time filtering as you type
  - Empty state shows "Start typing to search for customers..."
  - Cmd+K / Ctrl+K shortcut to focus search
- Clickable table rows (no checkboxes)
- Slide-in side panel showing:
  - Customer name header
  - Contact information card (email, phone)
  - Services history table with columns:
    - Service name
    - Date scheduled
    - Amount
    - Status (color-coded badges)
    - CTV employee name
- Status badges:
  - Green: Completed (Hoan thanh)
  - Yellow: Pending (Cho xu ly)
  - Red: Cancelled (Da huy)

#### Sample Data
- 10 Vietnamese customers with generated emails
- 13 service records across customers
- 3 CTV accounts (Gold, Silver, Bronze levels)

---

### Technical Stack
- **Backend:** Python Flask 3.0.0
- **Database:** MySQL (Railway)
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Dependencies:**
  - flask==3.0.0
  - flask-cors==4.0.0
  - mysql-connector-python==8.2.0

---

### Files Created/Modified
- `backend.py` - Flask server with API endpoints
- `dashboard.html` - Frontend dashboard with side panel
- `requirements.txt` - Python dependencies

---

### How to Run
1. Install dependencies: `pip3 install -r requirements.txt`
2. Start server: `python3 backend.py`
3. Open browser: `http://localhost:4000`

