/**
 * Admin Dashboard - Navigation Module
 * Sidebar navigation and page switching
 * 
 * Created: December 30, 2025
 */

/**
 * Navigate to a page section
 * @param {string} page - Page name (overview, ctv, hierarchy, etc.)
 */
function navigateTo(page) {
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
    document.querySelector(`.sidebar-nav a[data-page="${page}"]`).classList.add('active');
    
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    
    // Load page-specific data
    if (page === 'overview') {
        if (typeof initOverview === 'function') {
            initOverview();
        } else {
            loadStats();
        }
    }
    if (page === 'ctv') loadCTVList();
    if (page === 'registrations') loadRegistrations();
    if (page === 'commissions') loadCommissions();
    if (page === 'settings') loadCommissionSettings();
    if (page === 'signup-terms') loadSignupTermsByLanguage();
    if (page === 'clients') loadClientsWithServices();
    if (page === 'activity-logs') {
        loadActivityLogs(1);
        loadActivityStats();
    }
}

/**
 * Initialize navigation event listeners
 */
function initNavigation() {
    document.querySelectorAll('.sidebar-nav a[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            navigateTo(page);
        });
    });
}

