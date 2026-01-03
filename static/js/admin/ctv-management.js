/**
 * Admin Dashboard - CTV Management Module
 * CTV list, search, create, and dropdown population
 * 
 * Created: December 30, 2025
 */

// State - Global variable accessible across all admin modules
window.allCTV = window.allCTV || [];

/**
 * Load CTV list from API
 */
async function loadCTVList() {
    // Check if we should show inactive CTVs
    const showInactive = document.getElementById('showInactiveCTV')?.checked || false;
    const activeOnly = !showInactive;
    
    const result = await api(`/api/admin/ctv?active_only=${activeOnly}`);
    if (result.status === 'success') {
        window.allCTV = result.data;
        renderCTVTable(window.allCTV);
        // For dropdowns, only use active CTVs for better UX
        const activeCTV = showInactive ? result.data.filter(c => c.is_active !== false) : result.data;
        populateCTVSelects(activeCTV);
    }
}

/**
 * Render CTV table
 * @param {Array} data - CTV data array
 */
function renderCTVTable(data) {
    const tbody = document.getElementById('ctvTableBody');
    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-secondary)">${t('no_ctv_found')}</td></tr>`;
        return;
    }
    tbody.innerHTML = data.map(ctv => `
        <tr>
            <td>${ctv.ma_ctv}</td>
            <td>${ctv.ten}</td>
            <td>${ctv.email || '-'}</td>
            <td>${ctv.sdt || '-'}</td>
            <td>${ctv.nguoi_gioi_thieu_code || '-'}</td>
            <td><span class="badge badge-${ctv.cap_bac?.toLowerCase() || 'bronze'}">${ctv.cap_bac || 'Bronze'}</span></td>
            <td><span class="badge badge-${ctv.is_active !== false ? 'active' : 'inactive'}">${ctv.is_active !== false ? t('active') : t('inactive')}</span></td>
            <td>
                <button class="btn btn-secondary" style="padding:6px 12px;font-size:12px" onclick="viewHierarchy('${ctv.ma_ctv}')">Tree</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Populate CTV select dropdowns
 * @param {Array} ctvList - CTV data array (optional)
 */
function populateCTVSelects(ctvList = null) {
    // Use provided list or fall back to allCTV (filtered to active only for dropdowns)
    const listForDropdowns = ctvList || window.allCTV.filter(c => c.is_active !== false);
    const options = listForDropdowns.map(c => `<option value="${c.ma_ctv}">${c.ten} (${c.ma_ctv})</option>`).join('');
    
    // Populate regular dropdowns
    const commissionFilter = document.getElementById('commissionCtvFilter');
    if (commissionFilter) {
        commissionFilter.innerHTML = `<option value="">${t('all_ctvs')}</option>` + options;
    }
    
    const referrerSelect = document.getElementById('newCtvReferrer');
    if (referrerSelect) {
        referrerSelect.innerHTML = `<option value="">${t('none_root')}</option>` + options;
    }
    
    // Initialize searchable dropdown for hierarchy
    initHierarchyDropdown();
}

/**
 * Show create CTV modal
 */
function showCreateCTVModal() {
    document.getElementById('createCTVModal').classList.add('active');
    // Re-apply translations to modal elements
    applyTranslations();
    // Re-populate referrer dropdown with translated option
    if (window.allCTV.length > 0) {
        const options = window.allCTV.map(c => `<option value="${c.ma_ctv}">${c.ten} (${c.ma_ctv})</option>`).join('');
        document.getElementById('newCtvReferrer').innerHTML = `<option value="">${t('none_root')}</option>` + options;
    }
}

/**
 * Create new CTV
 */
async function createCTV() {
    const data = {
        ma_ctv: document.getElementById('newCtvCode').value,
        ten: document.getElementById('newCtvName').value,
        email: document.getElementById('newCtvEmail').value,
        sdt: document.getElementById('newCtvPhone').value,
        nguoi_gioi_thieu: document.getElementById('newCtvReferrer').value || null,
        cap_bac: 'Bronze'
    };
    
    const result = await api('/api/admin/ctv', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    if (result.status === 'success') {
        alert(`CTV created! Default password: ${result.default_password}`);
        closeModal('createCTVModal');
        document.getElementById('createCTVForm').reset();
        loadCTVList();
    } else {
        alert('Error: ' + result.message);
    }
}

/**
 * Normalize Vietnamese text for better search matching
 * Removes accents and converts to lowercase
 * @param {string} str - String to normalize
 * @returns {string} - Normalized string
 */
function normalizeVietnamese(str) {
    if (!str) return '';
    return str
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
        .trim();
}

/**
 * Initialize CTV search handler
 */
function initCTVSearch() {
    const searchInput = document.getElementById('ctvSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = normalizeVietnamese(e.target.value);
            
            // If search is empty, show all CTVs
            if (!term) {
                renderCTVTable(window.allCTV);
                return;
            }
            
            // Filter CTVs - normalize all fields for comparison
            const filtered = window.allCTV.filter(c => {
                const code = normalizeVietnamese(c.ma_ctv || '');
                const name = normalizeVietnamese(c.ten || '');
                const email = normalizeVietnamese(c.email || '');
                const phone = (c.sdt || '').toString().trim();
                
                return code.includes(term) ||
                       name.includes(term) ||
                       email.includes(term) ||
                       phone.includes(term);
            });
            
            renderCTVTable(filtered);
        });
    }
}

