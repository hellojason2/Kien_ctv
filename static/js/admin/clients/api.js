/**
 * Admin Dashboard - Clients Module - API
 * Handles data fetching and export.
 * 
 * NOTE: If this file approaches 50MB, it must be split into smaller modules.
 * Files larger than 50MB cannot be synchronized or edited safely.
 */

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
 * Export clients to Excel
 */
function exportClientsExcel() {
    const search = document.getElementById('clientSearch').value;
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    
    const token = localStorage.getItem('session_token');
    window.open(`/api/admin/clients/export?${params}&token=${token}`, '_blank');
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
    
    // Initialize view state
    updateViewToggleState();
}
