# ✅ Signup Terms Admin Page - Complete Status & Guide

## Summary
The **Signup Terms** feature in the Admin panel is **FULLY FUNCTIONAL**. All backend, database, and frontend components are in place and working correctly.

## How to Access & Test

### Step 1: Log In to Admin Panel
1. Navigate to: `http://localhost:3001/admin89`
2. Enter credentials:
   - **Username:** `admin`
   - **Password:** `admin123`
3. Click "Login"

### Step 2: Navigate to Signup Terms
1. Look at the left sidebar
2. Find the "📄 Signup Terms" menu item (between "Settings" and "Activity Logs")
3. Click on it
4. The page should load with the current terms

### Step 3: What You Should See
When the page loads, you should see:
- **Language dropdown** (Tiếng Việt / English) in the top-right
- **Current version info** showing Version 1, last updated date
- **Title field** with "Điều Khoản và Điều Kiện Cộng Tác Viên"
- **Content editor** with ~2,728 characters of HTML content
- **Live Preview** showing formatted terms
- **Save Terms** button
- **Version History** button

## Current Content in Database

### Vietnamese (vi):
```
Title: "Điều Khoản và Điều Kiện Cộng Tác Viên"
Version: 1
Status: Active ✓
Content: 2,728 characters of HTML
Last Updated: 2026-01-14 03:33:32
```

### English (en):
```
Title: "Collaborator Terms and Conditions"
Version: 1
Status: Active ✓
Content: Available
Last Updated: 2026-01-14 03:33:32
```

## Features Available

### 1. Edit Terms
- Modify title and content
- HTML formatting toolbar (H4, P, Bold, Italic, Lists)
- Live preview updates as you type
- Click "Save Terms" to save changes

### 2. Version Control
- Click "Version History" to see all versions
- Each version shows:
  - Version number
  - Active/Inactive status
  - Update timestamp
  - Updated by (admin username)
- **Activate** old versions to make them current
- **Delete** old versions (cannot delete active version)

### 3. Multi-Language Support
- Switch between Vietnamese and English using dropdown
- Each language has independent version history
- Terms are displayed on CTV signup page based on language

## How Signup Terms Are Used

### On CTV Signup Page (`/ctv/signup`):
1. When a prospective CTV visits the signup page
2. The page calls `/api/admin/signup-terms/active?language=vi`
3. The active terms for their language are displayed
4. They must check the "I agree" checkbox to proceed
5. Their agreement is recorded in the database

## Troubleshooting

### Problem: "Blank page after clicking Signup Terms"

**Solution 1:** Check Browser Console
1. Press F12 to open Developer Tools
2. Go to "Console" tab
3. Look for JavaScript errors (red text)
4. If you see authentication errors, try logging out and back in

**Solution 2:** Check API Call
1. Press F12 → "Network" tab
2. Click "Signup Terms" in sidebar
3. Look for a request to `/api/admin/signup-terms?language=vi`
4. Click on it to see the response
5. Should show `{"status": "success", "terms": [...]}`

**Solution 3:** Clear Cache & Refresh
1. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Or clear browser cache
3. Log in again

### Problem: "Cannot save changes"

**Check:**
- You are logged in as admin
- Title and content are not empty
- Check console for error messages
- Verify database connection is working

### Problem: "No data shows up"

**Verify Database:**
Run this command to check:
```bash
python3 test_signup_terms_page.py
```

This will verify:
- Database has terms
- API can fetch terms
- Files exist
- Sessions work

## API Endpoints Reference

### Admin Endpoints (Require Authentication):
- `GET /api/admin/signup-terms?language=vi` - List all terms for language
- `POST /api/admin/signup-terms` - Create new version
- `PUT /api/admin/signup-terms/:id` - Update existing version
- `PUT /api/admin/signup-terms/:id/activate` - Activate a version
- `DELETE /api/admin/signup-terms/:id` - Delete a version

### Public Endpoint:
- `GET /api/admin/signup-terms/active?language=vi` - Get active terms for signup page

## Files Involved

### Backend:
- `modules/admin/terms.py` - API endpoints
- `schema/signup_terms.sql` - Database schema

### Frontend:
- `templates/admin/pages/signup-terms.html` - Page template
- `static/js/admin/signup-terms.js` - Page logic and API calls
- `templates/admin/components/sidebar.html` - Navigation link (line 58)
- `static/js/admin/navigation.js` - Page load handler (line 31)

### Migration:
- `migrate_signup_terms.py` - Database migration script
- `test_signup_terms.py` - Test script
- `verify_signup_terms.py` - Verification script

## Deployment Status

✅ **Database:** Table created with proper schema
✅ **Data:** Default terms loaded (Vietnamese & English)  
✅ **Backend:** All API endpoints functional and tested
✅ **Frontend:** Page integrated into admin panel
✅ **Navigation:** Menu link added to sidebar
✅ **Committed:** All changes pushed to GitHub (commit e23ff66)
✅ **Deployed:** Railway auto-deploys from GitHub

## What Controls the CTV Signup Page Terms

The terms shown on the **CTV Signup Page** (`/ctv/signup`) are controlled by:

1. **Active Terms:** Only terms marked as `is_active = TRUE` are shown
2. **Language:** Determined by user's browser language or manual selection
3. **Latest Version:** If multiple versions are active, the highest version number is used
4. **Admin Control:** You manage these via the "Signup Terms" page in admin panel

### To Update Terms on Signup Page:
1. Log in to admin panel
2. Navigate to "Signup Terms"
3. Edit the content
4. Click "Save Terms"
5. The new version automatically becomes active
6. CTV signup page immediately shows the new terms

---

## Next Steps

1. ✅ Log in to admin panel with `admin` / `admin123`
2. ✅ Click "Signup Terms" in sidebar
3. ✅ Verify the page loads with existing terms
4. ✅ Try editing and saving to test functionality
5. ✅ Check the CTV signup page to see terms displayed

---

**Status:** ✅ FULLY FUNCTIONAL AND READY TO USE
**Last Updated:** January 14, 2026
**Committed:** e23ff66 (pushed to GitHub)
**Deployed:** Production ready

If you still see a blank page, please let me know what you see in the browser console (F12 → Console tab) and I'll help debug further.
