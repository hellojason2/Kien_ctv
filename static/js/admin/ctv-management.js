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
    tbody.innerHTML = data.map(ctv => {
        // Check if code is numeric only
        const isNumericCode = /^\d+$/.test(ctv.ma_ctv);
        const codeStyle = isNumericCode ? '' : 'color:#b91c1c;font-weight:600;';
        
        return `
        <tr>
            <td style="${codeStyle}">${ctv.ma_ctv}${!isNumericCode ? ' ⚠️' : ''}</td>
            <td>${ctv.ten}</td>
            <td>${ctv.email || '-'}</td>
            <td>${ctv.sdt || '-'}</td>
            <td>${ctv.nguoi_gioi_thieu_code || '-'}</td>
            <td><span class="badge badge-${ctv.cap_bac?.toLowerCase() || 'bronze'}">${ctv.cap_bac || 'Bronze'}</span></td>
            <td><span class="badge badge-${ctv.is_active !== false ? 'active' : 'inactive'}">${ctv.is_active !== false ? t('active') : t('inactive')}</span></td>
            <td>
                <div style="display:flex;gap:4px;flex-wrap:wrap">
                    <button class="btn btn-secondary" style="padding:6px 10px;font-size:11px" onclick="viewHierarchy('${ctv.ma_ctv}')" title="View Tree">🌳</button>
                    <button class="btn btn-primary" style="padding:6px 10px;font-size:11px" onclick="showChangePasswordModal('${ctv.ma_ctv}')" title="Change Password">🔑</button>
                    <button class="btn btn-danger" style="padding:6px 10px;font-size:11px;background:#fee2e2;color:#b91c1c;border-color:#fecaca" onclick="deleteCTV('${ctv.ma_ctv}', '${ctv.ten.replace(/'/g, "\\'")}')" title="Delete CTV">🗑️</button>
                </div>
            </td>
        </tr>
    `}).join('');
    // Apply translations for new content
    applyTranslations();
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
    
    // Initialize searchable dropdowns
    initHierarchyDropdown();
    initReferrerDropdown();
}

/**
 * Show create CTV modal
 */
function showCreateCTVModal() {
    document.getElementById('createCTVModal').classList.add('active');
    // Re-apply translations to modal elements
    applyTranslations();
    
    // Generate CTV Code
    generateCTVCode().then(code => {
        const input = document.getElementById('newCtvCode');
        if (input) input.value = code;
    });
    
    // Load CTV levels for datalist
    loadCTVLevels();
    
    // Reset referrer dropdown
    const input = document.getElementById('referrerSearch');
    const hiddenInput = document.getElementById('newCtvReferrer');
    if (input) input.value = '';
    if (hiddenInput) hiddenInput.value = '';
}

/**
 * Load available CTV levels from database
 */
async function loadCTVLevels() {
    try {
        const result = await api('/api/admin/ctv/levels');
        if (result.status === 'success' && result.levels) {
            const datalist = document.getElementById('levelOptions');
            if (datalist) {
                datalist.innerHTML = result.levels.map(level => 
                    `<option value="${level}">`
                ).join('');
            }
        }
    } catch (error) {
        console.error('Error loading CTV levels:', error);
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
        cap_bac: document.getElementById('newCtvLevel').value || 'Đã đặt cọc'
    };
    
    const result = await api('/api/admin/ctv', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    if (result.status === 'success') {
        alert(`CTV created! Default password: ${result.default_password}`);
        closeModal('createCTVModal');
        document.getElementById('createCTVForm').reset();
        // Reset custom dropdowns
        const input = document.getElementById('referrerSearch');
        if (input) input.value = '';
        const hiddenInput = document.getElementById('newCtvReferrer');
        if (hiddenInput) hiddenInput.value = '';
        
        loadCTVList();
    } else {
        alert('Error: ' + result.message);
    }
}

/**
 * Generate next CTV code based on existing list
 */
async function generateCTVCode() {
    // Ensure list is loaded
    if (!window.allCTV || window.allCTV.length === 0) {
        await loadCTVList();
    }
    
    let maxId = 0;
    if (window.allCTV && window.allCTV.length > 0) {
        window.allCTV.forEach(ctv => {
            // Extract numeric part from "CTVxxx" or just "xxx"
            const match = ctv.ma_ctv.match(/(\d+)/);
            if (match) {
                const num = parseInt(match[1], 10);
                if (num > maxId) maxId = num;
            }
        });
    }
    
    const nextId = maxId + 1;
    // Format as CTV + 3 digits (e.g. CTV005)
    return `CTV${String(nextId).padStart(3, '0')}`;
}

/**
 * Normalize Vietnamese text for better search matching
 * Removes accents and converts to lowercase
 * @param {string} str - String to normalize
 * @returns {string} - Normalized string
 */
function normalizeVietnamese(str) {
    if (!str) return '';
    return str.toString()
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

/**
 * Initialize searchable referrer dropdown
 */
function initReferrerDropdown() {
    const dropdown = document.getElementById('referrerDropdown');
    const input = document.getElementById('referrerSearch');
    const list = document.getElementById('referrerList');
    const hiddenInput = document.getElementById('newCtvReferrer');
    
    if (!dropdown || !input || !list) return;

    // Show dropdown on focus
    input.addEventListener('focus', () => {
        dropdown.classList.add('open');
        renderReferrerList(input.value);
    });

    // Filter on input
    input.addEventListener('input', (e) => {
        renderReferrerList(e.target.value);
        dropdown.classList.add('open');
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove('open');
            // Restore text from value if exists, else clear
            const selectedValue = hiddenInput.value;
            if (selectedValue) {
                const ctv = (window.allCTV || []).find(c => c.ma_ctv === selectedValue);
                if (ctv) {
                    input.value = `${ctv.ten} (${ctv.ma_ctv})`;
                }
            } else {
                input.value = '';
            }
        }
    });

    // Toggle on arrow click
    const arrow = dropdown.querySelector('.dropdown-arrow');
    if (arrow) {
        arrow.addEventListener('click', (e) => {
            e.stopPropagation();
            if (dropdown.classList.contains('open')) {
                dropdown.classList.remove('open');
            } else {
                dropdown.classList.add('open');
                input.focus();
                renderReferrerList(input.value);
            }
        });
    }
}

/**
 * Render referrer list
 */
function renderReferrerList(searchTerm = '') {
    const list = document.getElementById('referrerList');
    if (!list) return;
    
    const term = normalizeVietnamese(searchTerm);
    const hiddenInput = document.getElementById('newCtvReferrer');
    const selectedValue = hiddenInput ? hiddenInput.value : '';

    // Filter active CTVs
    let filtered = (window.allCTV || []).filter(c => c.is_active !== false);
    
    if (term) {
        filtered = filtered.filter(c => {
            const code = normalizeVietnamese(c.ma_ctv || '');
            const name = normalizeVietnamese(c.ten || '');
            const phone = (c.sdt || '').toString();
            return code.includes(term) || name.includes(term) || phone.includes(term);
        });
    }

    // Always include "None (Root CTV)" option at top if search term is empty or matches "root"
    let html = '';
    // Translation fallback
    const noneText = (typeof t === 'function' ? t('none_root') : null) || 'None (Root CTV)';
    const noResultsText = (typeof t === 'function' ? t('no_ctv_found') : null) || 'No CTV found';

    if (!term || normalizeVietnamese(noneText).includes(term) || 'root'.includes(term)) {
        html += `
        <div class="dropdown-item ${selectedValue === '' ? 'selected' : ''}" 
             onclick="selectReferrer('')">
            <span>${noneText}</span>
        </div>`;
    }

    if (filtered.length === 0 && !html) {
        html = `<div class="no-results">${noResultsText}</div>`;
    } else {
        html += filtered.slice(0, 50).map(c => `
            <div class="dropdown-item ${c.ma_ctv === selectedValue ? 'selected' : ''}" 
                 onclick="selectReferrer('${c.ma_ctv}')">
                <span><strong>${c.ten}</strong> (${c.ma_ctv})</span>
            </div>
        `).join('');
    }

    list.innerHTML = html;
}

/**
 * Select referrer
 */
function selectReferrer(ctvCode) {
    const hiddenInput = document.getElementById('newCtvReferrer');
    const input = document.getElementById('referrerSearch');
    const dropdown = document.getElementById('referrerDropdown');
    
    if (hiddenInput) hiddenInput.value = ctvCode;
    
    if (ctvCode) {
        const ctv = (window.allCTV || []).find(c => c.ma_ctv === ctvCode);
        if (ctv && input) {
            input.value = `${ctv.ten} (${ctv.ma_ctv})`;
        }
    } else {
        // Clear input for "None" selection
        if (input) input.value = '';
    }
    
    if (dropdown) dropdown.classList.remove('open');
}


/**
 * Show change password modal
 * @param {string} ctvCode - CTV Code
 */
function showChangePasswordModal(ctvCode) {
    document.getElementById('changePasswordCtvCode').value = ctvCode;
    document.getElementById('newPassword').value = '';
    document.getElementById('changePasswordModal').classList.add('active');
    applyTranslations();
}

/**
 * Submit change password
 */
async function submitChangePassword() {
    const ctvCode = document.getElementById('changePasswordCtvCode').value;
    const newPassword = document.getElementById('newPassword').value;

    if (!newPassword) {
        alert(t('enter_password'));
        return;
    }

    const result = await api(`/api/admin/ctv/${ctvCode}`, {
        method: 'PUT',
        body: JSON.stringify({ password: newPassword })
    });

    if (result.status === 'success') {
        alert(t('password_changed'));
        closeModal('changePasswordModal');
    } else {
        alert('Error: ' + result.message);
    }
}

/**
 * Delete a single CTV
 * @param {string} ctvCode - CTV code to delete
 * @param {string} ctvName - CTV name for confirmation
 */
async function deleteCTV(ctvCode, ctvName) {
    const confirmMsg = `⚠️ DELETE CTV?\n\nCode: ${ctvCode}\nName: ${ctvName}\n\nThis will PERMANENTLY remove this CTV from the system.`;
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    // Second confirm for safety
    if (!confirm(`⚠️ FINAL CONFIRMATION\n\nAre you ABSOLUTELY SURE you want to delete:\n${ctvCode} - ${ctvName}?\n\nClick OK to DELETE or Cancel to abort.`)) {
        return;
    }
    
    try {
        const result = await api(`/api/admin/ctv/${ctvCode}/hard-delete`, {
            method: 'DELETE'
        });
        
        if (result.status === 'success') {
            alert(`✅ CTV "${ctvCode}" has been deleted successfully.`);
            loadCTVList();
        } else {
            alert('❌ Error: ' + (result.message || 'Failed to delete CTV'));
        }
    } catch (error) {
        console.error('Delete CTV error:', error);
        alert('❌ Error deleting CTV: ' + error.message);
    }
}

/**
 * Delete all CTVs with non-numeric codes
 */
async function deleteNonNumericCTVs() {
    // First, find all non-numeric CTVs
    const nonNumericCTVs = (window.allCTV || []).filter(ctv => !/^\d+$/.test(ctv.ma_ctv));
    
    if (nonNumericCTVs.length === 0) {
        alert('✅ No CTVs with non-numeric codes found. All codes are valid!');
        return;
    }
    
    // Show list of CTVs to be deleted
    const listPreview = nonNumericCTVs.slice(0, 10).map(c => `• ${c.ma_ctv} - ${c.ten}`).join('\n');
    const moreText = nonNumericCTVs.length > 10 ? `\n... and ${nonNumericCTVs.length - 10} more` : '';
    
    const confirmMsg = `⚠️ BULK DELETE WARNING\n\nFound ${nonNumericCTVs.length} CTV(s) with non-numeric codes:\n\n${listPreview}${moreText}\n\nClick OK to DELETE ALL of them.`;
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    // Second confirm for bulk delete
    if (!confirm(`⚠️ FINAL CONFIRMATION\n\nYou are about to DELETE ${nonNumericCTVs.length} CTV(s).\n\nThis action CANNOT be undone!\n\nClick OK to proceed or Cancel to abort.`)) {
        return;
    }
    
    try {
        const result = await api('/api/admin/ctv/delete-non-numeric', {
            method: 'DELETE'
        });
        
        if (result.status === 'success') {
            alert(`✅ Successfully deleted ${result.deleted_count} CTV(s) with non-numeric codes.`);
            loadCTVList();
        } else {
            alert('❌ Error: ' + (result.message || 'Failed to delete CTVs'));
        }
    } catch (error) {
        console.error('Delete non-numeric CTVs error:', error);
        alert('❌ Error: ' + error.message);
    }
}
