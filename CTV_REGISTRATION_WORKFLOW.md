# CTV Registration & Approval Workflow

## Overview
The CTV registration system allows new collaborators to sign up through a public form. Their applications are stored as "pending" and require manual admin approval before they become active CTVs.

## How It Works

### 1. **CTV Signup Page** (`/ctv/signup`)
- Public-facing registration form
- No authentication required
- Collects applicant information:
  - Full Name (required)
  - Phone Number (required)
  - Email (optional)
  - Address (optional)
  - Date of Birth (optional)
  - ID Number (optional)
  - Referrer CTV Code (optional - validated against existing CTVs)
  - Password (required)

### 2. **Registration Submission**
When a user submits the form:
- **Validation checks:**
  - Phone number must be valid (9-11 digits)
  - Password must be at least 6 characters
  - Phone cannot already exist in the `ctv` table
  - Phone cannot have an existing pending registration
  - Referrer code (if provided) must exist in the system

- **What gets created:**
  - New record in `ctv_registrations` table with `status = 'pending'`
  - Password is hashed using SHA256
  - Timestamp is recorded

- **User feedback:**
  - Success: "Registration submitted successfully. Awaiting admin approval."
  - Error: Specific error message (duplicate phone, invalid referrer, etc.)

### 3. **Admin Review** (`/admin` → Registrations page)
Admins can view and manage pending registrations:

**Filter Options:**
- **Pending**: New applications awaiting review
- **Approved**: Successfully approved registrations
- **Rejected**: Declined applications
- **All**: Complete history

**For each registration, admins can:**
- **View Details**: See all submitted information
- **Approve**: Convert to active CTV account
- **Reject**: Decline the application

### 4. **Approval Process**
When an admin approves a registration:

1. **Admin provides:**
   - CTV Code (can auto-generate next available numeric code)
   - Initial Level (default: "Đồng"/Bronze)

2. **System creates:**
   - New record in `ctv` table with:
     - All information from registration
     - Assigned CTV code
     - Password hash (same as registration)
     - `active = TRUE`
     - `ngay_tao = NOW()`

3. **Registration record updated:**
   - `status = 'approved'`
   - `reviewed_at = NOW()`
   - `reviewed_by = [admin_username]`
   - `admin_notes = 'Approved as [CTV_CODE]'`

4. **New CTV can now:**
   - Log in to `/ctv/portal` with phone + password
   - Access their dashboard
   - Start referring clients

### 5. **Rejection Process**
When an admin rejects a registration:

1. **Admin provides:**
   - Optional reason for rejection

2. **Registration record updated:**
   - `status = 'rejected'`
   - `reviewed_at = NOW()`
   - `reviewed_by = [admin_username]`
   - `admin_notes = [rejection reason]`

3. **No CTV account is created**
4. Applicant would need to reapply with a different phone number

## Database Schema

### `ctv_registrations` table
```sql
CREATE TABLE IF NOT EXISTS ctv_registrations (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    dob DATE,
    id_number VARCHAR(50),
    referrer_code VARCHAR(50),
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(50),
    UNIQUE(phone, status)
);
```

## API Endpoints

### Public Endpoints
- `GET /ctv/signup` - Display signup form
- `POST /api/ctv/signup` - Submit registration

### Admin Endpoints (Auth Required)
- `GET /api/admin/registrations?status=[pending|approved|rejected|all]` - List registrations
- `POST /api/admin/registrations/{id}/approve` - Approve registration
  - Body: `{ "ctv_code": "123", "level": "Đồng" }`
- `POST /api/admin/registrations/{id}/reject` - Reject registration
  - Body: `{ "reason": "..." }`
- `POST /api/admin/ctv/generate-code` - Generate next available CTV code

## Files Involved

### Backend
- `modules/ctv/signup.py` - Signup form & submission logic
- `modules/admin/registrations.py` - Admin approval/rejection logic
- `modules/admin/ctv.py` - CTV code generation
- `schema/ctv_registrations.sql` - Database schema

### Frontend
- `templates/ctv_signup.html` - Public signup form
- `templates/admin/pages/registrations.html` - Admin review page
- `static/js/ctv/signup.js` - Signup form JavaScript
- `static/js/admin/registrations.js` - Admin review JavaScript

## Security Features

1. **Password Security**: SHA256 hashing (matches existing CTV auth)
2. **Duplicate Prevention**: 
   - Unique constraint on `(phone, status)` in registrations
   - Check against existing CTVs before registration
3. **Referrer Validation**: System verifies referrer code exists
4. **Admin-Only Approval**: Only authenticated admins can approve/reject
5. **Audit Trail**: Tracks who reviewed, when, and what decision was made

## User Experience Flow

```
User visits /ctv/signup
    ↓
Fills out registration form
    ↓
Submits application
    ↓
Sees success message: "Registration submitted. Awaiting admin approval."
    ↓
[Admin reviews in admin panel]
    ↓
Admin approves with CTV code
    ↓
CTV account created
    ↓
User can now login at /ctv/portal
```

## Benefits of This Approach

1. **Quality Control**: Manual review prevents spam/fake accounts
2. **Flexible Assignment**: Admin can assign appropriate CTV code and level
3. **Complete Audit Trail**: Full history of registrations and decisions
4. **Referrer Validation**: Ensures MLM hierarchy integrity from the start
5. **No Wasted Codes**: CTV codes only assigned to approved applications
6. **Easy Recovery**: Rejected applicants can be identified and contacted

## Future Enhancements (Optional)

1. Email notifications when registration is approved/rejected
2. Bulk approval for multiple pending registrations
3. Admin dashboard widget showing pending registration count
4. Auto-assignment of CTV codes based on rules
5. Application notes/comments thread for admin discussion
6. SMS verification of phone numbers
