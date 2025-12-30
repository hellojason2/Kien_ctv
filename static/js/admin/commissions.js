/**
 * Admin Dashboard - Commissions Module
 * Commission reports and exports
 * 
 * Created: December 30, 2025
 */

/**
 * Load commissions (grouped by CTV)
 */
async function loadCommissions() {
    const month = document.getElementById('commissionMonthFilter').value;
    
    let url = '/api/admin/commissions/summary?';
    if (month) url += `month=${month}&`;
    
    const result = await api(url);
    if (result.status === 'success') {
        const tbody = document.getElementById('commissionsTableBody');
        
        // Update grand totals
        document.getElementById('totalCtvCount').textContent = result.total_ctv || 0;
        document.getElementById('grandTotalService').textContent = formatCurrency(result.grand_total?.total_service_price || 0);
        document.getElementById('grandTotalCommission').textContent = formatCurrency(result.grand_total?.total_commission || 0);
        
        if (result.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">Khong co hoa hong</td></tr>';
            return;
        }
        tbody.innerHTML = result.data.map(c => `
            <tr>
                <td style="font-weight:600;">${c.ctv_code}</td>
                <td>${c.ctv_name || '-'}</td>
                <td>${c.ctv_phone || '-'}</td>
                <td>${formatCurrency(c.total_service_price)}</td>
                <td style="color:var(--accent-green); font-weight:600;">${formatCurrency(c.total_commission)}</td>
            </tr>
        `).join('');
    }
}

/**
 * Initialize commission filter handlers
 */
function initCommissionFilters() {
    const monthFilter = document.getElementById('commissionMonthFilter');
    if (monthFilter) {
        monthFilter.addEventListener('change', loadCommissions);
    }
}

/**
 * Export commissions to Excel
 */
function exportCommissionsExcel() {
    const month = document.getElementById('commissionMonthFilter').value;
    const params = new URLSearchParams();
    if (month) params.append('month', month);
    
    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/commissions/summary/export?${params}&token=${token}`, '_blank');
}

