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
        container.innerHTML = result.settings.map(s => `
            <div class="commission-card l${s.level}">
                <div class="level">Level ${s.level}</div>
                <div class="rate">${(s.rate * 100).toFixed(2)}%</div>
                <input type="number" step="0.0001" value="${s.rate}" data-level="${s.level}" placeholder="Rate">
            </div>
        `).join('');
    }
}

/**
 * Save commission settings
 */
async function saveCommissionSettings() {
    const inputs = document.querySelectorAll('#commissionSettings input');
    const settings = Array.from(inputs).map(input => ({
        level: parseInt(input.dataset.level),
        rate: parseFloat(input.value)
    }));
    
    const result = await api('/api/admin/commission-settings', {
        method: 'PUT',
        body: JSON.stringify({ settings })
    });
    
    if (result.status === 'success') {
        alert('Commission settings saved!');
        loadCommissionSettings();
    } else {
        alert('Error: ' + result.message);
    }
}

