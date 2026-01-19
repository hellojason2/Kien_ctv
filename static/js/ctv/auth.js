/**
 * CTV Portal - Authentication Module
 * DOES: Handles login, logout, password change, and auth checking
 * INPUTS: User credentials from login form
 * OUTPUTS: Authentication state
 * FLOW: login -> showPortal / checkAuth -> showPortal
 */

// Auto-load saved credentials from localStorage
function loadSavedCredentials() {
    const savedMaCTV = localStorage.getItem('ctv_saved_phone');
    const savedPassword = localStorage.getItem('ctv_saved_password');
    
    // Always load saved credentials if they exist
    if (savedMaCTV) {
        const maCTVInput = document.getElementById('maCTV');
        if (maCTVInput) maCTVInput.value = savedMaCTV;
    }
    if (savedPassword) {
        const passwordInput = document.getElementById('password');
        if (passwordInput) passwordInput.value = savedPassword;
    }
    
    // Check the remember me box by default if credentials exist
    const rememberMeCheck = document.getElementById('rememberMe');
    if (rememberMeCheck && (savedMaCTV || savedPassword)) {
        rememberMeCheck.checked = true;
    }
}

// Login handler
async function handleLogin(e) {
    e.preventDefault();
    const maCTV = document.getElementById('maCTV').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('loginBtn');
    const loginError = document.getElementById('loginError');
    const loginForm = document.getElementById('loginForm');
    const loginSuccess = document.getElementById('loginSuccess');
    
    loginBtn.disabled = true;
    loginBtn.textContent = t('logging_in');
    loginError.classList.remove('show');
    
    const result = await api('/ctv/login', {
        method: 'POST',
        body: JSON.stringify({ ma_ctv: maCTV, password })
    });
    
    if (result.status === 'success') {
        setAuthToken(result.token);
        localStorage.setItem('ctvToken', result.token);
        setCurrentUser(result.ctv);
        
        // Always save credentials after successful login for convenience
        // This auto-fills the form next time user visits
        localStorage.setItem('ctv_saved_phone', maCTV);
        localStorage.setItem('ctv_saved_password', password);
        
        // Show success animation
        loginForm.style.display = 'none';
        loginSuccess.classList.add('show');
        
        // Wait then show portal
        setTimeout(() => {
            showPortal();
        }, 1500);
    } else {
        loginError.textContent = result.message || t('login_failed');
        loginError.classList.add('show');
        loginBtn.disabled = false;
        loginBtn.textContent = t('login');
    }
}

// Logout handler
async function handleLogout() {
    await api('/ctv/logout', { method: 'POST' });
    setAuthToken(null);
    setCurrentUser(null);
    localStorage.removeItem('ctvToken');
    
    // Redirect to main dashboard
    window.location.href = '/';
}

// Change Password handler
async function handleChangePassword(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorEl = document.getElementById('changePasswordError');
    const successEl = document.getElementById('changePasswordSuccess');
    const submitBtn = document.getElementById('changePasswordBtn');
    
    // Reset messages
    errorEl.classList.remove('show');
    errorEl.textContent = '';
    successEl.style.display = 'none';
    successEl.textContent = '';
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        errorEl.textContent = t('password_mismatch');
        errorEl.classList.add('show');
        return;
    }
    
    // Validate length
    if (newPassword.length < 6) {
        errorEl.textContent = t('password_too_short');
        errorEl.classList.add('show');
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = t('loading');
    
    const result = await api('/api/ctv/change-password', {
        method: 'POST',
        body: JSON.stringify({ 
            current_password: currentPassword, 
            new_password: newPassword 
        })
    });
    
    if (result.status === 'success') {
        successEl.textContent = t('password_changed');
        successEl.style.display = 'block';
        // Clear form
        document.getElementById('changePasswordForm').reset();
    } else {
        errorEl.textContent = result.message || t('login_failed');
        errorEl.classList.add('show');
    }
    
    submitBtn.disabled = false;
    submitBtn.textContent = t('change_password_btn');
}

// Show Portal
async function showPortal() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('portal').classList.add('active');
    await loadProfile();
    // Don't load recent commissions here - let initDashboardDateFilter handle it with date filter
    // This prevents it from loading multiple times
    // await loadRecentCommissions();
    if (typeof loadLifetimeStats === 'function') {
        await loadLifetimeStats();
    }
}

// Check Auth
async function checkAuth() {
    const token = getAuthToken();
    if (token) {
        const result = await api('/ctv/check-auth');
        if (result.authenticated) {
            showPortal();
        } else {
            setAuthToken(null);
            localStorage.removeItem('ctvToken');
        }
    }
}

// Initialize auth event listeners
function initAuth() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', handleChangePassword);
    }
    
    // Load saved credentials
    loadSavedCredentials();
}

