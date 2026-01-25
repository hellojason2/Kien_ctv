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
    const loginPage = document.getElementById('loginPage');
    const dashboard = document.getElementById('dashboard');

    console.log('showDashboard called', { loginPage, dashboard });

    if (loginPage) {
        loginPage.style.display = 'none';
    }

    if (dashboard) {
        dashboard.classList.add('active');
    }

    // Hide language toggle when dashboard is active
    const langToggle = document.querySelector('.lang-toggle');
    if (langToggle) langToggle.style.display = 'none';

    // Initialize overview page if it exists
    if (typeof initOverview === 'function') {
        initOverview();
    } else {
        await loadStats();
    }
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
/**
 * Initialize logout handler
 */
function initLogout() {
    const handleLogout = async (e, skipApi = false) => {
        if (e && e.preventDefault) e.preventDefault();

        if (!skipApi) {
            try {
                await api('/admin89/logout', { method: 'POST' });
            } catch (err) {
                console.warn('Logout API failed, continuing with local logout', err);
            }
        }

        setAuthToken(null);

        const loginPage = document.getElementById('loginPage');
        const dashboard = document.getElementById('dashboard');

        if (loginPage) loginPage.style.display = 'flex';
        if (dashboard) dashboard.classList.remove('active');

        // Show language toggle again on logout
        const langToggle = document.querySelector('.lang-toggle');
        if (langToggle) langToggle.style.display = 'flex';

        // Clear any open modals or overlays
        document.querySelectorAll('.modal-overlay, .mobile-menu-popup').forEach(el => {
            el.classList.remove('active');
            el.style.display = '';
        });
        document.body.style.overflow = '';
    };

    // Desktop Logout
    const logoutBtn = document.getElementById('adminLogoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);

    // Mobile Logout
    const mobileLogoutBtn = document.getElementById('adminMobileLogoutBtn');
    if (mobileLogoutBtn) mobileLogoutBtn.addEventListener('click', handleLogout);

    // Legacy/Fallback Logout
    const legacyBtn = document.getElementById('logoutBtn');
    if (legacyBtn) legacyBtn.addEventListener('click', handleLogout);

    // Listen for 401 Unauthorized events from api.js
    window.addEventListener('auth:unauthorized', () => {
        // Only trigger if we are currently logged in (dashboard is active)
        if (document.getElementById('dashboard').classList.contains('active')) {
            handleLogout(null, true); // Skip API call as session is already dead
        }
    });
}

