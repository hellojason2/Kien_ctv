/**
 * CTV Portal - Commissions Module
 * DOES: Loads and displays commission data
 * INPUTS: API responses from /api/ctv/my-commissions
 * OUTPUTS: Renders commission lists and summary tables
 * FLOW: loadRecentCommissions/loadAllCommissions -> Render to DOM
 */

// Load Recent Commissions (Dashboard)
async function loadRecentCommissions() {
    const result = await api('/api/ctv/my-commissions');
    if (result.status === 'success') {
        const container = document.getElementById('recentCommissions');
        if (result.commissions.length === 0) {
            container.innerHTML = `<div class="empty-state">${t('no_commissions')}</div>`;
            return;
        }
        
        const levelColors = ['#22c55e', '#3b82f6', '#d97706', '#ec4899', '#8b5cf6'];
        
        container.innerHTML = result.commissions.slice(0, 5).map(c => `
            <div class="commission-item">
                <div class="left">
                    <div class="level-dot" style="background:${levelColors[c.level]}"></div>
                    <div>
                        <div class="info">Level ${c.level} - ${(c.commission_rate * 100).toFixed(2)}%</div>
                        <div class="date">${c.created_at}</div>
                    </div>
                </div>
                <div class="amount">+${formatCurrency(c.commission_amount)}</div>
                <div class="commission-tooltip">
                    <div class="tooltip-row">
                        <span class="tooltip-label">${t('from_ctv')}:</span>
                        <span class="tooltip-value">${c.source_ctv_name || 'N/A'}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">${t('customer')}:</span>
                        <span class="tooltip-value">${c.customer_name || 'N/A'}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">${t('service')}:</span>
                        <span class="tooltip-value">${c.service_name || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// Load All Commissions with date filtering
async function loadAllCommissions(fromDate = null, toDate = null) {
    // Build URL with query params
    let url = '/api/ctv/my-commissions';
    const params = new URLSearchParams();
    
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    
    if (params.toString()) url += '?' + params.toString();
    
    const result = await api(url);
    if (result.status === 'success') {
        const levelColors = ['#22c55e', '#3b82f6', '#d97706', '#ec4899', '#8b5cf6'];
        
        // Summary table
        const summaryContainer = document.getElementById('earningsSummary');
        if (result.summary.by_level.length === 0) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('no_commissions_period')}</div>`;
        } else {
            summaryContainer.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>${t('level')}</th>
                            <th>${t('count')}</th>
                            <th>${t('total_commission')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.summary.by_level.map(s => `
                            <tr>
                                <td><span class="level-badge level-${s.level}">Level ${s.level}</span></td>
                                <td>${s.count}</td>
                                <td style="color:#22c55e;font-weight:600">${formatCurrency(s.total)}</td>
                            </tr>
                        `).join('')}
                        <tr style="font-weight:700">
                            <td>${t('all')}</td>
                            <td></td>
                            <td style="color:#22c55e">${formatCurrency(result.summary.total)}</td>
                        </tr>
                    </tbody>
                </table>
            `;
        }
    }
}

// Apply time filter preset
function applyTimeFilter() {
    const timeFilter = document.getElementById('earningsTimeFilter').value;
    const today = new Date();
    let fromDate, toDate;
    
    switch(timeFilter) {
        case 'day':
            fromDate = today;
            toDate = today;
            break;
        case 'month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = today;
            break;
        case '3months':
            fromDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
            toDate = today;
            break;
        case 'year':
            fromDate = new Date(today.getFullYear(), 0, 1);
            toDate = today;
            break;
        case 'custom':
        default:
            // Keep current date inputs, don't change them
            return;
    }
    
    // Update date inputs
    document.getElementById('earningsFromDate').value = fromDate.toISOString().split('T')[0];
    document.getElementById('earningsToDate').value = toDate.toISOString().split('T')[0];
    
    // Auto-filter after applying time preset
    filterCommissions();
}

// Filter commissions by date
function filterCommissions() {
    const fromDate = document.getElementById('earningsFromDate').value;
    const toDate = document.getElementById('earningsToDate').value;
    loadAllCommissions(fromDate, toDate);
}

// Set default earnings date filter (start of current month to today)
function setEarningsDefaultDateFilter() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    const fromDate = document.getElementById('earningsFromDate');
    const toDate = document.getElementById('earningsToDate');
    const timeFilter = document.getElementById('earningsTimeFilter');
    
    if (fromDate) {
        fromDate.value = firstDayOfMonth.toISOString().split('T')[0];
    }
    if (toDate) {
        toDate.value = today.toISOString().split('T')[0];
    }
    if (timeFilter) {
        timeFilter.value = 'month';
    }
}

