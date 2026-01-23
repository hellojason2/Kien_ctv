/**
 * Admin Dashboard - Clients Module
 * Client cards, services, pagination
 * 
 * Created: December 30, 2025
 */

// State
let allClients = [];
let clientsCurrentPage = 1;
let clientsTotalPages = 1;
let currentClientView = localStorage.getItem('clientView') || 'grid';

/**
 * Load clients with services
 * @param {number} page - Page number
 */
async function loadClientsWithServices(page = 1) {
    clientsCurrentPage = page;
    const search = document.getElementById('clientSearch')?.value || '';
    const status = document.getElementById('clientStatusFilter')?.value || '';
    const grid = document.getElementById('clientsGrid');
    
    grid.innerHTML = '<div class="loading">' + t('loading') + '</div>';
    
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', 50);
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    
    try {
        const result = await api(`/api/admin/clients-with-services?${params}`);
        
        if (result && result.status === 'success') {
            allClients = result.clients;
            clientsTotalPages = result.pagination.total_pages || 1;
            
            // Update count display
            document.getElementById('clientsCount').textContent = 
                `${t('showing')} ${result.clients.length} ${t('of')} ${result.pagination.total} ${t('clients')}`;
            
            // Render based on current view
            if (currentClientView === 'table') {
                renderClientTable(result.clients);
                document.getElementById('clientsGrid').style.display = 'none';
                document.getElementById('clientsTableContainer').style.display = 'block';
            } else {
                renderClientCards(result.clients);
                document.getElementById('clientsGrid').style.display = 'grid';
                document.getElementById('clientsTableContainer').style.display = 'none';
            }
            
            updateViewToggleState();
            updateClientsPagination(result.pagination);
        } else {
            const errorMsg = result?.message || t('error_loading_clients') || 'Lỗi khi tải danh sách khách hàng';
            grid.innerHTML = `
                <div class="no-clients-message">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <p>${errorMsg}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading clients:', error);
        grid.innerHTML = `
            <div class="no-clients-message">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p>${error.message || t('error_loading_clients') || 'Lỗi khi tải danh sách khách hàng'}</p>
            </div>
        `;
    }
}

/**
 * Update clients pagination controls
 * @param {object} pagination - Pagination object
 */
function updateClientsPagination(pagination) {
    const info = document.getElementById('clientsPaginationInfo');
    const controls = document.getElementById('clientsPaginationControls');
    
    const start = (pagination.page - 1) * pagination.per_page + 1;
    const end = Math.min(pagination.page * pagination.per_page, pagination.total);
    info.textContent = `${start}-${end} ${t('of')} ${pagination.total}`;
    
    let html = '';
    const totalPages = pagination.total_pages || 1;
    const currentPage = pagination.page;
    
    // Previous button
    html += `<button class="btn btn-secondary" ${currentPage <= 1 ? 'disabled' : ''} onclick="loadClientsWithServices(${currentPage - 1})" style="padding: 8px 12px; font-size: 12px;">Prev</button>`;
    
    // Page numbers
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button class="btn btn-secondary" onclick="loadClientsWithServices(1)" style="padding: 8px 12px; font-size: 12px;">1</button>`;
        if (startPage > 2) html += `<span style="color: var(--text-secondary); padding: 0 8px;">...</span>`;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const isActive = i === currentPage;
        html += `<button class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}" onclick="loadClientsWithServices(${i})" style="padding: 8px 12px; font-size: 12px;">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span style="color: var(--text-secondary); padding: 0 8px;">...</span>`;
        html += `<button class="btn btn-secondary" onclick="loadClientsWithServices(${totalPages})" style="padding: 8px 12px; font-size: 12px;">${totalPages}</button>`;
    }
    
    // Next button
    html += `<button class="btn btn-secondary" ${currentPage >= totalPages ? 'disabled' : ''} onclick="loadClientsWithServices(${currentPage + 1})" style="padding: 8px 12px; font-size: 12px;">Next</button>`;
    
    controls.innerHTML = html;
}

/**
 * Render client cards
 * @param {Array} clients - Client array
 */
function renderClientCards(clients) {
    const grid = document.getElementById('clientsGrid');
    
    if (!clients || clients.length === 0) {
        grid.innerHTML = `
            <div class="no-clients-message">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
                <p>${t('no_clients')}</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = clients.map(client => renderClientCard(client)).join('');
}

/**
 * Render a single client card
 * @param {object} client - Client object
 * @returns {string} - HTML string
 */
function renderClientCard(client) {
    const initials = getInitials(client.ten_khach);
    const depositClass = client.overall_deposit === 'Da coc' ? 'deposited' : 'not-deposited';
    const depositText = client.overall_deposit === 'Da coc' ? t('da_coc') : t('chua_coc');
    
    const servicesHTML = client.services.map((svc, idx) => renderServiceCard(svc, idx)).join('');
    
    return `
        <div class="client-card">
            <div class="client-card-header">
                <div class="client-avatar">${initials}</div>
                <div class="client-main-info">
                    <div class="client-name" onclick="showCommissionReport('${escapeHtml(client.sdt)}', '${escapeHtml(client.ten_khach)}')" style="cursor: pointer;">${escapeHtml(client.ten_khach)}</div>
                    <div class="client-phone">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        ${escapeHtml(client.sdt)}
                    </div>
                </div>
                <div class="service-count-badge">${client.service_count} ${client.service_count === 1 ? t('service') : t('services')}</div>
            </div>
            <div class="client-info-row">
                <div class="client-info-item">
                    <span class="client-info-label">${t('co_so')}</span>
                    <span class="client-info-value">${escapeHtml(client.co_so || '-')}</span>
                </div>
                <div class="client-info-item">
                    <span class="client-info-label">${t('first_visit')}</span>
                    <span class="client-info-value">${client.first_visit_date || '-'}</span>
                </div>
                <div class="client-info-item">
                    <span class="client-info-label">${t('nguoi_chot')}</span>
                    <span class="client-info-value">${escapeHtml(client.nguoi_chot || '-')}</span>
                </div>
                <span class="client-status-badge ${depositClass}">${depositText}</span>
            </div>
            <div class="services-container">
                <div class="services-title">${t('services_title')} (${client.services.length})</div>
                <div class="services-grid">
                    ${servicesHTML}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render a service card
 * @param {object} service - Service object
 * @param {number} index - Service index
 * @returns {string} - HTML string
 */
function renderServiceCard(service, index) {
    const depositClass = service.deposit_status === 'Da coc' ? 'deposited' : 'not-deposited';
    const depositText = service.deposit_status === 'Da coc' ? t('da_coc') : t('chua_coc');
    
    const datesHTML = `
        ${service.ngay_nhap_don 
            ? `<div class="service-appointment">
                   <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                       <line x1="16" y1="2" x2="16" y2="6"/>
                       <line x1="8" y1="2" x2="8" y2="6"/>
                       <line x1="3" y1="10" x2="21" y2="10"/>
                   </svg>
                   <span>${t('ngay_nhap_don')}</span>
                   <span class="date">${service.ngay_nhap_don}</span>
               </div>` 
            : ''}
        ${service.ngay_hen_lam 
            ? `<div class="service-appointment">
                   <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                       <line x1="16" y1="2" x2="16" y2="6"/>
                       <line x1="8" y1="2" x2="8" y2="6"/>
                       <line x1="3" y1="10" x2="21" y2="10"/>
                   </svg>
                   <span>${t('ngay_hen_lam')}</span>
                   <span class="date">${service.ngay_hen_lam}</span>
               </div>` 
            : ''}
    `;
    
    return `
        <div class="service-card">
            <div class="service-card-header">
                <div class="service-number">${service.service_number}</div>
                <span class="service-deposit-status ${depositClass}">${depositText}</span>
            </div>
            <div class="service-name">${escapeHtml(service.dich_vu || t('unknown_service'))}</div>
            <div class="service-details">
                <div class="service-detail-row">
                    <span class="service-detail-label">${t('tong_tien')}</span>
                    <span class="service-detail-value amount">${formatClientCurrency(service.tong_tien)}</span>
                </div>
                <div class="service-detail-row">
                    <span class="service-detail-label">${t('tien_coc')}</span>
                    <span class="service-detail-value deposit">${formatClientCurrency(service.tien_coc)}</span>
                </div>
                <div class="service-detail-row">
                    <span class="service-detail-label">${t('phai_dong')}</span>
                    <span class="service-detail-value remaining">${formatClientCurrency(service.phai_dong)}</span>
                </div>
            </div>
            ${datesHTML}
        </div>
    `;
}

/**
 * Switch between Grid and List/Table view
 * @param {string} view - 'grid' or 'list' (mapped to 'table')
 */
function switchClientView(view) {
    // Map 'list' to 'table' for internal consistency
    const internalView = view === 'list' ? 'table' : 'grid';
    currentClientView = internalView;
    localStorage.setItem('clientView', internalView);
    
    const grid = document.getElementById('clientsGrid');
    const table = document.getElementById('clientsTableContainer');
    
    if (internalView === 'table') {
        grid.style.display = 'none';
        table.style.display = 'block';
        renderClientTable(allClients);
    } else {
        grid.style.display = 'grid';
        table.style.display = 'none';
        renderClientCards(allClients);
    }
    
    updateViewToggleState();
}

/**
 * Update toggle buttons active state
 */
function updateViewToggleState() {
    const gridBtn = document.getElementById('viewGridBtn');
    const listBtn = document.getElementById('viewListBtn');
    
    if (gridBtn && listBtn) {
        gridBtn.classList.toggle('active', currentClientView === 'grid');
        listBtn.classList.toggle('active', currentClientView === 'table');
    }
}

/**
 * Render client table rows
 * @param {Array} clients - Client array
 */
function renderClientTable(clients) {
    const tbody = document.getElementById('clientsTableBody');
    if (!tbody) return;
    
    if (!clients || clients.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: #9ca3af;">${t('no_clients')}</td></tr>`;
        return;
    }
    
    tbody.innerHTML = clients.map(client => {
        const servicesList = client.services.map(s => s.dich_vu).join(', ');
        
        return `
            <tr>
                <td>
                    <div class="client-name-badge" 
                         title="${escapeHtml(client.ten_khach)}" 
                         onclick="showCommissionReport('${escapeHtml(client.sdt)}', '${escapeHtml(client.ten_khach)}')"
                         style="cursor: pointer;">
                        ${escapeHtml(client.ten_khach)}
                    </div>
                </td>
                <td><div class="cell-phone">${escapeHtml(client.sdt)}</div></td>
                <td>${escapeHtml(client.co_so || '-')}</td>
                <td>${client.first_visit_date || '-'}</td>
                <td>${escapeHtml(client.nguoi_chot || '-')}</td>
                <td>
                    <div style="display:flex; flex-direction:column; gap:4px;">
                        <span class="cell-services-count">${client.service_count} ${client.service_count === 1 ? t('service') : t('services')}</span>
                        <span style="font-size:12px; color:#6b7280; max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escapeHtml(servicesList)}">
                            ${escapeHtml(servicesList)}
                        </span>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Initialize client search and filter handlers
 */
function initClientSearch() {
    const searchInput = document.getElementById('clientSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            loadClientsWithServices(1);
        }, 300));
    }
    
    // Status filter change handler
    const statusFilter = document.getElementById('clientStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            loadClientsWithServices(1);
        });
    }
    
    // Initialize view state
    updateViewToggleState();
}

/**
 * Export clients to Excel
 */
function exportClientsExcel() {
    const search = document.getElementById('clientSearch')?.value || '';
    const status = document.getElementById('clientStatusFilter')?.value || '';
    
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    
    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/clients/export?${params}&token=${token}`, '_blank');
}

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
}// Close on outside click
window.onclick = function(event) {
    const modal = document.getElementById('commissionReportModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}