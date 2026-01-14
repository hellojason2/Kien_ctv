# Customizable Commission Level Labels

## Overview

The system now supports customizable labels for commission levels. Instead of hardcoded "Level 0", "Level 1", etc., you can now name each level according to your business needs.

## Features

### For Admin Panel
- **Settings Page**: Edit level labels directly in the Commission Settings page
- **Editable Labels**: Click on the label input field to change the name of each level
- **Real-time Updates**: Changes are saved immediately and reflected across the entire system
- **Custom Names**: Use any name you want (e.g., "Personal", "Team", "Regional", "National", "Global")

### Where Labels Appear
- Admin dashboard - commission tables
- CTV portal - earnings breakdown
- Commission debug page
- All commission reports

## Migration

### Database Migration

Before using this feature, you need to add the `label` column to the `commission_settings` table.

#### Option 1: Run Migration Script (Production)

```bash
# Set your DATABASE_URL first
export DATABASE_URL="your_postgresql_connection_string"

# Run the migration
python3 migrate_level_labels.py
```

#### Option 2: Manual SQL (If migration script fails)

```sql
-- Add label column
ALTER TABLE commission_settings 
ADD COLUMN IF NOT EXISTS label VARCHAR(50);

-- Set default labels for existing rows
UPDATE commission_settings 
SET label = 'Level ' || level::text
WHERE label IS NULL;
```

## Usage

### Admin: Changing Level Labels

1. Log in to the admin panel
2. Navigate to **Settings** page
3. Find the **Commission Rates by Level** section
4. Click on the label input field (where it says "Level 0", "Level 1", etc.)
5. Type your custom label (e.g., "Personal Sale", "Direct Referral", "Team Level")
6. Click **Save Changes**

### Example Custom Labels

**Traditional MLM Names:**
- Level 0 → "Personal Sales"
- Level 1 → "Direct Downline"
- Level 2 → "Second Generation"
- Level 3 → "Third Generation"
- Level 4 → "Fourth Generation"

**Business-focused Names:**
- Level 0 → "Direct Commission"
- Level 1 → "Team Bonus"
- Level 2 → "Regional Override"
- Level 3 → "National Override"
- Level 4 → "Global Override"

**Tiered Names:**
- Level 0 → "Bronze"
- Level 1 → "Silver"
- Level 2 → "Gold"
- Level 3 → "Platinum"
- Level 4 → "Diamond"

## API Endpoints

### Get Commission Labels (Public)
```
GET /api/commission-labels
```

Returns:
```json
{
  "status": "success",
  "labels": {
    "0": "Personal Sales",
    "1": "Direct Downline",
    "2": "Second Generation",
    "3": "Third Generation",
    "4": "Fourth Generation"
  }
}
```

### Get/Update Settings (Admin Only)
```
GET /api/admin/commission-settings
PUT /api/admin/commission-settings
```

The PUT request now accepts a `label` field for each level:
```json
{
  "settings": [
    {
      "level": 0,
      "rate": 0.25,
      "label": "Personal Sales",
      "is_active": true
    },
    ...
  ]
}
```

## Technical Details

### Database Schema
- **Table**: `commission_settings`
- **New Column**: `label VARCHAR(50)` - Stores the custom label for each level
- **Default Value**: "Level X" if not set

### Frontend
- **Global Cache**: Labels are cached in `window.commissionLabels` for performance
- **Utility Functions**: 
  - `loadCommissionLabels()` - Fetches labels from API
  - `getCommissionLabel(level)` - Gets label for a specific level
  - `formatLevelBadge(level)` - Formats a level badge with custom label

### Cache Invalidation
When you save new labels in the admin settings, the frontend cache is automatically cleared, ensuring all displays show the updated labels immediately.

## Troubleshooting

### Labels Not Updating
1. Clear browser cache and refresh the page
2. Check if the migration was successful
3. Verify labels were saved in the database:
   ```sql
   SELECT level, rate, label FROM commission_settings ORDER BY level;
   ```

### Migration Failed
If the automatic migration fails, you can manually add the column using the SQL commands provided above.

## Files Modified

### Backend
- `schema/postgresql_schema.sql` - Added label column to schema
- `modules/admin/commissions.py` - Updated to handle label field
- `modules/api/commissions.py` - Added `/api/commission-labels` endpoint
- `migrate_level_labels.py` - Migration script

### Frontend
- `static/js/commission-labels.js` - New utility file for label management
- `static/js/admin/settings.js` - Updated to allow label editing
- `static/js/admin/main.js` - Load labels on init
- `static/js/ctv/main.js` - Load labels on init
- `static/js/ctv/commissions.js` - Use custom labels in displays
- `static/js/admin/debug-commission.js` - Use custom labels in debug view
- `static/css/admin/forms.css` - Added styling for label input

### Templates
- `templates/admin/base.html` - Include commission-labels.js
- `templates/ctv/base.html` - Include commission-labels.js
- `templates/admin/pages/debug-commission.html` - Include commission-labels.js

## Created: January 14, 2026
