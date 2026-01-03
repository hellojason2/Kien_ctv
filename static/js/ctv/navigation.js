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
    if (page === 'clients' && typeof switchToCardView === 'function') {
        switchToCardView();
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
    
    // Mobile menu button
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
    
    // Set initial active state
    const activePage = document.querySelector('.page-section.active');
    if (activePage) {
        const pageId = activePage.id.replace('page-', '');
        navigateToPage(pageId);
    }
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

