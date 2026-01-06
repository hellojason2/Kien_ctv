/**
 * Admin Dashboard - Clients Module - Reports
 * Handles commission reports and modals.
 * 
 * NOTE: If this file approaches 50MB, it must be split into smaller modules.
 * Files larger than 50MB cannot be synchronized or edited safely.
 */

/**
 * Show Commission Report Modal
 */
async function showCommissionReport(phone, name) {
    const modal = document.getElementById('commissionReportModal');
    const list = document.getElementById('reportTransactionsList');
    
    // Reset
    document.getElementById('reportClientName').textContent = name;
    document.getElementById('reportClientPhone').textContent = phone;
    document.getElementById('reportTotalCommission').textContent = 'Loading...';
    list.innerHTML = '<div class="loading">Loading report...</div>';
    
    modal.style.display = 'block';
    
    try {
        const result = await api(`/api/admin/clients/commission-report?sdt=${encodeURIComponent(phone)}&ten_khach=${encodeURIComponent(name)}`);
        
        if (result.status === 'success') {
            document.getElementById('reportTotalCommission').textContent = formatClientCurrency(result.summary.total_commission_paid);
            document.getElementById('reportTotalRevenue').textContent = `Revenue: ${formatClientCurrency(result.summary.total_revenue)}`;
            
            if (result.transactions.length === 0) {
                list.innerHTML = '<div style="text-align:center; padding:20px; color:#6b7280;">No commission records found.</div>';
                return;
            }
            
            list.innerHTML = result.transactions.map(tx => {
                const commissionsHTML = tx.commissions.map(c => `
                    <div style="display:flex; justify-content:space-between; padding:8px; border-bottom:1px solid #f3f4f6; font-size:13px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="background:#e5e7eb; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;">L${c.level}</span>
                            <span style="font-weight:500;">${escapeHtml(c.ctv_name || c.ctv_code)}</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:600; color:#4a7c23;">${formatClientCurrency(c.commission_amount)}</div>
                            <div style="font-size:11px; color:#6b7280;">${(c.commission_rate * 100).toFixed(2)}%</div>
                        </div>
                    </div>
                `).join('');
                
                return `
                    <div style="background:white; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden;">
                        <div style="padding:12px; background:#f9fafb; border-bottom:1px solid #e5e7eb; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <div style="font-weight:600; color:#111827;">${escapeHtml(tx.service_name)}</div>
                                <div style="font-size:12px; color:#6b7280;">${tx.date} • Closer: ${escapeHtml(tx.closer || 'N/A')}</div>
                            </div>
                            <div style="font-weight:700; color:#111827;">${formatClientCurrency(tx.amount)}</div>
                        </div>
                        <div style="padding:0;">
                            ${commissionsHTML || '<div style="padding:12px; color:#9ca3af; font-style:italic;">No commissions generated</div>'}
                        </div>
                        <div style="padding:8px 12px; background:#f0fdf4; border-top:1px solid #e5e7eb; display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#166534;">
                            <span>Total Commission</span>
                            <span>${formatClientCurrency(tx.total_commission)}</span>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            list.innerHTML = `<div style="color:red; padding:20px;">Error: ${result.message}</div>`;
        }
    } catch (error) {
        console.error(error);
        list.innerHTML = `<div style="color:red; padding:20px;">Error loading report</div>`;
    }
}

function closeCommissionReportModal() {
    document.getElementById('commissionReportModal').style.display = 'none';
}

// Close on outside click
window.onclick = function(event) {
    const modal = document.getElementById('commissionReportModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
