/**
 * Admin Dashboard - Settings Module
 * Commission settings management
 * 
 * Created: December 30, 2025
 */

/**
 * Load commission settings
 */
async function loadCommissionSettings() {
    const result = await api('/api/admin/commission-settings');
    if (result.status === 'success') {
        const container = document.getElementById('commissionSettings');
        container.innerHTML = result.settings.map(s => {
            const isActive = s.is_active !== false;
            const disabledClass = isActive ? '' : 'disabled';
            return `
            <div class="commission-card l${s.level} ${disabledClass}" data-level="${s.level}">
                <div class="card-header-row">
                    <div class="level">Level ${s.level}</div>
                    <label class="toggle-switch">
                        <input type="checkbox" class="level-toggle" data-level="${s.level}" ${isActive ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="rate">${(s.rate * 100).toFixed(2)}%</div>
                <input type="number" step="0.0001" value="${s.rate}" data-level="${s.level}" placeholder="Rate" ${isActive ? '' : 'disabled'}>
            </div>
        `}).join('');

        // Disable save button initially
        const saveBtn = document.querySelector('button[onclick="saveCommissionSettings()"]');
        if (saveBtn) {
            saveBtn.disabled = true;
            
            // Enable on change for rate inputs
            container.querySelectorAll('input[type="number"]').forEach(input => {
                input.addEventListener('input', () => {
                    saveBtn.disabled = false;
                });
            });
            
            // Enable on change for toggle switches
            container.querySelectorAll('.level-toggle').forEach(toggle => {
                toggle.addEventListener('change', (e) => {
                    saveBtn.disabled = false;
                    const level = e.target.dataset.level;
                    const card = container.querySelector(`.commission-card[data-level="${level}"]`);
                    const rateInput = card.querySelector('input[type="number"]');
                    
                    if (e.target.checked) {
                        card.classList.remove('disabled');
                        rateInput.disabled = false;
                    } else {
                        card.classList.add('disabled');
                        rateInput.disabled = true;
                    }
                });
            });
        }
    }
}

/**
 * Save commission settings
 */
async function saveCommissionSettings() {
    const saveBtn = document.querySelector('button[onclick="saveCommissionSettings()"]');
    if (saveBtn) saveBtn.disabled = true;

    const container = document.getElementById('commissionSettings');
    const cards = container.querySelectorAll('.commission-card');
    
    const settings = Array.from(cards).map(card => {
        const level = parseInt(card.dataset.level);
        const rateInput = card.querySelector('input[type="number"]');
        const toggleInput = card.querySelector('.level-toggle');
        
        return {
            level: level,
            rate: parseFloat(rateInput.value),
            is_active: toggleInput ? toggleInput.checked : true
        };
    });
    
    const result = await api('/api/admin/commission-settings', {
        method: 'PUT',
        body: JSON.stringify({ settings })
    });
    
    if (result.status === 'success') {
        alert('Commission settings saved!');
        loadCommissionSettings();
    } else {
        alert('Error: ' + result.message);
        if (saveBtn) saveBtn.disabled = false;
    }
}

