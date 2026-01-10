from flask import jsonify, request
from .blueprint import admin_bp
from ..auth import require_admin
from ..google_sync import GoogleSheetSync
from ..db_pool import get_db_connection
import logging

logger = logging.getLogger(__name__)

@admin_bp.route('/api/admin/reset-data/preview', methods=['GET'])
@require_admin
def reset_data_preview():
    """
    Get current database counts before hard reset.
    Returns counts for each source type.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get counts for each source
        counts = {}
        for source in ['tham_my', 'nha_khoa', 'gioi_thieu']:
            cur.execute("SELECT COUNT(*) FROM khach_hang WHERE source = %s", (source,))
            counts[source] = cur.fetchone()[0]
        
        # Get total commissions count
        cur.execute("SELECT COUNT(*) FROM commissions")
        counts['commissions'] = cur.fetchone()[0]
        
        # Get total
        counts['total'] = counts['tham_my'] + counts['nha_khoa'] + counts['gioi_thieu']
        
        cur.close()
        conn.close()
        
        logger.info(f"Hard Reset Preview - Database counts: {counts}")
        
        return jsonify({
            'status': 'success',
            'counts': counts
        })
        
    except Exception as e:
        logger.error(f"Error getting reset preview: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/api/admin/reset-data', methods=['POST'])
@require_admin
def reset_data():
    """
    Hard reset client service data:
    1. Clear khach_hang table for tham_my, nha_khoa, gioi_thieu
    2. Re-import all rows from Google Sheets
    3. Recalculate commissions
    
    Returns detailed logs for frontend display.
    """
    try:
        logger.info("=" * 60)
        logger.info("HARD RESET INITIATED")
        logger.info("=" * 60)
        
        syncer = GoogleSheetSync()
        success, result, logs = syncer.hard_reset_with_logs()
        
        if success:
            logger.info("=" * 60)
            logger.info("HARD RESET COMPLETED SUCCESSFULLY")
            logger.info(f"Stats: {result}")
            logger.info("=" * 60)
            
            return jsonify({
                'status': 'success', 
                'message': 'Hard reset completed successfully',
                'stats': result,
                'logs': logs
            })
        else:
            logger.error(f"HARD RESET FAILED: {result}")
            return jsonify({
                'status': 'error', 
                'message': f'Hard reset failed: {result}',
                'logs': logs
            }), 500
            
    except Exception as e:
        logger.error(f"HARD RESET EXCEPTION: {e}")
        import traceback
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'logs': [{'type': 'error', 'message': str(e), 'step': 'exception'}]
        }), 500
