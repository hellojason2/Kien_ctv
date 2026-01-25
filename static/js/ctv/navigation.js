/**
 * CTV Portal - Navigation Module
 * DOES: Handles sidebar navigation between pages and collapsible sidebar
 * INPUTS: Click events on sidebar icons
 * OUTPUTS: Page transitions and data loading
 * FLOW: User clicks -> Update active state -> Load page data
 * 
 * Updated: January 24, 2026 - Added collapsible sidebar functionality
 */

/* ═══════════════════════════════════════════════════════════════════
   SIDEBAR COLLAPSE STATE MANAGEMENT
   ═══════════════════════════════════════════════════════════════════ */

// Sidebar state - separate for mobile and desktop
let sidebarMobileOpen = false; // Mobile: starts closed
let sidebarDesktopCollapsed = localStorage.getItem('ctvSidebarCollapsed') === 'true';

/**
 * Check if currently on mobile
 */
function isMobileView() {
    return window.innerWidth <= 768;
}

/**
 * Open sidebar (mobile only)
 */
function openMobileSidebar() {
    const sidebar = document.getElementById('ctvSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    sidebarMobileOpen = true;

    if (sidebar) {
        sidebar.classList.remove('collapsed');
    }
    if (backdrop) {
        backdrop.classList.add('active');
    }
    document.body.style.overflow = 'hidden';
}

/**
 * Close sidebar (mobile only)
 */
function closeMobileSidebar() {
    const sidebar = document.getElementById('ctvSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    sidebarMobileOpen = false;

    if (sidebar) {
        sidebar.classList.add('collapsed');
    }
    if (backdrop) {
        backdrop.classList.remove('active');
    }
    document.body.style.overflow = '';
}

/**
 * Toggle sidebar collapsed state (desktop only)
 */
function toggleSidebarCollapsed() {
    // On mobile, use open/close functions instead
    if (isMobileView()) {
        if (sidebarMobileOpen) {
            closeMobileSidebar();
        } else {
            openMobileSidebar();
        }
        return;
    }

    // Desktop behavior
    const sidebar = document.getElementById('ctvSidebar');
    const mainWrapper = document.querySelector('.main-wrapper');
    const floatingHeader = document.querySelector('.floating-header');

    sidebarDesktopCollapsed = !sidebarDesktopCollapsed;

    if (sidebar) {
        sidebar.classList.toggle('collapsed', sidebarDesktopCollapsed);
    }

    if (mainWrapper) {
        mainWrapper.classList.toggle('sidebar-collapsed', sidebarDesktopCollapsed);
    }

    if (floatingHeader) {
        floatingHeader.classList.toggle('sidebar-collapsed', sidebarDesktopCollapsed);
    }

    // Persist desktop state
    localStorage.setItem('ctvSidebarCollapsed', sidebarDesktopCollapsed);
}

/**
 * Initialize sidebar state on load
 */
function initSidebarCollapse() {
    const sidebar = document.getElementById('ctvSidebar');
    const mainWrapper = document.querySelector('.main-wrapper');
    const floatingHeader = document.querySelector('.floating-header');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const backdrop = document.getElementById('sidebarBackdrop');
    const headerMenuBtn = document.getElementById('headerMenuBtn');

    // Mobile: Always start with sidebar closed (hidden)
    if (isMobileView()) {
        if (sidebar) sidebar.classList.add('collapsed');
        sidebarMobileOpen = false;
    } else {
        // Desktop: Apply saved collapsed state
        if (sidebar && sidebarDesktopCollapsed) {
            sidebar.classList.add('collapsed');
        }
        if (mainWrapper && sidebarDesktopCollapsed) {
            mainWrapper.classList.add('sidebar-collapsed');
        }
        if (floatingHeader && sidebarDesktopCollapsed) {
            floatingHeader.classList.add('sidebar-collapsed');
        }
    }

    // Desktop collapse button
    if (collapseBtn) {
        collapseBtn.addEventListener('click', toggleSidebarCollapsed);
    }

    // Mobile menu button (hamburger) - ONLY opens sidebar
    if (headerMenuBtn) {
        headerMenuBtn.addEventListener('click', openMobileSidebar);
    }

    // Backdrop click - ONLY closes sidebar
    if (backdrop) {
        backdrop.addEventListener('click', closeMobileSidebar);
    }

    // Handle window resize
    window.addEventListener('resize', handleResize);
}

/**
 * Handle window resize - adjust state appropriately
 */
function handleResize() {
    const sidebar = document.getElementById('ctvSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (isMobileView()) {
        // Switching to mobile - close sidebar if it was open from desktop
        if (!sidebarMobileOpen && sidebar) {
            sidebar.classList.add('collapsed');
        }
        // Hide backdrop if sidebar is closed
        if (!sidebarMobileOpen && backdrop) {
            backdrop.classList.remove('active');
        }
    } else {
        // Switching to desktop - apply desktop collapsed state
        if (sidebar) {
            sidebar.classList.toggle('collapsed', sidebarDesktopCollapsed);
        }
        // Always hide backdrop on desktop
        if (backdrop) {
            backdrop.classList.remove('active');
        }
        document.body.style.overflow = '';
    }
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE NAVIGATION
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Navigate to a page
 * @param {string} page - Page identifier
 */
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

    // Auto-close sidebar on mobile after navigation
    if (isMobileView() && sidebarMobileOpen) {
        closeMobileSidebar();
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

/**
 * Update page title in header
 * @param {string} page - Page identifier
 */
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

/* ═══════════════════════════════════════════════════════════════════
   NAVIGATION INITIALIZATION
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Initialize navigation
 */
function initNavigation() {
    // Initialize sidebar collapse functionality
    initSidebarCollapse();

    // Desktop sidebar navigation
    document.querySelectorAll('.sidebar-icon[data-page]').forEach(icon => {
        icon.addEventListener('click', () => {
            const page = icon.dataset.page;
            navigateToPage(page);
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
        headerMenuBtn.addEventListener('click', openMobileSidebar);
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

/* ═══════════════════════════════════════════════════════════════════
   HEADER LANGUAGE DROPDOWN
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Toggle header language dropdown
 * @param {Event} e - Click event
 */
function toggleHeaderLang(e) {
    e.stopPropagation();
    const dropdown = document.getElementById('headerLangDropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

/**
 * Close header language dropdown
 */
function closeHeaderLang() {
    const dropdown = document.getElementById('headerLangDropdown');
    if (dropdown) {
        dropdown.classList.remove('active');
    }
}

/**
 * Update header language label
 */
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

/**
 * Open mobile menu popup
 */
function openMobileMenu() {
    const popup = document.getElementById('mobileMenuPopup');
    if (popup) {
        popup.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close mobile menu popup
 */
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

// Export functions for global access
window.toggleSidebarCollapsed = toggleSidebarCollapsed;
window.openMobileSidebar = openMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;
window.navigateToPage = navigateToPage;
