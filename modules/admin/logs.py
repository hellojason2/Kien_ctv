from flask import jsonify, request, g
from .blueprint import admin_bp
from ..auth import require_admin
from ..activity_logger import (
    get_activity_logs,
    get_activity_stats,
    get_activity_logs_grouped,
    get_suspicious_ips,
    cleanup_old_logs,
    log_data_export
)

@admin_bp.route('/api/admin/activity-logs', methods=['GET'])
@require_admin
def list_activity_logs():
    """Get activity logs with filtering and pagination"""
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        per_page = min(per_page, 100)
        
        result = get_activity_logs(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'logs': result['logs'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result.get('total_pages', 1)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/stats', methods=['GET'])
@require_admin
def get_logs_stats():
    """Get activity log statistics"""
    try:
        stats = get_activity_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/export', methods=['GET'])
@require_admin
def export_activity_logs():
    """Export activity logs as CSV"""
    import csv
    import io
    
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        
        result = get_activity_logs(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=1,
            per_page=10000
        )
        
        logs = result['logs']
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'ID', 'Timestamp', 'Event Type', 'User Type', 'User ID',
            'IP Address', 'Endpoint', 'Method', 'Status Code', 'Details'
        ])
        
        for log in logs:
            details_str = ''
            if log.get('details'):
                if isinstance(log['details'], dict):
                    details_str = str(log['details'])
                else:
                    details_str = str(log['details'])
            
            writer.writerow([
                log.get('id', ''),
                log.get('timestamp', ''),
                log.get('event_type', ''),
                log.get('user_type', ''),
                log.get('user_id', ''),
                log.get('ip_address', ''),
                log.get('endpoint', ''),
                log.get('method', ''),
                log.get('status_code', ''),
                details_str
            ])
        
        admin_username = g.current_user.get('username', 'admin')
        log_data_export('admin', admin_username, 'activity_logs', len(logs))
        
        output.seek(0)
        from flask import Response
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=activity_logs_{date_from or "all"}_{date_to or "now"}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/cleanup', methods=['POST'])
@require_admin
def cleanup_logs():
    """Clean up old activity logs"""
    data = request.get_json() or {}
    days = data.get('days', 90)
    
    if days < 30:
        return jsonify({
            'status': 'error',
            'message': 'Minimum retention period is 30 days'
        }), 400
    
    try:
        deleted_count = cleanup_old_logs(days)
        
        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted_count} logs older than {days} days',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/event-types', methods=['GET'])
@require_admin
def get_event_types():
    """Get list of available event types for filtering"""
    event_types = [
        {'value': 'login_success', 'label': 'Login Success', 'color': 'green'},
        {'value': 'login_failed', 'label': 'Login Failed', 'color': 'red'},
        {'value': 'logout', 'label': 'Logout', 'color': 'blue'},
        {'value': 'api_call', 'label': 'API Call', 'color': 'gray'},
        {'value': 'ctv_created', 'label': 'CTV Created', 'color': 'purple'},
        {'value': 'ctv_updated', 'label': 'CTV Updated', 'color': 'orange'},
        {'value': 'ctv_deleted', 'label': 'CTV Deleted', 'color': 'red'},
        {'value': 'commission_adjusted', 'label': 'Commission Adjusted', 'color': 'yellow'},
        {'value': 'data_export', 'label': 'Data Export', 'color': 'cyan'},
        {'value': 'settings_changed', 'label': 'Settings Changed', 'color': 'pink'}
    ]
    
    return jsonify({
        'status': 'success',
        'event_types': event_types
    })


@admin_bp.route('/api/admin/activity-logs/grouped', methods=['GET'])
@require_admin
def list_activity_logs_grouped():
    """Get activity logs grouped by user+IP combination"""
    try:
        event_type = request.args.get('event_type')
        user_type = request.args.get('user_type')
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        per_page = min(per_page, 100)
        
        result = get_activity_logs_grouped(
            event_type=event_type,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            date_from=date_from,
            date_to=date_to,
            search=search if search else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'groups': result['groups'],
            'suspicious_ips': result['suspicious_ips'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result.get('total_pages', 1)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/suspicious-ips', methods=['GET'])
@require_admin
def get_suspicious_ips_endpoint():
    """Get IPs that are logged into multiple accounts"""
    try:
        suspicious = get_suspicious_ips()
        
        return jsonify({
            'status': 'success',
            'suspicious_ips': suspicious,
            'count': len(suspicious)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/activity-logs/details', methods=['GET'])
@require_admin
def get_logs_by_user_ip():
    """Get detailed logs for a specific user+IP combination"""
    try:
        user_id = request.args.get('user_id')
        ip_address = request.args.get('ip_address')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not user_id and not ip_address:
            return jsonify({'status': 'error', 'message': 'user_id or ip_address required'}), 400
        
        result = get_activity_logs(
            user_id=user_id if user_id else None,
            ip_address=ip_address if ip_address else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'logs': result['logs'],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result.get('total_pages', 1)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

