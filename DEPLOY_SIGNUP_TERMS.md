# Deploy Signup Terms Feature to Production

## Problem
The `signup_terms` table exists locally but needs to be deployed to Railway production.

## Solution - Deploy Migration

### Step 1: Push code to GitHub/Railway

Make sure all files are committed and pushed:

```bash
# Check what files changed
git status

# Add all files
git add -A

# Commit
git commit -m "Add signup terms database migration and feature"

# Push to GitHub (Railway will auto-deploy)
git push origin main
```

### Step 2: Run Migration on Railway

Once the code is deployed, you need to run the migration on the production database.

**Option A: Use Railway CLI (Recommended)**

```bash
# Install Railway CLI if not already installed
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Run the migration
railway run python3 migrate_signup_terms.py
```

**Option B: Use Railway Dashboard**

1. Go to Railway Dashboard
2. Open your project
3. Go to the service
4. Click on "Console" or "Shell" tab
5. Run: `python3 migrate_signup_terms.py`

**Option C: SSH into Railway**

If your service supports SSH:
```bash
railway ssh
python3 migrate_signup_terms.py
exit
```

### Step 3: Verify Migration

After running the migration, verify it worked:

```bash
railway run python3 -c "
from modules.db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor

conn = get_db_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute('SELECT id, language, title, LENGTH(content) as len FROM signup_terms')
terms = cursor.fetchall()

print('Signup Terms in Production:')
for term in terms:
    print(f'  {term[\"language\"]}: {term[\"title\"]} ({term[\"len\"]} chars)')

cursor.close()
return_db_connection(conn)
"
```

You should see:
```
Signup Terms in Production:
  vi: Điều Khoản và Điều Kiện Cộng Tác Viên (2728 chars)
  en: Collaborator Terms and Conditions (2626 chars)
```

### Step 4: Test the Feature

1. **Test Signup Page:**
   - Go to: `https://your-app.railway.app/ctv/signup`
   - Click "Điều khoản và Điều kiện"
   - Verify the modal shows the full terms

2. **Test Admin Panel:**
   - Go to: `https://your-app.railway.app/admin89`
   - Login
   - Navigate to "Signup Terms" section
   - Switch language between Vietnamese and English
   - Verify both show full content

## Troubleshooting

### If Migration Fails

**Error: "signup_terms already exists"**
- The table already exists. Check if it has data:
  ```bash
  railway run python3 -c "from modules.db_pool import execute_query; print(execute_query('SELECT COUNT(*) FROM signup_terms'))"
  ```

**Error: "Database connection failed"**
- Check if DATABASE_URL is set correctly in Railway environment variables

### If Terms Still Show Empty in Admin Panel

1. Check browser console for JavaScript errors
2. Verify the API endpoint works:
   ```bash
   curl https://your-app.railway.app/api/admin/signup-terms/active?language=en
   ```
3. Clear browser cache and hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

### If Signup Page Shows Hardcoded Terms

The signup page has fallback hardcoded Vietnamese terms in the HTML. If you see these, it means:
- The JavaScript failed to load
- The API call failed
- The `loadSignupTerms()` function didn't execute

Check the browser console for errors.

## Files Modified

- `migrate_signup_terms.py` - Migration script to create table and insert default terms
- `schema/signup_terms.sql` - SQL schema for the table
- `modules/admin/terms.py` - Backend API for managing terms
- `templates/admin/pages/signup-terms.html` - Admin UI for editing terms
- `static/js/admin/signup-terms.js` - Admin UI JavaScript
- `static/js/ctv/signup.js` - Updated to load terms from database
- `templates/ctv_signup.html` - Has fallback hardcoded terms

## Important Notes

1. **The database migration MUST be run on production** - Just pushing code is not enough!
2. **Local database already has the migration** - You've successfully run it locally
3. **Railway needs the migration run separately** - Railway only deploys code, not database changes
4. **The signup page will work without the migration** - It has fallback hardcoded Vietnamese terms
5. **The admin panel needs the database** - It won't show anything if the table doesn't exist

## After Deployment

Once everything is working:
1. Test creating new terms versions in the admin panel
2. Test switching between Vietnamese and English
3. Test the version history feature
4. Verify the signup page loads the correct language
