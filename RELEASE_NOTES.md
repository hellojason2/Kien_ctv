# Release Notes - CTV Dashboard

## Version 1.9.2 - December 30, 2025

### Activity Logs - Grouped View & Suspicious IP Detection

**Time:** December 30, 2025

---

#### Overview

Enhanced the Activity Logs page with grouped view and suspicious IP detection. Logs are now grouped by user+IP combination into collapsible tabs, making it easier to review activity patterns. Added automatic detection and alerting for IPs logged into multiple accounts.

#### New Features

**1. Grouped View (Collapsible Tabs)**
- Logs are now grouped by unique user+IP combinations
- Each group shows: User type, User ID, IP address, Activity count, Last activity timestamp
- Click to expand and see detailed logs for that group
- Toggle between Grouped View and traditional Table View

**2. Suspicious IP Detection**
- Automatically detects IPs logged into multiple different accounts
- Shows alert banner at top of Activity Logs page when suspicious IPs found
- Each suspicious IP shows all associated accounts (Admin or CTV)
- Groups with suspicious IPs are flagged with "Multi-Account IP" badge

#### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/activity-logs/grouped` | GET | Get logs grouped by user+IP combination |
| `/api/admin/activity-logs/suspicious-ips` | GET | Get IPs with multiple accounts |
| `/api/admin/activity-logs/details` | GET | Get detailed logs for specific user+IP |

#### Backend Changes

**File: `modules/activity_logger.py`**
- Added `get_suspicious_ips()` - Finds IPs logged into multiple accounts (last 7 days)
- Added `get_activity_logs_grouped()` - Returns logs grouped by user+IP

**File: `modules/admin_routes.py`**
- Added 3 new endpoints for grouped logs and suspicious IP detection
- Updated imports for new functions

#### Frontend Changes

**File: `templates/admin.html`**
- Added suspicious IP alert banner (red themed, shows when IPs with multiple accounts detected)
- Added grouped logs container with collapsible sections
- Added "Grouped View" toggle checkbox
- Added new JavaScript functions:
  - `toggleGroupedView()` - Switch between grouped and table view
  - `loadGroupedLogs()` - Fetch and render grouped logs
  - `displaySuspiciousIPs()` - Render suspicious IP alert
  - `toggleLogGroup()` - Expand/collapse individual groups
  - `loadFlatLogs()` - Original table view (refactored)
- Added new translation keys for VI and EN

#### UI Components

**Suspicious IP Alert:**
- Red-themed alert banner
- Shows IP address with all associated accounts
- Account badges color-coded by type (purple=admin, cyan=CTV)

**Grouped Log Entry:**
- Collapsible header with chevron icon
- Shows user type badge, user ID, IP address in monospace
- "Multi-Account IP" warning badge for suspicious groups
- Activity count and last activity timestamp
- Expandable detail table with timestamp, event, endpoint, status, details

#### Translation Keys Added

| Key | Vietnamese | English |
|-----|-----------|---------|
| `grouped_view` | Xem nhom | Grouped View |
| `groups` | nhom | groups |
| `activities` | hoat dong | activities |
| `click_to_load` | Bam de tai chi tiet | Click to load details |
| `suspicious_ips_detected` | Phat hien IP dang nghi | Suspicious IPs Detected |
| `multi_account_ip` | Nhieu tai khoan | Multi-Account IP |
| `accounts` | tai khoan | accounts |

#### Files Modified

| File | Changes |
|------|---------|
| `modules/activity_logger.py` | Added `get_suspicious_ips()`, `get_activity_logs_grouped()` |
| `modules/admin_routes.py` | Added 3 new endpoints, updated imports |
| `templates/admin.html` | Added grouped view UI, suspicious IP alert, new JS functions, translations |

---

## Version 1.9.1 - December 29, 2025

### Sidebar Menu Hover Tooltips (Language-Aware) - All Pages

**Time:** December 29, 2025

---

#### Overview

Added hover tooltip functionality with full language support (Vietnamese/English) to sidebar menu icons across **ALL dashboards**. When hovering over an icon in the sidebar, a styled tooltip appears showing what the icon represents. **All tooltips are language-aware and update when switching between Vietnamese (VI) and English (EN).**

#### Changes Made

**File: `dashboard.html` (Main Dashboard)**
- Added language toggle buttons (VI/EN) in top-right corner
- Added full translations object with Vietnamese and English strings
- Added CSS tooltip styles using `::before` and `::after` pseudo-elements
- Added `data-i18n-tooltip` attributes to all sidebar icons
- Added `data-i18n` and `data-i18n-placeholder` for phone check UI
- Updated `checkPhoneDuplicate()` to use translated strings
- Tooltips translate when switching language:
  - VI: "Trang Chu", "Doi Chieu", "Khach Hang", "Quan Tri", "Cong CTV"
  - EN: "Home", "Phone Check", "Customers", "Admin Panel", "CTV Portal"
- Phone check button and results now translate:
  - VI: "Doi Chieu", "TRUNG", "KHONG TRUNG", "Nhap SDT"
  - EN: "Check", "DUPLICATE", "NOT DUPLICATE", "Enter Phone"

**File: `templates/admin.html`**
- Added CSS tooltip styles for `.sidebar-nav a` and `.home-btn` elements
- Added `data-i18n-tooltip` attributes to all sidebar links
- Updated `applyTranslations()` function to handle `data-i18n-tooltip` attributes
- Tooltips translate when switching language (VI/EN toggle):
  - VI: "Trang Chu", "Tong Quan", "Quan Ly CTV", "Cap Bac", "Hoa Hong", "Khach Hang", "Cai Dat", "Nhat Ky", "Dang Xuat"
  - EN: "Home Dashboard", "Overview", "CTV Management", "Hierarchy", "Commissions", "Clients", "Settings", "Activity Logs", "Logout"
- Tooltips only appear on mobile when sidebar text is hidden

**File: `templates/ctv_portal.html`**
- Updated CSS tooltip styles to use `data-tooltip` attribute instead of `title`
- Updated `applyTranslations()` function to set `data-tooltip` from `data-i18n-title` keys
- Removed hardcoded `title` attributes from sidebar icons
- Tooltips translate when switching language (VI/EN toggle):
  - VI: "Tong Quan", "Hoa Hong", "Mang Luoi", "Khach Hang", "Tim Kiem", "Cai Dat", "Dang Xuat"
  - EN: "Overview", "Earnings", "Network", "Customers", "Search", "Settings", "Logout"

#### Tooltip Features

- Dark background (#1a1a1a) with white text
- Rounded corners (8px border-radius)
- Arrow pointer using CSS borders
- Smooth fade-in animation (0.2s ease)
- Box shadow for depth
- Responsive positioning (right on desktop, above on mobile)
- **Language-aware:** Automatically updates when VI/EN language is toggled
- **Persistent:** Language preference saved to localStorage

---

## Version 1.9.0 - December 30, 2025

### Major Database Performance Optimization

**Time:** December 30, 2025

---

#### Overview

Fixed critical performance issue where the "Khách Hàng" (Clients) page was taking forever to load. Reduced API response time from **3+ seconds to ~1.2 seconds** (60% improvement).

#### Root Cause Analysis

The slow loading was caused by multiple issues:
1. **N+1 Query Problem:** For 50 clients, the system was executing 51 separate database queries (1 for list + 50 for services)
2. **Multiple Database Connections:** Each request opened 4-6 separate database connections (~0.4s each)
3. **No Connection Pooling:** Every database call established a new TCP connection to Railway's remote database
4. **Synchronous Activity Logging:** Activity logs blocked the response while writing to database

#### Changes Made

**New File: `modules/db_pool.py`**
- Singleton MySQL connection pool (10 connections)
- Reuses connections instead of creating new ones
- Fallback to direct connection if pool fails

**Modified: `modules/admin_routes.py`**
- Refactored `/api/admin/clients-with-services` endpoint
- Changed from N+1 queries to 2-query batch approach:
  1. Get paginated client list (GROUP BY query)
  2. Batch-fetch all services for those clients (single query with window function)
- Smart count query optimization (skips on last page)

**Modified: `modules/auth.py`**
- Optimized `@require_admin` decorator
- Combined session validation + admin info into single JOIN query (saves ~0.5s)
- Removed redundant token checking (was checking 3 locations separately)

**Modified: `modules/activity_logger.py`**
- Made activity logging **asynchronous**
- Uses background thread with queue to avoid blocking API responses
- Activity logs written after response is sent to client

**Database Indexes Added:**
- `idx_khach_hang_sdt_ten_ngay` (sdt, ten_khach, ngay_nhap_don) - for GROUP BY optimization
- `idx_khach_hang_ten` (ten_khach) - for name search

#### Performance Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| API Response Time | 3.1s | 1.2s | 60% faster |
| Database Queries per Request | 51 | 3 | 94% reduction |
| DB Connections per Request | 4-6 | 1 | 80% reduction |

#### Technical Details

**Query Optimization:**
```sql
-- Before: N+1 (51 queries for 50 clients)
SELECT ... FROM khach_hang GROUP BY sdt, ten_khach LIMIT 50;
-- Then for EACH client:
SELECT ... FROM khach_hang WHERE sdt = ? AND ten_khach = ? LIMIT 3;

-- After: 2 queries total
-- Query 1: Get clients
SELECT ... FROM khach_hang GROUP BY sdt, ten_khach LIMIT 50;
-- Query 2: Batch fetch all services with window function
SELECT * FROM (
    SELECT ..., ROW_NUMBER() OVER (PARTITION BY sdt, ten_khach ORDER BY ngay_nhap_don DESC) as rn
    FROM khach_hang
    WHERE (sdt, ten_khach) IN ((...), (...), ...)
) WHERE rn <= 3;
```

**Connection Pooling:**
```python
# modules/db_pool.py
pool = MySQLConnectionPool(pool_size=10, pool_reset_session=True, ...)
```

#### Remaining Latency

The remaining ~1.2s is primarily network latency to Railway's remote database (~0.4s per roundtrip). This is unavoidable without:
- Moving to a local database
- Implementing Redis caching
- Using a database proxy/connection manager

#### Files Modified

| File | Changes |
|------|---------|
| `modules/db_pool.py` | NEW - Connection pool singleton |
| `modules/admin_routes.py` | Optimized client query, uses pool |
| `modules/auth.py` | Combined auth queries, uses pool |
| `modules/activity_logger.py` | Async logging with queue, uses pool |
| `modules/ctv_routes.py` | Uses connection pool |
| `modules/mlm_core.py` | Uses connection pool |

---

## Version 1.8.2 - December 30, 2025

### Activity Logs & Clients Page Fix + Auth Fix

**Time:** December 30, 2025

---

#### Bug Fix 1: API Function Name

Fixed Activity Logs and Clients page not loading data due to incorrect function call.

**Changes Made:**

**Frontend (`templates/admin.html`):**
- Fixed `apiCall` to `api` in 3 locations:
  - `loadClientsWithServices()` - Line 2410
  - `loadActivityLogs()` - Line 2727
  - `loadActivityStats()` - Line 2855

**Issue Details:**
The code was calling a non-existent `apiCall` function instead of the correct `api` function. This caused:
- Activity Logs table stuck on "Loading..." forever
- Clients page not loading data
- No error visible because the undefined function failed silently

---

#### Bug Fix 2: Cookie-Based Auth Not Working

Fixed dashboard not showing after cookie-based login (login overlay stayed visible).

**Changes Made:**

**Frontend (`templates/admin.html`):**
- Modified `checkAuth()` function to always check with server
- Previously only checked if localStorage token existed
- Now checks server auth via cookie even without localStorage token

**Issue Details:**
The `checkAuth()` function had a condition `if (authToken)` that prevented it from calling the server when localStorage was empty. But the server uses cookie-based auth (`session_token` cookie), so users who were logged in via cookie but had no localStorage token would see the login overlay on the dashboard.

---

## Version 1.8.1 - December 29, 2025

### Clients Page Pagination

**Time:** December 29, 2025

---

#### Overview

Added pagination to the Clients page in Admin Panel. Previously the page was limited to 50 clients; now it shows all 5,924+ clients with 50 per page and navigation controls.

#### Changes Made

**Backend (`modules/admin_routes.py`):**
- Modified `/api/admin/clients-with-services` endpoint
- Added `page` and `per_page` query parameters
- Returns `pagination` object with page, per_page, total, total_pages

**Frontend (`templates/admin.html`):**
- Added pagination controls below the clients grid
- Added client count display in header
- Search now resets to page 1
- Added `updateClientsPagination()` function

#### API Response Changes

```json
{
  "status": "success",
  "clients": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 5924,
    "total_pages": 119
  }
}
```

---

## Version 1.8.0 - December 29, 2025

### Website Activity Logger System

**Time:** December 29, 2025

---

#### Overview

Added comprehensive activity logging system to track all website activities including logins, logouts, failed login attempts, API calls, CTV management actions, and commission adjustments. All logs are accessible via a new Activity Logs tab in the Admin Panel.

#### New Files Created

| File | Purpose |
|------|---------|
| `migrate_activity_logs.py` | Database migration script for activity_logs table |
| `modules/activity_logger.py` | Core logging functions and Flask middleware |

#### Database Schema

**New Table: `activity_logs`**
- `id` INT PRIMARY KEY AUTO_INCREMENT
- `timestamp` DATETIME - When the event occurred
- `event_type` VARCHAR(50) - Type of event (login_success, login_failed, logout, api_call, etc.)
- `user_type` VARCHAR(20) - admin, ctv, or null for anonymous
- `user_id` VARCHAR(100) - Username or ma_ctv
- `ip_address` VARCHAR(45) - Client IP (supports IPv4/IPv6)
- `user_agent` TEXT - Browser/device information
- `endpoint` VARCHAR(255) - API endpoint or page accessed
- `method` VARCHAR(10) - HTTP method
- `status_code` INT - HTTP response status code
- `details` JSON - Additional context
- `country`, `city` VARCHAR - Geolocation (optional)

**Indexes Added:**
- `idx_timestamp` - For date range queries
- `idx_user` - For user-specific queries
- `idx_event` - For event type filtering
- `idx_ip` - For IP-based lookups

#### Event Types Tracked

| Event Type | Trigger | Details Captured |
|------------|---------|------------------|
| `login_success` | Successful login | user_type, user_id |
| `login_failed` | Failed login attempt | attempted username |
| `logout` | User logout | session info |
| `api_call` | Admin API requests | endpoint, duration |
| `ctv_created` | New CTV created | admin, ctv_code, name |
| `ctv_updated` | CTV modified | admin, changes |
| `ctv_deleted` | CTV deactivated | admin, ctv_code |
| `commission_adjusted` | Manual adjustment | old/new values |
| `data_export` | CSV/data exports | export_type, count |

#### Admin API Endpoints Added

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/activity-logs` | GET | List logs with filtering/pagination |
| `/api/admin/activity-logs/stats` | GET | Get log statistics |
| `/api/admin/activity-logs/export` | GET | Export logs as CSV |
| `/api/admin/activity-logs/cleanup` | POST | Clean up old logs |
| `/api/admin/activity-logs/event-types` | GET | Get event types list |

#### Admin Panel UI

**New Tab: Activity Logs**
- Stats cards: Logins Today, Failed Logins, Unique IPs, Total Logs
- Filters: Event Type, User Type, Date Range, Search
- Paginated table with color-coded event badges
- CSV export functionality
- Responsive design for mobile/tablet

#### Files Modified

| File | Changes |
|------|---------|
| `modules/auth.py` | Added login/logout event logging |
| `modules/admin_routes.py` | Added activity log endpoints, logging for CTV/commission changes |
| `templates/admin.html` | Added Activity Logs tab, UI, and JavaScript functions |
| `backend.py` | Registered activity logging middleware |

#### Integration Points

The logger hooks into:
1. **Auth Module** - Login success/failed, logout events
2. **Admin Routes** - All admin API calls via middleware
3. **CTV Management** - Create, update, delete actions
4. **Commission Adjustments** - Manual commission changes

#### IP Detection

Supports multiple proxy configurations:
- X-Forwarded-For header
- X-Real-IP header
- CF-Connecting-IP (Cloudflare)
- Direct remote address

#### Maintenance

- Logs retained for 90 days by default
- Cleanup endpoint: `POST /api/admin/activity-logs/cleanup`
- IP masking function available for privacy compliance

#### Security

- Admin-only access to logs (uses `@require_admin` decorator)
- PII handling: IP addresses can be masked after configurable days
- Activity logs excluded from logging to prevent infinite loops

---

## Version 1.7.5 - December 29, 2025

### Commission Hover Tooltip Feature

**Time:** December 29, 2025, 11:59 PM

---

#### Overview

Added hover tooltip to commission items in the CTV Portal. When a user hovers over a commission entry in "Tat Ca Hoa Hong" (All Commissions) or "Hoa Hong Gan Day" (Recent Commissions), a tooltip now displays additional information about the transaction source.

#### Changes Made

**File:** `modules/ctv_routes.py`

| Change Type | Description |
|-------------|-------------|
| API Enhancement | Modified `/api/ctv/my-commissions` endpoint to include source CTV, customer, and service info |
| Database JOINs | Added LEFT JOINs to services, ctv, and customers tables |

**New API Response Fields:**

| Field | Description |
|-------|-------------|
| `source_ctv_name` | Name of the CTV who made the sale |
| `source_ctv_code` | Code of the CTV who made the sale |
| `customer_name` | Name of the customer |
| `service_name` | Name of the service/product |

**File:** `templates/ctv_portal.html`

| Change Type | Description |
|-------------|-------------|
| CSS | Added `.commission-tooltip` styling with smooth hover animation |
| JavaScript | Updated `loadRecentCommissions()` and `loadAllCommissions()` to render tooltips |
| Translations | Added `from_ctv` translation key (VI: "Tu CTV", EN: "From CTV") |

**Tooltip Display:**
- Shows on hover over any commission item
- Dark background (#1a1a1a) with white text
- Displays: Source CTV name, Customer name, Service name
- Smooth fade-in animation
- Mobile-responsive (centered on smaller screens)

---

## Version 1.7.4 - December 29, 2025

### CTV Portal Full Translation Fix

**Time:** December 29, 2025, 11:55 PM

---

#### Overview

Fixed translation system in CTV Portal where many elements were not translating when switching between Vietnamese (VI) and English (EN). Now all text elements translate correctly when clicking the language toggle buttons.

#### Changes Made

**File:** `templates/ctv_portal.html`

| Change Type | Description |
|-------------|-------------|
| HTML data-i18n attributes | Added `data-i18n` attributes to all static text elements that were hardcoded |
| JavaScript dynamic content | Updated all `innerHTML` assignments to use `t()` translation function |
| New translation keys | Added 15+ new translation keys for missing strings |

**New Translation Keys Added:**

| Key | Vietnamese | English |
|-----|-----------|---------|
| `direct_level1` | Truc Tiep (Level 1) | Direct (Level 1) |
| `recent_commissions` | Hoa Hong Gan Day | Recent Commissions |
| `select_filter_hint` | Chon ngay va nhan Loc... | Select dates and click Filter... |
| `click_filter_hint` | Nhan Loc de xem danh sach | Click Filter to view list |
| `commission_by_customer` | Hoa Hong Theo Khach Hang | Commission by Customer |
| `no_commissions_period` | Khong co hoa hong... | No commissions in this period |
| `transactions` | Giao Dich | Transactions |
| `revenue` | Doanh Thu | Revenue |
| `total_members` | TONG THANH VIEN | TOTAL MEMBERS |
| `levels_deep` | SO CAP | LEVELS DEEP |
| `direct_recruits` | GIOI THIEU TRUC TIEP | DIRECT RECRUITS |
| `expand_all` | Mo Rong | Expand All |
| `collapse_all` | Thu Gon | Collapse All |
| `ctv_code_col` | Ma CTV | CTV Code |
| `name_col` | Ten | Name |
| `email_col` | Email | Email |
| `phone_col` | SDT | Phone |
| `rank_col` | Cap Bac | Rank |
| `card_view` | Card View | Card View |
| `table_view` | Table View | Table View |
| `search_name_phone` | Tim theo ten hoac SDT... | Search by name or phone... |
| `customer_name` | Ten Khach | Customer Name |
| `appointment_date` | Ngay Hen | Appointment |

**Elements Now Translated:**

1. **Dashboard Page**
   - Phone check title, placeholder, button
   - Stats card labels (Total Earnings, This Month, Network Size, Direct Level 1)
   - Recent Commissions header

2. **Earnings Page**
   - Date filter labels
   - Commission by Customer section
   - All Commissions header
   - Stats by Level header
   - Table headers (Level, Count, Total Commission)

3. **Network Page**
   - Your Network header
   - Tree stats (Total Members, Levels Deep, Direct Recruits)
   - Expand/Collapse buttons
   - Direct Referrals List header
   - Table headers (CTV Code, Name, Email, Phone, Rank)

4. **Customers Page**
   - Card/Table view toggle buttons
   - Search placeholder
   - Date filter labels
   - Status dropdown options
   - Table headers

5. **Search Page**
   - Search in Network header
   - Search placeholder
   - Search hint text
   - Empty state messages

6. **Dynamic Content (JavaScript)**
   - No commissions message
   - No data message
   - No customers message
   - No referrals message
   - Searching indicator
   - Error messages

---

## Version 1.7.3 - December 29, 2025

### Default Start Date in Date Filters

**Time:** December 29, 2025, 11:45 PM

---

#### Overview

All date filter views now automatically default the "From Date" (Tu ngay) to the earliest customer record date for the CTV and their network. This eliminates the need to manually select a start date when filtering data.

#### Changes Made

**Backend (`modules/ctv_routes.py`):**

| Endpoint | Description |
|----------|-------------|
| `GET /api/ctv/earliest-date` | NEW - Returns the earliest `ngay_hen_lam` date from `khach_hang` table for the CTV's network |

**Frontend (`templates/ctv_portal.html`):**

| Change | Description |
|--------|-------------|
| `setDefaultDateFilters()` | NEW - Function that fetches earliest date and sets it as default for all date inputs |
| `showPortal()` | Updated to call `setDefaultDateFilters()` after loading profile |
| Commission date filter | Defaults to earliest date -> today |
| Customer date filter | Defaults to earliest date -> today |

#### How It Works

1. When CTV logs in and portal loads, the system fetches the earliest customer date
2. The earliest `ngay_hen_lam` (appointment date) across all customers in the CTV's network is returned
3. All "From Date" inputs are automatically populated with this date
4. All "To Date" inputs are automatically populated with today's date
5. User can still manually adjust dates as needed

#### Files Modified

| File | Change |
|------|--------|
| `modules/ctv_routes.py` | Added `/api/ctv/earliest-date` endpoint |
| `templates/ctv_portal.html` | Added `setDefaultDateFilters()` function, updated `showPortal()` |

---

## Version 1.7.2 - December 29, 2025

### Remove Level Dropdown from Create CTV Form

**Time:** December 29, 2025, 11:15 PM

---

#### Changes Made

**File:** `templates/admin.html`

| Change | Description |
|--------|-------------|
| Removed Level dropdown | The Level/Bronze/Silver/Gold dropdown has been removed from the "Add New CTV" modal |
| Default value | New CTVs are now automatically assigned "Bronze" level by default |

#### Reason
Simplified the CTV creation process by removing the unnecessary Level selection field.

---

## Version 1.7.1 - December 29, 2025

### Add New CTV Modal - Vietnamese Translation Fix

**Time:** December 29, 2025, 10:45 PM

---

#### Issue
The "Add New CTV" modal in admin panel was displaying labels in English even when Vietnamese language was selected.

#### Changes Made

**File:** `templates/admin.html`

| Element | Before | After |
|---------|--------|-------|
| Modal title | `Add New CTV` (hardcoded) | Uses `data-i18n="add_new_ctv"` |
| CTV Code label | `CTV Code *` (hardcoded) | Uses `data-i18n="ctv_code"` |
| Name label | `Name *` (hardcoded) | Uses `data-i18n="name"` |
| Email label | `Email` (hardcoded) | Uses `data-i18n="email"` |
| Phone label | `Phone` (hardcoded) | Uses `data-i18n="phone"` |
| Referrer label | `Referrer (Nguoi gioi thieu)` (hardcoded) | Uses `data-i18n="referrer_label"` |
| Level label | `Level` (hardcoded) | Uses `data-i18n="level"` |
| Cancel button | `Cancel` (hardcoded) | Uses `data-i18n="cancel"` |
| Create button | `Create CTV` (hardcoded) | Uses `data-i18n="create_ctv"` |
| Referrer dropdown | Hardcoded `None (Root CTV)` | Uses `t('none_root')` function |
| Commission filter | Hardcoded `All CTVs` | Uses `t('all_ctvs')` function |

**New translations added:**
- `ctv_code_placeholder`: "VD: CTV012" (VI) / "e.g., CTV012" (EN)

**Function updates:**
- `populateCTVSelects()`: Now uses translation function for dropdown options
- `setLanguage()`: Now re-populates dropdowns when language changes

---

## Version 1.7.0 - December 29, 2025

### CTV Login System Refactor

**Time:** December 29, 2025

---

### Overview

Major changes to CTV authentication system:
1. CTV codes sanitized - removed Vietnamese diacritics, spaces, and special characters (only alphanumeric allowed)
2. Login changed from email to CTV code (case-insensitive)
3. All passwords reset to "123456"
4. Added password change functionality

### Changes Made

#### New File: `migrate_ctv_codes.py`

Migration script that:
- Sanitizes all `ma_ctv` values (removes accents, spaces, special chars)
- Updates `nguoi_gioi_thieu` references to match new codes
- Updates `khach_hang.nguoi_chot` references
- Resets all CTV passwords to "123456" (hashed)

**Usage:**
```bash
python migrate_ctv_codes.py           # Preview changes
python migrate_ctv_codes.py migrate   # Apply changes
```

#### Backend (`modules/auth.py`)

| Function | Change |
|----------|--------|
| `ctv_login()` | Now authenticates by `ma_ctv` (case-insensitive) instead of email |
| `change_ctv_password()` | NEW - Allows CTVs to change their password |

#### Backend (`modules/ctv_routes.py`)

| Endpoint | Change |
|----------|--------|
| `POST /ctv/login` | Now accepts `ma_ctv` field instead of `email` |
| `POST /api/ctv/change-password` | NEW - Change password endpoint (requires auth) |

#### Frontend (`templates/ctv_portal.html`)

| Change | Description |
|--------|-------------|
| Login form | Changed from Email input to CTV Code input |
| Settings page | NEW - Added settings page with change password form |
| Sidebar | Added settings icon |
| Translations | Added Vietnamese/English for settings section |

### Files Modified

| File | Change |
|------|--------|
| `migrate_ctv_codes.py` | NEW - Migration script |
| `modules/auth.py` | Updated login, added password change |
| `modules/ctv_routes.py` | Updated login endpoint, added change-password endpoint |
| `templates/ctv_portal.html` | Updated login form, added settings page |

### Login Instructions

After running migration:
- **Username:** CTV code (case-insensitive, e.g., "BsDieu" or "BSDIEU")
- **Password:** 123456 (users should change this)

---

## Version 1.6.1 - December 29, 2025

### Phone Duplicate Check - 360 Day Time Limit

**Time:** December 29, 2025

---

### Overview

Added a 360-day time limit to the "Đã đến làm" / "Đã cọc" status condition in the phone duplicate checker. Previously, any record with these statuses would be considered a duplicate regardless of when it occurred. Now, only records within the last 360 days are considered duplicates.

### Changes Made

#### Backend (`backend.py`)

**Modified Duplicate Condition 1:**
- **Before:** `trang_thai IN ('Da den lam', 'Da coc')` - always matched
- **After:** `trang_thai IN ('Da den lam', 'Da coc') AND ngay_hen_lam >= DATE_SUB(CURDATE(), INTERVAL 360 DAY)`

**Updated Logic:**
| Condition | Description | Time Limit |
|-----------|-------------|------------|
| 1 | Status = "Đã đến làm" or "Đã cọc" | Within last 360 days |
| 2 | Future appointment scheduled | Today to +180 days |
| 3 | Order entry date | Within last 60 days |

### Files Modified

| File | Change |
|------|--------|
| `backend.py` | Updated SQL query to add 360-day limit to Condition 1 |

---

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

