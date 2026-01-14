/**
 * CTV Registrations Management
 * Handles viewing and approving/rejecting CTV registration requests
 */

let currentFilter = 'pending';
let currentRegistrationId = null;
let registrations = [];
let availableLevels = [];

/**
 * Load available CTV levels from database
 */
async function loadCTVLevels() {
    try {
        const result = await api('/api/admin/ctv/levels');
        if (result.status === 'success' && result.levels) {
            availableLevels = result.levels;
            return result.levels;
        }
    } catch (error) {
        console.error('Error loading CTV levels:', error);
    }
    return [];
}

/**
 * Load registrations based on current filter
 */
async function loadRegistrations() {
    try {
        const response = await api(`/api/admin/registrations?status=${currentFilter}`, {
            method: 'GET'
        });

        if (response.status === 'success') {
            registrations = response.registrations;
            renderRegistrationsTable(registrations);
            updateRegistrationCounts();
        } else {
            alert(response.message || 'Failed to load registrations');
            // Show error in table
            const tbody = document.getElementById('registrationsTableBody');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" style="text-align: center; padding: 40px; color: var(--accent-red);">
                            <p>Error: ${response.message || 'Failed to load data'}</p>
                            <button class="btn btn-secondary" onclick="loadRegistrations()" style="margin-top:10px">Retry</button>
                        </td>
                    </tr>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading registrations:', error);
        alert('Error loading registrations');
        
        // Show error in table
        const tbody = document.getElementById('registrationsTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: var(--accent-red);">
                        <p>Connection Error</p>
                        <button class="btn btn-secondary" onclick="loadRegistrations()" style="margin-top:10px">Retry</button>
                    </td>
                </tr>
            `;
        }
    }
}

/**
 * Update counts in filter tabs
 */
async function updateRegistrationCounts() {
    try {
        // Fetch counts for all statuses
        const [pending, approved, rejected] = await Promise.all([
            api('/api/admin/registrations?status=pending', { method: 'GET' }),
            api('/api/admin/registrations?status=approved', { method: 'GET' }),
            api('/api/admin/registrations?status=rejected', { method: 'GET' })
        ]);

        document.getElementById('pendingCount').textContent = pending.pagination?.total || 0;
        document.getElementById('approvedCount').textContent = approved.pagination?.total || 0;
        document.getElementById('rejectedCount').textContent = rejected.pagination?.total || 0;
    } catch (error) {
        console.error('Error updating counts:', error);
    }
}

/**
 * Render registrations table
 */
function renderRegistrationsTable(data) {
    const tbody = document.getElementById('registrationsTableBody');
    
    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="margin: 0 auto 16px; opacity: 0.5;">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <p data-i18n="no_registrations">No registrations found</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = data.map(reg => {
        const statusClass = `status-${reg.status}`;
        const statusText = reg.status.charAt(0).toUpperCase() + reg.status.slice(1);
        
        return `
            <tr>
                <td>#${reg.id}</td>
                <td>${escapeHtml(reg.full_name)}</td>
                <td>${escapeHtml(reg.phone)}</td>
                <td>${reg.email ? escapeHtml(reg.email) : '-'}</td>
                <td>${reg.referrer_code ? `${reg.referrer_code} ${reg.referrer_name ? '(' + escapeHtml(reg.referrer_name) + ')' : ''}` : '-'}</td>
                <td>${reg.created_at || '-'}</td>
                <td><span class="status-badge ${statusClass}" data-i18n="${reg.status}">${statusText}</span></td>
                <td>
                    <div class="action-buttons">
                        ${reg.status === 'pending' ? `
                            <button class="btn-approve" onclick="showApproveModal(${reg.id})" title="Approve">
                                ✓ <span data-i18n="approve">Approve</span>
                            </button>
                            <button class="btn-reject" onclick="showRejectModal(${reg.id})" title="Reject">
                                ✗ <span data-i18n="reject">Reject</span>
                            </button>
                        ` : ''}
                        <button class="btn-view" onclick="showViewDetailsModal(${reg.id})" title="View Details">
                            👁️ <span data-i18n="view">View</span>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Re-translate if needed
    if (window.translatePage) {
        translatePage();
    }
}

/**
 * Filter registrations by status
 */
function filterRegistrations(status) {
    currentFilter = status;
    
    // Update active tab
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.status === status);
    });
    
    loadRegistrations();
}

/**
 * Show approve modal
 */
async function showApproveModal(registrationId) {
    currentRegistrationId = registrationId;
    const registration = registrations.find(r => r.id === registrationId);
    
    if (!registration) return;
    
    const modal = document.getElementById('approveModal');
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
            modalContent.style.position = 'relative';
            modalContent.style.zIndex = '100000';
        }
        // Ensure all buttons are clickable
        const buttons = modal.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.style.pointerEvents = 'auto';
            btn.style.cursor = 'pointer';
            btn.style.zIndex = '100003';
            btn.style.position = 'relative';
        });
    }
    
    const detailsHtml = `
        <div class="detail-row">
            <span class="detail-label" data-i18n="full_name">Full Name</span>
            <span class="detail-value">${escapeHtml(registration.full_name)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label" data-i18n="phone_number">Phone</span>
            <span class="detail-value">${escapeHtml(registration.phone)}</span>
        </div>
        ${registration.email ? `
        <div class="detail-row">
            <span class="detail-label" data-i18n="email">Email</span>
            <span class="detail-value">${escapeHtml(registration.email)}</span>
        </div>
        ` : ''}
        ${registration.referrer_code ? `
        <div class="detail-row">
            <span class="detail-label" data-i18n="referrer">Referrer</span>
            <span class="detail-value">${registration.referrer_code} ${registration.referrer_name ? '(' + escapeHtml(registration.referrer_name) + ')' : ''}</span>
        </div>
        ` : ''}
        ${registration.signature_image ? `
        <div class="detail-row" style="flex-direction: column; align-items: flex-start; gap: 8px;">
            <span class="detail-label" data-i18n="signature">Signature</span>
            <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; width: 100%; display: flex; justify-content: center;">
                <img src="${registration.signature_image}" alt="Signature" style="max-width: 100%; max-height: 100px; object-fit: contain;">
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('approveDetails').innerHTML = detailsHtml;
    // Auto-populate CTV code with phone number
    document.getElementById('approveCtVCode').value = registration.phone;
    
    // Load and populate levels
    const levels = availableLevels.length > 0 ? availableLevels : await loadCTVLevels();
    const levelSelect = document.getElementById('approveLevel');
    levelSelect.innerHTML = levels.map(level => 
        `<option value="${level}">${level}</option>`
    ).join('');
    
    // Set default value to first level if available
    if (levels.length > 0) {
        levelSelect.value = levels[0];
    }
    
    document.getElementById('approveModal').style.display = 'flex';
    
    // Ensure buttons are clickable
    ensureModalButtonsClickable('approveModal');
    
    if (window.translatePage) {
        translatePage();
    }
}

/**
 * Close approve modal
 */
function closeApproveModal() {
    const modal = document.getElementById('approveModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
    currentRegistrationId = null;
}

/**
 * Generate CTV code for approval
 */
async function generateCTVCodeForApproval() {
    try {
        const response = await api('/api/admin/ctv/generate-code', {
            method: 'POST'
        });
        
        if (response.status === 'success' && response.ctv_code) {
            document.getElementById('approveCtVCode').value = response.ctv_code;
        } else {
            alert('Failed to generate CTV code');
        }
    } catch (error) {
        console.error('Error generating code:', error);
        alert('Error generating CTV code');
    }
}

/**
 * Confirm approval
 */
async function confirmApproval() {
    if (!currentRegistrationId) {
        alert('No registration selected');
        return;
    }
    
    const ctvCodeInput = document.getElementById('approveCtVCode');
    const levelSelect = document.getElementById('approveLevel');
    
    if (!ctvCodeInput || !levelSelect) {
        alert('Form elements not found');
        return;
    }
    
    const ctvCode = ctvCodeInput.value.trim();
    const level = levelSelect.value;
    
    if (!ctvCode) {
        alert('Please enter a CTV code');
        return;
    }
    
    try {
        const response = await api(`/api/admin/registrations/${currentRegistrationId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ctv_code: ctvCode,
                level: level
            })
        });
        
        if (response.status === 'success') {
            alert(`Registration approved! CTV code: ${ctvCode}`);
            closeApproveModal();
            loadRegistrations();
            // Update sidebar badge
            if (typeof initPendingRegistrationsBadge === 'function') {
                initPendingRegistrationsBadge();
            }
        } else {
            alert(response.message || 'Failed to approve registration');
        }
    } catch (error) {
        console.error('Error approving registration:', error);
        alert('Error approving registration');
    }
}

/**
 * Show reject modal
 */
function showRejectModal(registrationId) {
    currentRegistrationId = registrationId;
    const registration = registrations.find(r => r.id === registrationId);
    
    if (!registration) return;
    
    const modal = document.getElementById('rejectModal');
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
            modalContent.style.position = 'relative';
            modalContent.style.zIndex = '100000';
        }
        // Ensure all buttons are clickable
        const buttons = modal.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.style.pointerEvents = 'auto';
            btn.style.cursor = 'pointer';
            btn.style.zIndex = '100003';
            btn.style.position = 'relative';
        });
    }
    
    const detailsHtml = `
        <div class="detail-row">
            <span class="detail-label" data-i18n="full_name">Full Name</span>
            <span class="detail-value">${escapeHtml(registration.full_name)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label" data-i18n="phone_number">Phone</span>
            <span class="detail-value">${escapeHtml(registration.phone)}</span>
        </div>
        ${registration.email ? `
        <div class="detail-row">
            <span class="detail-label" data-i18n="email">Email</span>
            <span class="detail-value">${escapeHtml(registration.email)}</span>
        </div>
        ` : ''}
        ${registration.signature_image ? `
        <div class="detail-row" style="flex-direction: column; align-items: flex-start; gap: 8px;">
            <span class="detail-label" data-i18n="signature">Signature</span>
            <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; width: 100%; display: flex; justify-content: center;">
                <img src="${registration.signature_image}" alt="Signature" style="max-width: 100%; max-height: 100px; object-fit: contain;">
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('rejectDetails').innerHTML = detailsHtml;
    document.getElementById('rejectReason').value = '';
    document.getElementById('rejectModal').style.display = 'flex';
    
    // Ensure buttons are clickable
    ensureModalButtonsClickable('rejectModal');
    
    if (window.translatePage) {
        translatePage();
    }
}

/**
 * Close reject modal
 */
function closeRejectModal() {
    const modal = document.getElementById('rejectModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
    currentRegistrationId = null;
}

/**
 * Confirm rejection
 */
async function confirmRejection() {
    if (!currentRegistrationId) return;
    
    const reason = document.getElementById('rejectReason').value.trim() || 'No reason provided';
    
    try {
        const response = await api(`/api/admin/registrations/${currentRegistrationId}/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reason: reason
            })
        });
        
        if (response.status === 'success') {
            alert('Registration rejected');
            closeRejectModal();
            loadRegistrations();
            // Update sidebar badge
            if (typeof initPendingRegistrationsBadge === 'function') {
                initPendingRegistrationsBadge();
            }
        } else {
            alert(response.message || 'Failed to reject registration');
        }
    } catch (error) {
        console.error('Error rejecting registration:', error);
        alert('Error rejecting registration');
    }
}

/**
 * Show view details modal
 */
function showViewDetailsModal(registrationId) {
    const registration = registrations.find(r => r.id === registrationId);
    
    if (!registration) return;
    
    const modal = document.getElementById('viewDetailsModal');
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
    
    const detailsHtml = `
        <div class="registration-details">
            <div class="detail-row">
                <span class="detail-label">ID</span>
                <span class="detail-value">#${registration.id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label" data-i18n="full_name">Full Name</span>
                <span class="detail-value">${escapeHtml(registration.full_name)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label" data-i18n="phone_number">Phone</span>
                <span class="detail-value">${escapeHtml(registration.phone)}</span>
            </div>
            ${registration.email ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="email">Email</span>
                <span class="detail-value">${escapeHtml(registration.email)}</span>
            </div>
            ` : ''}
            ${registration.address ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="address">Address</span>
                <span class="detail-value">${escapeHtml(registration.address)}</span>
            </div>
            ` : ''}
            ${registration.dob ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="dob">Date of Birth</span>
                <span class="detail-value">${registration.dob}</span>
            </div>
            ` : ''}
            ${registration.id_number ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="id_number">ID Number</span>
                <span class="detail-value">${escapeHtml(registration.id_number)}</span>
            </div>
            ` : ''}
            ${registration.referrer_code ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="referrer">Referrer</span>
                <span class="detail-value">${registration.referrer_code} ${registration.referrer_name ? '(' + escapeHtml(registration.referrer_name) + ')' : ''}</span>
            </div>
            ` : ''}
            <div class="detail-row">
                <span class="detail-label" data-i18n="status">Status</span>
                <span class="detail-value"><span class="status-badge status-${registration.status}" data-i18n="${registration.status}">${registration.status.charAt(0).toUpperCase() + registration.status.slice(1)}</span></span>
            </div>
            <div class="detail-row">
                <span class="detail-label" data-i18n="submitted_date">Submitted Date</span>
                <span class="detail-value">${registration.created_at || '-'}</span>
            </div>
            ${registration.reviewed_at ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="reviewed_date">Reviewed Date</span>
                <span class="detail-value">${registration.reviewed_at}</span>
            </div>
            ` : ''}
            ${registration.reviewed_by ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="reviewed_by">Reviewed By</span>
                <span class="detail-value">${escapeHtml(registration.reviewed_by)}</span>
            </div>
            ` : ''}
            ${registration.admin_notes ? `
            <div class="detail-row">
                <span class="detail-label" data-i18n="notes">Notes</span>
                <span class="detail-value">${escapeHtml(registration.admin_notes)}</span>
            </div>
            ` : ''}
            ${registration.signature_image ? `
            <div class="detail-row" style="flex-direction: column; align-items: flex-start; gap: 8px;">
                <span class="detail-label" data-i18n="signature">Signature</span>
                <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; width: 100%; display: flex; justify-content: center;">
                    <img src="${registration.signature_image}" alt="Signature" style="max-width: 100%; max-height: 150px; object-fit: contain;">
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    document.getElementById('fullRegistrationDetails').innerHTML = detailsHtml;
    document.getElementById('viewDetailsModal').style.display = 'flex';
    
    // Ensure buttons are clickable
    ensureModalButtonsClickable('viewDetailsModal');
    
    if (window.translatePage) {
        translatePage();
    }
}

/**
 * Close view details modal
 */
function closeViewDetailsModal() {
    const modal = document.getElementById('viewDetailsModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load registrations when page is shown
// Ensure modal buttons are clickable after modal is shown
function ensureModalButtonsClickable(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Force all buttons to be clickable
    setTimeout(() => {
        const buttons = modal.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.style.pointerEvents = 'auto';
            btn.style.cursor = 'pointer';
            btn.style.zIndex = '100003';
            btn.style.position = 'relative';
            
            // Remove any event blockers
            btn.onclick = btn.onclick || (() => {});
        });
        
        // Add click handler to overlay to close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                if (modalId === 'approveModal') {
                    closeApproveModal();
                } else if (modalId === 'rejectModal') {
                    closeRejectModal();
                } else if (modalId === 'viewDetailsModal') {
                    closeViewDetailsModal();
                }
            }
        });
    }, 100);
}

document.addEventListener('pageChanged', (e) => {
    if (e.detail.page === 'registrations') {
        loadRegistrations();
        loadCTVLevels(); // Preload levels for faster modal display
    }
});
