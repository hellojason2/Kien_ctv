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
    const adminLangSwitcher = document.getElementById('adminLangSwitcher');
    const mobileToggle = document.getElementById('adminMobileLangToggle');
    // Mobile CSS expects .mobile-menu-lang.active .mobile-lang-popup, so we toggle parent
    const mobileContainer = mobileToggle ? mobileToggle.closest('.mobile-menu-lang') : null;

    // NEW: Header Language Switcher
    const headerLangSwitcher = document.getElementById('adminHeaderLangSwitcher');

    // Desktop Toggle
    if (adminLangSwitcher) {
        const toggleBtn = adminLangSwitcher.querySelector('.sidebar-icon');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                adminLangSwitcher.classList.toggle('active');
            });
        }
    }

    // Mobile Menu Toggle
    if (mobileToggle && mobileContainer) {
        mobileToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            mobileContainer.classList.toggle('active');
        });
    }

    // Header Language Toggle
    if (headerLangSwitcher) {
        const toggleBtn = headerLangSwitcher.querySelector('.header-lang-trigger');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                headerLangSwitcher.classList.toggle('active');
            });
        }
    }

    // Global Click (Close when clicking outside)
    document.addEventListener('click', (e) => {
        // Close Desktop
        if (adminLangSwitcher && !adminLangSwitcher.contains(e.target)) {
            adminLangSwitcher.classList.remove('active');
        }

        // Close Mobile Menu
        if (mobileContainer && !mobileContainer.contains(e.target)) {
            mobileContainer.classList.remove('active');
        }

        // Close Header Language
        if (headerLangSwitcher && !headerLangSwitcher.contains(e.target)) {
            headerLangSwitcher.classList.remove('active');
        }
    });
}

/**
 * Initialize horizontal scroll detection for sidebar collapse
 */
function initSidebarScrollCollapse() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    if (!sidebar || !mainContent) return;

    let scrollTimeout = null;
    const SCROLL_THRESHOLD = 10; // Minimum pixels scrolled to trigger collapse

    function collapseSidebar() {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }

    function expandSidebar() {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(() => {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        }, 200);
    }

    function handleScroll(e) {
        const target = e.target;
        let scrollLeft = 0;

        // Get scrollLeft from the event target (could be window, document, or an element)
        if (target === window || target === document || target === document.documentElement || target === document.body) {
            scrollLeft = window.pageXOffset || document.documentElement.scrollLeft || document.body.scrollLeft || 0;
        } else {
            scrollLeft = target.scrollLeft || 0;
        }

        // Clear any existing timeout
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }

        // If scrolling right (positive scrollLeft beyond threshold)
        if (scrollLeft > SCROLL_THRESHOLD) {
            collapseSidebar();
        } else {
            // When scrolled back to left, restore sidebar after a short delay
            expandSidebar();
        }
    }

    // Listen to scroll events on window
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Use a MutationObserver to watch for dynamically added scrollable containers
    const observer = new MutationObserver(() => {
        // Find all potentially scrollable containers
        const scrollableSelectors = [
            '.table-container',
            '.card-body',
            'table',
            '[style*="overflow-x"]',
            '[style*="overflow: auto"]',
            '[style*="overflow: scroll"]'
        ];

        scrollableSelectors.forEach(selector => {
            const elements = mainContent.querySelectorAll(selector);
            elements.forEach(el => {
                // Only add listener if not already added
                if (!el.dataset.scrollListenerAdded) {
                    el.addEventListener('scroll', handleScroll, { passive: true });
                    el.dataset.scrollListenerAdded = 'true';
                }
            });
        });
    });

    // Start observing the main content area for changes
    observer.observe(mainContent, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });

    // Initial check for existing scrollable elements
    setTimeout(() => {
        const scrollableSelectors = ['.table-container', '.card-body', 'table'];
        scrollableSelectors.forEach(selector => {
            const elements = mainContent.querySelectorAll(selector);
            elements.forEach(el => {
                el.addEventListener('scroll', handleScroll, { passive: true });
                el.dataset.scrollListenerAdded = 'true';
            });
        });
    }, 100);

    // Also check on resize in case viewport changes
    window.addEventListener('resize', () => {
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft || 0;
        if (scrollLeft <= SCROLL_THRESHOLD) {
            expandSidebar();
        }
    });
}

/**
 * Initialize sidebar collapse button click handler
 */
function initSidebarCollapseButton() {
    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.main-content');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');

    if (!sidebar || !mainContent || !collapseBtn) return;

    // Restore saved state from localStorage
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }

    // Toggle on click
    collapseBtn.addEventListener('click', () => {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('sidebar-collapsed');

        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    });
}

/**
 * Initialize all event handlers and check auth
 */
async function initializeApp() {
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

    // NOTE: Sidebar collapse is handled by navigation.js initSidebarCollapse()
    // Do NOT call initSidebarScrollCollapse() or initSidebarCollapseButton() here
    // as they conflict with the navigation.js state management

    // Initialize pending registrations badge
    initPendingRegistrationsBadge();

    // Check authentication
    checkAuth();
}

/**
 * Initialize and update the pending registrations badge
 */
async function initPendingRegistrationsBadge() {
    const badges = [
        document.getElementById('pendingRegistrationsBadge'),
        document.getElementById('pendingRegistrationsBadge_nav')
    ];

    try {
        // Fetch count from API
        const response = await fetch('/api/admin/registrations/count', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('session_token')}`
            }
        });

        if (!response.ok) return;

        const data = await response.json();
        if (data.status === 'success') {
            const count = data.count;

            badges.forEach(badge => {
                if (!badge) return;

                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            });
        }
    } catch (error) {
        console.error('Error fetching pending registrations count:', error);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Also initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

