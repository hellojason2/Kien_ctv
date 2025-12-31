/**
 * Admin Dashboard - Commissions Module
 * Commission reports and exports
 * 
 * Created: December 30, 2025
 * Updated: December 30, 2025 - Added date range filters (quick filters and custom date range)
 */

let currentFilterType = null; // 'quick' or 'custom'
let currentFilterValue = null; // stores filter data

/**
 * Load commissions (grouped by CTV)
 */
async function loadCommissions() {
    let url = '/api/admin/commissions/summary?';
    const params = new URLSearchParams();
    
    if (currentFilterType === 'custom') {
        const dateFrom = document.getElementById('commissionDateFrom').value;
        const dateTo = document.getElementById('commissionDateTo').value;
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
    } else if (currentFilterType === 'quick' && currentFilterValue) {
        if (currentFilterValue.month) {
            params.append('month', currentFilterValue.month);
        } else if (currentFilterValue.date_from && currentFilterValue.date_to) {
            params.append('date_from', currentFilterValue.date_from);
            params.append('date_to', currentFilterValue.date_to);
        }
    }
    
    if (params.toString()) url += params.toString() + '&';
    
    const result = await api(url);
    if (result.status === 'success') {
        const tbody = document.getElementById('commissionsTableBody');
        
        // Update grand totals
        document.getElementById('totalCtvCount').textContent = result.total_ctv || 0;
        document.getElementById('grandTotalService').textContent = formatCurrency(result.grand_total?.total_service_price || 0);
        document.getElementById('grandTotalCommission').textContent = formatCurrency(result.grand_total?.total_commission || 0);
        
        if (result.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">${t('no_commissions')}</td></tr>`;
            return;
        }
        tbody.innerHTML = result.data.map(c => `
            <tr>
                <td style="font-weight:600; white-space:nowrap;">${c.ctv_code}</td>
                <td style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px;">${c.ctv_name || '-'}</td>
                <td style="white-space:nowrap;">${c.ctv_phone || '-'}</td>
                <td style="text-align:right; white-space:nowrap;">${formatCurrency(c.total_service_price)}</td>
                <td style="color:var(--accent-green); font-weight:600; text-align:right; white-space:nowrap;">${formatCurrency(c.total_commission)}</td>
            </tr>
        `).join('');
    }
}

/**
 * Get date range for quick filters
 */
function getDateRangeForFilter(filterType) {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    
    let dateFrom, dateTo;
    
    switch(filterType) {
        case 'day':
            dateFrom = new Date(today);
            dateFrom.setHours(0, 0, 0, 0);
            dateTo = today;
            break;
        case '3day':
            dateFrom = new Date(today);
            dateFrom.setDate(dateFrom.getDate() - 2);
            dateFrom.setHours(0, 0, 0, 0);
            dateTo = today;
            break;
        case 'week':
            dateFrom = new Date(today);
            const dayOfWeek = dateFrom.getDay();
            dateFrom.setDate(dateFrom.getDate() - dayOfWeek);
            dateFrom.setHours(0, 0, 0, 0);
            dateTo = today;
            break;
        case 'month':
            dateFrom = new Date(today.getFullYear(), today.getMonth(), 1);
            dateFrom.setHours(0, 0, 0, 0);
            dateTo = today;
            return { month: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}` };
        case '3month':
            dateFrom = new Date(today);
            dateFrom.setMonth(dateFrom.getMonth() - 2);
            dateFrom.setDate(1);
            dateFrom.setHours(0, 0, 0, 0);
            dateTo = today;
            break;
        case 'year':
            dateFrom = new Date(today.getFullYear(), 0, 1);
            dateFrom.setHours(0, 0, 0, 0);
            dateTo = today;
            break;
        default:
            return null;
    }
    
    return {
        date_from: dateFrom.toISOString().split('T')[0],
        date_to: dateTo.toISOString().split('T')[0]
    };
}

/**
 * Apply quick filter
 */
function applyQuickFilter(filterType) {
    currentFilterType = 'quick';
    currentFilterValue = getDateRangeForFilter(filterType);
    
    // Clear custom date inputs
    document.getElementById('commissionDateFrom').value = '';
    document.getElementById('commissionDateTo').value = '';
    
    // Update button states
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.quick-filter-btn[data-filter="${filterType}"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    loadCommissions();
}

/**
 * Apply custom date range
 */
function applyCustomDateRange() {
    const dateFrom = document.getElementById('commissionDateFrom').value;
    const dateTo = document.getElementById('commissionDateTo').value;
    
    if (!dateFrom || !dateTo) {
        alert(t('please_select_both_dates'));
        return;
    }
    
    if (new Date(dateFrom) > new Date(dateTo)) {
        alert(t('date_from_must_be_before_date_to'));
        return;
    }
    
    currentFilterType = 'custom';
    currentFilterValue = {
        date_from: dateFrom,
        date_to: dateTo
    };
    
    // Clear quick filter buttons
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    loadCommissions();
}

/**
 * Initialize commission filter handlers
 */
function initCommissionFilters() {
    // Quick filter buttons
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filterType = this.getAttribute('data-filter');
            applyQuickFilter(filterType);
        });
    });
    
    // Set default to current month on load
    applyQuickFilter('month');
}

/**
 * Export commissions to Excel
 */
function exportCommissionsExcel() {
    const params = new URLSearchParams();
    
    if (currentFilterType === 'custom') {
        const dateFrom = document.getElementById('commissionDateFrom').value;
        const dateTo = document.getElementById('commissionDateTo').value;
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
    } else if (currentFilterType === 'quick' && currentFilterValue) {
        if (currentFilterValue.month) {
            params.append('month', currentFilterValue.month);
        } else if (currentFilterValue.date_from && currentFilterValue.date_to) {
            params.append('date_from', currentFilterValue.date_from);
            params.append('date_to', currentFilterValue.date_to);
        }
    }
    
    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/commissions/summary/export?${params.toString()}&token=${token}`, '_blank');
}

