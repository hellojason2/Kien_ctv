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
    const currentLang = getCurrentLang();
    
    // Initialize active state for language options before setting language
    // This ensures only one option is active at a time
    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.classList.remove('active');
        if (opt.dataset.lang === currentLang) {
            opt.classList.add('active');
        }
    });
    
    // Also initialize mobile language options
    document.querySelectorAll('.mobile-lang-popup .lang-option').forEach(opt => {
        opt.classList.remove('active');
        if (opt.dataset.lang === currentLang) {
            opt.classList.add('active');
        }
    });
    
    setLanguage(currentLang);
    
    // Setup language switcher click handler (desktop)
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
    
    // Update mobile language label when language changes
    const updateMobileLangLabel = () => {
        const mobileLabel = document.getElementById('mobileCurrentLangLabel');
        if (mobileLabel) {
            const currentLang = getCurrentLang();
            mobileLabel.textContent = currentLang ? currentLang.toUpperCase() : 'VI';
        }
    };
    
    // Update on language change
    const originalSetLanguage = window.setLanguage;
    if (originalSetLanguage) {
        window.setLanguage = function(lang) {
            originalSetLanguage(lang);
            updateMobileLangLabel();
        };
    }
    
    updateMobileLangLabel();
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
document.addEventListener('DOMContentLoaded', async function() {
    // Load commission labels first
    if (typeof loadCommissionLabels === 'function') {
        await loadCommissionLabels();
    }
    
    // Validate database schema first (10 second timeout)
    if (typeof initDatabaseValidation === 'function') {
        const dbValid = await initDatabaseValidation();
        if (!dbValid) {
            console.error('Database validation failed - app initialization halted');
            return; // Stop initialization if database is invalid
        }
    }
    
    // Initialize all modules
    initLanguage();
    initPopupClose();
    initAuth();
    initNavigation();
    initPhoneCheck();
    initClientSearch();
    
    // Initialize dashboard date filter
    if (typeof initDashboardDateFilter === 'function') {
        initDashboardDateFilter();
    }
    
    // Initialize data indicators with current config
    if (typeof updateAllIndicators === 'function') {
        // Wait a bit for page to render, then update indicators
        setTimeout(() => {
            updateAllIndicators();
        }, 200);
    }
    
    // Check authentication status
    checkAuth();
});

