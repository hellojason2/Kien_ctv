/**
 * CTV Portal - Phone Check Module
 * DOES: Checks for duplicate phone numbers in the system
 * INPUTS: Phone number from dashboard input
 * OUTPUTS: Display duplicate/not duplicate result
 * FLOW: checkPhonePortal -> API call -> Display result
 */

// Phone check in portal dashboard
async function checkPhonePortal() {
    const input = document.getElementById('dashPhoneInput');
    const result = document.getElementById('dashPhoneResult');
    const phone = input.value.trim();
    
    if (!phone || phone.length < 9) {
        result.textContent = t('phone_short');
        result.className = 'result';
        result.style.display = 'block';
        result.style.background = '#fef3c7';
        result.style.color = '#d97706';
        return;
    }
    
    try {
        const response = await api('/api/ctv/check-phone', {
            method: 'POST',
            body: JSON.stringify({ phone })
        });
        
        if (response.is_duplicate) {
            result.textContent = t('duplicate');
            result.className = 'result trung';
        } else {
            result.textContent = t('not_duplicate');
            result.className = 'result khong-trung';
        }
        result.style.display = 'block';
    } catch (error) {
        result.textContent = 'Error';
        result.style.display = 'block';
    }
}

// Initialize phone check events
function initPhoneCheck() {
    const phoneInput = document.getElementById('dashPhoneInput');
    if (phoneInput) {
        phoneInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') checkPhonePortal();
        });
    }
}

