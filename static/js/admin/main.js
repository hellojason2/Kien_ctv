/**
 * Admin Dashboard - Main Entry Point
 * Initialization and event wiring
 * 
 * Created: December 30, 2025
 */

/**
 * Generic export to Excel function
 * @param {string} endpoint - Export endpoint
 */
function exportToExcel(endpoint) {
    const token = localStorage.getItem('session_token');
    window.open(`${endpoint}?token=${token}`, '_blank');
}

/**
 * Initialize popup close handler for clicking outside
 */
function initPopupCloseHandlers() {
    document.addEventListener('click', (e) => {
        const langSwitcher = document.getElementById('langSwitcher');
        if (langSwitcher && !langSwitcher.contains(e.target)) {
            langSwitcher.classList.remove('active');
        }
    });
}

/**
 * Initialize all event handlers and check auth
 */
function initializeApp() {
    // Initialize language
    initLanguage();
    
    // Initialize popup close handlers
    initPopupCloseHandlers();
    
    // Initialize navigation
    initNavigation();
    
    // Initialize login form
    initLoginForm();
    
    // Initialize logout
    initLogout();
    
    // Initialize CTV search
    initCTVSearch();
    
    // Initialize client search
    initClientSearch();
    
    // Initialize commission filters
    initCommissionFilters();
    
    // Check authentication
    checkAuth();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Also initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

