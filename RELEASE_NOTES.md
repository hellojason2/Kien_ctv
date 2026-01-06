# Release Notes - CTV Dashboard

## [2026-01-06 03:45] - Large File Handling Tool
Added a utility script to handle files exceeding the 50MB synchronization limit.

### Features
- **File Chunker**: `file_chunker.py` allows splitting large files into 45MB chunks and reassembling them.
- **Usage**:
  - Split: `python3 file_chunker.py split <file>`
  - Join: `python3 file_chunker.py join <file>`

## [2026-01-06 02:35] - Bulk Password Reset
Reset all CTV passwords to `ctv123` as requested.

### Actions Performed
- Updated `password_hash` for all records in `ctv` table.
- Verified update on a sample record.

## [2026-01-06 02:55] - Client Management View Toggle
Added a feature to switch between Grid (Card) view and List (Table) view on the Client Management page.

### Features
- **View Toggle**: Added buttons to switch between Grid and List views.
- **Table View**: Implemented a detailed table view showing Client, Phone, Facility, First Visit, Closer, and Services.
- **Persistence**: The selected view preference is saved in the browser (localStorage).
- **Design**: Table view matches the "Green Header/Glassy" theme with clean typography.
- **Refinement**: Client names are now displayed in a unified green gradient badge with fixed dimensions for perfect alignment.
- **UI Polish**: Aligned the view toggle buttons with the search bar for a consistent layout.

## [2026-01-06 03:15] - Google Sheets Sync Optimization
Improved the sync worker to handle blank rows more intelligently.

### Improvements
- **Auto-Cleanup**: Rows marked as "update" but containing no data (blank rows) are now automatically deleted from the Google Sheet.
- **Efficiency**: Prevents processing of empty records and keeps the sheet clean.

## [2026-01-06 03:25] - Client Commission Report
Added a detailed commission report feature to the Client Management page.

### Features
- **Interactive Report**: Clicking a client's name (in Grid or Table view) opens a detailed Commission Report modal.
- **Breakdown**: Shows total revenue and total commission paid for that client.
- **Transaction Details**: Lists every transaction/service with a breakdown of commissions paid to the hierarchy (Level 0, Level 1, etc.).
- **Visualization**: Clearly shows who earned what from each service, including rates and amounts.

---

## [2026-01-06 02:45] - Fix Client Management Page Styling
Restored and updated CSS for the Client Management page to match the preferred design.

### Fixes
- Recreated `static/css/admin/clients.css` which was found to be empty.
- Updated styling to match the "Green Header" design:
  - Dark green card headers with white text.
  - Clean white background for info rows.
  - Hidden "Not Deposited" status badge in the client info row as requested.

---

## [2026-01-06 01:40] - Commission Settings UI Improvements
Improved the "Commission Settings" page for better user experience.

### Improvements
- **Save Button Logic**: The "Save Changes" button is now disabled (grayed out) by default and only becomes active when you actually change a commission rate.
- **Visual Feedback**: This prevents accidental clicks and clearly indicates when there are unsaved changes.
- **Auto-Disable**: After saving, the button automatically disables again until further changes are made.

### Files Modified
- `static/js/admin/settings.js` - Added change detection logic.
- `templates/admin/pages/settings.html` - Set initial button state to disabled.
- `static/js/admin/navigation.js` - Ensured settings are loaded correctly on navigation.

---

## [2026-01-06 01:30] - Automatic Commission Recalculation on Settings Change
Ensured that changing commission rates triggers a system-wide recalculation.

### Improvements
- **Auto-Recalculate**: When commission rates (L0-L4) are updated in the "Commission Settings" page, the system now automatically recalculates all historical commissions to reflect the new rates.
- **Consistency**: Guarantees that the "Commission Report" always matches the currently active commission settings.

### Files Modified
- `modules/admin/commissions.py` - Added `recalculate_all_commissions` call to `update_settings` endpoint.

---

## [2026-01-06 01:20] - Commission Calculation Optimization
Refactored commission calculation to be event-driven for better performance and reliability.

### Improvements
- **Event-Driven Calculation**: Commissions are now calculated immediately when data is synced from Google Sheets, rather than on every page load of the Admin Panel.
- **Performance**: The "Commission Report" page now loads much faster as it queries pre-calculated data.
- **Zero Commission Fix**: Ran a full recalculation to fix historical records that were missing commissions due to previous case-sensitivity issues.
- **Reliability**: Added a safety net in the sync worker to ensure all new records are processed.

### Files Modified
- `modules/admin/commissions.py` - Removed read-time calculation trigger.
- `sync_worker.py` - Added write-time calculation trigger.

---

## [2026-01-06 00:45] - Commission Calculation Fixes
Fixed issues where commissions were not being generated for some transactions due to case sensitivity.

### Improvements
- **Case-Insensitive Matching**: Updated commission calculation logic to match CTV codes case-insensitively (e.g., "ctv001" matches "CTV001").
- **Hierarchy Traversal**: Updated hierarchy lookups to be case-insensitive, ensuring the full upline is found regardless of input format.
- **Reliability**: Ensures that revenue records from Google Sheets (which might have inconsistent casing) correctly trigger commissions.

### Files Modified
- `modules/mlm/commissions.py` - Updated JOIN conditions.
- `modules/mlm/hierarchy.py` - Updated recursive queries.

---

## [2026-01-05 23:55] - Database Connection Retry Logic
Implemented automatic retry mechanism for login operations to handle transient network failures.

### Improvements
- **Login Retry**: `admin_login` and `ctv_login` now automatically retry up to 3 times if a database connection error (timeout, closed, SSL) occurs.
- **Connection Discard**: Failed connections are now explicitly discarded from the pool to prevent reuse of bad connections.
- **Enhanced Stability**: This addresses "SSL SYSCALL error: Operation timed out" issues common in cloud environments.

### Files Modified
- `modules/auth.py` - Added retry loop and error handling.
- `modules/db_pool.py` - Updated `return_db_connection` to support discarding connections.

---

## [2026-01-05 23:50] - Database Connection Stability Fixes
Implemented robust connection handling to prevent timeouts and "closed connection" errors.

### Improvements
- **TCP Keepalive**: Enabled TCP keepalive settings to prevent firewalls from dropping idle connections.
- **Connection Validation**: Added automatic validation (`SELECT 1`) when retrieving connections from the pool.
- **Auto-Recovery**: If a pooled connection is dead, it is automatically discarded and replaced with a fresh connection.
- **Timeout Increase**: Increased connection timeout from 10s to 15s.

### Files Modified
- `modules/db_pool.py` - Added keepalive params, validation logic, and fallback mechanism.

---

## [2026-01-05 21:00] - Google Sheets Live Sync Worker
Added background worker that syncs data from Google Sheets to PostgreSQL database in real-time.

### Features
- **Automatic Sync**: Polls Google Sheet every 30 seconds for new/updated rows
- **3 Tabs Supported**:
  - `Khach hang Tham my` -> `khach_hang` table
  - `Khach hang Nha khoa` -> `khach_hang` table
  - `Khach gioi thieu` -> `customers` + `services` tables
- **Column A Status**: Processes rows where Column A = "update" or empty
- **Feedback Loop**: Marks processed rows as "DONE" to prevent re-processing
- **Upsert Logic**: Updates existing records by phone number, or inserts new ones
- **CTV Auto-Creation**: Creates CTV accounts from referrer codes automatically

### Files Created/Modified
| File | Action |
|------|--------|
| `sync_worker.py` | Created - Main sync worker |
| `google_credentials.json` | Created - Service account credentials |
| `requirements.txt` | Updated - Added gspread, google-auth |
| `Procfile` | Updated - Added worker process |
| `.gitignore` | Created - Ignore credentials and cache files |

### How to Use
1. Share your Google Sheet with: `sheets-api-access@gen-lang-client-0960167774.iam.gserviceaccount.com`
2. Deploy to Railway (worker will start automatically)
3. Add new rows with "update" in Column A, or leave empty
4. Worker syncs data and marks rows as "DONE"

### Railway Deployment
The `Procfile` now includes:
```
web: python backend.py
worker: python sync_worker.py
```

---

## [2026-01-05 15:45] - CTV Data Import
Imported 45 CTV records from TSV file with proper hierarchy.

### Data Imported
| Rank | Count |
|------|-------|
| Cong Tac Vien | 27 |
| Giam Doc Kinh Doanh | 8 |
| Chuyen Vien Kinh Doanh | 6 |
| Truong Phong Kinh Doanh | 4 |

### Root CTVs (4 total)
- 972020908 - Tran Trung Kien [Giam Doc Kinh Doanh]
- 343287351 - Vu Tuan Linh [Chuyen Vien Kinh Doanh]
- 988196528 - Than Hai Yen [Cong Tac Vien]
- 963831092 - Ngo Phuong Hanh [Cong Tac Vien]

### Hierarchy
- Phone number used as `ma_ctv` (CTV code)
- `nguoi_gioi_thieu` references referrer's phone number
- Vietnamese rank names stored in `cap_bac`

---

## [2026-01-05 15:30] - Full Database Reset
Complete database wipe and restoration to default state.

### Actions Performed
- Dropped all existing tables (CASCADE)
- Recreated all 12 tables from `schema/postgresql_schema.sql`
- Restored default Admin account (`admin` / `admin123`)
- Restored default Commission configurations (Levels 0-4)
- Cleared all CTV records
- Cleared all Customer/Khach Hang records
- Cleared all Commission records
- Cleared all Activity logs
- Redis cache cleared (if available)

### Tables Restored
| Table | Records |
|-------|---------|
| admins | 1 (default) |
| hoa_hong_config | 5 (levels 0-4) |
| commission_settings | 5 (levels 0-4) |
| ctv | 0 |
| customers | 0 |
| khach_hang | 0 |
| commissions | 0 |
| services | 0 |
| sessions | 0 |
| activity_logs | 0 |

---

## [2026-01-05 10:15] - Admin Panel Theme Redesign (White/Glassy)
Complete visual overhaul of the admin panel from dark mode to a modern light theme.

### Design Changes
| Element | Before | After |
|---------|--------|-------|
| Background | Black (#0a0a0f) | Light gray gradient (#f5f7fa) |
| Panels/Cards | Dark (#12121a) | White with backdrop blur |
| Accent Color | Cyan (#06b6d4) | Green (#4a7c23) |
| Font | JetBrains Mono | Inter |
| Borders | Dark (#27272a) | Light (#e5e7eb) |
| Shadows | None | Soft shadows |

### Features
- **Glassy effect** on all panels with `backdrop-filter: blur(20px)`
- **Green gradient** for active sidebar items and primary buttons
- **Soft shadows** for depth and hierarchy
- **Color-coded level badges** (L0 green, L1 yellow, L2 red, L3 blue, L4 purple)
- **Improved contrast** for readability on light backgrounds

### Files Updated (8 CSS files + 1 template)
- `static/css/admin/base.css` - CSS variables
- `static/css/admin/layout.css` - Sidebar, stats grid
- `static/css/admin/components.css` - Buttons, cards, modals, login
- `static/css/admin/forms.css` - Inputs, dropdowns
- `static/css/admin/tables.css` - Tables
- `static/css/admin/hierarchy.css` - Tree view
- `static/css/admin/clients.css` - Client cards
- `static/css/admin/activity-logs.css` - Event badges
- `templates/admin/base.html` - Font changed to Inter

---

## [2026-01-05 03:30] - Enhanced Commission Debug Details
- Added ability to view Client Details by clicking on a Commission row in the debug modal
- **Feature**: Click any row in "Commission Breakdown" table to see a popup with Client Name, Phone, Service, and Transaction Date
- **Backend**: Updated `/api/admin/debug/ctv-detail/<ctv_code>` to return extended client info (phone, service, closer) for both direct and indirect commissions
- **Frontend**: Added `client-info-modal` and click handlers to commission rows
- This allows identifying exactly *who* the client is for every commission, even for Level > 0 commissions (indirect sales)

## [2026-01-05 03:20] - Added Commission Debug Page (TEMPORARY)
- Created temporary debug page at `/admin/debug/commission-verify`
- Split panel view: Left shows CTV hierarchy, Right shows raw database tables
- **Bidirectional highlighting**: Click left to highlight in raw data, click right to scroll to hierarchy
- Shows commission rates, all CTVs, all clients (grouped), and all commissions
- Click any CTV node to see detailed breakdown with "Match?" verification
- **DELETE THESE FILES WHEN DONE**: `modules/admin/debug.py`, `templates/admin/pages/debug-commission.html`, `static/js/admin/debug-commission.js`

## [2026-01-04 10:15] - Added Auto Cache Busting for Static Files
- Added version-based cache busting to all CSS/JS files
- When deploying updates, change `APP_VERSION` in `backend.py` and all browsers will fetch fresh files
- No more manual browser refresh needed after deploys

### How to Use
When deploying, update the version in `backend.py`:
```python
APP_VERSION = "2026.01.05"  # Change this on each deploy
```

### Files Modified
- `backend.py` - Added APP_VERSION constant and context processor
- `templates/ctv/base.html` - Added `?v={{ version }}` to all static files
- `templates/admin/base.html` - Added `?v={{ version }}` to all static files

## [2026-01-04 09:45] - Fixed Commission Calculation Bug on CTV Portal
- Fixed bug where "Commission" card showed incorrect value (e.g., 45M commission on 20M revenue)
- Root cause: `monthly_earnings` was reading from commissions table which had corrupt/duplicate data
- Solution: Now calculates commission from source data (revenue × rate) same as Recent Commissions table

### What Was Fixed
- Changed `/api/ctv/me` endpoint to calculate commission from khach_hang + services tables
- Commission is now correctly calculated as: (period revenue) × (level 0 rate)
- This matches the calculation used by the `/api/ctv/commission` endpoint
- `modules/ctv/profile.py` - Updated monthly_earnings calculation to use source data instead of commissions table

### Result
- Total Earnings: 20,000,000đ (revenue)
- Commission: 5,000,000đ (25% of 20M) ✓ Correct!

## [2026-01-04 09:30] - Fixed Data Indicators Showing Incorrectly on CTV Portal
- Fixed bug where red envelope indicators were showing on ALL date filter buttons regardless of data availability
- CSS was not properly hiding indicators for emoji/icon/custom types - they were overriding the `display: none` rule
- JavaScript was setting inline display styles that bypassed CSS controls

### What Was Fixed
- Indicators now only show when the button has the `has-data` class (set by API response)
- Removed inline display style settings from `indicator_config.js`
- Updated CSS specificity to properly control indicator visibility

### Files Modified
- `static/css/ctv/components.css` - Fixed indicator display rules for all types (emoji, icon, custom, dot)
- `static/js/ctv/indicator_config.js` - Removed inline display style overrides

### Behavior
- Indicators only appear on date filter buttons when the API confirms data exists for that period
- Empty periods (no customers or services) will NOT show indicators

## [2026-01-04 04:00] - Database Schema Validation & Error Detection
- Added automatic database schema validation on page load
- Shows clear "Database Error" modal if connected to wrong database
- 10-second timeout for database connection checks
- Validates required tables: ctv, khach_hang, commissions, admins, sessions
- Validates essential columns for each table

### How It Works
