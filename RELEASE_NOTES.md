# Release Notes - CTV Dashboard

## Version 1.6.0 - December 29, 2025

### Client Services View Implementation

**Time:** Current Session

---

### Overview

Implemented a new Client Services card view displaying clients with their grouped services. Clients are grouped by phone number + name, with up to 3 services displayed per client card.

### Changes Made

#### Backend API Endpoints

**Admin Endpoint: `GET /api/admin/clients-with-services`**
- Groups `khach_hang` records by `sdt` + `ten_khach`
- Returns up to 3 services per client sorted by most recent
- Includes deposit status for each service (`Da coc` / `Chua coc`)
- Query params: `search`, `nguoi_chot`, `limit`

**CTV Endpoint: `GET /api/ctv/clients-with-services`**
- Same structure as admin endpoint
- **Access Control:** Only shows clients where `nguoi_chot` = logged-in CTV code
- Query params: `search`, `limit`

#### Admin Dashboard (`templates/admin.html`)

**New Sidebar Menu Item:**
- Added "Clients" / "Khách Hàng" menu option between Commissions and Settings

**New Clients Page Section:**
- Client cards with gradient purple header (#667eea to #764ba2)
- Client avatar with initials
- Client info row (Cơ sở, Ngày nhập đơn, Người chốt, Status badge)
- Services grid (3 columns on desktop, 2 on tablet, 1 on mobile)
- Service cards with deposit status, amounts, and appointment dates
- Search functionality with debounced input

**New CSS Styles:**
- `.client-card` - Main card container with hover effects
- `.client-card-header` - Gradient header with avatar
- `.client-info-row` - Client metadata display
- `.services-grid` - Responsive grid layout
- `.service-card` - Individual service display
- Responsive breakpoints at 1024px and 640px

**New JavaScript Functions:**
- `loadClientsWithServices()` - Fetch client data
- `renderClientCards()` - Render all cards
- `renderClientCard()` - Generate single card HTML
- `renderServiceCard()` - Generate service card HTML
- `getInitials()` - Extract name initials
- `formatClientCurrency()` - Vietnamese currency format
- `debounce()` - Search input debouncing

#### CTV Portal (`templates/ctv_portal.html`)

**View Toggle Feature:**
- Toggle between Card View and Table View
- Card View is default

**Client Cards View:**
- Same card design as admin dashboard
- Filtered to show only CTV's own clients
- Search functionality
- Service grouping and display

**Updated Customers Page:**
- Split into two sections: cardViewSection and tableViewSection
- View toggle buttons at top
- Maintained original table view functionality

#### Files Modified

| File | Changes |
|------|---------|
| `modules/admin_routes.py` | Added `/api/admin/clients-with-services` endpoint |
| `modules/ctv_routes.py` | Added `/api/ctv/clients-with-services` endpoint |
| `templates/admin.html` | Added Clients menu, page section, CSS, and JavaScript |
| `templates/ctv_portal.html` | Added card view with toggle, CSS, and JavaScript |

#### Data Structure

```json
{
  "status": "success",
  "clients": [
    {
      "ten_khach": "Minh Thủy Nguyễn",
      "sdt": "0988942155",
      "co_so": "Hồ Chí Minh",
      "ngay_nhap_don": "03/07/2020",
      "nguoi_chot": "Dungntt",
      "service_count": 2,
      "overall_status": "Da coc",
      "overall_deposit": "Da coc",
      "services": [
        {
          "id": 1,
          "service_number": 1,
          "dich_vu": "Cắt mí",
          "tong_tien": 23200000,
          "tien_coc": 1000000,
          "phai_dong": 22200000,
          "ngay_hen_lam": "15/07/2020",
          "trang_thai": "Da den lam",
          "deposit_status": "Da coc"
        }
      ]
    }
  ],
  "total": 50
}
```

#### Responsive Design

- **Desktop (>1024px):** 3-column services grid
- **Tablet (640-1024px):** 2-column services grid
- **Mobile (<640px):** 1-column services grid, stacked header elements

---

## Version 1.5.3 - December 29, 2025

### Responsive Design Improvements

**Time:** Previous Session

---

### Changes Made

**Admin Dashboard (`templates/admin.html`):**
- Fixed stats grid layout for tablet (2 columns) and mobile (1-2 columns)
- Fixed sidebar collapse on mobile - hides text labels, shows only icons
- Added horizontal scroll for tables on mobile devices
- Improved form elements sizing for touch devices
- Added modal responsive styles

**Main Dashboard (`dashboard.html`):**
- Converted sidebar to bottom navigation bar on mobile
- Improved header layout for mobile (stacked elements)
- Added touch-friendly table scrolling
- Optimized phone check input for mobile

**CTV Portal (`templates/ctv_portal.html`):**
- Matched responsive behavior with admin dashboard
- Updated hierarchy tree with new L1-L5 level badges
- Added tree stats (Total Members, Levels Deep, Direct Recruits)
- Added expand/collapse all buttons
- Improved table responsive behavior

**Files Modified:**
- `templates/admin.html`
- `dashboard.html`
- `templates/ctv_portal.html`

---

## Version 1.5.2 - December 28, 2025

### Hierarchy Tree Redesign

**Time:** Previous Session

---

### Changes Made

**Visual Redesign:**
- Updated hierarchy tree with modern dark theme design
- Added gradient background with purple/blue tones (`linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)`)
- Implemented level badges with distinct colors:
  - L1 (Level 0): Red (#ff6b6b)
  - L2 (Level 1): Orange (#ffa502)
  - L3 (Level 2): Green (#2ed573)
  - L4 (Level 3): Blue (#1e90ff)
  - L5 (Level 4): Purple (#a55eea) with "CUT OFF" badge

**New Features:**
- **Stats Cards**: Display total members, levels deep, and direct recruits at the top
- **Expand/Collapse All**: Buttons to quickly expand or collapse the entire tree
- **Real-time Search**: Search by name or CTV code with highlighting and auto-scroll
- **Collapsible Nodes**: Click on any node with children to expand/collapse
- **Responsive Design**: Works on mobile, tablet, and desktop

**Level Mapping:**
- Database Level 0 = Display as L1 (root)
- Database Level 1 = Display as L2
- Database Level 2 = Display as L3
- Database Level 3 = Display as L4
- Database Level 4 = Display as L5 (with CUT OFF badge)

**Files Modified:**
- `templates/admin.html`: Updated CSS, HTML structure, and JavaScript functions

---

## Version 1.5.1 - December 28, 2025

### Commission Backfill Fix

**Time:** Current Session

---

### Issue Fixed

**Problem:** Admin dashboard showed "No commissions found" even though there were 1,207 completed transactions in the `khach_hang` table.

**Root Cause:** 
- The `commissions` table existed but was empty (0 records)
- Commissions are only automatically calculated when transactions are created via `/api/services` endpoint
- Historical transactions imported from CSV were never processed for commission calculation

**Solution:**
- Created and executed commission backfill script
- Processed all 1,127 completed transactions (`trang_thai = 'Da den lam'`)
- Calculated commissions for entire MLM hierarchy (levels 0-4)
- Created 2,356 commission records in the database

**Result:**
- Commissions now visible in admin dashboard
- All historical transactions have commission records
- Commission filtering (by CTV, month, level) now works correctly

---

## Version 1.5.0 - December 28, 2025

### Bulk Data Import from Google Sheets

**Time:** 23:30 (GMT+7)

---

### Data Import Summary

Successfully imported production data from Google Sheets:

| Data Type | Records | Source |
|-----------|---------|--------|
| CTV | 52 | `Du lieu - CTV.csv` |
| Auto-created CTV | 109 | From customer data |
| Customers | 6,800 | `Du lieu - Check trung.csv` |

### Import Script Created

**File:** `import_csv_data.py`

**Features:**
- Topological sorting for CTV hierarchy (referrers inserted first)
- Date format conversion (DD/MM/YYYY to YYYY-MM-DD)
- Currency parsing (14.100.000 to 14100000)
- Case-insensitive CTV code matching
- Auto-creation of missing CTVs from customer data
- Batch insert with progress reporting
- Data verification report

**Usage:**
```bash
python3 import_csv_data.py              # Import all data
python3 import_csv_data.py --ctv-only   # CTVs only
python3 import_csv_data.py --customers-only  # Customers only
python3 import_csv_data.py --dry-run    # Preview without inserting
```

### Database Schema Updates

Columns modified to handle real-world data:
- `khach_hang.gio` VARCHAR(20) -> VARCHAR(100)
- `khach_hang.sdt` VARCHAR(15) -> VARCHAR(50)
- `khach_hang.trang_thai` VARCHAR(50) -> VARCHAR(100)

### Data Verification Results

- CTV hierarchy depth: 10 levels
- Total revenue tracked: 32+ billion VND
- Date range: 2020-2025
- Top performers identified with revenue breakdown

---

## Version 1.4.0 - January 2025

### Database Optimization Analysis & Recommendations

**Time:** January 2025

---

### Database Performance Analysis

**Analysis Completed:**
- Reviewed current MySQL setup and query patterns
- Identified optimization opportunities
- Created comprehensive database recommendation document

**Key Findings:**
- MySQL is appropriate for current use case (structured relational data)
- Performance can be improved 5-10x with proper indexing
- No need to switch databases at current scale

**Files Added:**
- `DATABASE_RECOMMENDATION.md` - Comprehensive database analysis and recommendations
- `optimize_database.py` - Script to add indexes and optimize queries

**Recommendations:**
1. **Stay with MySQL** - Optimize current setup first
2. **Add composite indexes** - For phone lookups, date ranges, CTV queries
3. **Implement caching** - Redis for frequently accessed data
4. **Monitor performance** - Track query times as data grows

**Next Steps:**
- Run `python optimize_database.py` to add performance indexes
- Consider PostgreSQL only if >10M customers
- Consider hybrid approach (MySQL + Elasticsearch) only for advanced search needs

---

## Version 1.3.0 - December 28, 2025

### CTV System Restructure - New Customer Management

**Time:** 18:55 (GMT+7)

---

### New Features Added

#### Database Schema Changes

**New Table: `khach_hang`** (Customer Transactions)
- `id` INT PRIMARY KEY AUTO_INCREMENT
- `ngay_nhap_don` DATE - Order entry date
- `ten_khach` VARCHAR(100) - Customer name
- `sdt` VARCHAR(15) INDEX - Phone number (for duplicate check)
- `co_so` VARCHAR(100) - Facility/location
- `ngay_hen_lam` DATE - Appointment date (key for commission)
- `gio` VARCHAR(20) - Time
- `dich_vu` VARCHAR(500) - Service
- `tong_tien` DECIMAL(15,0) - Total amount (commission basis)
- `tien_coc` DECIMAL(15,0) - Deposit
- `phai_dong` DECIMAL(15,0) - Remaining
- `nguoi_chot` VARCHAR(20) FK - CTV code
- `ghi_chu` TEXT - Notes
- `trang_thai` VARCHAR(50) - Status (Da den lam, Da coc, Huy lich, Cho xac nhan)

**New Table: `hoa_hong_config`** (Commission Rates)
| Level | Percent | Description |
|-------|---------|-------------|
| 0 | 25.0% | Doanh so ban than |
| 1 | 5.0% | Level 1 (truc tiep gioi thieu) |
| 2 | 2.5% | Level 2 |
| 3 | 1.25% | Level 3 |
| 4 | 0.625% | Level 4 (cap cuoi) |

#### Public Phone Duplicate Check (No Auth Required)

**New API Endpoint:** `POST /api/check-duplicate`
- Input: `{ "phone": "0979832523" }`
- Output: `{ "is_duplicate": true/false, "message": "..." }`
- Duplicate conditions (ANY = duplicate):
  1. `trang_thai IN ('Da den lam', 'Da coc')`
  2. `ngay_hen_lam >= TODAY AND < TODAY + 180 days`
  3. `ngay_nhap_don >= TODAY - 60 days`

**Dashboard UI:** Added phone check input in header
- Shows "TRUNG" (red) or "KHONG TRUNG" (green)
- No login required
- Enter key support

#### CTV Portal Enhancements

**New Page: "Khach Hang Cua Toi" (My Customers)**
- Lists all customers where `nguoi_chot` = logged-in CTV
- Date range filter on `ngay_hen_lam`
- Status filter (Da den lam, Da coc, Huy lich, Cho xac nhan)
- Summary stats (total, completed, pending, revenue)

**New API Endpoints:**
- `GET /api/ctv/customers` - List CTV's customers
  - Query params: `?from=YYYY-MM-DD&to=YYYY-MM-DD&status=...`
- `GET /api/ctv/commission` - Commission with date filter
  - Query params: `?from=YYYY-MM-DD&to=YYYY-MM-DD`
  - Only counts transactions where `trang_thai = 'Da den lam'`
- `POST /api/ctv/check-phone` - Phone check (requires auth)

**Dashboard Additions:**
- Phone check card at top of dashboard
- Date filter for commission calculation

**Earnings Page Additions:**
- Date range filter for `ngay_hen_lam`
- New "Hoa Hong Theo Khach Hang" section
- Commission breakdown by level with date filtering

#### Updated Commission Calculation

- Commission now based on `khach_hang` table instead of `services`
- Only counts transactions where `trang_thai = 'Da den lam'`
- Filter by `ngay_hen_lam` date range
- Uses rates from `hoa_hong_config` table

#### Migration Script

**New File: `migrate_khach_hang.py`**
- Creates `khach_hang` and `hoa_hong_config` tables
- Inserts sample customer data with various statuses
- Run: `python3 migrate_khach_hang.py sample`

---

### Files Modified/Created

| File | Action |
|------|--------|
| `migrate_khach_hang.py` | Created - New migration script |
| `modules/mlm_core.py` | Modified - Updated commission logic, added `hoa_hong_config` support |
| `modules/ctv_routes.py` | Modified - Added customer endpoints, date filter |
| `backend.py` | Modified - Added public check-duplicate endpoint |
| `dashboard.html` | Modified - Added phone check UI |
| `templates/ctv_portal.html` | Modified - Added customer list, date filter, phone check |

---

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

