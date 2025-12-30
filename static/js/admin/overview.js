/**
 * Admin Dashboard - Overview Page Module
 * Dashboard statistics and top earners
 * 
 * Created: December 30, 2025
 */

/**
 * Load dashboard statistics
 */
async function loadStats() {
    const result = await api('/api/admin/stats');
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
                    <div class="header-name" data-i18n="ctv_name">CTV</div>
                    <div class="header-revenue" data-i18n="total_revenue">Total Revenue</div>
                    <div class="header-commission" data-i18n="total_commission">Total Commission</div>
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
            topEarnersEl.innerHTML = '<div style="color:var(--text-secondary)">No earnings this month</div>';
        }
    }
}

