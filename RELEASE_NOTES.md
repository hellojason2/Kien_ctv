# Release Notes

## Commission Calculation and Filtering Logic Fixes

- **Status Check**: Verified and enforced strict filtering by `trang_thai = 'Đã đến làm'` (or 'Da den lam') across all commission-related modules.
- **Date Basis**: Updated all reports and commission lists to use `ngay_hen_lam` (Appointment Date) for filtering and attribution, replacing incorrect usage of `created_at`.

### Modified Files:
- `modules/admin/stats.py`: Updated `get_date_ranges_with_data` to use transaction dates.
- `modules/admin/commissions.py`: Updated `list_commissions` and `list_commissions_summary` to use transaction dates and strict status filtering.
- `modules/ctv/commissions.py`: Updated `get_my_commissions` to use transaction dates.

### Verified Files (No Changes Needed):
- `modules/mlm/commissions.py`
- `modules/admin/debug.py`
- `modules/ctv/profile.py`
