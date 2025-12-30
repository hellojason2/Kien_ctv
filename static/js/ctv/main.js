/**
 * CTV Portal - Main Entry Point
 * DOES: Initializes all modules and sets up global event listeners
 * FLOW: DOMContentLoaded -> Initialize all modules -> Check auth
 * 
 * ══════════════════════════════════════════════════════════════
 * MODULE LOAD ORDER:
 * 1. api.js        - API helper and state
 * 2. utils.js      - Utility functions
 * 3. translations.js - i18n system
 * 4. auth.js       - Authentication
 * 5. navigation.js - Page navigation
 * 6. profile.js    - Profile loading
 * 7. commissions.js - Commission data
 * 8. network.js    - MLM tree
 * 9. phone-check.js - Phone validation
 * 10. clients.js   - Client cards
 * 11. main.js      - This file (initialization)
 * ══════════════════════════════════════════════════════════════
 */

// Initialize language on page load
function initLanguage() {
    setLanguage(getCurrentLang());
    
    // Setup language switcher click handler
    const langSwitcher = document.getElementById('langSwitcher');
    if (langSwitcher) {
        const langIcon = langSwitcher.querySelector('.sidebar-icon');
        if (langIcon) {
            langIcon.addEventListener('click', toggleLangPopup);
        }
    }
    
    // Setup login page language toggle
    const loginLangBtn = document.querySelector('.login-lang-btn');
    if (loginLangBtn) {
        loginLangBtn.addEventListener('click', toggleLoginLangPopup);
    }
}

// Close popups when clicking outside
function initPopupClose() {
    document.addEventListener('click', (e) => {
        const switcher = document.getElementById('langSwitcher');
        const loginToggle = document.getElementById('loginLangToggle');
        
        if (switcher && !switcher.contains(e.target)) {
            switcher.classList.remove('active');
        }
        if (loginToggle && !loginToggle.contains(e.target)) {
            loginToggle.classList.remove('active');
        }
    });
}

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    initLanguage();
    initPopupClose();
    initAuth();
    initNavigation();
    initPhoneCheck();
    initClientSearch();
    
    // Check authentication status
    checkAuth();
});

