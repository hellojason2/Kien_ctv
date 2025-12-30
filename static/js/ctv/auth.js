/**
 * CTV Portal - Authentication Module
 * DOES: Handles login, logout, password change, and auth checking
 * INPUTS: User credentials from login form
 * OUTPUTS: Authentication state
 * FLOW: login -> showPortal / checkAuth -> showPortal
 */

// Remember me - load saved credentials
function loadSavedCredentials() {
    const savedMaCTV = localStorage.getItem('ctv_remember_ma_ctv');
    const savedPassword = localStorage.getItem('ctv_remember_password');
    if (savedMaCTV) {
        const maCTVInput = document.getElementById('maCTV');
        const rememberMeCheck = document.getElementById('rememberMe');
        if (maCTVInput) maCTVInput.value = savedMaCTV;
        if (rememberMeCheck) rememberMeCheck.checked = true;
    }
    if (savedPassword) {
        const passwordInput = document.getElementById('password');
        if (passwordInput) passwordInput.value = savedPassword;
    }
}

// Login handler
async function handleLogin(e) {
    e.preventDefault();
    const maCTV = document.getElementById('maCTV').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    const loginBtn = document.getElementById('loginBtn');
    const loginError = document.getElementById('loginError');
    const loginForm = document.getElementById('loginForm');
    const loginSuccess = document.getElementById('loginSuccess');
    
    // Save or remove credentials based on remember me checkbox
    if (rememberMe) {
        localStorage.setItem('ctv_remember_ma_ctv', maCTV);
        localStorage.setItem('ctv_remember_password', password);
    } else {
        localStorage.removeItem('ctv_remember_ma_ctv');
        localStorage.removeItem('ctv_remember_password');
    }
    
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
    await loadRecentCommissions();
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

