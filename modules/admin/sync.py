from flask import jsonify, request
from .blueprint import admin_bp
from ..auth import require_admin
from ..google_sync import GoogleSheetSync, GOOGLE_SHEET_ID
from ..db_pool import get_db_connection, return_db_connection
from psycopg2.extras import RealDictCursor
import logging
import os

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
    Hard reset client service data (legacy - single call).
    For large datasets, use the step-by-step endpoints instead.
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


# ═══════════════════════════════════════════════════════════════════════════════
# STEP-BY-STEP HARD RESET (for large datasets / avoiding timeouts)
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/api/admin/reset-data/step/delete', methods=['POST'])
@require_admin
def reset_step_delete():
    """Step 1: Delete all records from khach_hang and commissions"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Delete khach_hang records
        cur.execute("""
            DELETE FROM khach_hang 
            WHERE source IN ('tham_my', 'nha_khoa', 'gioi_thieu')
        """)
        deleted_khach_hang = cur.rowcount
        
        # Delete commissions
        cur.execute("DELETE FROM commissions WHERE level >= 0")
        deleted_commissions = cur.rowcount
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        logger.info(f"RESET STEP 1: Deleted {deleted_khach_hang} khach_hang, {deleted_commissions} commissions")
        
        return jsonify({
            'status': 'success',
            'step': 'delete',
            'deleted_khach_hang': deleted_khach_hang,
            'deleted_commissions': deleted_commissions
        })
        
    except Exception as e:
        logger.error(f"RESET STEP 1 ERROR: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/reset-data/step/import/<tab_type>', methods=['POST'])
@require_admin  
def reset_step_import(tab_type):
    """Step 2-4: Import a specific tab (tham_my, nha_khoa, gioi_thieu)"""
    if tab_type not in ['tham_my', 'nha_khoa', 'gioi_thieu']:
        return jsonify({'status': 'error', 'message': 'Invalid tab type'}), 400
    
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        conn = syncer.get_db_connection()
        
        logger.info(f"RESET STEP IMPORT: Starting {tab_type}")
        
        # Use sync_tab_with_logs with hard_reset=True for fast import
        processed, errors, logs = syncer.sync_tab_with_logs(spreadsheet, conn, tab_type, hard_reset=True)
        
        conn.close()
        
        logger.info(f"RESET STEP IMPORT: {tab_type} - {processed} processed, {errors} errors")
        
        return jsonify({
            'status': 'success',
            'step': f'import_{tab_type}',
            'tab': tab_type,
            'processed': processed,
            'errors': errors,
            'logs': logs
        })
        
    except Exception as e:
        logger.error(f"RESET STEP IMPORT ERROR ({tab_type}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/reset-data/step/commissions', methods=['POST'])
@require_admin
def reset_step_commissions():
    """Step 5: Recalculate all commissions"""
    try:
        from modules.mlm_core import calculate_new_commissions_fast
        
        conn = get_db_connection()
        stats = calculate_new_commissions_fast(connection=conn)
        return_db_connection(conn)
        
        logger.info(f"RESET STEP COMMISSIONS: {stats}")
        
        return jsonify({
            'status': 'success',
            'step': 'commissions',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"RESET STEP COMMISSIONS ERROR: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/sync/manual', methods=['POST'])
@require_admin
def manual_sync():
    """
    Manually trigger a sync to pull new records from Google Sheets.
    Returns detailed logs for progress display.
    """
    try:
        from ..mlm_core import calculate_new_commissions_fast
        
        logs = []
        def add_log(message, level='info'):
            logs.append({'message': message, 'level': level, 'timestamp': datetime.now().isoformat()})
            logger.info(f"[SYNC {level.upper()}] {message}")
        
        from datetime import datetime
        
        add_log("Manual sync initiated")
        add_log("Connecting to Google Sheets...")
        
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        add_log("Connected to Google Sheets ✓")
        add_log("Connecting to database...")
        
        conn = syncer.get_db_connection()
        add_log("Connected to database ✓")
        
        stats = {
            'tham_my': {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'nha_khoa': {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'gioi_thieu': {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        }
        
        # Get DB counts before sync
        cur = conn.cursor()
        before_counts = {}
        for source in ['tham_my', 'nha_khoa', 'gioi_thieu']:
            cur.execute("SELECT COUNT(*) FROM khach_hang WHERE source = %s", (source,))
            before_counts[source] = cur.fetchone()[0]
        cur.close()
        
        add_log(f"Database before: TM={before_counts['tham_my']:,}, NK={before_counts['nha_khoa']:,}, GT={before_counts['gioi_thieu']:,}")
        
        # --- Sync Tham My ---
        add_log("")
        add_log("═══ Processing Thẩm Mỹ (Beauty) ═══")
        ins, upd = syncer.sync_tab_by_phone_matching(spreadsheet, conn, 'tham_my')
        stats['tham_my']['inserted'] = ins
        stats['tham_my']['updated'] = upd
        add_log(f"Thẩm Mỹ: {ins} new, {upd} updated")
        
        # --- Sync Nha Khoa ---
        add_log("")
        add_log("═══ Processing Nha Khoa (Dental) ═══")
        ins, upd = syncer.sync_tab_by_phone_matching(spreadsheet, conn, 'nha_khoa')
        stats['nha_khoa']['inserted'] = ins
        stats['nha_khoa']['updated'] = upd
        add_log(f"Nha Khoa: {ins} new, {upd} updated")
        
        # --- Sync Gioi Thieu ---
        add_log("")
        add_log("═══ Processing Giới Thiệu (Referral) ═══")
        ins, upd = syncer.sync_tab_by_phone_matching(spreadsheet, conn, 'gioi_thieu')
        stats['gioi_thieu']['inserted'] = ins
        stats['gioi_thieu']['updated'] = upd
        add_log(f"Giới Thiệu: {ins} new, {upd} updated")
        
        # Get DB counts after sync
        cur = conn.cursor()
        after_counts = {}
        for source in ['tham_my', 'nha_khoa', 'gioi_thieu']:
            cur.execute("SELECT COUNT(*) FROM khach_hang WHERE source = %s", (source,))
            after_counts[source] = cur.fetchone()[0]
        cur.close()
        
        add_log("")
        add_log(f"Database after: TM={after_counts['tham_my']:,}, NK={after_counts['nha_khoa']:,}, GT={after_counts['gioi_thieu']:,}")
        
        # Calculate total changes
        total_new = sum(s['inserted'] for s in stats.values())
        total_updated = sum(s['updated'] for s in stats.values())
        
        # Calculate commissions if there were any changes
        commission_stats = None
        if total_new > 0:
            add_log("")
            add_log("═══ Calculating Commissions ═══")
            commission_stats = calculate_new_commissions_fast(connection=conn)
            add_log(f"Commissions calculated: {commission_stats}")
        
        # Update heartbeat
        syncer.update_heartbeat(conn, total_new)
        
        conn.close()
        
        add_log("")
        add_log(f"✓ Sync complete! {total_new} new records, {total_updated} updated")
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'before_counts': before_counts,
            'after_counts': after_counts,
            'total_new': total_new,
            'total_updated': total_updated,
            'commission_stats': commission_stats,
            'logs': logs
        })
        
    except Exception as e:
        logger.error(f"MANUAL SYNC ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e), 'logs': logs if 'logs' in dir() else []}), 500


@admin_bp.route('/api/admin/sync/diagnose', methods=['GET'])
@require_admin
def diagnose_phone():
    """
    Diagnose a specific phone number - check if it exists in Google Sheet and database.
    Query params: phone - the phone number to check
    """
    phone = request.args.get('phone', '').strip()
    
    if not phone:
        return jsonify({'status': 'error', 'message': 'Phone number required'}), 400
    
    # Clean phone number
    phone_digits = ''.join(c for c in phone if c.isdigit())
    phone_suffix = phone_digits[-8:] if len(phone_digits) >= 8 else phone_digits
    
    result = {
        'phone': phone,
        'phone_digits': phone_digits,
        'phone_suffix': phone_suffix,
        'in_database': False,
        'db_records': [],
        'in_google_sheet': False,
        'sheet_records': [],
        'diagnosis': []
    }
    
    # Check database
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Search with multiple matching strategies
            cursor.execute("""
                SELECT id, ten_khach, sdt, co_so, ngay_nhap_don, ngay_hen_lam, 
                       dich_vu, tong_tien, nguoi_chot, source, trang_thai, created_at
                FROM khach_hang
                WHERE sdt = %s 
                   OR sdt LIKE %s
                   OR sdt LIKE %s
                ORDER BY ngay_nhap_don DESC NULLS LAST
                LIMIT 10
            """, (phone_digits, '%' + phone_suffix, phone_suffix + '%'))
            
            db_records = cursor.fetchall()
            if db_records:
                result['in_database'] = True
                result['db_records'] = [
                    {
                        'id': r['id'],
                        'ten_khach': r['ten_khach'],
                        'sdt': r['sdt'],
                        'co_so': r['co_so'],
                        'ngay_nhap_don': r['ngay_nhap_don'].isoformat() if r['ngay_nhap_don'] else None,
                        'ngay_hen_lam': r['ngay_hen_lam'].isoformat() if r['ngay_hen_lam'] else None,
                        'dich_vu': r['dich_vu'],
                        'tong_tien': float(r['tong_tien'] or 0),
                        'nguoi_chot': r['nguoi_chot'],
                        'source': r['source'],
                        'trang_thai': r['trang_thai'],
                        'created_at': r['created_at'].isoformat() if r['created_at'] else None
                    }
                    for r in db_records
                ]
            
            cursor.close()
            return_db_connection(connection)
        except Exception as e:
            logger.error(f"Database error in diagnose: {e}")
            result['diagnosis'].append(f"Database error: {e}")
            if connection:
                return_db_connection(connection)
    
    # Check Google Sheet
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Check all three tabs
        tabs_to_check = [
            ('tham_my', ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']),
            ('nha_khoa', ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']),
            ('gioi_thieu', ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral'])
        ]
        
        for tab_type, variations in tabs_to_check:
            worksheet = syncer.find_worksheet(spreadsheet, variations)
            if not worksheet:
                continue
            
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                continue
            
            headers = all_values[0]
            normalized_headers = [syncer.normalize_header(h) for h in headers]
            
            # Find phone column
            phone_col_idx = None
            for idx, h in enumerate(normalized_headers):
                if 'sdt' in h.lower() or 'dien thoai' in h.lower() or 'phone' in h.lower():
                    phone_col_idx = idx
                    break
            
            if phone_col_idx is None:
                continue
            
            # Search for phone number in sheet
            for row_idx, row in enumerate(all_values[1:], start=2):
                if phone_col_idx < len(row):
                    row_phone = syncer.clean_phone(row[phone_col_idx])
                    if row_phone and (row_phone == phone_digits or 
                                      row_phone.endswith(phone_suffix) or 
                                      phone_suffix in row_phone):
                        result['in_google_sheet'] = True
                        
                        # Build record dict
                        record = {'row_number': row_idx, 'tab': tab_type}
                        for j, h in enumerate(headers):
                            if j < len(row):
                                record[h] = row[j]
                        result['sheet_records'].append(record)
        
    except Exception as e:
        logger.error(f"Google Sheet error in diagnose: {e}")
        result['diagnosis'].append(f"Google Sheet error: {e}")
    
    # Generate diagnosis
    if result['in_google_sheet'] and not result['in_database']:
        result['diagnosis'].append("PROBLEM: Phone exists in Google Sheet but NOT in database!")
        result['diagnosis'].append("This indicates the sync worker has not processed this row.")
        result['diagnosis'].append("Possible causes:")
        result['diagnosis'].append("- Row was inserted in the middle of the sheet (count-based sync missed it)")
        result['diagnosis'].append("- Phone number format issue (cleaned differently)")
        result['diagnosis'].append("- Sync worker hasn't run since row was added")
        result['diagnosis'].append("SOLUTION: Use 'Force Sync' or enable phone matching sync mode")
    elif result['in_database'] and not result['in_google_sheet']:
        result['diagnosis'].append("Phone exists in database but NOT in Google Sheet")
        result['diagnosis'].append("This could be a manually added record or sheet cleanup")
    elif result['in_database'] and result['in_google_sheet']:
        result['diagnosis'].append("OK: Phone exists in both Google Sheet and database")
        # Check if data matches
        if result['db_records'] and result['sheet_records']:
            result['diagnosis'].append(f"Database has {len(result['db_records'])} record(s)")
            result['diagnosis'].append(f"Google Sheet has {len(result['sheet_records'])} record(s)")
    else:
        result['diagnosis'].append("Phone not found in either Google Sheet or database")
    
    return jsonify({'status': 'success', 'result': result})


@admin_bp.route('/api/admin/sync/integrity-check', methods=['GET'])
@require_admin
def integrity_check():
    """
    Full database integrity check - compare Google Sheet vs Database counts and find discrepancies.
    """
    result = {
        'tabs': {},
        'heartbeat': None,
        'discrepancies': [],
        'summary': {}
    }
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Get heartbeat status
        cursor.execute("""
            SELECT last_updated, cache_value 
            FROM commission_cache 
            WHERE cache_key = 'sync_worker_heartbeat'
        """)
        heartbeat = cursor.fetchone()
        if heartbeat:
            result['heartbeat'] = {
                'last_run': heartbeat['last_updated'].isoformat() if heartbeat['last_updated'] else None,
                'new_records': int(heartbeat['cache_value'] or 0)
            }
        
        # Get database counts by source
        for source in ['tham_my', 'nha_khoa', 'gioi_thieu']:
            cursor.execute("SELECT COUNT(*) as count FROM khach_hang WHERE source = %s", (source,))
            db_count = cursor.fetchone()['count']
            result['tabs'][source] = {'db_count': db_count, 'sheet_count': 0, 'difference': 0}
        
        cursor.close()
        return_db_connection(connection)
        
    except Exception as e:
        logger.error(f"Database error in integrity check: {e}")
        return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Get Google Sheet counts
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        tabs_config = [
            ('tham_my', ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']),
            ('nha_khoa', ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']),
            ('gioi_thieu', ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral'])
        ]
        
        for tab_type, variations in tabs_config:
            worksheet = syncer.find_worksheet(spreadsheet, variations)
            if worksheet:
                all_values = worksheet.get_all_values()
                sheet_count = len(all_values) - 1 if len(all_values) > 1 else 0
                result['tabs'][tab_type]['sheet_count'] = sheet_count
                result['tabs'][tab_type]['difference'] = sheet_count - result['tabs'][tab_type]['db_count']
                
                if result['tabs'][tab_type]['difference'] != 0:
                    result['discrepancies'].append({
                        'tab': tab_type,
                        'sheet_count': sheet_count,
                        'db_count': result['tabs'][tab_type]['db_count'],
                        'difference': result['tabs'][tab_type]['difference'],
                        'message': f"{tab_type}: Sheet has {sheet_count} rows, DB has {result['tabs'][tab_type]['db_count']} ({result['tabs'][tab_type]['difference']:+d})"
                    })
        
    except Exception as e:
        logger.error(f"Google Sheet error in integrity check: {e}")
        result['summary']['error'] = str(e)
    
    # Summary
    total_sheet = sum(t['sheet_count'] for t in result['tabs'].values())
    total_db = sum(t['db_count'] for t in result['tabs'].values())
    result['summary'] = {
        'total_sheet_rows': total_sheet,
        'total_db_rows': total_db,
        'total_difference': total_sheet - total_db,
        'has_discrepancies': len(result['discrepancies']) > 0
    }
    
    return jsonify({'status': 'success', 'result': result})


@admin_bp.route('/api/admin/sync/force-sync-tab', methods=['POST'])
@require_admin
def force_sync_tab():
    """
    Force sync a specific tab using phone matching (processes ALL rows).
    Body: { "tab": "tham_my" | "nha_khoa" | "gioi_thieu" }
    """
    data = request.get_json()
    tab_type = data.get('tab', '').strip() if data else ''
    
    if tab_type not in ['tham_my', 'nha_khoa', 'gioi_thieu']:
        return jsonify({'status': 'error', 'message': 'Invalid tab. Use: tham_my, nha_khoa, or gioi_thieu'}), 400
    
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        conn = syncer.get_db_connection()
        
        logger.info(f"Force sync started for tab: {tab_type}")
        
        # Use phone matching sync (processes ALL rows)
        processed, errors = syncer.sync_tab_by_phone_matching(spreadsheet, conn, tab_type)
        
        # Update heartbeat
        syncer.update_heartbeat(conn, processed)
        
        conn.close()
        
        logger.info(f"Force sync completed: {processed} processed, {errors} errors")
        
        return jsonify({
            'status': 'success',
            'message': f'Force sync completed for {tab_type}',
            'stats': {
                'processed': processed,
                'errors': errors
            }
        })
        
    except Exception as e:
        logger.error(f"Force sync error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/api/admin/sync/missing-phones', methods=['GET'])
@require_admin
def find_missing_phones():
    """
    Find phones that are in Google Sheet but not in database.
    Query params: tab - 'tham_my', 'nha_khoa', 'gioi_thieu' (optional, defaults to all)
    """
    tab_filter = request.args.get('tab', '').strip()
    limit = request.args.get('limit', 100, type=int)
    
    result = {
        'missing_phones': [],
        'checked_tabs': [],
        'total_missing': 0
    }
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Get all phone numbers from database
        cursor.execute("SELECT DISTINCT sdt FROM khach_hang WHERE sdt IS NOT NULL")
        db_phones = set(row[0] for row in cursor.fetchall())
        
        cursor.close()
        return_db_connection(connection)
        
    except Exception as e:
        return_db_connection(connection)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    try:
        syncer = GoogleSheetSync()
        client = syncer.get_google_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        tabs_config = [
            ('tham_my', ['Khach hang Tham my', 'Khách hàng Thẩm mỹ', 'Tham My', 'Thẩm mỹ']),
            ('nha_khoa', ['Khach hang Nha khoa', 'Khách hàng Nha khoa', 'Nha Khoa', 'Nha khoa']),
            ('gioi_thieu', ['Khach gioi thieu', 'Khách giới thiệu', 'Gioi Thieu', 'Referral'])
        ]
        
        if tab_filter:
            tabs_config = [(t, v) for t, v in tabs_config if t == tab_filter]
        
        for tab_type, variations in tabs_config:
            result['checked_tabs'].append(tab_type)
            
            worksheet = syncer.find_worksheet(spreadsheet, variations)
            if not worksheet:
                continue
            
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                continue
            
            headers = all_values[0]
            normalized_headers = [syncer.normalize_header(h) for h in headers]
            
            # Find phone column
            phone_col_idx = None
            for idx, h in enumerate(normalized_headers):
                if 'sdt' in h.lower() or 'dien thoai' in h.lower() or 'phone' in h.lower():
                    phone_col_idx = idx
                    break
            
            if phone_col_idx is None:
                continue
            
            # Find missing phones
            for row_idx, row in enumerate(all_values[1:], start=2):
                if len(result['missing_phones']) >= limit:
                    break
                    
                if phone_col_idx < len(row):
                    sheet_phone = syncer.clean_phone(row[phone_col_idx])
                    if sheet_phone and sheet_phone not in db_phones:
                        # Double check with suffix matching
                        phone_suffix = sheet_phone[-8:] if len(sheet_phone) >= 8 else sheet_phone
                        found = any(db_phone.endswith(phone_suffix) for db_phone in db_phones)
                        
                        if not found:
                            result['missing_phones'].append({
                                'phone': sheet_phone,
                                'tab': tab_type,
                                'row_number': row_idx,
                                'name': row[1] if len(row) > 1 else ''
                            })
        
        result['total_missing'] = len(result['missing_phones'])
        
    except Exception as e:
        logger.error(f"Error finding missing phones: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    return jsonify({'status': 'success', 'result': result})
