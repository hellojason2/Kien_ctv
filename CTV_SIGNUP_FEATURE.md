# CTV Signup Feature - Implementation Summary

## Overview
Created a complete CTV (Collaborator) signup system with admin approval workflow. New CTV applicants can fill out a registration form, and their applications will be reviewed by admins before approval.

## Features Implemented

### 1. Frontend Signup Page (`/ctv/signup`)
- **Template**: `templates/ctv_signup.html`
- **Styles**: `static/css/ctv/signup.css`
- **JavaScript**: `static/js/ctv/signup.js`

**Form Fields** (matching Google Sheet structure):
- Họ và tên (Full Name) * - Required
- Số điện thoại (Phone) * - Required  
- Email - Optional
- Địa chỉ (Address) - Optional
- Ngày sinh (Date of Birth) - Optional
- Số CCCD/CMND (ID Number) - Optional
- Mã CTV người giới thiệu (Referrer Code) - Optional
- Mật khẩu (Password) * - Required
- Xác nhận mật khẩu (Confirm Password) * - Required

**Features**:
- Bilingual support (Vietnamese/English)
- Form validation
- Password confirmation
- Phone number validation
- Checks for duplicate phone numbers
- Verifies referrer code exists
- Beautiful design matching website style

### 2. Backend API Endpoints

#### `/ctv/signup` (GET)
- Serves the signup page

#### `/api/ctv/signup` (POST)
- Handles registration submissions
- Validates all input
- Checks for existing phone numbers
- Verifies referrer codes
- Stores registration with `pending` status
- Returns success/error response

### 3. Admin Management APIs

#### `/api/admin/registrations` (GET)
- Lists all CTV registration requests
- Filter by status: `pending`, `approved`, `rejected`, `all`
- Pagination support
- Shows applicant details and referrer info

#### `/api/admin/registrations/<id>/approve` (POST)
- Approves a registration
- Creates CTV account in `ctv` table
- Requires CTV code assignment
- Updates registration status to `approved`
- Logs admin action

#### `/api/admin/registrations/<id>/reject` (POST)
- Rejects a registration
- Updates status to `rejected`
- Allows admin to provide rejection reason
- Logs admin action

### 4. Database Schema

**Table**: `ctv_registrations`
```sql
- id (SERIAL PRIMARY KEY)
- full_name (VARCHAR 255) - Applicant's full name
- phone (VARCHAR 20) - Phone number
- email (VARCHAR 255) - Email address
- address (TEXT) - Physical address
- dob (DATE) - Date of birth
- id_number (VARCHAR 50) - ID card number
- referrer_code (VARCHAR 50) - CTV code of referrer
- password_hash (VARCHAR 255) - Hashed password
- status (VARCHAR 20) - pending/approved/rejected
- admin_notes (TEXT) - Admin's notes/reason
- created_at (TIMESTAMP) - When registered
- reviewed_at (TIMESTAMP) - When reviewed
- reviewed_by (VARCHAR 50) - Admin who reviewed
```

**Indexes**:
- `idx_ctv_registrations_status` - Fast filtering by status
- `idx_ctv_registrations_phone` - Phone lookup
- `idx_ctv_registrations_created_at` - Sort by date

## File Structure

```
/templates/
  ctv_signup.html          # Signup page template

/static/css/ctv/
  signup.css               # Signup page styles

/static/js/ctv/
  signup.js                # Signup form logic

/modules/ctv/
  signup.py                # CTV signup routes

/modules/admin/
  registrations.py         # Admin approval routes

/schema/
  ctv_registrations.sql    # Database schema
```

## Admin Workflow

1. **User submits signup form** → Status: `pending`
2. **Admin reviews in admin panel** → Can see all applicant details
3. **Admin approves**:
   - Assigns CTV code
   - Creates account in `ctv` table
   - Status → `approved`
   - User can now login
4. **Admin rejects**:
   - Provides reason
   - Status → `rejected`
   - User notified (can implement email/SMS later)

## Access URLs

- **Signup Page**: `http://localhost:4000/ctv/signup`
- **Link added to**: CTV Login Page (`/ctv/portal`)
- **Admin Panel**: Needs UI integration (APIs ready)

## Next Steps (For Admin UI)

1. Add "Registrations" menu item to admin sidebar
2. Create admin page to display pending registrations
3. Add approve/reject buttons with modals
4. Show registration history (approved/rejected)
5. Add notifications for new registrations

## Security Features

- Passwords are hashed using `werkzeug.security`
- Phone number validation and deduplication
- Referrer code verification
- Prevents duplicate pending registrations
- Admin authentication required for approvals

## Testing

To test:
1. Visit: `http://localhost:4000/ctv/signup`
2. Fill out the form
3. Submit registration
4. Check database: `SELECT * FROM ctv_registrations;`
5. Use admin API to approve/reject

## Notes

- Form design matches existing website style (green theme, glass morphism)
- Bilingual interface (Vietnamese/English)
- Mobile responsive
- All fields except full_name, phone, and password are optional
- Database table created and ready
- Backend APIs fully functional
