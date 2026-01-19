/**
 * CTV Portal - Navigation Module
 * DOES: Handles sidebar navigation between pages
 * INPUTS: Click events on sidebar icons
 * OUTPUTS: Page transitions and data loading
 * FLOW: User clicks -> Update active state -> Load page data
 */

// Navigate to a page
function navigateToPage(page) {
    // Update active states in sidebar
    document.querySelectorAll('.sidebar-icon[data-page]').forEach(i => i.classList.remove('active'));
    const sidebarIcon = document.querySelector(`.sidebar-icon[data-page="${page}"]`);
    if (sidebarIcon) sidebarIcon.classList.add('active');
    
    // Update active states in mobile menu
    document.querySelectorAll('.mobile-menu-item[data-page]').forEach(i => i.classList.remove('active'));
    const menuItem = document.querySelector(`.mobile-menu-item[data-page="${page}"]`);
    if (menuItem) menuItem.classList.add('active');
    
    // Update page sections
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    const pageSection = document.getElementById(`page-${page}`);
    if (pageSection) pageSection.classList.add('active');
    
    // Update page title in header
    updatePageTitle(page);
    
    // Re-apply translations to ensure all text is in the correct language
    if (typeof applyTranslations === 'function') {
        applyTranslations();
    }
    
    // Load page data
    if (page === 'dashboard') {
        if (typeof loadLifetimeStats === 'function') loadLifetimeStats();
    }
    if (page === 'earnings') {
        if (typeof initEarnings === 'function') initEarnings();
    }
    if (page === 'network' && typeof loadNetwork === 'function') loadNetwork();
    if (page === 'clients') {
        if (typeof switchToCardView === 'function') {
            switchToCardView();
        }
        // Initialize search when clients page is shown
        if (typeof initClientSearch === 'function') {
            initClientSearch();
        }
    }
    if (page === 'booking' && typeof updateBookingReferrerPhone === 'function') {
        updateBookingReferrerPhone();
    }
}

// Update page title in header
function updatePageTitle(page) {
    const pageTitleEl = document.getElementById('headerPageTitle');
    if (!pageTitleEl) return;
    
    // Map page IDs to translation keys
    const pageTitleMap = {
        'dashboard': 'page_overview',
        'earnings': 'page_earnings',
        'network': 'page_network',
        'clients': 'page_customers',
        'booking': 'page_booking',
        'settings': 'page_settings'
    };
    
    const translationKey = pageTitleMap[page];
    if (translationKey && typeof t === 'function') {
        pageTitleEl.textContent = t(translationKey);
    } else {
        pageTitleEl.textContent = '';
    }
}

// Initialize navigation
function initNavigation() {
    // Desktop sidebar navigation
    document.querySelectorAll('.sidebar-icon[data-page]').forEach(icon => {
        icon.addEventListener('click', () => {
            const page = icon.dataset.page;
            navigateToPage(page);
            closeMobileMenu();
        });
    });
    
    // Mobile menu navigation
    document.querySelectorAll('.mobile-menu-item[data-page]').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            navigateToPage(page);
            closeMobileMenu();
        });
    });
    
    // Header action buttons (booking button in floating header)
    document.querySelectorAll('.header-action-btn[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            navigateToPage(page);
        });
    });
    
    // Header menu button (mobile)
    const headerMenuBtn = document.getElementById('headerMenuBtn');
    if (headerMenuBtn) {
        headerMenuBtn.addEventListener('click', openMobileMenu);
    }
    
    // Mobile menu button (legacy)
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', openMobileMenu);
    }
    
    // Mobile menu close button
    const mobileMenuClose = document.getElementById('mobileMenuClose');
    if (mobileMenuClose) {
        mobileMenuClose.addEventListener('click', closeMobileMenu);
    }
    
    // Mobile menu overlay
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', closeMobileMenu);
    }
    
    // Mobile logout button
    const mobileLogoutBtn = document.getElementById('mobileLogoutBtn');
    if (mobileLogoutBtn) {
        mobileLogoutBtn.addEventListener('click', () => {
            if (typeof handleLogout === 'function') {
                handleLogout();
            }
            closeMobileMenu();
        });
    }
    
    // Mobile language toggle
    const mobileLangToggle = document.getElementById('mobileLangToggle');
    if (mobileLangToggle) {
        mobileLangToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const langMenu = document.querySelector('.mobile-menu-lang');
            if (langMenu) {
                langMenu.classList.toggle('active');
            }
        });
    }
    
    // Close header language dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const langDropdown = document.getElementById('headerLangDropdown');
        const langBtn = document.getElementById('headerLangBtn');
        if (langDropdown && langBtn && !langBtn.contains(e.target) && !langDropdown.contains(e.target)) {
            langDropdown.classList.remove('active');
        }
    });
    
    // Set initial active state
    const activePage = document.querySelector('.page-section.active');
    if (activePage) {
        const pageId = activePage.id.replace('page-', '');
        navigateToPage(pageId);
    }
    
    // Update header language label on init
    updateHeaderLangLabel();
}

// Toggle header language dropdown
function toggleHeaderLang(e) {
    e.stopPropagation();
    const dropdown = document.getElementById('headerLangDropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

// Close header language dropdown
function closeHeaderLang() {
    const dropdown = document.getElementById('headerLangDropdown');
    if (dropdown) {
        dropdown.classList.remove('active');
    }
}

// Update header language label
function updateHeaderLangLabel() {
    const label = document.getElementById('headerLangLabel');
    if (label && typeof currentLang !== 'undefined') {
        label.textContent = currentLang.toUpperCase();
    }
    
    // Update active state on language options
    document.querySelectorAll('.header-lang-dropdown .lang-option').forEach(opt => {
        if (opt.dataset.lang === currentLang) {
            opt.classList.add('active');
        } else {
            opt.classList.remove('active');
        }
    });
}

// Open mobile menu
function openMobileMenu() {
    const popup = document.getElementById('mobileMenuPopup');
    if (popup) {
        popup.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

// Close mobile menu
function closeMobileMenu() {
    const popup = document.getElementById('mobileMenuPopup');
    if (popup) {
        popup.classList.remove('active');
        document.body.style.overflow = '';
    }
    // Close language popup if open
    const langMenu = document.querySelector('.mobile-menu-lang');
    if (langMenu) {
        langMenu.classList.remove('active');
    }
}

