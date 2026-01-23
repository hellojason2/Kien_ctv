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

/**
 * Sort services to prioritize consulting sources first
 * @param {Array} services - Services array
 * @returns {Array} - Sorted services array
 */
function sortCtvServicesConsultingFirst(services) {
    if (!services || services.length === 0) return services;
    
    // Default sort by date - removed consulting priority
    return [...services];
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
    
    // Sort services within each client to show consulting services first
    const processedClients = clients.map(client => ({
        ...client,
        services: sortCtvServicesConsultingFirst(client.services)
    }));
    
    grid.innerHTML = processedClients.map(client => renderCtvClientCard(client)).join('');
}

// Render single client card
function renderCtvClientCard(client) {
    const initials = getCtvInitials(client.ten_khach);
    
    // Sort services to show consulting first
    const sortedServices = sortCtvServicesConsultingFirst(client.services);
    
    // Convert services to table rows
    const servicesRows = sortedServices.map((svc, idx) => {
        
        const dateDisplay = svc.ngay_hen_lam || svc.ngay_nhap_don || '-';
        
        // Helper to get status class
        const getStatusClass = (status) => {
            if (!status) return '';
            const s = status.toLowerCase().trim();
            if (s === 'huy' || s === 'cancelled') return 'cancel';
            if (s === 'cho xac nhan' || s === 'pending') return 'pending';
            if (s === 'dang tu van' || s === 'consulting') return 'consulting';
            if (s === 'da den lam' || s === 'completed') return 'completed';
            if (s === 'da coc' || s === 'deposited') return 'deposited';
            return '';
        };

        const statusClass = getStatusClass(svc.trang_thai);
        
        return `
            <tr>
                <td>
                    <div class="svc-index">${idx + 1}</div>
                </td>
                <td>
                    <div class="svc-name">${escapeHtmlCTV(svc.dich_vu || t('unknown_service'))}</div>
                </td>
                <td>
                    <div class="svc-date">${dateDisplay}</div>
                    <div class="svc-status ${statusClass}">${escapeHtmlCTV(svc.trang_thai || '-')}</div>
                </td>
                <td class="text-right">
                    <div class="svc-price">${formatCtvCurrency(svc.tong_tien)}</div>
                    ${svc.phai_dong > 0 ? `<div class="svc-due">${t('phai_dong')}: ${formatCtvCurrency(svc.phai_dong)}</div>` : ''}
                </td>
            </tr>
        `;
    }).join('');
    
    return `
        <div class="client-card">
            <div class="client-card-header">
                <div class="client-avatar">${initials}</div>
                <div class="client-main-info">
                    <div class="client-name">
                        ${escapeHtmlCTV(client.ten_khach)}
                    </div>
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
            </div>
            <div class="services-container">
                <table class="services-list-table">
                    <thead>
                        <tr>
                            <th style="width: 40px">#</th>
                            <th>${t('dich_vu')}</th>
                            <th>${t('status')} / ${t('date')}</th>
                            <th class="text-right">${t('tong_tien')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${servicesRows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// Render single service card - REMOVED (replaced by table rows above)
// Keeping function just in case of reference but it is unused by renderCtvClientCard now
function renderCtvServiceCard(service, index) {
    return ''; 
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
        <div class="client-table-wrapper">
            <table class="client-table" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th>${t('ten_khach')}</th>
                        <th>${t('sdt')}</th>
                        <th>${t('co_so')}</th>
                        <th style="text-align: center;">${t('service_count')}</th>
                        <th style="text-align: right;">${t('tong_tien')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${clients.map(client => {
                        // Show overall status if available
                        const totalAmount = getClientTotal(client);
                        
                        return `
                            <tr>
                                <td class="col-name">${escapeHtmlCTV(client.ten_khach || '-')}</td>
                                <td class="col-phone">${escapeHtmlCTV(client.sdt || '-')}</td>
                                <td class="col-location">${escapeHtmlCTV(client.co_so || '-')}</td>
                                <td class="col-count" style="text-align: center;">${client.service_count || 0}</td>
                                <td class="col-amount" style="text-align: right;">${formatCtvCurrency(totalAmount)}</td>
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
let clientSearchInitialized = false;
function initClientSearch() {
    const searchInput = document.getElementById('ctvClientSearch');
    if (searchInput) {
        // Check if already initialized by checking for a data attribute
        if (!searchInput.dataset.searchInitialized) {
            searchInput.addEventListener('input', debounceCTV(() => {
                loadCtvClientsWithServices();
            }, 300));
            searchInput.dataset.searchInitialized = 'true';
            clientSearchInitialized = true;
        }
    }
}
