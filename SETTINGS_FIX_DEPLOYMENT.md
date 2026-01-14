# Settings Fix - Quick Deployment Guide

## What Was Fixed
The admin settings page was not showing commission levels because the database was missing the `label` column in the `commission_settings` table.

## Deployment Steps

### For Railway/Production
The database has already been fixed on the production server. No additional steps needed.

### For New Deployments
The schema file (`schema/postgresql_schema.sql`) has been updated to include both `label` and `is_active` columns, so new deployments will work automatically.

### For Existing Deployments (If Needed)
If you encounter this issue on another deployment:

1. **Quick Fix via Python:**
   ```bash
   python3 fix_commission_settings.py
   ```

2. **Or via SQL:**
   ```bash
   psql $DATABASE_URL -f schema/add_is_active_column.sql
   ```

## Verification
After deployment, the settings page at `/admin89` → Settings should show:
- All 5 commission levels (0-4)
- Editable labels for each level
- Toggle switches to enable/disable each level
- Rate input fields
- Save button that becomes enabled when changes are made

## Files Changed in This Fix
### Critical Files (Must Deploy):
- `schema/postgresql_schema.sql` - Updated schema with both columns
- `static/js/admin/settings.js` - Already had proper label support

### Helper Scripts (Optional, for troubleshooting):
- `fix_commission_settings.py` - Database fix script
- `test_commission_settings_api.py` - API test script
- `COMMISSION_SETTINGS_FIX.md` - This documentation

---
**Status:** ✅ FIXED - Ready for deployment
**Date:** January 14, 2026
