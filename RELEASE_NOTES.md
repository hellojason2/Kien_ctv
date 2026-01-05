# Release Notes - CTV Dashboard

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

### Files Modified
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
