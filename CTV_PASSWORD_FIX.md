# CTV Password Authentication Fix

## Issue Summary
CTVs were unable to login after admin approval because their signup passwords weren't working. Admin had to manually reset passwords for approved CTVs.

## Root Cause
The system had a mix of password formats in the database:
- **Legacy format**: Plain SHA256 hash (no salt) - stored as a single 64-character hex string
- **New format**: Salted SHA256 hash - stored as `salt:hash` format

When old registrations (with plain SHA256) were approved, the incompatible hash was copied to the CTV table, making login impossible.

## Solution Implemented

### 1. Enhanced Password Verification (`modules/auth.py`)
Updated `verify_password()` function to support **both formats**:

```python
def verify_password(password, stored_hash):
    """
    Verify password against stored hash - supports both formats:
    - New format: "salt:hash" (salted SHA256)
    - Legacy format: plain SHA256 hash (for backward compatibility)
    """
    if not stored_hash:
        return False
    
    try:
        # New format: salt:hash
        if ':' in stored_hash:
            salt, expected_hash = stored_hash.split(':', 1)
            actual_hash = hashlib.sha256((salt + password).encode()).hexdigest()
            return actual_hash == expected_hash
        
        # Legacy format: plain SHA256 hash
        else:
            plain_hash = hashlib.sha256(password.encode()).hexdigest()
            return plain_hash == stored_hash
    except Exception:
        return False
```

**Benefits**:
- ✅ Existing CTVs with old password format can still login
- ✅ New signups use secure salted hashes
- ✅ No password reset required for existing users

### 2. Enhanced Approval Process (`modules/admin/registrations.py`)
Added detection and warning for legacy password formats during approval:

```python
# Check password hash format and warn if it's legacy format
password_hash = registration['password_hash']
is_legacy_format = password_hash and ':' not in password_hash
warning_message = ''

if is_legacy_format:
    warning_message = ' (Warning: Using legacy password format - user can still login)'
```

**Benefits**:
- ✅ Admins are informed when approving accounts with old password format
- ✅ Transparency in the approval process
- ✅ User can still login successfully with their original password

### 3. Ensured New Signups Use Proper Format
Verified that `modules/ctv/signup.py` correctly uses the `hash_password()` function:

```python
# Line 266: Hash password using proper hash_password function (salt:hash format)
password_hash = hash_password(password)
```

**Benefits**:
- ✅ All new signups automatically get secure salted hashes
- ✅ Forward compatibility ensured

## Testing Performed

### Test 1: New Format (Salt:Hash)
- ✅ Created test signup with password "NewPassword123"
- ✅ Hash stored in format: `salt:hash`
- ✅ Simulated admin approval
- ✅ Login successful with original password
- ✅ Wrong password correctly rejected

### Test 2: Legacy Format (Plain SHA256)
- ✅ Created test signup with legacy hash (password "123456")
- ✅ Hash stored as plain SHA256 (no colon)
- ✅ Simulated admin approval
- ✅ Login successful with original password (backward compatibility working!)
- ✅ Wrong password correctly rejected

### Test 3: End-to-End Flow
- ✅ Complete signup → approval → login workflow verified
- ✅ Both password formats work correctly
- ✅ No password reset required

## Deployment

**Status**: ✅ **DEPLOYED TO PRODUCTION**

**Git commit**: `5d49c82`
**Push status**: Successfully pushed to GitHub (origin/main)

### Files Modified
1. `modules/auth.py` - Enhanced password verification
2. `modules/admin/registrations.py` - Added legacy hash detection
3. `modules/ctv/signup.py` - Verified proper hash usage
4. `static/js/ctv/signup.js` - Frontend signup form
5. `templates/ctv_signup.html` - Signup template

## Impact

### For Existing CTVs
- ✅ Can login with their original signup password
- ✅ No action required from users
- ✅ No password reset needed

### For New CTVs
- ✅ Passwords stored securely with salt
- ✅ Immediate login after approval
- ✅ Enhanced security

### For Admins
- ✅ Clear warnings for legacy password formats
- ✅ No manual password resets required
- ✅ Smooth approval process

## Security Notes

### Backward Compatibility
The system now accepts both formats for **verification only**. All **new passwords** are stored with the secure salted format.

### Why Legacy Format Support is Safe
1. Legacy hashes are **read-only** - no new passwords are stored this way
2. The verification function only accepts valid passwords
3. Wrong passwords are still rejected correctly
4. This is a common approach for password migration

### Future Enhancement (Optional)
Consider implementing a "password rehash on next login" feature:
- When a user with legacy format logs in successfully
- Generate a new salted hash and update the database
- Gradually migrate all users to the secure format

## Verification Commands

To verify the fix is working:

```bash
# Check password hash format in database
SELECT 
    ma_ctv, 
    CASE 
        WHEN password_hash LIKE '%:%' THEN 'New (salt:hash)'
        ELSE 'Legacy (plain SHA256)'
    END as format
FROM ctv 
LIMIT 10;

# Test login with both formats
# (Use the CTV portal login page)
```

## Summary

✅ **Issue Fixed**: CTVs can now login immediately after admin approval  
✅ **Backward Compatible**: Existing accounts work without password reset  
✅ **Secure**: New accounts use salted password hashing  
✅ **Deployed**: Changes pushed to production  
✅ **Tested**: Comprehensive testing confirms both formats work  

**Date**: January 15, 2026  
**Status**: RESOLVED ✅
