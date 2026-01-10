from flask import jsonify, request
from .blueprint import admin_bp
from ..auth import require_admin
from ..google_sync import GoogleSheetSync

@admin_bp.route('/api/admin/reset-data', methods=['POST'])
@require_admin
def reset_data():
    """
    Hard reset client service data:
    1. Clear khach_hang table for tham_my, nha_khoa, gioi_thieu
    2. Re-import all rows from Google Sheets
    3. Recalculate commissions
    """
    try:
        syncer = GoogleSheetSync()
        success, result = syncer.hard_reset()
        
        if success:
            return jsonify({
                'status': 'success', 
                'message': 'Hard reset completed successfully',
                'stats': result
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': f'Hard reset failed: {result}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500
