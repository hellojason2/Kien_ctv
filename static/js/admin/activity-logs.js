/**
 * Admin Dashboard - Activity Logs Module
 * Activity logs, grouped view, stats, exports
 * 
 * Created: December 30, 2025
 */

// State
let activityLogsCurrentPage = 1;
let activityLogsTotalPages = 1;
let isGroupedView = true;
let suspiciousIPsData = {};
let expandedGroups = new Set();

/**
 * Toggle between grouped and flat view
 */
function toggleGroupedView() {
    isGroupedView = document.getElementById('groupedViewToggle').checked;
    const groupedContainer = document.getElementById('groupedLogsContainer');
    const tableView = document.getElementById('activityLogsTable');

    if (isGroupedView) {
        groupedContainer.style.display = 'block';
        tableView.style.display = 'none';
    } else {
        groupedContainer.style.display = 'none';
        tableView.style.display = 'table';
    }

    loadActivityLogs(1);
}

/**
 * Load activity logs
 * @param {number} page - Page number
 */
async function loadActivityLogs(page = 1) {
    activityLogsCurrentPage = page;
    try {
        if (isGroupedView) {
            await loadGroupedLogs(page);
        } else {
            await loadFlatLogs(page);
        }
    } catch (e) {
        console.error("Error loading activity logs:", e);
        const groupedBody = document.getElementById('groupedLogsBody');
        const tbody = document.getElementById('activityLogsBody');
        const msg = (typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs') + ': ' + e.message;
        if (groupedBody) groupedBody.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--accent-red);">${msg}</div>`;
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="color: var(--accent-red); text-align: center; padding: 20px;">${msg}</td></tr>`;
    }
}

/**
 * Load grouped logs
 * @param {number} page - Page number
 */
async function loadGroupedLogs(page = 1) {
    const groupedBody = document.getElementById('groupedLogsBody');
    if (!groupedBody) return;

    groupedBody.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">' + (typeof t === 'function' ? t('loading') : 'Loading...') + '</div>';

    const eventType = document.getElementById('logEventType')?.value;
    const userType = document.getElementById('logUserType')?.value;
    const dateFrom = document.getElementById('logDateFrom')?.value;
    const dateTo = document.getElementById('logDateTo')?.value;
    const search = document.getElementById('logSearch')?.value;

    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', 50);
    if (eventType) params.append('event_type', eventType);
    if (userType) params.append('user_type', userType);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (search) params.append('search', search);

    let result;
    try {
        result = await api(`/api/admin/activity-logs/grouped?${params}`);
    } catch (e) {
        console.error("API error loading grouped logs:", e);
        groupedBody.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--accent-red);">${(typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs')}: ${e.message}</div>`;
        return;
    }

    if (result && result.status === 'success') {
        const groups = result.groups || [];
        suspiciousIPsData = result.suspicious_ips || {};
        activityLogsTotalPages = (result.pagination && result.pagination.total_pages) || 1;

        const total = (result.pagination && result.pagination.total) || 0;
        const msg = (typeof t === 'function' ? t('showing') : 'Showing') + ` ${groups.length} ` +
            (typeof t === 'function' ? t('groups') : 'groups') + ` ${typeof t === 'function' ? t('of') : 'of'} ${total}`;

        const logsCountEl = document.getElementById('logsCount');
        if (logsCountEl) logsCountEl.textContent = msg;

        // Show suspicious IPs alert
        displaySuspiciousIPs(suspiciousIPsData);

        if (groups.length === 0) {
            groupedBody.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">' + (typeof t === 'function' ? t('no_logs_found') : 'No logs found') + '</div>';
        } else {
            groupedBody.innerHTML = groups.map((group, idx) => {
                // Create a safe ID avoiding special characters
                const safeIp = (group.ip_address || 'unknown').replace(/[^a-zA-Z0-9]/g, '-');
                const safeUser = (group.user_id || 'unknown').replace(/[^a-zA-Z0-9]/g, '-');
                const groupId = `group-${safeUser}-${safeIp}`;

                // Safe lookup for suspicious IPs
                const isSuspicious = suspiciousIPsData &&
                    group.ip_address &&
                    suspiciousIPsData[group.ip_address] &&
                    suspiciousIPsData[group.ip_address].length > 1;

                const isExpanded = expandedGroups.has(groupId);

                // Escape values for onclick attribute using HTML entities
                const escUserId = (group.user_id || '').replace(/'/g, "&#39;").replace(/"/g, "&quot;");
                const escIpAddr = (group.ip_address || '').replace(/'/g, "&#39;").replace(/"/g, "&quot;");

                return `
                <div class="log-group" style="border-bottom: 1px solid var(--border-color);">
                    <div class="log-group-header" 
                         onclick="toggleLogGroup('${groupId}', '${escUserId}', '${escIpAddr}')" 
                         style="padding: 14px 16px; cursor: pointer; display: flex; align-items: center; gap: 12px; transition: background 0.2s; ${isSuspicious ? 'background: rgba(239, 68, 68, 0.05);' : ''}"
                         onmouseover="this.style.background='var(--bg-tertiary)'" 
                         onmouseout="this.style.background='${isSuspicious ? 'rgba(239, 68, 68, 0.05)' : ''}'">
                        
                        <svg id="${groupId}-chevron" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" 
                             style="transition: transform 0.2s; transform: rotate(${isExpanded ? '90deg' : '0deg'}); flex-shrink: 0; color: var(--text-secondary);">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        
                        <div style="display: flex; align-items: center; gap: 10px; flex: 1; flex-wrap: wrap;">
                            <span style="color: ${group.user_type === 'admin' ? 'var(--accent-purple)' : 'var(--accent-cyan)'}; font-weight: 600; font-size: 13px;">
                                ${group.user_type ? group.user_type.toUpperCase() : '-'}
                            </span>
                            <span style="font-weight: 500; color: var(--text-primary);">${group.user_id || '-'}</span>
                            <span style="font-family: monospace; font-size: 12px; color: var(--text-secondary); padding: 2px 8px; background: var(--bg-tertiary); border-radius: 4px;">
                                ${group.ip_address || '-'}
                            </span>
                            ${isSuspicious ? `
                                <span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border-radius: 4px; font-size: 11px; font-weight: 600;">
                                    <svg width="12" height="12" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                                    ${typeof t === 'function' ? t('multi_account_ip') : 'Multi-Account IP'}
                                </span>
                            ` : ''}
                        </div>
                        
                        <div style="display: flex; align-items: center; gap: 16px; flex-shrink: 0;">
                            <span style="font-size: 12px; color: var(--text-secondary);">
                                ${group.log_count} ${typeof t === 'function' ? t('activities') : 'activities'}
                            </span>
                            <span style="font-size: 11px; color: var(--text-muted);">
                                ${group.last_activity || '-'}
                            </span>
                        </div>
                    </div>
                    
                    <div id="${groupId}-content" class="log-group-content" style="display: ${isExpanded ? 'block' : 'none'}; background: var(--bg-secondary); border-top: 1px solid var(--border-color);">
                        <div id="${groupId}-logs" style="padding: 0;">
                            <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">
                                ${typeof t === 'function' ? t('click_to_load') : 'Click to load'}
                            </div>
                        </div>
                    </div>
                </div>
                `;
            }).join('');
        }

        if (result.pagination) updateLogsPagination(result.pagination);
    } else {
        const errorMsg = (result && result.message) || (typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs');
        groupedBody.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--accent-red);">${errorMsg}</div>`;
    }
}

/**
 * Display suspicious IPs alert
 * @param {object} suspiciousIPs - Suspicious IPs data
 */
function displaySuspiciousIPs(suspiciousIPs) {
    const alertDiv = document.getElementById('suspiciousIPsAlert');
    const alertBody = document.getElementById('suspiciousIPsBody');

    const ipCount = Object.keys(suspiciousIPs).length;

    if (ipCount === 0) {
        if (alertDiv) alertDiv.style.display = 'none';
        return;
    }

    if (alertDiv) alertDiv.style.display = 'block';

    if (alertBody) {
        alertBody.innerHTML = Object.entries(suspiciousIPs).map(([ip, users]) => `
            <div style="padding: 8px 12px; background: rgba(239, 68, 68, 0.08); border-radius: 6px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="font-family: monospace; font-weight: 600; color: var(--accent-red);">${ip}</span>
                    <span style="font-size: 11px; color: var(--text-secondary);">${users.length} ${typeof t === 'function' ? t('accounts') : 'accounts'}</span>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    ${users.map(u => `
                        <span style="padding: 2px 8px; border-radius: 4px; font-size: 11px; background: ${u.user_type === 'admin' ? 'rgba(139, 92, 246, 0.15)' : 'rgba(6, 182, 212, 0.15)'}; color: ${u.user_type === 'admin' ? 'var(--accent-purple)' : 'var(--accent-cyan)'};">
                            ${u.user_type ? u.user_type.toUpperCase() : '-'}: ${u.user_id}
                        </span>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }
}

/**
 * Close suspicious IPs alert
 */
function closeSuspiciousIPsAlert() {
    const alertDiv = document.getElementById('suspiciousIPsAlert');
    if (alertDiv) {
        alertDiv.style.display = 'none';
    }
}

/**
 * Toggle log group expansion
 * @param {string} groupId - Group ID
 * @param {string} userId - User ID
 * @param {string} ip - IP Address
 */
async function toggleLogGroup(groupId, userId, ip) {
    const content = document.getElementById(`${groupId}-content`);
    const chevron = document.getElementById(`${groupId}-chevron`);
    const logsDiv = document.getElementById(`${groupId}-logs`);

    if (!content || !chevron || !logsDiv) return;

    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(90deg)';
        expandedGroups.add(groupId);

        // Load detailed logs for this group
        // Parameters are passed directly from the onclick handler

        logsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">' + (typeof t === 'function' ? t('loading') : 'Loading...') + '</div>';

        const params = new URLSearchParams();
        if (userId && userId !== 'unknown') params.append('user_id', userId);
        if (ip && ip !== 'unknown') params.append('ip_address', ip);
        params.append('per_page', 20);

        let result;
        try {
            result = await api(`/api/admin/activity-logs/details?${params}`);
        } catch (e) {
            console.error("API error loading log details:", e);
            logsDiv.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--accent-red); font-size: 13px;">${(typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs')}: ${e.message}</div>`;
            return;
        }

        if (result && result.status === 'success' && result.logs && result.logs.length > 0) {
            logsDiv.innerHTML = `
                <table class="data-table" style="width: 100%; margin: 0;">
                    <thead>
                        <tr>
                            <th style="padding: 10px 12px; font-size: 11px;">${typeof t === 'function' ? t('timestamp') : 'Timestamp'}</th>
                            <th style="padding: 10px 12px; font-size: 11px;">${typeof t === 'function' ? t('event') : 'Event'}</th>
                            <th style="padding: 10px 12px; font-size: 11px;">${typeof t === 'function' ? t('endpoint') : 'Endpoint'}</th>
                            <th style="padding: 10px 12px; font-size: 11px;">${typeof t === 'function' ? t('status') : 'Status'}</th>
                            <th style="padding: 10px 12px; font-size: 11px;">${typeof t === 'function' ? t('details') : 'Details'}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.logs.map(log => `
                            <tr>
                                <td style="padding: 8px 12px; font-size: 11px; white-space: nowrap;">${log.timestamp || '-'}</td>
                                <td style="padding: 8px 12px;">${getEventBadge(log.event_type)}</td>
                                <td style="padding: 8px 12px; font-size: 11px; max-width: 180px; overflow: hidden; text-overflow: ellipsis;" title="${log.endpoint || ''}">${log.endpoint || '-'}</td>
                                <td style="padding: 8px 12px;">${getStatusBadge(log.status_code)}</td>
                                <td style="padding: 8px 12px; font-size: 11px; max-width: 150px; overflow: hidden; text-overflow: ellipsis;" title="${(JSON.stringify(log.details || {})).replace(/"/g, '&quot;')}">${formatDetails(log.details)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                ${(result.pagination && result.pagination.total > 20) ? `
                    <div style="padding: 10px 16px; text-align: center; font-size: 12px; color: var(--text-secondary); background: var(--bg-tertiary);">
                        ${typeof t === 'function' ? t('showing') : 'Showing'} 20 ${typeof t === 'function' ? t('of') : 'of'} ${result.pagination.total} ${typeof t === 'function' ? t('logs') : 'logs'}
                    </div>
                ` : ''}
            `;
        } else {
            logsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">' + (typeof t === 'function' ? t('no_logs_found') : 'No logs found') + '</div>';
        }
    } else {
        const errorMsg = (result && result.message) || (typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs');
        logsDiv.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--accent-red); font-size: 13px;">${errorMsg}</div>`;
    }
}

/**
 * Load flat logs (non-grouped)
 * @param {number} page - Page number
 */
async function loadFlatLogs(page = 1) {
    const tbody = document.getElementById('activityLogsBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="7" class="loading">' + (typeof t === 'function' ? t('loading') : 'Loading...') + '</td></tr>';

    const eventType = document.getElementById('logEventType')?.value;
    const userType = document.getElementById('logUserType')?.value;
    const dateFrom = document.getElementById('logDateFrom')?.value;
    const dateTo = document.getElementById('logDateTo')?.value;
    const search = document.getElementById('logSearch')?.value;

    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', 50);
    if (eventType) params.append('event_type', eventType);
    if (userType) params.append('user_type', userType);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (search) params.append('search', search);

    let result;
    try {
        result = await api(`/api/admin/activity-logs?${params}`);
    } catch (e) {
        console.error("API error loading flat logs:", e);
        tbody.innerHTML = `<tr><td colspan="7" style="color: var(--accent-red); text-align: center; padding: 20px;">${(typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs')}: ${e.message}</td></tr>`;
        return;
    }

    if (result && result.status === 'success') {
        const logs = result.logs || [];
        activityLogsTotalPages = (result.pagination && result.pagination.total_pages) || 1;

        const total = (result.pagination && result.pagination.total) || 0;
        const msg = (typeof t === 'function' ? t('showing') : 'Showing') + ` ${logs.length} ` +
            (typeof t === 'function' ? t('of') : 'of') + ` ${total} ` + (typeof t === 'function' ? t('logs') : 'logs');

        const logsCountEl = document.getElementById('logsCount');
        if (logsCountEl) logsCountEl.textContent = msg;

        // Hide suspicious IPs alert in flat view
        const suspAlert = document.getElementById('suspiciousIPsAlert');
        if (suspAlert) suspAlert.style.display = 'none';

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-secondary);">' + (typeof t === 'function' ? t('no_logs_found') : 'No logs found') + '</td></tr>';
        } else {
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td style="white-space: nowrap; font-size: 12px;">${log.timestamp || '-'}</td>
                    <td>${getEventBadge(log.event_type)}</td>
                    <td>
                        <span style="color: ${log.user_type === 'admin' ? 'var(--accent-purple)' : 'var(--accent-cyan)'}; font-weight: 500;">
                            ${log.user_type ? log.user_type.toUpperCase() : '-'}
                        </span>
                        <br>
                        <span style="font-size: 12px; color: var(--text-secondary);">${log.user_id || '-'}</span>
                    </td>
                    <td style="font-family: monospace; font-size: 12px;">${log.ip_address || '-'}</td>
                    <td style="font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${log.endpoint || ''}">${log.endpoint || '-'}</td>
                    <td>${getStatusBadge(log.status_code)}</td>
                    <td style="font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${(JSON.stringify(log.details || {})).replace(/"/g, '&quot;')}">
                        ${formatDetails(log.details)}
                    </td>
                </tr>
            `).join('');
        }

        if (result.pagination) updateLogsPagination(result.pagination);
    } else {
        const errorMsg = (result && result.message) || (typeof t === 'function' ? t('error_loading_logs') : 'Error loading logs');
        tbody.innerHTML = `<tr><td colspan="7" style="color: var(--accent-red); text-align: center;">${errorMsg}</td></tr>`;
    }
}

/**
 * Get event badge HTML
 * @param {string} eventType - Event type
 * @returns {string} - Badge HTML
 */
function getEventBadge(eventType) {
    const badges = {
        'login_success': { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', label: 'Login' },
        'login_failed': { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', label: 'Failed Login' },
        'logout': { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', label: 'Logout' },
        'api_call': { color: '#6b7280', bg: 'rgba(107, 114, 128, 0.15)', label: 'API' },
        'ctv_created': { color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', label: 'CTV+' },
        'ctv_updated': { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', label: 'CTV~' },
        'ctv_deleted': { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', label: 'CTV-' },
        'commission_adjusted': { color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)', label: 'Comm$' },
        'data_export': { color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)', label: 'Export' },
        'settings_changed': { color: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', label: 'Settings' }
    };

    const badge = badges[eventType] || { color: '#6b7280', bg: 'rgba(107, 114, 128, 0.15)', label: eventType };
    return `<span style="display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: ${badge.bg}; color: ${badge.color};">${badge.label}</span>`;
}

/**
 * Get status badge HTML
 * @param {number} statusCode - HTTP status code
 * @returns {string} - Badge HTML
 */
function getStatusBadge(statusCode) {
    if (!statusCode) return '-';

    let color = 'var(--text-secondary)';
    if (statusCode >= 200 && statusCode < 300) color = 'var(--accent-green)';
    else if (statusCode >= 400 && statusCode < 500) color = 'var(--accent-orange)';
    else if (statusCode >= 500) color = 'var(--accent-red)';

    return `<span style="font-family: monospace; color: ${color};">${statusCode}</span>`;
}

/**
 * Format log details
 * @param {object} details - Details object
 * @returns {string} - Formatted string
 */
function formatDetails(details) {
    if (!details) return '-';
    if (typeof details === 'string') {
        try {
            details = JSON.parse(details);
        } catch {
            return details;
        }
    }

    if (details.action) return details.action;
    if (details.duration_ms) return `${details.duration_ms}ms`;

    const keys = Object.keys(details);
    if (keys.length === 0) return '-';
    return keys.slice(0, 2).map(k => `${k}: ${details[k]}`).join(', ');
}

/**
 * Update logs pagination controls
 * @param {object} pagination - Pagination object
 */
function updateLogsPagination(pagination) {
    const info = document.getElementById('paginationInfo');
    const controls = document.getElementById('paginationControls');

    const start = (pagination.page - 1) * pagination.per_page + 1;
    const end = Math.min(pagination.page * pagination.per_page, pagination.total);
    info.textContent = `${start}-${end} ${t('of')} ${pagination.total}`;

    let html = '';

    // Previous button
    html += `<button class="btn btn-secondary" ${pagination.page <= 1 ? 'disabled' : ''} onclick="loadActivityLogs(${pagination.page - 1})" style="padding: 8px 12px; font-size: 12px;">Prev</button>`;

    // Page numbers
    const totalPages = pagination.total_pages || 1;
    const currentPage = pagination.page;

    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        html += `<button class="btn btn-secondary" onclick="loadActivityLogs(1)" style="padding: 8px 12px; font-size: 12px;">1</button>`;
        if (startPage > 2) html += `<span style="color: var(--text-secondary); padding: 0 8px;">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        const isActive = i === currentPage;
        html += `<button class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}" onclick="loadActivityLogs(${i})" style="padding: 8px 12px; font-size: 12px;">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span style="color: var(--text-secondary); padding: 0 8px;">...</span>`;
        html += `<button class="btn btn-secondary" onclick="loadActivityLogs(${totalPages})" style="padding: 8px 12px; font-size: 12px;">${totalPages}</button>`;
    }

    // Next button
    html += `<button class="btn btn-secondary" ${pagination.page >= totalPages ? 'disabled' : ''} onclick="loadActivityLogs(${pagination.page + 1})" style="padding: 8px 12px; font-size: 12px;">Next</button>`;

    controls.innerHTML = html;
}

/**
 * Load activity stats
 */
async function loadActivityStats() {
    const result = await api('/api/admin/activity-logs/stats');

    if (result.status === 'success') {
        const stats = result.stats;
        document.getElementById('statLoginsToday').textContent = stats.logins_today || 0;
        document.getElementById('statFailedLogins').textContent = stats.failed_logins_today || 0;
        document.getElementById('statUniqueIPs').textContent = stats.unique_ips_today || 0;
        document.getElementById('statTotalLogs').textContent = formatNumber(stats.total_logs || 0);
    }
}

/**
 * Refresh activity logs
 */
function refreshActivityLogs() {
    loadActivityLogs(activityLogsCurrentPage);
    loadActivityStats();
}

/**
 * Export activity logs
 */
async function exportActivityLogs() {
    const eventType = document.getElementById('logEventType').value;
    const userType = document.getElementById('logUserType').value;
    const dateFrom = document.getElementById('logDateFrom').value;
    const dateTo = document.getElementById('logDateTo').value;
    const search = document.getElementById('logSearch').value;

    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (userType) params.append('user_type', userType);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (search) params.append('search', search);

    // Open export URL in new window for download
    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/activity-logs/export?${params}&token=${token}`, '_blank');
}

/**
 * Export activity logs to Excel
 */
function exportActivityLogsExcel() {
    const eventType = document.getElementById('logEventType').value;
    const userType = document.getElementById('logUserType').value;
    const dateFrom = document.getElementById('logDateFrom').value;
    const dateTo = document.getElementById('logDateTo').value;
    const search = document.getElementById('logSearch').value;

    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (userType) params.append('user_type', userType);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (search) params.append('search', search);

    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/activity-logs/export-xlsx?${params}&token=${token}`, '_blank');
}

