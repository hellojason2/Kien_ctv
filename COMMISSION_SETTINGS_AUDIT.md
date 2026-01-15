# Commission Settings Audit Report
**Date**: January 15, 2026
**Status**: ⚠️ CRITICAL ISSUES FOUND

## 🔴 **PROBLEM SUMMARY**

The system has **TWO** commission settings tables that are **OUT OF SYNC**, causing inconsistencies in commission calculations.

---

## 📊 **CURRENT STATE**

### Table 1: `commission_settings` (Admin Panel Shows This)
| Level | Label | Rate | Status | Description |
|-------|-------|------|--------|-------------|
| 0 | LS | **24.00%** | ✅ ACTIVE | Self commission |
| 1 | TEAM | **4.00%** | ✅ ACTIVE | Direct referral |
| 2 | Support | **2.00%** | ✅ ACTIVE | Level 2 |
| 3 | Level 3 | **1.25%** | ❌ INACTIVE | Level 3 |
| 4 | Level 4 | **0.63%** | ❌ INACTIVE | Level 4 |

### Table 2: `hoa_hong_config` (System ACTUALLY Uses This)
| Level | Rate | Status |
|-------|------|--------|
| 0 | **20.00%** | ✅ ACTIVE |
| 1 | **5.00%** | ✅ ACTIVE |
| 2 | **2.50%** | ❌ INACTIVE |
| 3 | **1.25%** | ❌ INACTIVE |
| 4 | **0.625%** | ❌ INACTIVE |

---

## ⚠️ **MISMATCHES DETECTED**

### Level 0 (Self Commission):
- **Admin Panel**: 24.00% ✅ ACTIVE
- **Actual System**: 20.00% ✅ ACTIVE
- **DIFFERENCE**: **4%** mismatch!

### Level 1 (Direct Referral):
- **Admin Panel**: 4.00% ✅ ACTIVE
- **Actual System**: 5.00% ✅ ACTIVE
- **DIFFERENCE**: **1%** mismatch!

### Level 2:
- **Admin Panel**: 2.00% ✅ ACTIVE
- **Actual System**: 2.50% ❌ INACTIVE
- **DIFFERENCE**: **0.5%** rate + status mismatch!

---

## 🔧 **ROOT CAUSE**

**File**: `modules/mlm/commissions.py` (lines 45-65)

The system prioritizes `hoa_hong_config` table over `commission_settings`:

```python
# Try hoa_hong_config first
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'hoa_hong_config')")
if cursor.fetchone()['exists']:
    cursor.execute("SELECT level, percent, is_active FROM hoa_hong_config ORDER BY level")
    # ... uses this table
    return rates

# Only uses commission_settings as fallback if hoa_hong_config doesn't exist
```

**Problem**: The admin panel updates `commission_settings`, but the commission calculation logic uses `hoa_hong_config`. Changes made in the admin panel **don't take effect**!

---

## ✅ **RECOMMENDED FIXES**

### Option 1: **Sync on Update** (Recommended)
When admin saves commission settings, update **BOTH** tables:

**File**: `modules/admin/commissions.py` (line 121-130)

```python
# Already updating commission_settings...

# Also update legacy table hoa_hong_config if it exists to keep them in sync
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'hoa_hong_config')")
if cursor.fetchone()['exists']:
    cursor.execute("""
        UPDATE hoa_hong_config 
        SET percent = %s, is_active = %s
        WHERE level = %s
    """, (rate * 100, new_is_active, level))  # Note: hoa_hong_config stores as percent (0-100)
```

✅ **Status**: This code already exists but may have a bug!

### Option 2: **Remove Priority** (Alternative)
Change `modules/mlm/commissions.py` to use `commission_settings` as primary source:

1. Swap the order - check `commission_settings` first
2. Use `hoa_hong_config` only as fallback for backwards compatibility

### Option 3: **Remove Legacy Table** (Long-term)
1. Drop `hoa_hong_config` table
2. Update all code to use only `commission_settings`
3. Simplify maintenance

---

## 🎯 **IMMEDIATE ACTION REQUIRED**

1. **Verify** the sync code in `modules/admin/commissions.py` line 121-130
2. **Manually sync** the two tables right now:
   ```sql
   UPDATE hoa_hong_config SET percent = 24.0, is_active = true WHERE level = 0;
   UPDATE hoa_hong_config SET percent = 4.0, is_active = true WHERE level = 1;
   UPDATE hoa_hong_config SET percent = 2.0, is_active = true WHERE level = 2;
   ```
3. **Test** commission calculations with updated rates
4. **Monitor** for future sync issues

---

## 📝 **TESTING CHECKLIST**

- [ ] Query both tables and verify they match
- [ ] Update a rate in admin panel
- [ ] Query both tables again - should still match
- [ ] Create a test transaction and verify commission uses correct rates
- [ ] Check Redis cache is invalidated properly

---

## 💡 **DEFAULT RATES** (Fallback)

If both tables fail, system uses these hardcoded defaults:

```python
DEFAULT_COMMISSION_RATES = {
    0: 0.25,      # 25% - self
    1: 0.05,      # 5% - direct referral
    2: 0.025,     # 2.5% - level 2
    3: 0.0125,    # 1.25% - level 3
    4: 0.00625    # 0.625% - level 4
}
```

---

**END OF REPORT**
