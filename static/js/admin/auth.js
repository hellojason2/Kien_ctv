/**
 * Admin Dashboard - Authentication Module
 * Login, logout, and auth checking
 * 
 * Created: December 30, 2025
 */

/**
 * Show the main dashboard
 */
async function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboard').classList.add('active');
    // Hide language toggle when dashboard is active
    const langToggle = document.querySelector('.lang-toggle');
    if (langToggle) langToggle.style.display = 'none';
    await loadStats();
    await loadCTVList();
    await loadCommissionSettings();
}

/**
 * Check authentication status on load
 */
async function checkAuth() {
    // Always check with server - auth might be via cookie even without localStorage token
    try {
        const result = await api('/admin89/check-auth');
        if (result.authenticated) {
            // Update authToken if we got authenticated via cookie
            if (!getAuthToken() && result.user) {
                setAuthToken(result.user.token || 'cookie-auth');
            }
            showDashboard();
        } else {
            setAuthToken(null);
        }
    } catch (e) {
        // API call failed, show login
        setAuthToken(null);
    }
}

/**
 * Initialize login form handler
 */
function initLoginForm() {
    // Load saved credentials if remember me was checked
    const savedUsername = localStorage.getItem('admin_remember_username');
    const savedPassword = localStorage.getItem('admin_remember_password');
    
    if (savedUsername && savedPassword) {
        document.getElementById('username').value = savedUsername;
        document.getElementById('password').value = savedPassword;
        const rememberMeCheck = document.getElementById('rememberMe');
        if (rememberMeCheck) rememberMeCheck.checked = true;
    }
    
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('rememberMe').checked;
        
        const result = await api('/admin89/login', {
            method: 'POST',
            body: JSON.stringify({ username, password, remember_me: rememberMe })
        });
        
        if (result.status === 'success') {
            setAuthToken(result.token);
            
            // Save or remove credentials based on remember me checkbox
            if (rememberMe) {
                localStorage.setItem('admin_remember_username', username);
                localStorage.setItem('admin_remember_password', password);
            } else {
                localStorage.removeItem('admin_remember_username');
                localStorage.removeItem('admin_remember_password');
            }
            
            showDashboard();
        } else {
            document.getElementById('loginError').textContent = result.message || 'Login failed';
        }
    });
}

/**
 * Initialize logout handler
 */
function initLogout() {
    document.getElementById('logoutBtn').addEventListener('click', async (e) => {
        e.preventDefault();
        await api('/admin89/logout', { method: 'POST' });
        setAuthToken(null);
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('dashboard').classList.remove('active');
        // Show language toggle again on logout
        const langToggle = document.querySelector('.lang-toggle');
        if (langToggle) langToggle.style.display = 'flex';
    });
}

