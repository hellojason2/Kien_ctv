/**
 * Admin Dashboard - CTV Management Module
 * CTV list, search, create, and dropdown population
 * 
 * Created: December 30, 2025
 */

// State - Global variable accessible across all admin modules
window.allCTV = window.allCTV || [];

/**
 * Format referrer as a nice badge with phone icon
 * @param {string} code - Referrer phone/code
 * @param {string} name - Referrer name (optional)
 * @returns {string} - HTML string for the badge
 */
function formatReferrerBadge(code, name) {
    if (!code) return '-';

    const phoneIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>`;

    // Format the phone number nicely (add spaces for readability)
    const formattedCode = formatPhoneDisplay(code);

    if (name) {
        return `<span class="badge badge-referrer" title="${code}">${phoneIcon}${formattedCode}<span class="badge-referrer-name">(${escapeHtmlCTV(name)})</span></span>`;
    }

    return `<span class="badge badge-referrer" title="${code}">${phoneIcon}${formattedCode}</span>`;
}

/**
 * Format phone number for display (add spaces for readability)
 * @param {string} phone - Phone number
 * @returns {string} - Formatted phone number
 */
function formatPhoneDisplay(phone) {
    if (!phone) return '';
    // Remove non-digit characters
    const digits = phone.toString().replace(/\D/g, '');

    // Format Vietnamese phone (10 digits): 0xxx xxx xxx
    if (digits.length === 10 && digits.startsWith('0')) {
        return digits.slice(0, 4) + ' ' + digits.slice(4, 7) + ' ' + digits.slice(7);
    }
    // Format 9-digit number (without leading 0): xxx xxx xxx
    if (digits.length === 9) {
        return digits.slice(0, 3) + ' ' + digits.slice(3, 6) + ' ' + digits.slice(6);
    }
    // Return as-is for other formats
    return phone;
}

/**
 * Escape HTML for CTV context (prevent XSS)
 * @param {string} text - Text to escape
 * @returns {string} - Escaped HTML
 */
function escapeHtmlCTV(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

    // Also load pending registrations
    // loadPendingRegistrations(); - Removed as per user request to use Registrations tab instead
}


/**
 * Load pending registrations - REMOVED (Moved to Registrations tab)
 */
// function loadPendingRegistrations() { ... }


/**
 * Approve registration - REMOVED (Moved to Registrations tab)
 */
// function approveRegistration(id) { ... }

/**
 * Reject registration - REMOVED (Moved to Registrations tab)
 */
// function rejectRegistration(id) { ... }


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
    const labelCode = t('code');
    const labelName = t('name');
    const labelEmail = t('email');
    const labelPhone = t('phone');
    const labelReferrer = t('referrer');
    const labelLevel = t('level');
    const labelStatus = t('status');
    const labelActions = t('actions');

    tbody.innerHTML = data.map(ctv => {
        // Check if code is numeric only
        const isNumericCode = /^\d+$/.test(ctv.ma_ctv);
        const codeStyle = isNumericCode ? '' : 'color:#b91c1c;font-weight:600;';

        return `
        <tr>
            <td data-label="${labelCode}" style="${codeStyle}">
                ${ctv.ma_ctv}${!isNumericCode ? ' ⚠️' : ''}
            </td>
            <td data-label="${labelName}">
                <strong>${ctv.ten}</strong>
            </td>
            <td data-label="${labelEmail}">
                ${ctv.email || '-'}
            </td>
            <td data-label="${labelPhone}">
                ${ctv.sdt || '-'}
            </td>
            <td data-label="${labelReferrer}">
                ${formatReferrerBadge(ctv.nguoi_gioi_thieu_code, ctv.nguoi_gioi_thieu_name)}
            </td>
            <td data-label="${labelLevel}">
                <span class="badge badge-${ctv.cap_bac?.toLowerCase() || 'bronze'}">${ctv.cap_bac || 'Bronze'}</span>
            </td>
            <td data-label="${labelStatus}">
                <span class="badge badge-${ctv.is_active !== false ? 'active' : 'inactive'}">${ctv.is_active !== false ? t('active') : t('inactive')}</span>
            </td>
            <td data-label="${labelActions}">
                <div class="mobile-actions-grid">
                    <button class="btn btn-secondary" onclick="viewHierarchy('${ctv.ma_ctv}')" title="View Tree">🌳</button>
                    <button class="btn btn-info" onclick="showEditCTVModal('${ctv.ma_ctv}')" title="Edit CTV">✏️</button>
                    <button class="btn btn-primary" onclick="showChangePasswordModal('${ctv.ma_ctv}')" title="Change Password">🔑</button>
                    <button class="btn btn-danger" onclick="deleteCTV('${ctv.ma_ctv}', '${ctv.ten.replace(/'/g, "\\'")}')" title="Delete CTV">🗑️</button>
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
    const modal = document.getElementById('createCTVModal');
    if (!modal) {
        console.error('createCTVModal element not found!');
        return;
    }

    // Force show modal - multiple methods to ensure it works
    modal.classList.add('active');
    modal.style.display = 'flex';
    modal.style.zIndex = '99999';
    modal.style.pointerEvents = 'auto';

    // Ensure modal content is visible
    const modalContent = modal.querySelector('.modal');
    if (modalContent) {
        modalContent.style.display = 'block';
        modalContent.style.visibility = 'visible';
        modalContent.style.opacity = '1';
        modalContent.style.pointerEvents = 'auto';
        modalContent.style.zIndex = '100000';
    }

    console.log('Modal shown:', modal.style.display, modal.classList.contains('active'));

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
 * Show edit CTV modal
 * @param {string} ctvCode - CTV Code to edit
 */
async function showEditCTVModal(ctvCode) {
    // Find the CTV in our loaded list
    const ctv = window.allCTV.find(c => c.ma_ctv === ctvCode);

    if (!ctv) {
        alert('CTV not found');
        return;
    }

    const modal = document.getElementById('editCTVModal');
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
        modal.style.zIndex = '99999';
        modal.style.pointerEvents = 'auto';
        const modalContent = modal.querySelector('.modal');
        if (modalContent) {
            modalContent.style.display = 'block';
            modalContent.style.visibility = 'visible';
            modalContent.style.opacity = '1';
            modalContent.style.pointerEvents = 'auto';
        }
    }

    // Populate the form fields
    document.getElementById('editCtvCode').value = ctv.ma_ctv;
    document.getElementById('editCtvName').value = ctv.ten || '';
    document.getElementById('editCtvPhone').value = ctv.sdt || '';
    document.getElementById('editCtvEmail').value = ctv.email || '';
    document.getElementById('editCtvLevel').value = ctv.cap_bac || '';

    // Show the modal
    document.getElementById('editCTVModal').classList.add('active');
    applyTranslations();

    // Load CTV levels for datalist
    loadCTVLevels();
}

/**
 * Submit edit CTV form
 */
async function submitEditCTV() {
    const ctvCode = document.getElementById('editCtvCode').value;
    const data = {
        ten: document.getElementById('editCtvName').value,
        sdt: document.getElementById('editCtvPhone').value,
        email: document.getElementById('editCtvEmail').value,
        cap_bac: document.getElementById('editCtvLevel').value
    };

    // Validate required fields
    if (!data.ten) {
        alert(t('enter_name') || 'Please enter a name');
        return;
    }

    const result = await api(`/api/admin/ctv/${ctvCode}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });

    if (result.status === 'success') {
        alert(t('ctv_updated') || 'CTV updated successfully');
        closeModal('editCTVModal');
        document.getElementById('editCTVForm').reset();
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
            const searchValue = e.target.value;

            // If search is empty, show all CTVs
            if (!term && !searchValue) {
                renderCTVTable(window.allCTV);
                return;
            }

            // Extract digits only from search term for phone comparison
            const searchDigits = searchValue.replace(/\D/g, '');
            const searchDigitsNoZero = searchDigits.replace(/^0+/, ''); // Remove leading zeros

            // Filter CTVs - normalize all fields for comparison
            const filtered = window.allCTV.filter(c => {
                const code = normalizeVietnamese(c.ma_ctv || '');
                const name = normalizeVietnamese(c.ten || '');
                const email = normalizeVietnamese(c.email || '');
                const phone = (c.sdt || '').toString().replace(/\D/g, ''); // Extract digits from phone
                const phoneNoZero = phone.replace(/^0+/, ''); // Remove leading zeros from stored phone

                // DATA: Referrer info
                const referrerCode = normalizeVietnamese(c.nguoi_gioi_thieu_code || '');
                const referrerName = normalizeVietnamese(c.nguoi_gioi_thieu_name || '');
                const referrerPhone = (c.nguoi_gioi_thieu_code || '').toString().replace(/\D/g, '');
                const referrerPhoneNoZero = referrerPhone.replace(/^0+/, '');

                // Match by code, name, email, or phone (with flexible phone matching)
                // ALSO match by referrer code/phone/name
                return code.includes(term) ||
                    name.includes(term) ||
                    email.includes(term) ||
                    referrerCode.includes(term) ||
                    referrerName.includes(term) ||
                    // Phone matching
                    phone.includes(searchDigits) ||
                    phone.includes(searchDigitsNoZero) ||
                    phoneNoZero.includes(searchDigits) ||
                    phoneNoZero.includes(searchDigitsNoZero) ||
                    // Referrer Phone matching
                    (searchDigits.length > 3 && referrerPhone.includes(searchDigits)) ||
                    (searchDigits.length > 3 && referrerPhoneNoZero.includes(searchDigits)) ||

                    (searchDigits.length >= 8 && phone.includes(searchDigits.slice(-8))) ||
                    (searchDigits.length >= 8 && phoneNoZero.includes(searchDigits.slice(-8)));
            });

            renderCTVTable(filtered);
        });
    }
}

// Initialize search when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initCTVSearch();
});

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
        // Extract digits only from search term for phone comparison
        const searchDigits = searchTerm.replace(/\D/g, '');
        const searchDigitsNoZero = searchDigits.replace(/^0+/, ''); // Remove leading zeros

        filtered = filtered.filter(c => {
            const code = normalizeVietnamese(c.ma_ctv || '');
            const name = normalizeVietnamese(c.ten || '');
            const phone = (c.sdt || '').toString().replace(/\D/g, ''); // Extract digits from phone
            const phoneNoZero = phone.replace(/^0+/, ''); // Remove leading zeros from stored phone

            // Match by code, name, or phone (with flexible phone matching)
            return code.includes(term) ||
                name.includes(term) ||
                phone.includes(searchDigits) ||
                phone.includes(searchDigitsNoZero) ||
                phoneNoZero.includes(searchDigits) ||
                phoneNoZero.includes(searchDigitsNoZero) ||
                (searchDigits.length >= 8 && phone.includes(searchDigits.slice(-8))) || // Last 8 digits
                (searchDigits.length >= 8 && phoneNoZero.includes(searchDigits.slice(-8)));
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

    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
        modal.style.zIndex = '99999';
        modal.style.pointerEvents = 'auto';
        const modalContent = modal.querySelector('.modal');
        if (modalContent) {
            modalContent.style.display = 'block';
            modalContent.style.visibility = 'visible';
            modalContent.style.opacity = '1';
            modalContent.style.pointerEvents = 'auto';
        }
    }

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
