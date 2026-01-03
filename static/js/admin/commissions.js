/**
 * Admin Dashboard - Commissions Module
 * Commission reports and exports
 * 
 * Created: December 30, 2025
 * Updated: December 30, 2025 - Added date range filters (quick filters and custom date range)
 */

let currentFilterType = null; // 'quick' or 'custom'
let currentFilterValue = null; // stores filter data
let currentFilterName = null; // stores the filter name (day, week, month, etc.)

/**
 * Show loading state with skeleton loaders
 */
function showCommissionsLoading() {
    const tbody = document.getElementById('commissionsTableBody');
    const grandTotalEl = document.getElementById('commissionGrandTotal');
    
    // Show skeleton loaders in table
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td><div class="skeleton-loader small"></div></td>
                <td><div class="skeleton-loader medium"></div></td>
                <td><div class="skeleton-loader small"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
            </tr>
            <tr>
                <td><div class="skeleton-loader small"></div></td>
                <td><div class="skeleton-loader medium"></div></td>
                <td><div class="skeleton-loader small"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
            </tr>
            <tr>
                <td><div class="skeleton-loader small"></div></td>
                <td><div class="skeleton-loader medium"></div></td>
                <td><div class="skeleton-loader small"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
            </tr>
            <tr>
                <td><div class="skeleton-loader small"></div></td>
                <td><div class="skeleton-loader medium"></div></td>
                <td><div class="skeleton-loader small"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
            </tr>
            <tr>
                <td><div class="skeleton-loader small"></div></td>
                <td><div class="skeleton-loader medium"></div></td>
                <td><div class="skeleton-loader small"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
                <td style="text-align:right;"><div class="skeleton-loader medium" style="margin-left:auto;"></div></td>
            </tr>
        `;
    }
    
    // Show skeleton loaders in summary cards
    if (grandTotalEl) {
        const totalCtvEl = document.getElementById('totalCtvCount');
        const grandTotalServiceEl = document.getElementById('grandTotalService');
        const grandTotalCommissionEl = document.getElementById('grandTotalCommission');
        const grandTotalServiceCountEl = document.getElementById('grandTotalServiceCount');
        
        if (totalCtvEl) {
            totalCtvEl.innerHTML = '<div class="skeleton-loader medium"></div>';
        }
        if (grandTotalServiceEl) {
            grandTotalServiceEl.innerHTML = '<div class="skeleton-loader medium"></div>';
        }
        if (grandTotalCommissionEl) {
            grandTotalCommissionEl.innerHTML = '<div class="skeleton-loader medium"></div>';
        }
        if (grandTotalServiceCountEl) {
            grandTotalServiceCountEl.style.display = 'none';
        }
    }
}

/**
 * Load commissions (grouped by CTV)
 */
async function loadCommissions() {
    const tbody = document.getElementById('commissionsTableBody');
    if (!tbody) {
        console.error('Commissions table body not found');
        return;
    }
    
    // Show loading state with skeleton loaders
    showCommissionsLoading();
    
    const params = new URLSearchParams();
    
    if (currentFilterType === 'custom') {
        const dateFrom = document.getElementById('commissionDateFrom')?.value;
        const dateTo = document.getElementById('commissionDateTo')?.value;
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
    
    let url = '/api/admin/commissions/summary';
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    try {
        const result = await api(url);
        
        if (result.status === 'error') {
            console.error('Commission API Error:', result.message);
            const errorMsg = result.message || 'Unknown error';
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--error-color, #ef4444)">Error: ${errorMsg}</td></tr>`;
            return;
        }
        
        if (result.status === 'success') {
            // Update grand totals
            const totalCtvEl = document.getElementById('totalCtvCount');
            const grandTotalServiceEl = document.getElementById('grandTotalService');
            const grandTotalCommissionEl = document.getElementById('grandTotalCommission');
            const grandTotalServiceCountEl = document.getElementById('grandTotalServiceCount');
            const serviceCountBadgeEl = document.getElementById('serviceCountBadge');
            
            // Re-enable buttons after loading completes
            document.querySelectorAll('.quick-filter-btn').forEach(btn => {
                btn.disabled = false;
            });
            const applyBtn = document.querySelector('.custom-date-range .btn-primary');
            if (applyBtn) applyBtn.disabled = false;
            
            if (totalCtvEl) totalCtvEl.textContent = result.total_ctv || 0;
            if (grandTotalServiceEl) grandTotalServiceEl.textContent = formatCurrency(result.grand_total?.total_service_price || 0);
            if (grandTotalCommissionEl) grandTotalCommissionEl.textContent = formatCurrency(result.grand_total?.total_commission || 0);
            
            // Show service count badge if there are services
            const totalServiceCount = result.grand_total?.total_service_count || 0;
            if (totalServiceCount > 0 && grandTotalServiceCountEl && serviceCountBadgeEl) {
                grandTotalServiceCountEl.style.display = 'block';
                serviceCountBadgeEl.textContent = `${totalServiceCount} dịch vụ`;
                if (result.grand_total?.total_commission === 0) {
                    serviceCountBadgeEl.style.background = 'var(--accent-orange, #f97316)';
                    serviceCountBadgeEl.textContent = `${totalServiceCount} dịch vụ, 0 hoa hồng`;
                } else {
                    serviceCountBadgeEl.style.background = 'var(--accent-blue, #3b82f6)';
                }
            } else if (grandTotalServiceCountEl) {
                grandTotalServiceCountEl.style.display = 'none';
            }
            
            if (!result.data || result.data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">${t('no_commissions') || 'No commissions found'}</td></tr>`;
                return;
            }
            tbody.innerHTML = result.data.map(c => {
                const serviceCount = c.service_count || 0;
                const hasServicesNoCommission = c.has_services_no_commission || false;
                const serviceBadge = serviceCount > 0 ? 
                    `<span style="display:inline-block; background:${hasServicesNoCommission ? 'var(--accent-orange, #f97316)' : 'var(--accent-blue, #3b82f6)'}; color:white; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:6px;">${serviceCount} dịch vụ${hasServicesNoCommission ? ', 0 HH' : ''}</span>` : '';
                
                return `
                <tr>
                    <td style="font-weight:600; white-space:nowrap;">${c.ctv_code || '-'}</td>
                    <td style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px;">${c.ctv_name || '-'}</td>
                    <td style="white-space:nowrap;">${c.ctv_phone || '-'}</td>
                    <td style="text-align:right; white-space:nowrap;">
                        ${formatCurrency(c.total_service_price || 0)}
                        ${serviceBadge}
                    </td>
                    <td style="color:var(--accent-green); font-weight:600; text-align:right; white-space:nowrap;">${formatCurrency(c.total_commission || 0)}</td>
                </tr>
            `;
            }).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">${t('no_commissions') || 'No commissions found'}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading commissions:', error);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--error-color, #ef4444)">Error loading commissions: ${error.message}</td></tr>`;
        
        // Re-enable buttons on error
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.disabled = false;
        });
        const applyBtn = document.querySelector('.custom-date-range .btn-primary');
        if (applyBtn) applyBtn.disabled = false;
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
 * Update the total revenue label based on current filter
 */
function updateTotalRevenueLabel() {
    const labelEl = document.getElementById('totalRevenueLabel');
    if (!labelEl) return;
    
    let labelText = t('total_revenue_for_period') || 'Tổng Dịch Vụ';
    
    if (currentFilterType === 'quick' && currentFilterName) {
        switch(currentFilterName) {
            case 'day':
                labelText = t('total_revenue_for_today') || 'Tổng Dịch Vụ Hôm Nay';
                break;
            case 'week':
                labelText = t('total_revenue_for_week') || 'Tổng Dịch Vụ Tuần Này';
                break;
            case 'month':
                labelText = t('total_revenue_for_month') || 'Tổng Dịch Vụ Tháng Này';
                break;
            default:
                labelText = t('total_revenue_for_period') || 'Tổng Dịch Vụ';
        }
    } else if (currentFilterType === 'custom') {
        labelText = t('total_revenue_for_custom') || 'Tổng Dịch Vụ';
    }
    
    labelEl.textContent = labelText;
}

/**
 * Apply quick filter
 */
function applyQuickFilter(filterType) {
    currentFilterType = 'quick';
    currentFilterName = filterType;
    currentFilterValue = getDateRangeForFilter(filterType);
    
    // Clear custom date inputs
    document.getElementById('commissionDateFrom').value = '';
    document.getElementById('commissionDateTo').value = '';
    
    // Update button states
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.quick-filter-btn[data-filter="${filterType}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Disable all buttons during loading
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // Update label
    updateTotalRevenueLabel();
    
    // Show loading state immediately
    showCommissionsLoading();
    
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
    currentFilterName = null;
    currentFilterValue = {
        date_from: dateFrom,
        date_to: dateTo
    };
    
    // Clear quick filter buttons
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Disable custom date apply button during loading
    const applyBtn = document.querySelector('.custom-date-range .btn-primary');
    if (applyBtn) applyBtn.disabled = true;
    
    // Update label
    updateTotalRevenueLabel();
    
    // Show loading state immediately
    showCommissionsLoading();
    
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
    
    // Custom date range apply button
    const customDateBtn = document.querySelector('.custom-date-range .btn-primary');
    if (customDateBtn) {
        customDateBtn.addEventListener('click', applyCustomDateRange);
    }
    
    // Set default to current month on load
    // Only if commissions page is visible or if no filter is set
    if (!currentFilterType) {
        applyQuickFilter('month');
    } else {
        // Update label if filter is already set
        updateTotalRevenueLabel();
    }
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

