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

/**
 * Load clients with services
 * @param {number} page - Page number
 */
async function loadClientsWithServices(page = 1) {
    clientsCurrentPage = page;
    const search = document.getElementById('clientSearch')?.value || '';
    const grid = document.getElementById('clientsGrid');
    
    grid.innerHTML = '<div class="loading">' + t('loading') + '</div>';
    
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', 50);
    if (search) params.append('search', search);
    
    try {
        const result = await api(`/api/admin/clients-with-services?${params}`);
        
        if (result && result.status === 'success') {
            allClients = result.clients;
            clientsTotalPages = result.pagination.total_pages || 1;
            
            // Update count display
            document.getElementById('clientsCount').textContent = 
                `${t('showing')} ${result.clients.length} ${t('of')} ${result.pagination.total} ${t('clients')}`;
            
            renderClientCards(result.clients);
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
                    <div class="client-name">${escapeHtml(client.ten_khach)}</div>
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
 * Initialize client search handler
 */
function initClientSearch() {
    const searchInput = document.getElementById('clientSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            loadClientsWithServices(1);
        }, 300));
    }
}

/**
 * Export clients to Excel
 */
function exportClientsExcel() {
    const search = document.getElementById('clientSearch').value;
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    
    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/clients/export?${params}&token=${token}`, '_blank');
}

