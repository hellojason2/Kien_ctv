/**
 * Admin Dashboard - Overview Page Module
 * Dashboard statistics and top earners
 * 
 * Created: December 30, 2025
 * Updated: December 30, 2025 - Added month and day filtering
 */

/**
 * Initialize overview page
 */
function initOverview() {
    // Set default month to current month
    const monthInput = document.getElementById('overviewMonthFilter');
    const dayInput = document.getElementById('overviewDayFilter');
    
    if (monthInput) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        monthInput.value = `${year}-${month}`;
    }
    
    // Auto-update month when day is selected
    if (dayInput) {
        dayInput.addEventListener('change', function() {
            if (this.value && monthInput) {
                const selectedDate = new Date(this.value);
                const year = selectedDate.getFullYear();
                const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
                monthInput.value = `${year}-${month}`;
            }
        });
    }
    
    // Load initial stats
    loadStats();
}

/**
 * Apply date filters and reload stats
 */
function applyOverviewFilters() {
    loadStats();
}

/**
 * Load dashboard statistics with optional month and day filters
 */
async function loadStats() {
    const monthInput = document.getElementById('overviewMonthFilter');
    const dayInput = document.getElementById('overviewDayFilter');
    
    // Build query parameters
    const params = new URLSearchParams();
    if (monthInput && monthInput.value) {
        params.append('month', monthInput.value);
    }
    if (dayInput && dayInput.value) {
        params.append('day', dayInput.value);
    }
    
    const url = '/api/admin/stats' + (params.toString() ? '?' + params.toString() : '');
    const result = await api(url);
    
    if (result.status === 'success') {
        const s = result.stats;
        document.getElementById('statTotalCTV').textContent = s.total_ctv;
        document.getElementById('statMonthlyCommission').textContent = formatCurrency(s.monthly_commission);
        document.getElementById('statMonthlyTx').textContent = s.monthly_transactions;
        document.getElementById('statMonthlyRevenue').textContent = formatCurrency(s.monthly_revenue);
        
        // Top earners with revenue and commission columns
        const topEarnersEl = document.getElementById('topEarners');
        if (s.top_earners.length > 0) {
            topEarnersEl.innerHTML = `
                <div class="earner-header">
                    <div class="header-name" data-i18n="ctv_name">${t('ctv_name')}</div>
                    <div class="header-revenue" data-i18n="total_revenue">${t('total_revenue')}</div>
                    <div class="header-commission" data-i18n="total_commission">${t('total_commission')}</div>
                </div>
                ${s.top_earners.map(e => `
                <div class="earner-row">
                    <div class="earner-info">
                        <div class="name">${e.ten}</div>
                        <div class="code">${e.ctv_code}</div>
                    </div>
                    <div class="revenue">${formatCurrency(e.total_revenue)}</div>
                    <div class="commission">${formatCurrency(e.total_commission)}</div>
                </div>
                `).join('')}
            `;
            // Apply translations to dynamically added elements
            if (typeof applyTranslations === 'function') {
                applyTranslations();
            }
        } else {
            topEarnersEl.innerHTML = `<div style="color:var(--text-secondary)">${t('no_earnings')}</div>`;
        }
    }
}

