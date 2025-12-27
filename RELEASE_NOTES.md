# Release Notes - CTV Dashboard

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

