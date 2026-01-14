/**
 * Admin Dashboard - Signup Terms Management
 * Handles editing of signup agreement terms
 * 
 * Created: January 14, 2026
 */

let currentTermsId = null;
let currentTermsLanguage = 'vi';

/**
 * Load signup terms by language
 */
async function loadSignupTermsByLanguage() {
    console.log('loadSignupTermsByLanguage called');
    
    const languageSelect = document.getElementById('termsLanguageSelect');
    if (!languageSelect) {
        console.error('termsLanguageSelect element not found!');
        return;
    }
    
    const language = languageSelect.value || 'vi';
    currentTermsLanguage = language;
    
    console.log(`Loading terms for language: ${language}`);
    
    try {
        const result = await api(`/api/admin/signup-terms?language=${language}`);
        console.log('API result:', result);
        
        if (result.status === 'success' && result.terms && result.terms.length > 0) {
            console.log(`Found ${result.terms.length} terms`);
            // Load the active term or the latest one
            const activeTerm = result.terms.find(t => t.is_active) || result.terms[0];
            console.log('Loading term:', activeTerm.id, activeTerm.title);
            loadSignupTermsIntoEditor(activeTerm);
        } else {
            console.log('No terms found, clearing editor');
            // No terms found, clear editor
            clearTermsEditor();
        }
    } catch (error) {
        console.error('Error loading signup terms:', error);
        clearTermsEditor();
    }
}

/**
 * Load terms into editor
 */
function loadSignupTermsIntoEditor(term) {
    console.log('loadSignupTermsIntoEditor called with term:', term.id);
    currentTermsId = term.id;
    
    const titleInput = document.getElementById('termsTitle');
    const contentTextarea = document.getElementById('termsContent');
    
    if (!titleInput || !contentTextarea) {
        console.error('Required form elements not found!', {titleInput, contentTextarea});
        return;
    }
    
    titleInput.value = term.title || '';
    contentTextarea.value = term.content || '';
    
    console.log(`Loaded: title="${term.title?.substring(0, 30)}...", content length=${term.content?.length}`);
    
    // Update metadata
    const versionEl = document.getElementById('currentVersion');
    const updatedEl = document.getElementById('lastUpdated');
    const updatedByEl = document.getElementById('updatedBy');
    
    if (versionEl) versionEl.textContent = term.version || '-';
    if (updatedEl) updatedEl.textContent = term.updated_at 
        ? new Date(term.updated_at).toLocaleString() 
        : '-';
    if (updatedByEl) updatedByEl.textContent = term.updated_by || '-';
    
    // Update preview
    updateTermsPreview();
    
    // Enable save button
    const saveBtn = document.getElementById('saveTermsBtn');
    if (saveBtn) saveBtn.disabled = false;
    
    console.log('Terms loaded into editor successfully');
}

/**
 * Clear terms editor
 */
function clearTermsEditor() {
    currentTermsId = null;
    document.getElementById('termsTitle').value = '';
    document.getElementById('termsContent').value = '';
    document.getElementById('currentVersion').textContent = '-';
    document.getElementById('lastUpdated').textContent = '-';
    document.getElementById('updatedBy').textContent = '-';
    document.getElementById('termsPreview').innerHTML = '<p class="preview-placeholder">Preview will appear here...</p>';
}

/**
 * Enable save button when content changes
 */
function enableSaveButton() {
    document.getElementById('saveTermsBtn').disabled = false;
}

/**
 * Update terms preview
 */
function updateTermsPreview() {
    const content = document.getElementById('termsContent').value;
    const previewBox = document.getElementById('termsPreview');
    
    if (content.trim()) {
        previewBox.innerHTML = content;
    } else {
        previewBox.innerHTML = '<p class="preview-placeholder">Preview will appear here...</p>';
    }
}

/**
 * Insert HTML tag at cursor position
 */
function insertTermsTag(tag) {
    const textarea = document.getElementById('termsContent');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const beforeText = textarea.value.substring(0, start);
    const afterText = textarea.value.substring(end);
    
    let insertText;
    if (selectedText) {
        insertText = `<${tag}>${selectedText}</${tag}>`;
    } else {
        insertText = `<${tag}></${tag}>`;
    }
    
    textarea.value = beforeText + insertText + afterText;
    
    // Set cursor position
    const newPosition = start + insertText.length - (tag.length + 3);
    textarea.focus();
    textarea.setSelectionRange(newPosition, newPosition);
    
    updateTermsPreview();
    enableSaveButton();
}

/**
 * Format as list
 */
function formatTermsList() {
    const textarea = document.getElementById('termsContent');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    if (selectedText) {
        const lines = selectedText.split('\n').filter(line => line.trim());
        const listItems = lines.map(line => `<p>- ${line.trim()}</p>`).join('\n');
        
        const beforeText = textarea.value.substring(0, start);
        const afterText = textarea.value.substring(end);
        
        textarea.value = beforeText + listItems + afterText;
        updateTermsPreview();
        enableSaveButton();
    } else {
        insertTermsTag('p');
    }
}

/**
 * Save signup terms
 */
async function saveSignupTerms() {
    const title = document.getElementById('termsTitle').value.trim();
    const content = document.getElementById('termsContent').value.trim();
    
    if (!title || !content) {
        alert('Please enter both title and content');
        return;
    }
    
    const saveBtn = document.getElementById('saveTermsBtn');
    saveBtn.disabled = true;
    
    let result;
    if (currentTermsId) {
        // Update existing term
        result = await api(`/api/admin/signup-terms/${currentTermsId}`, {
            method: 'PUT',
            body: JSON.stringify({
                title: title,
                content: content
            })
        });
    } else {
        // Create new term
        result = await api('/api/admin/signup-terms', {
            method: 'POST',
            body: JSON.stringify({
                language: currentTermsLanguage,
                title: title,
                content: content
            })
        });
    }
    
    if (result.status === 'success') {
        alert('Terms saved successfully!');
        loadSignupTermsByLanguage();
    } else {
        alert('Error: ' + result.message);
        saveBtn.disabled = false;
    }
}

/**
 * Show version history modal
 */
async function showTermsVersionHistory() {
    const modal = document.getElementById('versionHistoryModal');
    modal.style.display = 'flex';
    
    const versionList = document.getElementById('versionList');
    versionList.innerHTML = '<div class="loading">Loading versions...</div>';
    
    const language = currentTermsLanguage;
    const result = await api(`/api/admin/signup-terms?language=${language}`);
    
    if (result.status === 'success' && result.terms.length > 0) {
        versionList.innerHTML = result.terms.map(term => `
            <div class="version-item ${term.is_active ? 'active' : ''}">
                <div class="version-header">
                    <div class="version-info">
                        <strong>Version ${term.version}</strong>
                        ${term.is_active ? '<span class="version-badge">ACTIVE</span>' : ''}
                        <span>•</span>
                        <span>${new Date(term.updated_at).toLocaleString()}</span>
                        <span>•</span>
                        <span>By: ${term.updated_by || 'Unknown'}</span>
                    </div>
                    <div class="version-actions">
                        <button class="btn btn-sm btn-secondary" onclick="loadTermsVersion(${term.id})">Load</button>
                        ${!term.is_active ? `<button class="btn btn-sm btn-primary" onclick="activateTermsVersion(${term.id})">Activate</button>` : ''}
                        ${!term.is_active ? `<button class="btn btn-sm btn-danger" onclick="deleteTermsVersion(${term.id})">Delete</button>` : ''}
                    </div>
                </div>
                <div class="version-content">
                    <strong>${term.title}</strong>
                    <div style="margin-top: 10px; color: #586069; font-size: 12px;">
                        ${term.content.substring(0, 200)}...
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        versionList.innerHTML = '<p>No versions found</p>';
    }
}

/**
 * Close version history modal
 */
function closeVersionHistoryModal() {
    document.getElementById('versionHistoryModal').style.display = 'none';
}

/**
 * Load a specific version
 */
async function loadTermsVersion(termId) {
    const language = currentTermsLanguage;
    const result = await api(`/api/admin/signup-terms?language=${language}`);
    
    if (result.status === 'success') {
        const term = result.terms.find(t => t.id === termId);
        if (term) {
            loadSignupTermsIntoEditor(term);
            closeVersionHistoryModal();
        }
    }
}

/**
 * Activate a specific version
 */
async function activateTermsVersion(termId) {
    if (!confirm('Are you sure you want to activate this version? It will deactivate the current version.')) {
        return;
    }
    
    const result = await api(`/api/admin/signup-terms/${termId}/activate`, {
        method: 'PUT'
    });
    
    if (result.status === 'success') {
        alert('Version activated successfully!');
        showTermsVersionHistory(); // Refresh the list
        loadSignupTermsByLanguage(); // Reload current view
    } else {
        alert('Error: ' + result.message);
    }
}

/**
 * Delete a specific version
 */
async function deleteTermsVersion(termId) {
    if (!confirm('Are you sure you want to delete this version? This cannot be undone.')) {
        return;
    }
    
    const result = await api(`/api/admin/signup-terms/${termId}`, {
        method: 'DELETE'
    });
    
    if (result.status === 'success') {
        alert('Version deleted successfully!');
        showTermsVersionHistory(); // Refresh the list
    } else {
        alert('Error: ' + result.message);
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('versionHistoryModal');
    if (modal && e.target === modal) {
        closeVersionHistoryModal();
    }
});
