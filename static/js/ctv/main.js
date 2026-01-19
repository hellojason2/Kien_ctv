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
    initBooking();
    
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

/**
 * Copy referral link to clipboard
 * Generates a signup link with the CTV's phone number as referrer
 */
function copyReferralLink() {
    // Get the CTV's phone number from state
    const ctvPhone = window.ctvPhone || localStorage.getItem('ctv_phone');
    
    if (!ctvPhone) {
        showToast(t('login_failed') || 'Please login first', 'error');
        return;
    }
    
    // Generate the referral link
    const baseUrl = window.location.origin;
    const referralLink = `${baseUrl}/ctv/signup?ref=${encodeURIComponent(ctvPhone)}`;
    
    // Copy to clipboard
    navigator.clipboard.writeText(referralLink).then(() => {
        showToast(t('referral_link_copied') || 'Referral link copied!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = referralLink;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast(t('referral_link_copied') || 'Referral link copied!', 'success');
        } catch (e) {
            showToast('Failed to copy link', 'error');
        }
        document.body.removeChild(textArea);
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Remove existing toast if any
    const existingToast = document.querySelector('.referral-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `referral-toast referral-toast-${type}`;
    toast.innerHTML = `
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            ${type === 'success' 
                ? '<path d="M20 6L9 17l-5-5"></path>' 
                : '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>'
            }
        </svg>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

