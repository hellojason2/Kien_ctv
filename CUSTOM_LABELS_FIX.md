# Custom Level Labels - Universal Update Fix

## Issue Summary
The user configured custom level labels in the admin settings page:
- Level 0 → "LS" with 25% commission
- Level 1 → "TEAM" with 5% commission

However, the hierarchy views throughout the app were still showing:
- Old hardcoded labels: "L0", "L1", "L2", "L3", "L4"
- Old rank field: "Công Tác Viên" (from `cap_bac` database field)
- Old commission percentages: "20.00%"

The custom labels were not being universally applied across all hierarchy and commission displays.

## Root Cause
Multiple JavaScript files were rendering level badges and labels with hardcoded formats:
1. `static/js/admin/hierarchy.js` - Used `L${displayLevel}` and `cap_bac` field
2. `static/js/ctv/network.js` - Used `L${displayLevel}` and `cap_bac` field  
3. `static/js/admin/debug-commission.js` - Used `L${c.level}` and `Level ${c.level}` in multiple places
4. `static/js/ctv/commissions.js` - Used `LEVEL ${c.level}` in lifetime stats table

These files were not calling the `getCommissionLabel()` function from `commission-labels.js`.

## Solution Implemented

### Files Updated
1. **static/js/admin/hierarchy.js**
   - Changed badge from `L${displayLevel}` to `${levelLabel}` where `levelLabel = getCommissionLabel(displayLevel)`
   - Changed rank display from `${node.cap_bac || 'Bronze'} | ${commissionPercent}%` to `${levelLabel} | ${commissionPercent}%`

2. **static/js/ctv/network.js**
   - Changed badge from `L${displayLevel}` to `${levelLabel}` where `levelLabel = getCommissionLabel(displayLevel)`
   - Changed info display from `${node.cap_bac || 'Bronze'}` to `${levelLabel}`

3. **static/js/admin/debug-commission.js**
   - Updated 5 different places where level labels were hardcoded:
     - Commission breakdown: Changed `'Personal (L0)'` / `Level ${group.closer_level}` to `getCommissionLabel(group.closer_level)`
     - Commissions table: Changed `L${c.level}` to `getCommissionLabel(c.level)`
     - Calculation table: Changed `L${c.level}` to `getCommissionLabel(c.level)`
     - Downline table: Changed `L${d.level}` to `getCommissionLabel(d.level)`
     - Client info modal: Changed `Level ${c.level}` to `getCommissionLabel(c.level)`

4. **static/js/ctv/commissions.js**
   - Lifetime stats table: Changed `LEVEL ${c.level}` to `${getCommissionLabel(c.level)}`

### How It Works
The `getCommissionLabel()` function (from `commission-labels.js`):
1. Checks if custom labels are loaded in `window.commissionLabels`
2. If not, returns default "Level X" format
3. If yes, returns the custom label for that level

The labels are loaded on app initialization:
- Admin: `static/js/admin/main.js` calls `loadCommissionLabels()` on line 156
- CTV Portal: `static/js/ctv/main.js` calls `loadCommissionLabels()` on line 98

## What Changed Everywhere

### Before (with LS=25%, TEAM=5% settings):
```
Hierarchy Node Display:
- Badge: "L0"
- Rank: "Công Tác Viên | 20.00%"

Commission Tables:
- Level Badge: "L0"
```

### After (with LS=25%, TEAM=5% settings):
```
Hierarchy Node Display:
- Badge: "LS"
- Rank: "LS | 25.00%"

Next Level:
- Badge: "TEAM"
- Rank: "TEAM | 5.00%"

Commission Tables:
- Level Badge: "LS" or "TEAM" (depending on level)
```

## Testing Checklist

To verify the fix works correctly:

### Admin Dashboard
1. ✅ Navigate to Settings page
2. ✅ Verify commission settings show your custom labels (LS, TEAM, etc.)
3. ✅ Navigate to Hierarchy page
4. ✅ Select a CTV and view their hierarchy tree
5. ✅ Verify level badges show custom labels (LS, TEAM) instead of L0, L1
6. ✅ Verify rank display shows "LS | 25.00%" instead of "Công Tác Viên | 20.00%"
7. ✅ Navigate to Debug Commission page
8. ✅ Verify all commission tables show custom labels

### CTV Portal
1. ✅ Login as a CTV
2. ✅ Navigate to Network/Team page
3. ✅ Verify hierarchy tree shows custom labels
4. ✅ Navigate to Commissions/Earnings page
5. ✅ Verify commission tables show custom labels in lifetime stats

## Deployment

Changes have been committed and pushed to GitHub:
```
Commit: 67ea8b0
Message: Fix: Universal update for custom level labels across all hierarchy displays
Files: 4 JavaScript files modified
```

The changes will automatically deploy to Railway on the next build.

## Cache Busting

The Flask app uses automatic cache busting based on file modification time, so users will automatically get the updated JavaScript files on their next page load without needing to clear browser cache.

## API Used

- `GET /api/commission-labels` - Returns custom labels from database
  - Called by: `loadCommissionLabels()` in `commission-labels.js`
  - Returns: `{ "status": "success", "labels": { "0": "LS", "1": "TEAM", ... } }`

## Database Schema

Custom labels are stored in the `commission_settings` table:
```sql
SELECT level, rate, label, is_active 
FROM commission_settings 
ORDER BY level;
```

Example output:
| level | rate | label | is_active |
|-------|------|-------|-----------|
| 0     | 0.25 | LS    | true      |
| 1     | 0.05 | TEAM  | true      |
| 2     | 0.00 | Level 2 | false   |
| 3     | 0.00 | Level 3 | false   |
| 4     | 0.00 | Level 4 | false   |

## Notes

- The fix ensures ALL displays of commission levels throughout the entire application now use the custom labels
- Labels are loaded once on app initialization and cached in memory
- When settings are changed, the cache is automatically invalidated
- The system falls back to "Level X" format if custom labels fail to load
- This is a client-side only change - no database migrations needed
- Works for both active and inactive levels (though inactive levels don't typically display)
