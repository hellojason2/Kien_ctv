/**
 * CTV Portal - Clients Module
 * DOES: Loads and displays client cards with their services
 * INPUTS: API response from /api/ctv/clients-with-services
 * OUTPUTS: Renders client card grid
 * FLOW: loadCtvClientsWithServices -> renderCtvClientCards -> renderCtvClientCard/renderCtvServiceCard
 */

let ctvClients = [];
let currentView = 'card';

// Switch to card view
function switchToCardView() {
    currentView = 'card';
    document.getElementById('cardViewSection').style.display = 'block';
    document.getElementById('tableViewSection').style.display = 'none';
    document.getElementById('cardViewBtn').classList.add('active');
    document.getElementById('tableViewBtn').classList.remove('active');
    loadCtvClientsWithServices();
}

// Switch to table view
function switchToTableView() {
    currentView = 'table';
    document.getElementById('cardViewSection').style.display = 'none';
    document.getElementById('tableViewSection').style.display = 'block';
    document.getElementById('cardViewBtn').classList.remove('active');
    document.getElementById('tableViewBtn').classList.add('active');
    loadCtvClientsWithServices();
}

// Load clients with services
async function loadCtvClientsWithServices() {
    const search = document.getElementById('ctvClientSearch')?.value || '';
    let url = '/api/ctv/clients-with-services';
    if (search) {
        url += `?search=${encodeURIComponent(search)}`;
    }
    
    try {
        const result = await api(url);
        
        if (result.status === 'success') {
            ctvClients = result.clients;
            if (currentView === 'card') {
                renderCtvClientCards(result.clients);
            } else {
                renderCtvClientTable(result.clients);
            }
        } else {
            // Render error to the correct container based on current view
            const errorHTML = `
                <div class="no-clients-message">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <p>${result.message || t('error_loading_data') || 'Loi khi tai du lieu'}</p>
                </div>
            `;
            
            if (currentView === 'card') {
                document.getElementById('ctvClientsGrid').innerHTML = errorHTML;
            } else {
                document.getElementById('ctvClientsTable').innerHTML = errorHTML;
            }
        }
    } catch (error) {
        console.error('Error loading clients:', error);
        const errorHTML = `
            <div class="no-clients-message">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p>${t('error_loading_data') || 'Loi khi tai du lieu'}</p>
            </div>
        `;
        
        if (currentView === 'card') {
            document.getElementById('ctvClientsGrid').innerHTML = errorHTML;
        } else {
            document.getElementById('ctvClientsTable').innerHTML = errorHTML;
        }
    }
}

// Render client cards
function renderCtvClientCards(clients) {
    const grid = document.getElementById('ctvClientsGrid');
    
    if (!clients || clients.length === 0) {
        grid.innerHTML = `
            <div class="no-clients-message">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
                <p>${t('no_customers')}</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = clients.map(client => renderCtvClientCard(client)).join('');
}

// Render single client card
function renderCtvClientCard(client) {
    const initials = getCtvInitials(client.ten_khach);
    const depositBadgeHTML = client.overall_deposit === 'Da coc' ? `<span class="client-status-badge deposited">${t('da_coc')}</span>` : '';
    
    const servicesHTML = client.services.map((svc, idx) => renderCtvServiceCard(svc, idx)).join('');
    
    return `
        <div class="client-card">
            <div class="client-card-header">
                <div class="client-avatar">${initials}</div>
                <div class="client-main-info">
                    <div class="client-name">${escapeHtmlCTV(client.ten_khach)}</div>
                    <div class="client-phone">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        ${escapeHtmlCTV(client.sdt)}
                    </div>
                </div>
                <div class="service-count-badge">${client.service_count} ${t('dich_vu')}</div>
            </div>
            <div class="client-info-row">
                <div class="client-info-item">
                    <span class="client-info-label">${t('co_so')}</span>
                    <span class="client-info-value">${escapeHtmlCTV(client.co_so || '-')}</span>
                </div>
                <div class="client-info-item">
                    <span class="client-info-label">${t('first_visit')}</span>
                    <span class="client-info-value">${client.first_visit_date || '-'}</span>
                </div>
                ${depositBadgeHTML}
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

// Render single service card
function renderCtvServiceCard(service, index) {
    const depositBadgeHTML = service.deposit_status === 'Da coc' ? `<span class="service-deposit-status deposited">${t('da_coc')}</span>` : '';
    
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
                ${depositBadgeHTML}
            </div>
            <div class="service-name">${escapeHtmlCTV(service.dich_vu || t('unknown_service'))}</div>
            <div class="service-details">
                <div class="service-detail-row">
                    <span class="service-detail-label">${t('tong_tien')}</span>
                    <span class="service-detail-value amount">${formatCtvCurrency(service.tong_tien)}</span>
                </div>
                <div class="service-detail-row">
                    <span class="service-detail-label">${t('tien_coc')}</span>
                    <span class="service-detail-value deposit">${formatCtvCurrency(service.tien_coc)}</span>
                </div>
                <div class="service-detail-row">
                    <span class="service-detail-label">${t('phai_dong')}</span>
                    <span class="service-detail-value remaining">${formatCtvCurrency(service.phai_dong)}</span>
                </div>
            </div>
            ${datesHTML}
        </div>
    `;
}

// Render client table
function renderCtvClientTable(clients) {
    const tableContainer = document.getElementById('ctvClientsTable');
    
    if (!clients || clients.length === 0) {
        tableContainer.innerHTML = `
            <div class="no-clients-message">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
                <p>${t('no_customers')}</p>
            </div>
        `;
        return;
    }
    
    // Calculate total amount per client from services
    const getClientTotal = (client) => {
        if (!client.services || client.services.length === 0) return 0;
        return client.services.reduce((sum, svc) => sum + (svc.tong_tien || 0), 0);
    };
    
    const tableHTML = `
        <div class="client-table-wrapper" style="overflow-x: auto;">
            <table class="client-table" style="width: 100%; border-collapse: collapse; background: var(--bg-secondary); border-radius: 8px; overflow: hidden; min-width: 600px;">
                <thead>
                    <tr style="background: var(--bg-tertiary); border-bottom: 2px solid var(--border-color);">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: var(--text-primary); border-right: 1px solid var(--border-color);">${t('ten_khach')}</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: var(--text-primary); border-right: 1px solid var(--border-color);">${t('sdt')}</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: var(--text-primary); border-right: 1px solid var(--border-color);">${t('co_so')}</th>
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: var(--text-primary); border-right: 1px solid var(--border-color);">${t('service_count')}</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: var(--text-primary); border-right: 1px solid var(--border-color);">${t('tong_tien')}</th>
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: var(--text-primary);">${t('trang_thai_coc')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${clients.map(client => {
                        const depositBadgeHTML = client.overall_deposit === 'Da coc' 
                            ? `<span class="table-status-badge deposited" style="padding: 4px 8px; border-radius: 4px; font-size: 12px;">${t('da_coc')}</span>`
                            : '';
                        const totalAmount = getClientTotal(client);
                        
                        return `
                            <tr style="border-bottom: 1px solid var(--border-color);">
                                <td style="padding: 12px; color: var(--text-primary); border-right: 1px solid var(--border-color); font-weight: 500;">${escapeHtmlCTV(client.ten_khach || '-')}</td>
                                <td style="padding: 12px; color: var(--text-primary); border-right: 1px solid var(--border-color);">${escapeHtmlCTV(client.sdt || '-')}</td>
                                <td style="padding: 12px; color: var(--text-primary); border-right: 1px solid var(--border-color);">${escapeHtmlCTV(client.co_so || '-')}</td>
                                <td style="padding: 12px; text-align: center; color: var(--text-primary); border-right: 1px solid var(--border-color);">${client.service_count || 0}</td>
                                <td style="padding: 12px; text-align: right; color: var(--accent-color); border-right: 1px solid var(--border-color); font-weight: 500;">${formatCtvCurrency(totalAmount)}</td>
                                <td style="padding: 12px; text-align: center;">
                                    ${depositBadgeHTML}
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    tableContainer.innerHTML = tableHTML;
}

// Initialize client search
function initClientSearch() {
    const searchInput = document.getElementById('ctvClientSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounceCTV(() => {
            loadCtvClientsWithServices();
        }, 300));
    }
}

