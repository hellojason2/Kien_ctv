/**
 * CTV Portal - Commissions Module
 * DOES: Loads and displays commission data
 * INPUTS: API responses from /api/ctv/my-commissions
 * OUTPUTS: Renders commission lists and summary tables
 * FLOW: loadRecentCommissions/loadAllCommissions -> Render to DOM
 */

// Earnings date filter state
let earningsDateFilter = {
    preset: 'month',
    fromDate: null,
    toDate: null
};

/**
 * Initialize earnings page
 */
function initEarnings() {
    // Set default to current month
    applyEarningsPreset('month');
    // Load lifetime stats (static, never changes)
    loadEarningsLifetimeStats();
    // Check which date ranges have data and show indicators
    checkDateRangesWithData('earnings');
}

/**
 * Check which date ranges have data and show red dot indicators
 */
async function checkDateRangesWithData(pageType = 'earnings') {
    try {
        // Wait a bit for the page to be fully rendered
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const result = await api('/api/ctv/date-ranges-with-data');
        
        if (result.status === 'success' && result.ranges_with_data) {
            const pageId = pageType === 'earnings' ? 'page-earnings' : 'page-dashboard';
            const page = document.getElementById(pageId);
            if (!page) return;
            
            // Update each button based on data availability
            Object.keys(result.ranges_with_data).forEach(preset => {
                const button = page.querySelector(`.btn-filter-preset[data-preset="${preset}"]`);
                if (button) {
                    if (result.ranges_with_data[preset]) {
                        button.classList.add('has-data');
                        // Update indicator element if it exists
                        const indicator = button.querySelector('.data-indicator');
                        if (indicator && typeof updateIndicatorElement === 'function') {
                            updateIndicatorElement(indicator);
                        }
                    } else {
                        button.classList.remove('has-data');
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error checking date ranges with data:', error);
    }
}

/**
 * Show loading state on earnings summary card
 */
function showEarningsSummaryLoading() {
    const summaryContainer = document.getElementById('earningsSummary');
    if (summaryContainer) {
        summaryContainer.innerHTML = `
            <div style="padding: 20px;">
                <div class="skeleton-loader" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="skeleton-loader" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="skeleton-loader" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="skeleton-loader" style="height: 20px;"></div>
            </div>
        `;
    }
}

/**
 * Hide loading state on earnings summary card
 */
function hideEarningsSummaryLoading() {
    // Loading is hidden when data is rendered
}

/**
 * Apply earnings date preset
 */
function applyEarningsPreset(preset) {
    const today = new Date();
    let fromDate, toDate;
    
    // Update active button (only in earnings page)
    const earningsPage = document.getElementById('page-earnings');
    if (earningsPage) {
        earningsPage.querySelectorAll('.btn-filter-preset').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.preset === preset) {
                btn.classList.add('active');
            }
        });
    }
    
    // Hide custom date filter if not custom
    if (preset !== 'custom') {
        const customFilter = document.getElementById('earningsCustomDateFilter');
        if (customFilter) customFilter.style.display = 'none';
    }
    
    switch(preset) {
        case 'today':
            fromDate = today;
            toDate = today;
            break;
        case '3days':
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - 3);
            toDate = today;
            break;
        case 'week':
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - today.getDay()); // Start of week (Sunday)
            toDate = today;
            break;
        case 'month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = today;
            break;
        case 'lastmonth':
            fromDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            toDate = new Date(today.getFullYear(), today.getMonth(), 0); // Last day of previous month
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
            return; // Don't load, wait for custom filter
        default:
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = today;
    }
    
    earningsDateFilter.preset = preset;
    earningsDateFilter.fromDate = formatDateForAPI(fromDate);
    earningsDateFilter.toDate = formatDateForAPI(toDate);
    
    // Update date inputs for reference
    const fromInput = document.getElementById('earningsFromDate');
    const toInput = document.getElementById('earningsToDate');
    if (fromInput) fromInput.value = earningsDateFilter.fromDate;
    if (toInput) toInput.value = earningsDateFilter.toDate;
    
    // Show loading animation
    showEarningsSummaryLoading();
    
    // Reload commissions with date filter
    loadAllCommissions(earningsDateFilter.fromDate, earningsDateFilter.toDate);
}

/**
 * Toggle custom date filter visibility
 */
function toggleEarningsCustomDateFilter() {
    const customFilter = document.getElementById('earningsCustomDateFilter');
    if (!customFilter) return;
    
    const isVisible = customFilter.style.display !== 'none';
    
    // Update active button
    const earningsPage = document.getElementById('page-earnings');
    if (earningsPage) {
        earningsPage.querySelectorAll('.btn-filter-preset').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.preset === 'custom') {
                btn.classList.add('active');
            }
        });
    }
    
    customFilter.style.display = isVisible ? 'none' : 'block';
}

/**
 * Apply custom date filter
 */
function applyEarningsCustomDateFilter() {
    const fromDate = document.getElementById('earningsFromDate')?.value;
    const toDate = document.getElementById('earningsToDate')?.value;
    
    if (!fromDate || !toDate) {
        alert(t('select_filter_hint') || 'Please select both from and to dates');
        return;
    }
    
    earningsDateFilter.preset = 'custom';
    earningsDateFilter.fromDate = fromDate;
    earningsDateFilter.toDate = toDate;
    
    // Show loading animation
    showEarningsSummaryLoading();
    
    loadAllCommissions(fromDate, toDate);
}

/**
 * Format date for API (YYYY-MM-DD)
 */
function formatDateForAPI(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Set default date filter for earnings page
 */
function setEarningsDefaultDateFilter() {
    applyEarningsPreset('month');
}

// Load Recent Commissions (Dashboard) with optional date filter
// Uses /api/ctv/customers endpoint to get recent services from khach_hang table
async function loadRecentCommissions(fromDate = null, toDate = null) {
    let url = '/api/ctv/customers';
    const params = new URLSearchParams();
    
    if (fromDate) params.append('from', fromDate);
    if (toDate) params.append('to', toDate);
    
    if (params.toString()) url += '?' + params.toString();
    
    const result = await api(url);
    if (result.status === 'success') {
        const container = document.getElementById('recentCommissions');
        
        // Filter to only completed services (Da den lam, Da coc)
        const completedServices = result.customers.filter(c =>
            c.trang_thai === 'Da den lam' || c.trang_thai === 'Da coc'
        );
        
        if (completedServices.length === 0) {
            container.innerHTML = `<div class="empty-state">${t('no_commissions')}</div>`;
            return;
        }
        
        // Get commission rate for Level 0 (self) - default 25%
        const selfRate = 0.25;
        
        container.innerHTML = completedServices.slice(0, 5).map(c => {
            const commission = c.tong_tien * selfRate;
            return `
            <div class="commission-item">
                <div class="left">
                    <div class="level-dot" style="background:#22c55e"></div>
                    <div>
                        <div class="info">${c.dich_vu || t('service')}</div>
                        <div class="date">${c.ngay_hen_lam || c.ngay_nhap_don || ''}</div>
                    </div>
                </div>
                <div class="amount">+${formatCurrency(commission)}</div>
                <div class="commission-tooltip">
                    <div class="tooltip-row">
                        <span class="tooltip-label">${t('customer')}:</span>
                        <span class="tooltip-value">${c.ten_khach || 'N/A'}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">${t('revenue')}:</span>
                        <span class="tooltip-value">${formatCurrency(c.tong_tien)}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">${t('rate')}:</span>
                        <span class="tooltip-value">25%</span>
                    </div>
                </div>
            </div>
        `}).join('');
    }
}

// Load Lifetime Statistics (all-time, never changes)
async function loadEarningsLifetimeStats() {
    const result = await api('/api/ctv/lifetime-stats');
    
    if (result.status === 'success') {
        const stats = result.stats;
        const container = document.getElementById('earningsLifetimeStats');
        
        if (!container) return;
        
        // Calculate Level 0 rate from the data (total_commissions / total_revenue * 100)
        // Or use default 25% if revenue is 0
        let level0Rate = 25.0;
        if (stats.total_revenue && stats.total_revenue > 0 && stats.total_commissions) {
            level0Rate = (stats.total_commissions / stats.total_revenue) * 100;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>${t('level')}</th>
                        <th>${t('revenue')}</th>
                        <th>${t('rate')}</th>
                        <th>${t('count')}</th>
                        <th>${t('total_commission')}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="level-badge level-0">Level 0</span></td>
                        <td>${formatCurrency(stats.total_revenue || 0)}</td>
                        <td>${level0Rate.toFixed(1)}%</td>
                        <td>${stats.total_transactions || 0}</td>
                        <td style="color:#22c55e;font-weight:600">${formatCurrency(stats.total_commissions || 0)}</td>
                    </tr>
                    <tr style="font-weight:700;background:#f8f9fa;">
                        <td>${t('all')}</td>
                        <td>${formatCurrency(stats.total_revenue || 0)}</td>
                        <td>${level0Rate.toFixed(1)}%</td>
                        <td>${stats.total_transactions || 0}</td>
                        <td style="color:#22c55e">${formatCurrency(stats.total_commissions || 0)}</td>
                    </tr>
                </tbody>
            </table>
        `;
    } else {
        const container = document.getElementById('earningsLifetimeStats');
        if (container) {
            container.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
    }
}

// Load All Commissions with date filtering - uses /api/ctv/commission endpoint
// which calculates commissions based on khach_hang table with ngay_hen_lam filter
async function loadAllCommissions(fromDate = null, toDate = null) {
    // Build URL with query params - use the commission endpoint that queries khach_hang
    let url = '/api/ctv/commission';
    const params = new URLSearchParams();

    // Support both old format (month/day) and new format (fromDate/toDate)
    // If fromDate/toDate are provided, use them; otherwise check for month/day in earningsDateFilter
    if (fromDate && toDate) {
        params.append('from', fromDate);
        params.append('to', toDate);
    } else if (earningsDateFilter.fromDate && earningsDateFilter.toDate) {
        params.append('from', earningsDateFilter.fromDate);
        params.append('to', earningsDateFilter.toDate);
    }

    if (params.toString()) url += '?' + params.toString();
    
    try {
        const result = await api(url);
        if (result.status === 'success') {
        const levelColors = ['#22c55e', '#3b82f6', '#d97706', '#ec4899', '#8b5cf6'];
        
        // Summary table
        const summaryContainer = document.getElementById('earningsSummary');
        if (!result.by_level || result.by_level.length === 0) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('no_commissions_period')}</div>`;
        } else {
            summaryContainer.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>${t('level')}</th>
                            <th>${t('revenue')}</th>
                            <th>${t('rate')}</th>
                            <th>${t('count')}</th>
                            <th>${t('total_commission')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.by_level.map(s => `
                            <tr>
                                <td><span class="level-badge level-${s.level}">Level ${s.level}</span></td>
                                <td>${formatCurrency(s.total_revenue)}</td>
                                <td>${s.rate.toFixed(1)}%</td>
                                <td>${s.transaction_count}</td>
                                <td style="color:#22c55e;font-weight:600">${formatCurrency(s.commission)}</td>
                            </tr>
                        `).join('')}
                        <tr style="font-weight:700;background:#f8f9fa;">
                            <td>${t('all')}</td>
                            <td></td>
                            <td></td>
                            <td>${result.total.transactions}</td>
                            <td style="color:#22c55e">${formatCurrency(result.total.commission)}</td>
                        </tr>
                    </tbody>
                </table>
            `;
        }
        // Hide loading animation
        hideEarningsSummaryLoading();
    } else {
        // Show error state
        const summaryContainer = document.getElementById('earningsSummary');
        if (summaryContainer) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
    }
    } catch (error) {
        console.error('Error loading commissions:', error);
        const summaryContainer = document.getElementById('earningsSummary');
        if (summaryContainer) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
    }
}


