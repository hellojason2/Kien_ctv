# Release Notes - CTV Dashboard

## [2026-01-03 03:17] - Ultra-Fast Commission Calculation with Smart Caching
- Implemented smart delta-based commission calculation for instant load times
- Added commission_cache table to track last processed record IDs
- New function `calculate_new_commissions_fast()` only processes NEW records since last calculation
- Second and subsequent requests are instant (cache hit - no calculation needed)
- Reduced commission load time from minutes to < 1 second

### How It Works
1. Cache stores `last_kh_max_id` and `last_svc_max_id` (last processed record IDs)
2. On each request, compare current max IDs with cached max IDs
3. If no new records (current max <= cached max) → return immediately (FAST)
4. If new records exist → only query records with id > last_max_id
5. Calculate commissions for those new records only
6. Update cache with new max IDs

### Performance Results
- First run (backfill): Calculates all missing commissions
- Second run: 0.6s (cache hit - no calculation)
- Subsequent runs: Instant unless new data added

### Files Modified
- `modules/mlm_core.py` - Added `calculate_new_commissions_fast()` and `get_commission_cache_status()`
- `modules/admin_routes.py` - Updated to use fast calculation
- `modules/ctv_routes.py` - Updated to use fast calculation
- `modules/__init__.py` - Exported new functions
- `schema/postgresql_schema.sql` - Added commission_cache table

### New Endpoints
- `GET /api/admin/commission-cache/status` - View cache status for monitoring

### Database Changes
- Added `commission_cache` table with columns:
  - `last_kh_max_id` - Last processed khach_hang ID
  - `last_svc_max_id` - Last processed services ID
  - `total_kh_processed` / `total_svc_processed` - Running totals
  - `last_updated` - Timestamp of last calculation
## [2026-01-03 02:50] - Optimize Commission Calculation with Incremental Updates
- Replaced on-the-fly commission calculation with incremental approach for better performance
- New function `calculate_missing_commissions()` detects transactions without commissions and calculates only those
- Commission summary now uses stored commissions (fast indexed reads) + calculates only missing ones
- Admin stats endpoint now uses incremental calculation instead of recalculating everything
- Commissions are stored once, then reused - only new data triggers calculation
- Significantly faster load times for commission reports with large datasets

### Files Modified
- `modules/mlm_core.py` - Added `calculate_missing_commissions(connection, date_from, date_to)` function
- `modules/admin_routes.py` - Updated `list_commissions_summary()` to use incremental calculation
- `modules/admin_routes.py` - Updated `get_stats()` to use incremental calculation
- `modules/__init__.py` - Exported `calculate_missing_commissions` function

### Performance Improvement Logic
- Before: If commissions table empty → calculate ALL commissions on-the-fly (SLOW)
- After: Always use stored commissions + calculate only MISSING ones (FAST)
- Detection: Compare transaction IDs in commissions table vs khach_hang/services tables
- khach_hang uses negative transaction_id (-id), services uses positive transaction_id (id)

### New Function: calculate_missing_commissions()
```python
calculate_missing_commissions(connection=None, date_from=None, date_to=None)
# Returns: {'khach_hang': count, 'services': count, 'total': count, 'errors': count}
```

### Benefits
1. Fast reads: Always uses indexed commissions table
2. Incremental: Only calculates missing commissions (O(n) where n = missing records)
3. Automatic: Detects and fills gaps automatically on each request
4. Backward compatible: Works even if commissions table is empty
5. No manual backfill needed: Missing commissions calculated on-demand
## [2026-01-03 02:10] - Optimize Commission Calculation with Pre-Calculated Storage
- Changed commission calculation from on-the-fly to pre-calculated storage for performance
- Commissions are now calculated and stored in commissions table when data is created/updated
- Commission summary now reads from stored commissions table (fast) instead of calculating on-the-fly
- Added recalculate_all_commissions() function to backfill commissions for existing data
- Added admin endpoint POST /api/admin/commissions/recalculate to trigger recalculation
- Falls back to on-the-fly calculation only if commissions table is empty (backward compatibility)
- Significantly improved performance for commission summary queries

### Files Modified
- `modules/mlm_core.py` - Added calculate_commission_for_khach_hang(), calculate_commission_for_service(), recalculate_commissions_for_record(), recalculate_all_commissions()
- `modules/admin_routes.py` - Updated commission summary to use stored commissions (fast reads)
- `modules/admin_routes.py` - Added POST /api/admin/commissions/recalculate endpoint
- `modules/__init__.py` - Exported new commission calculation functions

### Performance Improvements
- Commission summary queries are now fast (reads from indexed commissions table)
- No more slow on-the-fly calculations for every request
- Commissions calculated once when data is created/updated, then reused

### New Functions
- calculate_commission_for_khach_hang() - Calculate and store commissions for khach_hang record
- calculate_commission_for_service() - Calculate and store commissions for service record
- recalculate_commissions_for_record() - Recalculate commissions for a single record
- recalculate_all_commissions() - Recalculate all commissions (backfill)

### Usage
- Call POST /api/admin/commissions/recalculate to backfill commissions for existing data
- Commissions will be automatically calculated when new khach_hang/services are created (if hooked up)
- Commission summary now uses stored data for fast queries
## [2026-01-03 01:51] - Fix Commission Summary to Calculate Commissions On-The-Fly
- Fixed commission summary to calculate commissions on-the-fly from revenue instead of only reading commissions table
- Commission now calculated for each CTV based on their level in the hierarchy
- Includes all CTVs who should receive commissions (L0-L4) even if they didn't close deals themselves
- Calculates L0 commission: Revenue from deals they closed × 25%
- Calculates L1-L4 commissions: Revenue from deals closed by their downline × respective rates
- Fixed issue where commission showed 0 despite high revenue in commission reports

### Files Modified
- `modules/admin_routes.py` - Updated `list_commissions_summary()` to calculate commissions on-the-fly

### Commission Calculation Logic
- For each transaction (khach_hang or services) with tong_tien > 0
- Build ancestor chain (upline) starting from the CTV who closed the deal
- Calculate commission for each CTV in the chain:
  - L0 (closer): tong_tien × 25%
  - L1 (direct referrer): tong_tien × 5%
  - L2 (referrer of L1): tong_tien × 2.5%
  - L3 (referrer of L2): tong_tien × 1.25%
  - L4 (referrer of L3): tong_tien × 0.625%
- Sum all commissions for each CTV across all transactions
- Include CTVs in summary even if they only receive commissions from downline (no direct deals)

### Bug Fixes
- Commission summary now shows correct commissions when commissions table is empty
- CTVs who receive commissions from downline are now included in the report
- Commission calculation matches the MLM hierarchy structure (John → Emily → Luke example)
## [2026-01-03 01:45] - Fix Commission Calculation in Admin Stats
- Fixed commission calculation to compute on-the-fly from khach_hang and services tables
- Commission now calculated from tong_tien (total cost) multiplied by commission rate based on CTV level
- If commissions table is empty, calculates commissions dynamically from actual service/client data
- Links each CTV to clients/services via nguoi_chot/ctv_code fields
- Calculates commission for entire CTV hierarchy (up to 4 levels) based on revenue
- Fixed issue where monthly commission showed 0 despite high revenue

### Files Modified
- `modules/admin_routes.py` - Added on-the-fly commission calculation from khach_hang and services tables
- `modules/admin_routes.py` - Imported build_ancestor_chain from mlm_core

### Bug Fixes
- Commission now correctly calculated from tong_tien field in khach_hang and services tables
- Commission calculated for all CTV levels in hierarchy (0-4) based on their commission rates
- Handles cases where commissions table is empty by calculating from source data
- Properly links CTVs to services/clients via nguoi_chot and ctv_code fields

### Commission Calculation Logic
- For each khach_hang/service with tong_tien > 0 and nguoi_chot/ctv_code
- Build ancestor chain (upline) for the CTV who closed the deal
- Calculate commission for each level: tong_tien * commission_rate[level]
- Sum all commissions across all transactions
- Commission rates: Level 0 (25%), Level 1 (5%), Level 2 (2.5%), Level 3 (1.25%), Level 4 (0.625%)
## [2026-01-03 01:40] - Fix Top Earners Error Loading Data
- Fixed top_earners query to handle NULL values properly using COALESCE
- Added error handling for top_earners query with try-catch block
- Improved error messages to show actual error details
- Added better null/undefined checks in JavaScript
- Added console logging for debugging API responses
- Fixed issue where top_earners could be undefined causing "Error loading data" message

### Files Modified
- `modules/admin_routes.py` - Added COALESCE to top_earners query, improved error handling
- `static/js/admin/overview.js` - Added better null checks, improved error messages, added logging

### Bug Fixes
- Top earners section no longer shows "Error loading data" when there are no commissions
- Properly handles empty top_earners array
- Better error messages show actual error details for debugging
## [2026-01-03 01:33] - Fix Admin Overview Stats Loading and Add Loading States
- Fixed stats not loading when date range filters are selected (3 months, etc.)
- Added loading states with skeleton loaders for all stat cards
- Added loading indicator for top earners section
- Filter buttons are disabled during loading to prevent duplicate requests
- Fixed transaction count query to properly handle date ranges (from_date/to_date)
- Added error handling with user-friendly error messages
- Added console logging for debugging

### Files Modified
- `static/js/admin/overview.js` - Added showOverviewLoading() function, improved error handling, added loading states
- `modules/admin_routes.py` - Fixed transaction count query to support date ranges

### Bug Fixes
- Stats now load correctly when selecting "3 Months" or any date range filter
- Transaction count now properly filters by date range
- Loading states prevent user confusion during data fetching

### UX Improvements
- Skeleton loaders show immediately when filters are clicked
- Buttons disabled during loading prevent accidental duplicate requests
- Clear error messages if data fails to load
- Consistent loading experience matching commission filters
## [2026-01-03 01:30] - Replace Admin Overview Date Filter with CTV-Style Filter Buttons
- Replaced month/day input fields with CTV-style filter button cards
- Added filter buttons: Today, 3 Days, This Week, This Month, Last Month, 3 Months, This Year, Custom
- Added red dot indicators on filter buttons to show which periods have data
- Filter buttons match CTV dashboard commission filter style exactly
- Added date range support to admin stats API (from_date/to_date parameters)
- Added date-ranges-with-data endpoint to check which periods have data

### Files Modified
- `templates/admin/pages/overview.html` - Replaced date inputs with filter button cards
- `static/js/admin/overview.js` - Complete rewrite to handle preset filters and data indicators
- `static/css/admin/components.css` - Added btn-filter-preset and data-indicator styles
- `modules/admin_routes.py` - Updated get_stats() to support date ranges, added date-ranges-with-data endpoint

### Features Added
- Uniform filter style matching CTV dashboard commission filters
- Red dot indicators showing which date ranges have data
- Card-based filter buttons with hover and active states
- Custom date range option with collapsible date inputs
- Consistent UX across admin and CTV dashboards

### API Changes
- `/api/admin/stats` now accepts `from_date` and `to_date` parameters in addition to `month` and `day`
- New endpoint `/api/admin/date-ranges-with-data` returns which preset periods have data
## [2026-01-03 01:18] - Add Loading States to Commission Filters
- Added skeleton loader animations when commission filters are clicked
- Loading state shows immediately when any filter button is clicked
- Skeleton loaders displayed in both table rows and summary cards during data loading
- Filter buttons are disabled during loading to prevent multiple simultaneous requests
- Improved UX to clearly indicate when new data is being fetched
- Loading states match CTV dashboard pattern for consistency

### Files Modified
- `static/js/admin/commissions.js` - Added `showCommissionsLoading()` function with skeleton loaders
- `static/css/admin/base.css` - Added skeleton loader CSS animations and styles
- `static/css/admin/forms.css` - Added disabled button styles for loading states

### Features Added
- Skeleton loader animations in commission table (5 rows)
- Skeleton loaders in summary cards (Total CTV, Total Revenue, Total Commission)
- Button disable state during loading to prevent duplicate requests
- Visual feedback that clearly shows data is being loaded
- Consistent loading experience matching CTV dashboard UX

### UX Improvements
- Users can now clearly see when filters are processing
- Prevents confusion about whether filters are working
- Prevents accidental multiple clicks during loading
- Smooth loading animations provide professional feel
## [2026-01-03 01:13] - Add Level Count Badge to ROOT CTV Search Dropdown
- Added level count badges next to CTV codes in the ROOT CTV selection dropdown
- Badge shows the number of levels below each CTV (e.g., "3" if CTV has 3 levels below)
- Badge only appears if CTV has at least one level below (no badge if no children)
- Badge displays with cyan background and adjusts color on hover/highlight
- Level count calculated using recursive CTE for efficient database queries

### Files Modified
- `modules/mlm_core.py` - Added `get_max_depth_below()` function to calculate maximum depth below a CTV
- `modules/admin_routes.py` - Updated `list_ctv()` endpoint to include `max_depth_below` field for each CTV
- `static/js/admin/hierarchy.js` - Updated `renderHierarchyList()` to display level count badges
- `static/css/admin/forms.css` - Added styling for `.level-count-badge` with flexbox layout

### Features Added
- Level count badges showing hierarchy depth below each CTV
- Badge only displays when CTV has children (levels > 0)
- Responsive badge styling that adapts to hover and highlight states
- Efficient database query using PostgreSQL recursive CTE

## [2026-01-03 01:11] - Add Date Period to Total Revenue Label
- Added dynamic date period display to "Tổng Dịch Vụ" (Total Revenue) label
- Label now shows the selected filter period (e.g., "Total Revenue for This Week", "Total Revenue for This Month")
- Supports all quick filters: Today, This Week, This Month, Last 3 Days, Last 3 Months, This Year
- Label updates automatically when filter changes
- Added translation keys for period-specific labels in both Vietnamese and English

### Files Modified
- `static/js/admin/commissions.js` - Added filter tracking and label update function
- `static/js/admin/translations.js` - Added translation keys for period-specific revenue labels
- `templates/admin/pages/commissions.html` - Added ID to revenue label for dynamic updates

### Features Added
- Dynamic "Tổng Dịch Vụ" label that reflects current date filter
- Shows "Tổng Dịch Vụ Tuần Này" when "This Week" filter is selected
- Shows "Tổng Dịch Vụ Tháng Này" when "This Month" filter is selected
- Shows "Tổng Dịch Vụ Hôm Nay" when "Today" filter is selected
- Falls back to "Tổng Dịch Vụ" for custom date ranges or other filters
## [2026-01-02 19:00] - Exclude Localhost from Suspicious IP Detection
- Excluded 127.0.0.1 (localhost) from suspicious IP detection
- Localhost is now filtered out as it represents admin local access, not suspicious activity
- Updated SQL query to exclude localhost IP from suspicious IP detection logic

### Files Modified
- `modules/activity_logger.py` - Added filter to exclude '127.0.0.1' from suspicious IP detection query

### Changes
- Suspicious IP detection now ignores localhost (127.0.0.1) since it's just admin accessing locally
- This prevents false positives in the suspicious IPs alert on Activity Logs page


## [2026-01-02 19:00] - Fix Commission Report to Show Services Even Without Commissions
- Fixed commission report to query both `khach_hang` and `services` tables
- Now shows CTVs who have services even if no commissions are calculated yet
- Added service count badges showing "X dịch vụ" for each CTV
- Added special badge "X dịch vụ, 0 HH" (orange) when services exist but commission is zero
- Added grand total service count badge in summary section
- Commission report now properly displays all CTVs with activity, not just those with commissions
- Users can now see that the system is working even when commissions haven't been calculated

### Files Modified
- `modules/admin_routes.py` - Updated `list_commissions_summary()` to query `khach_hang` and `services` tables in addition to `commissions` table
- `templates/admin/pages/commissions.html` - Added service count badge display area
- `static/js/admin/commissions.js` - Added service count badges and improved display logic

### Features Added
- Service count badges (blue) showing number of services per CTV
- Zero commission indicator (orange badge) when services exist but commission is 0
- Grand total service count badge in summary section
- Commission report now shows all CTVs with services, not just those with commissions

## [2026-01-02 18:30] - Fix Admin Commission Report Page
- Fixed commission report page not loading in admin dashboard
- Updated API function to include credentials (cookies) for authentication
- Fixed URL construction in commission loading function
- Improved error handling and user feedback
- Added loading state display
- Fixed initialization to prevent duplicate filter application
- Commission report now properly displays data or shows appropriate "no data" message

### Files Modified
- `static/js/admin/api.js` - Added `credentials: 'include'` to fetch options to send cookies
- `static/js/admin/commissions.js` - Fixed URL construction, improved error handling, added loading states

### Bug Fixes
- Previous issue: Commission report page was not loading data
- Root cause: API function wasn't sending cookies for session authentication
- Fix: Added credentials to fetch requests and improved error handling

## [2026-01-02 18:00] - Admin Dashboard Verification and Logic Alignment
- Verified all admin dashboard endpoints and database connections
- Updated admin stats endpoint to match CTV dashboard logic
- Admin stats now queries both `khach_hang` and `services` tables (matching CTV dashboard)
- Added support for Vietnamese status formats in admin queries
- All admin dashboard pages tested and verified:
  - Overview page: Stats endpoint working correctly
  - CTV Management: List, create, update, delete functions verified
  - Hierarchy page: Recursive CTE queries matching CTV dashboard
  - Commissions page: Commission queries verified
  - Clients page: Client grouping logic matches CTV dashboard
  - Settings page: Commission settings CRUD verified
  - Activity Logs: Logging and queries verified
- Database connections verified for all endpoints
- All logic matches between admin and CTV dashboards

### Files Modified
- `modules/admin_routes.py` - Updated `get_stats()` endpoint to query both `khach_hang` and `services` tables with Vietnamese status support

### Verification Results
- ✓ All 8 test categories passed
- ✓ Database connections working correctly
- ✓ Query logic matches CTV dashboard
- ⚠ Minor warning: Commission rate rounding difference (0.00625 vs 0.0063) - non-critical

## [2026-01-02 16:30] - Make Data Indicators Customizable for Holidays/Events
- Made data availability indicators fully customizable
- Can now use emojis (🎄, 🐉, 🎊), icons, or custom HTML instead of red dot
- Added preset configurations for holidays: Christmas, Chinese New Year, New Year, Valentine's, Halloween
- Easy switching via `setIndicatorPreset()` or `setCustomIndicator()` functions
- Supports emoji, icon classes, custom HTML, or default red dot
- Indicators automatically update when config changes
- Added bounce animation for emoji/icon indicators

### Files Added
- `static/js/ctv/indicator_config.js` - Configuration system for indicators
- `INDICATOR_CONFIG_README.md` - Complete guide for changing indicators

### Files Modified
- `templates/ctv/base.html` - Added indicator_config.js script
- `static/css/ctv/components.css` - Added styles for emoji/icon/custom indicators
- `static/js/ctv/commissions.js` - Updated to use config system
- `static/js/ctv/profile.js` - Updated to use config system
- `static/js/ctv/translations.js` - Updated to preserve and update indicators
- `static/js/ctv/main.js` - Added indicator initialization

### Usage Examples
```javascript
// Christmas
setIndicatorPreset('christmas'); // Shows 🎄

// Chinese New Year
setIndicatorPreset('chineseNewYear'); // Shows 🐉

// Custom emoji
setCustomIndicator('emoji', '🎊', '18px');

// Back to default red dot
setIndicatorPreset('default');
```

## [2026-01-02 16:00] - Add Data Availability Indicators to Date Filter Buttons
- Added red dot indicators on date filter buttons that have data available
- Created new API endpoint `/api/ctv/date-ranges-with-data` to check which date ranges have data
- Red dots appear on top-right corner of filter buttons (Today, 3 Days, Week, Month, Last Month, 3 Months, Year)
- Indicators check both `khach_hang` and `services` tables for data availability
- Applied to both Dashboard and Earnings pages
- Users can now quickly see which date ranges have data before clicking

### Files Modified
- `modules/ctv_routes.py` - Added `get_date_ranges_with_data()` endpoint
- `static/css/ctv/components.css` - Added `.data-indicator` styles for red dot (10px, red #ef4444, with shadow)
- `templates/ctv/pages/dashboard.html` - Added `<span class="data-indicator"></span>` to filter buttons
- `templates/ctv/pages/earnings.html` - Added `<span class="data-indicator"></span>` to filter buttons
- `static/js/ctv/commissions.js` - Added `checkDateRangesWithData()` function with 100ms delay for page rendering
- `static/js/ctv/profile.js` - Added `checkDashboardDateRangesWithData()` function with 100ms delay
- `static/js/ctv/translations.js` - Fixed `applyTranslations()` to preserve `.data-indicator` spans when translating button text

### Feature Details
- Red dot (10px) appears on top-right corner of buttons with data
- Positioned at top: -2px, right: -2px for optimal visibility
- White border (2px) around dot for visibility on light backgrounds
- Black border when button is active (dark background)
- Box shadow for better visibility
- Automatically checks data availability on page load
- Works for all preset date ranges except "Custom"
- Translation system now preserves indicator spans when language changes

### Bug Fixes
- Fixed translation function removing data-indicator spans when applying translations
- Increased dot size from 8px to 10px for better visibility
- Added `!important` flag to ensure dot displays when `has-data` class is present

## [2026-01-02 15:30] - Fix Stats by Level Date Filter and Add Loading Animation
- Fixed `/api/ctv/commission` endpoint to query both `khach_hang` and `services` tables for accurate revenue calculations
- Updated status filter to handle Vietnamese characters ('Đã đến làm', 'Đã cọc', 'Chờ xác nhận') in addition to non-Vietnamese formats
- Added loading animation (skeleton loader) to "Stats by Level" card when date filter is applied
- Fixed date filtering logic to properly apply date ranges to both tables
- Improved error handling in `loadAllCommissions()` function with try-catch blocks
- Stats by Level card now correctly displays revenue, commission, and transaction counts for all levels (0-4) based on selected date range

### Files Modified
- `modules/ctv_routes.py` - Updated `get_ctv_commission()` to query both tables and handle Vietnamese status values
- `static/js/ctv/commissions.js` - Added `showEarningsSummaryLoading()` and `hideEarningsSummaryLoading()` functions, integrated loading animation into filter functions

### Bug Fix Details
- Previous issue: Stats by Level card only queried `khach_hang` table, missing data from `services` table
- Previous issue: Status filter didn't match Vietnamese characters, causing missing revenue data
- Fix: Now queries both tables and combines results, handles all status format variations

## [2026-01-02 10:55] - Fix Table View Button and Improve Error Handling in CTV Clients Page
- Fixed Table button not working properly in CTV Portal Clients page
- Fixed error handling in `loadCtvClientsWithServices()` to render errors to the correct container (card or table view)
- Added try-catch wrapper around API calls to handle network errors gracefully
- Updated table view to show more relevant customer data: Name, Phone, Location, Service Count, Total Amount, Deposit Status
- Improved table rendering with better column headers and formatting
- Added table-specific CSS styles including hover effects and status badges
- The Table/Card toggle now properly switches between views and renders data to the correct container

### Files Modified
- `static/js/ctv/clients.js` - Fixed error handling and improved table view rendering
- `static/css/ctv/clients.css` - Added table view styles and status badges

### Bug Fix Details
- Previous bug: When API returned an error, the error message was always rendered to `ctvClientsGrid` (card view) even when in table view
- Fix: Now checks `currentView` variable and renders errors to the correct container (`ctvClientsGrid` for card view, `ctvClientsTable` for table view)

## [2025-12-30 22:15] - Add Mobile Popup Menu with Language Toggle for CTV Portal
- Added mobile popup menu for iPhone and small screen devices
- Language selection now available in mobile menu popup
- All menu items (Overview, Earnings, Network, Customers, Settings, Language, Logout) accessible via popup menu
- Menu button (hamburger icon) appears in bottom navigation on mobile
- Smooth slide-up animation for mobile menu
- Language toggle integrated into mobile menu with expandable submenu
- Responsive design works perfectly on iPhone, iPad, and desktop
- Desktop sidebar remains unchanged, mobile uses bottom navigation with popup menu

### Files Modified
- `templates/ctv/components/sidebar.html` - Added mobile menu button and popup menu structure
- `static/css/ctv/responsive.css` - Added mobile menu popup styles and animations
- `static/css/ctv/layout.css` - Added desktop hiding for mobile menu elements
- `static/js/ctv/navigation.js` - Added mobile menu toggle functions and navigation handlers
- `static/js/ctv/main.js` - Updated language initialization to support mobile menu
- `static/js/ctv/translations.js` - Updated setLanguage to update mobile language label

## [2025-12-30 22:00] - Add Month and Day Filters to Admin Overview Page
- Added month and day date filters to admin overview dashboard
- Users can now filter statistics by selecting a specific month or day
- Month filter defaults to current month on page load
- Day filter automatically updates month filter when a day is selected
- All statistics (commission, transactions, revenue, top earners) update based on selected date range
- Responsive design works on iPhone, iPad, and desktop devices
- All filter labels translated in Vietnamese and English

### Files Modified
- `templates/admin/pages/overview.html` - Added month and day filter inputs with apply button
- `modules/admin_routes.py` - Updated get_stats endpoint to accept month and day query parameters
- `static/js/admin/overview.js` - Added initOverview function and updated loadStats to handle date filters
- `static/js/admin/navigation.js` - Added initOverview call when navigating to overview page
- `static/js/admin/auth.js` - Updated showDashboard to call initOverview
- `static/js/admin/translations.js` - Added translation keys for filter_by_date, select_month, select_day

## [2025-12-30 21:30] - Update Referrer Column to Show CTV Code Instead of Name
- Changed referrer column in clients table view to display CTV code instead of CTV name
- Changed referrer column in admin CTV management table to display CTV code instead of CTV name
- Added table view rendering with EMAIL, PHONE, REFERRER (CTV code), and LEVEL columns for CTV portal
- Updated API endpoints to return referrer CTV code instead of referrer name
- Table view now properly loads and displays data when switching from card view
- Referrer now shows the CTV code instead of the CTV name in all views

### Files Modified
- `modules/ctv_routes.py` - Updated get_ctv_clients_with_services endpoint to include email, referrer_ctv_code, and level
- `modules/admin_routes.py` - Updated list_ctv endpoint to return nguoi_gioi_thieu_code instead of nguoi_gioi_thieu_name
- `static/js/ctv/clients.js` - Added renderCtvClientTable function and updated switchToTableView to load table data
- `static/js/admin/ctv-management.js` - Updated renderCTVTable to display referrer CTV code instead of name
- `templates/ctv_portal.html` - Added renderCtvClientTable function for inline table rendering
- `templates/admin.html` - Updated CTV table to display referrer CTV code instead of name
- `backend.py` - Updated CTV query to return referrer CTV code instead of name
- `modules/export_excel.py` - Updated export to use referrer CTV code field instead of name field

## [2025-12-30 21:00] - Enhanced Commission Report Date Range Filters
- Added quick filter buttons for common date ranges: Today, Last 3 Days, This Week, This Month, Last 3 Months, This Year
- Added custom date range picker allowing users to select specific start and end dates
- Updated backend API to support both month filter (existing) and date_from/date_to parameters
- Quick filters automatically calculate date ranges based on selected option
- Custom date range validates that start date is before end date
- Export to Excel functionality now respects all date filter types
- Responsive design works on iPhone, iPad, and desktop devices
- Quick filter buttons highlight when active
- Default filter set to current month on page load
- All filter labels translated in Vietnamese and English

### Files Modified
- `templates/admin/pages/commissions.html` - Added quick filter buttons and custom date range inputs
- `static/js/admin/commissions.js` - Added filter logic for quick filters and custom date ranges
- `static/js/admin/translations.js` - Added translation keys for all new filter labels
- `modules/admin_routes.py` - Updated commission summary API to support date_from and date_to parameters
- `static/css/admin/forms.css` - Added responsive styling for date filter components

## [2025-12-30 20:25] - Auto-Collapse Sidebar on Horizontal Scroll
- Added automatic sidebar collapse when page is scrolled horizontally to the right
- Sidebar smoothly slides out of view to prevent overlap with search bar and content
- Sidebar automatically expands back when scrolled to the left edge
- Monitors both window scroll and scrollable containers (tables, cards) for horizontal scrolling
- Uses MutationObserver to detect dynamically added scrollable elements
- Smooth CSS transitions for better user experience

### Files Modified
- `static/css/admin/layout.css` - Added collapsed state styles and transitions for sidebar
- `static/js/admin/main.js` - Added horizontal scroll detection and sidebar collapse logic

## [2025-12-30 20:15] - Fix CTV Search Not Finding Results
- Fixed CTV search functionality that was showing "not found" even when CTVs existed
- Improved search to normalize Vietnamese characters (remove accents) for better matching
- Added automatic CTV list loading when navigating to CTV Management page
- Enhanced search to handle whitespace, empty strings, and special characters properly
- Search now works with partial matches in CTV code, name, email, and phone fields

### Files Modified
- `static/js/admin/ctv-management.js` - Added Vietnamese text normalization function and improved search logic
- `static/js/admin/navigation.js` - Added loadCTVList() call when navigating to CTV management page

## [2025-12-30 19:56] - Fix Monthly Revenue Calculation Logic
- Fixed monthly revenue calculation to use distinct transaction amounts from commissions table
- Previously calculated from services table which could cause discrepancies with commission calculations
- Now both monthly commission and monthly revenue use the same data source (commissions table) for consistency
- Revenue is calculated as sum of distinct transaction amounts to avoid counting transactions multiple times
- Added fallback to services table if no commissions exist for the month

### Files Modified
- `modules/admin_routes.py` - Updated monthly revenue SQL query to use distinct transaction amounts from commissions table

## [2025-12-30 19:50] - Remove Decimal Places from Currency Display
- Updated all formatCurrency functions to remove decimal places from currency displays
- Added maximumFractionDigits: 0 option to Intl.NumberFormat for all currency formatting functions
- Affects monthly commission display and all other currency displays across admin and CTV portals
- Currency values now display as whole numbers (e.g., "5.462.453.012d" instead of "5.462.453.012,5d")

### Files Modified
- `static/js/admin/utils.js` - Updated formatCurrency and formatClientCurrency functions
- `static/js/ctv/utils.js` - Updated formatCurrency and formatCtvCurrency functions
- `templates/admin.html` - Updated inline formatCurrency function
- `templates/ctv_portal.html` - Updated inline formatCurrency function

## [2025-12-30 19:38] - Admin Login Remember Me Feature
- Added "Remember Me" checkbox to admin login form (checked by default)
- Implemented localStorage to save/load credentials when remember me is checked
- Updated backend to support longer session expiry (30 days) when remember me is enabled
- Added CSS styling for remember me checkbox in admin components
- Added translation keys for "remember_me" in both Vietnamese and English
- Modified `create_session()` function to accept `remember_me` parameter for extended sessions
- Updated cookie expiry to 30 days when remember me is checked (default: 24 hours)

### Files Modified
- `templates/admin/components/login.html` - Added remember me checkbox
- `static/css/admin/components.css` - Added remember me styling
- `static/js/admin/translations.js` - Added remember_me translation keys
- `static/js/admin/auth.js` - Added localStorage save/load functionality
- `modules/admin_routes.py` - Updated login endpoint to handle remember_me
- `modules/auth.py` - Updated `create_session()` and `admin_login()` to support remember_me

## [2025-12-30 15:45] - Vietnamese Translation Fixes
- Updated all Vietnamese translations in `static/js/ctv/translations.js` and `static/js/admin/translations.js` with correct accents.
- Fixed missing accents in `modules/export_excel.py` headers.
- Updated hardcoded Vietnamese status strings in backend routes (`modules/ctv_routes.py`, `modules/mlm_core.py`, `modules/admin_routes.py`, `backend.py`) to handle both accented and non-accented versions for compatibility.
- Fixed missing accents in database migration and import scripts (`migrate_khach_hang.py`, `import_csv_data.py`).
- Updated HTML language attributes to `en` while maintaining full Vietnamese support.
- Migrated existing database records for `trang_thai` (status) and `cap_bac` (rank) to include correct Vietnamese accents.
- Updated frontend JavaScript files to use translation functions instead of hardcoded strings.

## Version 3.0.1 - December 30, 2025

### Top Earners Section - 3-Column Layout Update

**Time:** December 30, 2025 - Night

---

#### Overview

Updated the "Top Thu Nhap Thang Nay" (Top Earners This Month) section to display 3 columns instead of 2.

#### Changes

**Before:**
- Column 1: CTV Name + Code
- Column 2: Total Earned (commission only)

**After:**
- Column 1: CTV Name + Code (unchanged)
- Column 2: Total Revenue
- Column 3: Total Commission

#### Files Modified

- `modules/admin_routes.py` - Updated SQL query to include `total_revenue` and `total_commission`
- `static/js/admin/overview.js` - Updated JS to render 3-column layout with headers
- `static/css/admin/components.css` - Added grid-based 3-column CSS styles
- `static/js/admin/translations.js` - Added translations for `ctv_name`, `total_revenue`, `total_commission`
- `templates/admin.html` - Updated inline CSS and JS for backward compatibility

---

## Version 3.0.0 - December 30, 2025

### Major Frontend Refactoring - Modular Architecture

**Time:** December 30, 2025 - Night

---

#### Overview

Refactored the monolithic `admin.html` (4000+ lines) and `ctv_portal.html` (3000+ lines) into modular components using Jinja2 templates and separate CSS/JS files. This improves maintainability, reduces load times, and enables better code organization.

#### Architecture Changes

**Before:**
```
templates/
  admin.html (4000+ lines - CSS, HTML, JS all in one)
  ctv_portal.html (3000+ lines - CSS, HTML, JS all in one)
```

**After:**
```
templates/
  admin/
    base.html                    # Main template with includes
    components/
      lang-toggle.html           # Language toggle buttons
      login.html                 # Login page
      sidebar.html               # Sidebar navigation
      modals.html                # Modal dialogs
    pages/
      overview.html              # Dashboard overview
      ctv-management.html        # CTV management
      hierarchy.html             # Hierarchy tree
      commissions.html           # Commission reports
      clients.html               # Client management
      settings.html              # Settings page
      activity-logs.html         # Activity logs
  ctv/
    base.html                    # Main template with includes
    components/
      login.html                 # Login page
      sidebar.html               # Sidebar navigation
      header.html                # Header component
    pages/
      dashboard.html             # Dashboard page
      earnings.html              # Earnings page
      network.html               # Network/hierarchy
      clients.html               # Clients page
      settings.html              # Settings page

static/
  css/
    admin/
      base.css                   # Global resets and variables
      components.css             # Buttons, badges, modals
      layout.css                 # Login, dashboard, sidebar
      forms.css                  # Form elements
      tables.css                 # Table styles
      hierarchy.css              # Tree visualization
      clients.css                # Client cards
      activity-logs.css          # Activity logs
    ctv/
      base.css                   # Global resets and variables
      login.css                  # Login page
      layout.css                 # Portal layout
      components.css             # Shared components
      cards.css                  # Stat and commission cards
      tree.css                   # Network tree
      clients.css                # Client cards
      responsive.css             # Mobile responsiveness
  js/
    admin/
      api.js                     # API helper function
      utils.js                   # Utility functions
      translations.js            # i18n system
      navigation.js              # Page navigation
      auth.js                    # Authentication
      overview.js                # Dashboard stats
      ctv-management.js          # CTV CRUD operations
      hierarchy.js               # Tree visualization
      commissions.js             # Commission reports
      clients.js                 # Client management
      settings.js                # Settings page
      activity-logs.js           # Activity logs
      excel-export.js            # Excel export
      main.js                    # Main entry point
    ctv/
      api.js                     # API helper function
      utils.js                   # Utility functions
      translations.js            # i18n system
      auth.js                    # Authentication
      navigation.js              # Page navigation
      profile.js                 # Profile loading
      commissions.js             # Commission data
      network.js                 # MLM tree
      phone-check.js             # Phone validation
      clients.js                 # Client cards
      main.js                    # Main entry point
```

#### Backend Changes

**Modified Files:**

| File | Change |
|------|--------|
| `modules/admin_routes.py` | Changed `/admin89` route from `send_file` to `render_template('admin/base.html')` |
| `modules/ctv_routes.py` | Changed `/ctv/portal` route from `send_file` to `render_template('ctv/base.html')` |

#### Benefits

1. **Maintainability**: Each module is self-contained and easier to update
2. **Reusability**: Components can be reused across pages
3. **Performance**: CSS/JS files can be cached by browser
4. **Debugging**: Easier to locate and fix issues in smaller files
5. **Team Collaboration**: Multiple developers can work on different modules
6. **Testing**: Individual modules can be tested in isolation

#### Module Documentation

Each JavaScript file includes header documentation following the project's modular code organization rules:

```javascript
/**
 * Module Name
 * DOES: Description of module purpose
 * INPUTS: What the module receives
 * OUTPUTS: What the module produces
 * FLOW: How it connects to other modules
 */
```

#### Files Created

| Category | Count | Location |
|----------|-------|----------|
| Admin CSS | 8 | `static/css/admin/` |
| Admin JS | 13 | `static/js/admin/` |
| Admin Templates | 11 | `templates/admin/` |
| CTV CSS | 8 | `static/css/ctv/` |
| CTV JS | 11 | `static/js/ctv/` |
| CTV Templates | 9 | `templates/ctv/` |

#### Migration Notes

- Original `admin.html` and `ctv_portal.html` files are preserved for reference
- The new modular templates are served via Jinja2's `render_template`
- All existing functionality is preserved
- No API changes required

---

## Version 2.0.9 - December 30, 2025

### Excel Export Feature - Admin Panel

**Time:** December 30, 2025 - Night

---

#### Overview

Added Excel (.xlsx) export functionality to all data pages in the Admin Panel. Each page now has an "Export Excel" button that downloads the current data view as a formatted Excel spreadsheet.

#### Changes Made

**1. New Export Module**
- Created `modules/export_excel.py` with reusable Excel generation utilities
- Styled headers with dark theme matching the admin UI
- Auto-sized columns based on content
- Currency and percentage number formatting
- Frozen header row for easy scrolling

**2. New API Endpoints**

| Endpoint | Data Exported |
|----------|---------------|
| `GET /api/admin/ctv/export` | All CTVs (code, name, phone, email, referrer, level, status, created) |
| `GET /api/admin/commissions/export` | Commission records with filters |
| `GET /api/admin/commissions/summary/export` | Commission summary by CTV |
| `GET /api/admin/clients/export` | Clients with service counts and totals |
| `GET /api/admin/activity-logs/export-xlsx` | Activity logs (Excel format) |
| `GET /api/admin/commission-settings/export` | Commission rate settings |

**3. Frontend Export Buttons**

Added "Export Excel" buttons to:
- **CTV Management page** - Exports all CTVs with current filters
- **Commissions page** - Exports commission summary by CTV
- **Clients page** - Exports all clients with service counts
- **Activity Logs page** - Added Excel option alongside CSV
- **Settings page** - Exports commission rate settings

**4. JavaScript Functions**
- `exportToExcel(endpoint)` - Generic export for simple endpoints
- `exportCommissionsExcel()` - Export commissions with month filter
- `exportClientsExcel()` - Export clients with search filter
- `exportActivityLogsExcel()` - Export logs with all filters

**5. Translations**
- Added `export_excel` translation key
- Vietnamese: "Xuat Excel"
- English: "Export Excel"

#### Files Created

| File | Description |
|------|-------------|
| `modules/export_excel.py` | Excel generation utilities with column configurations |

#### Files Modified

| File | Changes |
|------|---------|
| `requirements.txt` | Added openpyxl>=3.1.2 |
| `modules/admin_routes.py` | Added 6 export endpoints |
| `templates/admin.html` | Added export buttons, JavaScript functions, translations |

#### Dependencies Added

- `openpyxl>=3.1.2` - Python library for creating Excel files

---

## Version 2.0.8 - December 30, 2025

### Language Toggle Moved to Sidebar

**Time:** December 30, 2025 - Night

---

#### Overview

Moved the language toggle (VI/EN) from the fixed top-right corner to the sidebar menu in `dashboard.html`. The new design features a toggle button with a popup menu, consistent with the CTV portal's design.

#### Changes Made

**1. Removed Fixed Position Language Toggle**
- Removed the two-button language toggle from top-right corner
- Cleaned up old `.lang-toggle` and `.lang-btn` CSS

**2. Added Sidebar Language Toggle**
- New `.sidebar-lang` component placed above CTV Portal button
- Globe icon with current language label overlay
- Popup menu with language options (Vietnamese/English)
- Checkmark indicator for active language
- Gradient flag icons for visual appeal

**3. Updated JavaScript**
- Added `toggleLangPopup()` function for popup toggle
- Added `selectLanguage()` for language selection
- Added `updateLangUI()` to sync UI state
- Added click-outside handler to close popup
- Added new translation keys: `language`, `choose_language`

**4. Mobile Responsive**
- Popup appears above the icon on mobile (bottom navigation)
- Proper arrow positioning for mobile view

#### Files Modified

| File | Changes |
|------|---------|
| `dashboard.html` | Replaced fixed lang-toggle with sidebar-lang component, new CSS, updated JS |

---

## Version 2.0.7 - December 30, 2025

### Commission Page - Grouped by CTV with Totals

**Time:** December 30, 2025 - Night

---

#### Overview

Redesigned the Commissions (Hoa Hong) page in Admin Dashboard to show aggregated data grouped by CTV person instead of individual commission records. The new view displays 5 columns with totals per CTV.

#### Changes Made

**1. New Backend Endpoint**
- Added `GET /api/admin/commissions/summary` endpoint
- Groups all commissions by CTV code
- Returns: CTV code, CTV name, CTV phone, Total service price, Total commission
- Supports month filter: `?month=2025-12`
- Returns grand totals for all CTVs

**2. Updated Table Structure**
- Changed from 7 columns to 5 columns:
  - Ma CTV (CTV Code)
  - Ten CTV (CTV Name)
  - SDT (Phone)
  - Tong Dich Vu (Total Service Price)
  - Tong Hoa Hong (Total Commission)
- Removed: ID, Level, Rate, Transaction, Date columns

**3. Added Grand Total Summary**
- New summary cards above the table showing:
  - Tong CTV (Total CTV count)
  - Tong Dich Vu (Grand total service price)
  - Tong Hoa Hong (Grand total commission)

**4. Simplified Filters**
- Removed CTV filter dropdown (no longer needed since data is grouped)
- Kept month filter for time-based filtering

#### Files Modified

| File | Changes |
|------|---------|
| `modules/admin_routes.py` | Added `/api/admin/commissions/summary` endpoint |
| `templates/admin.html` | Updated commissions page HTML structure, JavaScript function, removed CTV filter |

---

## Version 2.0.6 - December 30, 2025

### CTV Active Filter - Default to Show Active Only

**Time:** December 30, 2025 - Night

---

#### Overview

Fixed the CTV Management page to show only active CTVs by default. The `filter_valid_ctv.py` script correctly sets `is_active = 0` for invalid CTVs, but the dashboard was displaying all CTVs regardless of their active status.

#### Changes Made

**1. Added Toggle Switch for Show/Hide Inactive CTVs**
- New toggle switch in CTV Management page header
- Default: OFF (only active CTVs shown)
- Toggle ON to see inactive CTVs as well

**2. Updated `loadCTVList()` Function**
- Now uses `active_only=true` parameter by default
- Respects toggle switch state when reloading

**3. Updated `populateCTVSelects()` Function**
- Accepts optional CTV list parameter
- Dropdowns always use only active CTVs for better UX

**4. Updated `renderHierarchyList()` Function**
- Filters to show only active CTVs in hierarchy dropdown

**5. Added Toggle Switch CSS**
- New `.toggle-switch` and `.toggle-slider` styles
- Smooth animation on state change

**6. Added Translations**
- Vietnamese: "Hien CTV Ngung"
- English: "Show Inactive"

#### Files Modified

| File | Changes |
|------|---------|
| `templates/admin.html` | Added toggle switch UI, CSS, updated JS functions, added translations |

---

## Version 2.0.5 - December 30, 2025

### Hierarchy Tree Loading Indicator

**Time:** December 30, 2025 - Night

---

#### Overview

Added a loading spinner indicator to the Hierarchy Tree page (Cay Cap Bac) to provide visual feedback while the tree data is being fetched from the server.

#### Changes Made

**1. Added Loading Spinner CSS**
- New `.hierarchy-loading` class with flexbox centering
- `.hierarchy-spinner` with rotating animation
- Loading text and subtext styles
- `@keyframes hierarchySpin` animation

**2. Added Loading HTML Element**
- Spinner div with loading text
- Subtext explaining the wait for large trees
- Placed between the tree wrapper and placeholder

**3. Updated `loadHierarchy()` Function**
- Shows loading indicator immediately when function starts
- Hides placeholder and wrapper during load
- Hides loading indicator when data arrives or on error
- Added try/catch error handling

**4. Added Translations**
- Vietnamese: "Dang tai cay cap bac...", "Vui long doi, co the mat mot luc cho cay lon"
- English: "Loading hierarchy tree...", "Please wait, this may take a moment for large trees"

#### Files Modified

| File | Changes |
|------|---------|
| `templates/admin.html` | Added CSS for loading spinner, added loading HTML element, updated loadHierarchy() function, added translations |

---

## Version 2.0.4 - December 30, 2025

### Earnings Filter - Changed from Level Filter to Time Period Filter

**Time:** December 30, 2025 - Night

---

#### Overview

Changed the earnings page filter dropdown from filtering by commission level (Level 0-4) to filtering by time periods (Today, This Month, 3 Months, This Year, Custom).

#### Changes Made

**1. Replaced Level Filter with Time Period Filter**
- Changed `earningsLevelFilter` select to `earningsTimeFilter`
- Options now: Custom, Today, This Month, 3 Months, This Year
- Time filter dropdown moved to appear before the date inputs

**2. Auto Date Range Selection**
- Selecting a time period automatically sets the From/To date inputs
- Today: Sets both dates to current date
- This Month: From 1st of current month to today
- 3 Months: From 1st of 3 months ago to today
- This Year: From January 1st to today
- Custom: Keeps manual date inputs unchanged

**3. Smart Custom Detection**
- When user manually changes date inputs, dropdown auto-switches to "Custom"

**4. Removed Level Filtering**
- `loadAllCommissions()` no longer accepts or passes `level` parameter
- Backend API call no longer includes level filter

**5. Added Translations**
- Vietnamese: Tuy chinh, Hom nay, 3 thang, Nam nay
- English: Custom, Today, 3 Months, This Year

#### Files Modified

| File | Changes |
|------|---------|
| `templates/ctv_portal.html` | Changed filter dropdown, added `applyTimeFilter()` function, updated `filterCommissions()` and `loadAllCommissions()` functions, added translations |

---

## Version 2.0.3 - December 30, 2025

### UI Update - Language Toggle Moved to Sidebar

**Time:** December 30, 2025 - Night

---

#### Overview

Moved the language toggle (VI/EN) from the fixed top-right corner to the sidebar menu, next to the logout button. The new design shows a single toggle button that opens a popup menu to select between Vietnamese and English.

#### Changes Made

**1. Removed Old Language Toggle**
- Removed fixed position toggle buttons from top-right corner
- Removed old `.lang-toggle` and `.lang-btn` CSS styles

**2. New Sidebar Language Button**
- Added globe icon with current language label (VI/EN) in sidebar
- Positioned between Settings and Logout icons
- Shows tooltip "Ngon Ngu" (VI) / "Language" (EN) on hover

**3. Language Popup Menu**
- Click the globe icon to open popup menu
- Popup slides in from the left of the icon
- Options: Vietnamese (VN flag) and English (US flag)
- Active language shows checkmark indicator
- Click outside to close popup

**4. Login Page Language Toggle**
- Added floating language button in top-right corner for login page
- Same popup style as sidebar version
- Shows current language (VI/EN) with globe icon
- Popup appears below the button

#### Files Modified

| File | Changes |
|------|---------|
| `templates/ctv_portal.html` | Removed old lang-toggle, added sidebar-lang component, added login page toggle, updated CSS and JavaScript |

#### UI Components Added

**Sidebar Language Switcher:**
```html
<div class="sidebar-lang" id="langSwitcher">
    <div class="sidebar-icon">
        <svg>...</svg>  <!-- Globe icon -->
        <span class="lang-current">VI</span>
    </div>
    <div class="lang-popup">
        <div class="lang-option" data-lang="vi">VN Tieng Viet</div>
        <div class="lang-option" data-lang="en">US English</div>
    </div>
</div>
```

**Login Page Language Button:**
```html
<div class="login-lang-toggle">
    <div class="login-lang-btn">
        <svg>...</svg>  <!-- Globe icon -->
        <span>VI</span>
    </div>
    <div class="login-lang-popup">...</div>
</div>
```

#### JavaScript Functions Added

| Function | Description |
|----------|-------------|
| `toggleLangPopup(e)` | Toggle sidebar language popup |
| `toggleLoginLangPopup(e)` | Toggle login page language popup |
| `selectLanguage(lang)` | Select language and close popup |

#### Translation Keys Added

| Key | Vietnamese | English |
|-----|-----------|---------|
| `language` | Ngon Ngu | Language |
| `choose_language` | Chon Ngon Ngu | Choose Language |

---

## Version 2.0.2 - December 30, 2025

### Feature - Filter Valid CTVs Migration Script

**Time:** December 30, 2025 - Night

---

#### Overview

Created a migration script to filter the CTV database to only keep valid CTVs from a provided CSV file. Invalid CTVs are deactivated (cannot login) but their records remain in the database to preserve client service associations.

#### Migration Script

**File:** `filter_valid_ctv.py`

**Features:**
- Preview mode (default): Shows what changes would be made without modifying the database
- Execute mode: Applies the changes after confirmation
- Case-insensitive CTV code matching
- Updates valid CTVs with details from CSV (name, phone, email, rank, referrer)
- Deactivates invalid CTVs by setting `is_active = 0` and clearing `password_hash`
- Preserves all `khach_hang.nguoi_chot` links (client-to-CTV associations remain intact)

**Usage:**
```bash
python3 filter_valid_ctv.py          # Preview mode (no changes)
python3 filter_valid_ctv.py execute  # Apply changes (requires confirmation)
```

#### Results

| CTV Status | Count | Login Access | Client Links |
|------------|-------|--------------|--------------|
| Valid (in CSV) | 52 | YES | Preserved |
| Invalid (not in CSV) | 94 | NO (deactivated) | Preserved |

#### Database Changes

```sql
-- For 52 valid CTVs from CSV
UPDATE ctv SET is_active = 1, ten = ?, sdt = ?, email = ?, cap_bac = ?, nguoi_gioi_thieu = ?
WHERE LOWER(ma_ctv) = LOWER(?);

-- For 94 invalid CTVs
UPDATE ctv SET is_active = 0, password_hash = NULL
WHERE ma_ctv NOT IN (valid_codes);
```

#### Security

The existing auth system already blocks deactivated CTVs from logging in:

**File:** `modules/auth.py` (lines 596-601)
```python
if not ctv.get('is_active', True):
    return {'error': 'Account is deactivated'}
```

#### Files Created

| File | Description |
|------|-------------|
| `filter_valid_ctv.py` | Migration script with preview and execute modes |

---

## Version 2.0.1 - December 30, 2025

### Changed - MLM Tree Level Display from L1-L5 to L0-L4

**Time:** December 30, 2025 - Night

---

#### Change

Updated the MLM network tree level badges to display L0-L4 instead of L1-L5 to match the actual database level values (0-4).

#### Files Modified

1. **`templates/admin.html`**
   - Updated CSS level badge classes from `.l1-.l5` to `.l0-.l4`
   - Updated `renderTree()` function to use `node.level` directly instead of `node.level + 1`
   - Updated comments to reflect L0-L4 mapping

2. **`templates/ctv_portal.html`**
   - Updated CSS level badge classes from `.l1-.l5` to `.l0-.l4`
   - Updated `renderTree()` function to use `node.level` directly instead of `node.level + 1`
   - Updated comments to reflect L0-L4 mapping

#### Visual Change

| Before | After |
|--------|-------|
| L1 (red) | L0 (red) |
| L2 (orange) | L1 (orange) |
| L3 (green) | L2 (green) |
| L4 (blue) | L3 (blue) |
| L5 (purple) | L4 (purple) |

---

## Version 2.0.0 - December 30, 2025

### Removed - Customers Page from CTV Portal

**Time:** December 30, 2025 - Night

---

#### Change

Completely removed the "Khach Hang" (Customers) page from the CTV Portal sidebar navigation. This page is no longer needed.

#### Files Modified

1. **`templates/ctv_portal.html`**
   - Removed customers sidebar icon from navigation
   - Removed customers page HTML section (`#page-customers`)
   - Removed customer table CSS styles (`.customer-table`)
   - Removed `loadMyCustomers()` JavaScript function
   - Removed `setDefaultDateFilters()` JavaScript function
   - Removed customers navigation handlers
   - Removed customers-related translation strings (Vietnamese and English)

#### Reason

Page functionality no longer needed in the CTV Portal.

---

## Version 1.9.9 - December 30, 2025

### UX Improvement - Stats Loading Skeleton

**Time:** December 30, 2025 - Night

---

#### Change

Added skeleton loading animation to the dashboard stats cards (Total Earnings, Monthly Earnings, Network Size, Services This Month) to improve user experience during data loading.

#### Features Added

1. **Skeleton Loading Animation**
   - Smooth shimmer animation while stats are loading
   - Color-coded skeletons matching each stat card's theme (green, blue, gold, pink)
   - Responsive skeleton sizes for mobile devices

2. **User Experience**
   - Users now see animated loading placeholders instead of confusing "0d" values
   - Clear visual feedback that data is being fetched

#### Files Modified

1. **`templates/ctv_portal.html`**
   - Added CSS keyframe animation `skeleton-shimmer`
   - Added `.skeleton-loader` class with responsive styles
   - Added color-themed skeleton variants for each stat card type
   - Updated initial stat card HTML to show skeleton loaders instead of zeros

---

## Version 1.9.8 - December 30, 2025

### Feature - Date Filter for Hoa Hong (Commission) Page

**Time:** December 30, 2025 - Night

---

#### Change

Added date filtering functionality to the Hoa Hong (Earnings/Commission) page in the CTV Portal. Users can now filter their commissions by date range and level.

#### Features Added

1. **Date Filter UI**
   - From date picker (default: first day of current month)
   - To date picker (default: today)
   - Level dropdown filter (All Levels, Level 0-4)
   - Filter button to apply filters

2. **Default Date Range**
   - When opening the Hoa Hong page, the filter automatically defaults to:
     - From: First day of current month
     - To: Today's date

3. **Commission List Display**
   - Added "Tat Ca Hoa Hong" (All Commissions) section showing individual commission entries
   - Each entry shows level, rate, date, amount, and tooltip with CTV/customer/service details

#### Files Modified

1. **`templates/ctv_portal.html`**
   - Added date filter card with date inputs, level dropdown, and filter button
   - Added commission list card section
   - Updated `loadAllCommissions()` function to accept date and level parameters
   - Added `filterCommissions()` function to handle filter button click
   - Added `setEarningsDefaultDateFilter()` function to set default dates
   - Added translation keys: `all_levels` (Vietnamese/English)

2. **`modules/ctv_routes.py`**
   - Updated `/api/ctv/my-commissions` endpoint to support `from_date` and `to_date` query parameters
   - Date range filter takes priority over legacy `month` parameter
   - Both commission list and summary respect the date filters

#### API Changes

`GET /api/ctv/my-commissions` now supports:
- `?from_date=2025-12-01&to_date=2025-12-31` (new date range filter)
- `?level=1` (filter by commission level)
- `?month=2025-12` (legacy, still supported but lower priority)

---

## Version 1.9.7 - December 30, 2025

### Removed - Search Page from CTV Portal

**Time:** December 30, 2025 - Night

---

#### Change

Completely removed the "Tim Kiem" (Search) page from the CTV Portal sidebar navigation.

#### Files Modified

1. **`templates/ctv_portal.html`**
   - Removed search sidebar icon from navigation
   - Removed search page HTML section (`#page-search`)
   - Removed search-related CSS styles (`.search-container`, `.search-input`, `.result-item`)
   - Removed search JavaScript functions (`searchTimeout`, `performSearch`)
   - Removed search translation strings (Vietnamese and English)

2. **`modules/ctv_routes.py`**
   - Removed `/api/ctv/my-network/search` endpoint
   - Removed `search_my_network()` function
   - Removed route comment from header documentation

#### Reason

Page functionality no longer needed in the CTV Portal.

---

## Version 1.9.6 - December 30, 2025

### Feature Update - Dashboard Stat Card Change

**Time:** December 30, 2025 - Night

---

#### Change

Changed the pink stat card on CTV Portal dashboard from "Truc Tiep (Level 1)" (direct downline count) to "Dich Vu Thang Nay" (Services This Month).

#### Files Modified

1. **`modules/ctv_routes.py`** - `/api/ctv/me` endpoint
   - Added new query to count completed services this month
   - Added `monthly_services_count` to stats response

2. **`templates/ctv_portal.html`**
   - Changed stat card label from `direct_level1` to `services_this_month`
   - Changed element ID from `statDirectCount` to `statMonthlyServices`
   - Updated JavaScript to use `monthly_services_count` stat
   - Added translations for Vietnamese and English

#### Technical Details

**New Backend Query:**
```sql
SELECT COUNT(*) as count
FROM khach_hang
WHERE nguoi_chot = %s 
AND trang_thai = 'Da den lam'
AND DATE_FORMAT(ngay_hen_lam, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
```

- Counts services where `nguoi_chot` = logged-in CTV
- Only counts completed services (`trang_thai = 'Da den lam'`)
- Filters by current month based on `ngay_hen_lam` (service date)

---

## Version 1.9.5 - December 30, 2025

### Bug Fix - Monthly Earnings Calculation

**Time:** December 30, 2025 - Night

---

#### Problem

"Tong Thu Nhap" (Total Earnings) and "Thu Nhap Thang Nay" (This Month's Income) were displaying the same value on the CTV Portal dashboard.

#### Root Cause

The monthly earnings query was filtering by `created_at` (when the commission record was inserted into the database) instead of the actual transaction/service date. If all commissions were imported or migrated at the same time, they would all have the same `created_at` timestamp, making total = monthly.

#### Solution

Updated the monthly earnings SQL query to join with `khach_hang` table and use `ngay_hen_lam` (actual scheduled service date) for filtering.

**File:** `modules/ctv_routes.py`

**Before:**
```sql
SELECT COALESCE(SUM(commission_amount), 0) as total
FROM commissions 
WHERE ctv_code = %s 
AND DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
```

**After:**
```sql
SELECT COALESCE(SUM(c.commission_amount), 0) as total
FROM commissions c
LEFT JOIN khach_hang kh ON c.transaction_id = kh.id
WHERE c.ctv_code = %s 
AND DATE_FORMAT(COALESCE(kh.ngay_hen_lam, c.created_at), '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m');
```

#### Technical Details

- Uses `LEFT JOIN` to link commissions to their source transaction in `khach_hang`
- Uses `COALESCE(kh.ngay_hen_lam, c.created_at)` as fallback if transaction record doesn't exist
- Filters by the actual service month, not the commission insertion date

---

## Version 1.9.4 - December 30, 2025

### Admin Panel Security Update - Hidden URL

**Time:** December 30, 2025 - Night

---

#### Overview

Removed the admin login button from the main dashboard sidebar and changed the admin URL to a secret path (`/admin89`) for security purposes.

#### Changes Made

**1. Removed Admin Button from Dashboard**

**File:** `dashboard.html`
- Removed the admin panel button (gear icon) from the sidebar
- Removed associated CSS styles for `.sidebar-icon.admin-login`
- Removed `admin_panel` translation keys from both VI and EN translations

**2. Changed Admin URL**

**File:** `modules/admin_routes.py`
- Changed `/admin/dashboard` to `/admin89` (main dashboard page)
- Changed `/admin/login` to `/admin89/login`
- Changed `/admin/logout` to `/admin89/logout`
- Changed `/admin/check-auth` to `/admin89/check-auth`
- Updated module structure map comments

**3. Updated Admin HTML Template**

**File:** `templates/admin.html`
- Updated login API call from `/admin/login` to `/admin89/login`
- Updated logout API call from `/admin/logout` to `/admin89/logout`
- Updated auth check API call from `/admin/check-auth` to `/admin89/check-auth`

#### Access Instructions

- **Admin Dashboard:** Navigate directly to `/admin89`
- No visible button on the main site - URL must be remembered

---

## Version 1.9.3 - December 30, 2025

### Vietnamese Translation Update - Phone Check Feature

**Time:** December 30, 2025 - Evening

---

#### Changes

Updated phone check feature with proper Vietnamese accents:

**Dashboard (dashboard.html):**
- Placeholder: "Doi Chieu SDT..." → "Nhập SDT Cần Kiểm Tra"
- Button: "Doi Chieu" → "Kiểm Tra Trùng Lặp"
- Sidebar tooltip: "Doi Chieu" → "Kiểm Tra Trùng Lặp"
- Translation keys updated with Vietnamese accents

**CTV Portal (ctv_portal.html):**
- Title: "Doi Chieu So Dien Thoai" → "Kiểm Tra Trùng Lặp Số Điện Thoại"
- Button: "Doi Chieu" → "Kiểm Tra Trùng Lặp"
- Placeholder: "Nhap so dien thoai..." → "Nhập SDT Cần Kiểm Tra"
- All translation keys updated with Vietnamese accents

---

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

