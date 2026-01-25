/**
 * Admin Dashboard - Navigation Module
 * Sidebar navigation, page switching, collapsible groups, and responsive behavior
 * 
 * Created: December 30, 2025
 * Updated: January 25, 2026 - TG KOL Style Mobile Sidebar (matches CTV behavior)
 */

/* ═══════════════════════════════════════════════════════════════════
   STATE MANAGEMENT
   ═══════════════════════════════════════════════════════════════════ */

// Sidebar state - separate for mobile and desktop (TG KOL Style)
let sidebarMobileOpen = false; // Mobile: starts closed
let sidebarDesktopCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

// For backward compatibility
let sidebarCollapsed = sidebarDesktopCollapsed;

// Expanded groups state (persisted)
let expandedGroups = JSON.parse(localStorage.getItem('expandedGroups') || '{}');

/**
 * Check if currently on mobile
 */
function isMobileView() {
    return window.innerWidth <= 768;
}

/**
 * Get current active page from URL or DOM
 */
function getCurrentActivePage() {
    const activeLink = document.querySelector('.sidebar-nav a.active[data-page]');
    return activeLink ? activeLink.dataset.page : 'overview';
}

/* ═══════════════════════════════════════════════════════════════════
   MOBILE SIDEBAR FUNCTIONS (TG KOL STYLE)
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Open sidebar (mobile only) - TG KOL Style
 */
function openMobileSidebar() {
    const sidebar = document.getElementById('adminSidebar');
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
 * Close sidebar (mobile only) - TG KOL Style
 */
function closeMobileSidebar() {
    const sidebar = document.getElementById('adminSidebar');
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

/* ═══════════════════════════════════════════════════════════════════
   DESKTOP SIDEBAR COLLAPSE FUNCTIONALITY
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Toggle sidebar collapsed state (desktop only)
 */
function toggleSidebarCollapsed() {
    // On mobile, don't toggle - use openMobileSidebar/closeMobileSidebar instead
    if (isMobileView()) {
        return;
    }

    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.main-content');

    sidebarDesktopCollapsed = !sidebarDesktopCollapsed;
    sidebarCollapsed = sidebarDesktopCollapsed; // backward compat

    if (sidebar) {
        sidebar.classList.toggle('collapsed', sidebarDesktopCollapsed);
    }

    if (mainContent) {
        mainContent.classList.toggle('sidebar-collapsed', sidebarDesktopCollapsed);
    }

    // Persist state on desktop
    localStorage.setItem('sidebarCollapsed', sidebarDesktopCollapsed);
}

/**
 * Initialize sidebar collapse state on load
 */
function initSidebarCollapse() {
    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.main-content');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const backdrop = document.getElementById('sidebarBackdrop');
    const mobileMenuBtn = document.getElementById('adminMobileMenuBtn');

    // Mobile: Always start with sidebar closed (hidden)
    // Sidebar HTML has 'collapsed' class by default for mobile
    if (isMobileView()) {
        // Ensure collapsed on mobile
        if (sidebar) sidebar.classList.add('collapsed');
        sidebarMobileOpen = false;
    } else {
        // Desktop: Apply saved collapsed state
        // If user had it expanded, remove the default collapsed class
        if (sidebar) {
            if (sidebarDesktopCollapsed) {
                sidebar.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
            }
        }
        if (mainContent) {
            mainContent.classList.toggle('sidebar-collapsed', sidebarDesktopCollapsed);
        }
    }

    // Desktop collapse button
    if (collapseBtn) {
        collapseBtn.addEventListener('click', toggleSidebarCollapsed);
    }

    // Mobile menu button (hamburger) - ONLY opens sidebar
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', openMobileSidebar);
    }

    // Backdrop click - closes sidebar
    if (backdrop) {
        backdrop.addEventListener('click', closeMobileSidebar);
    }

    // Close button (X) inside sidebar - closes sidebar on mobile
    const closeBtn = document.getElementById('sidebarCloseBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMobileSidebar);
    }

    // Handle window resize
    window.addEventListener('resize', handleResize);
}

/**
 * Handle window resize - adjust state appropriately
 * IMPORTANT: On mobile, sidebar should NEVER auto-expand. It stays collapsed
 * until user explicitly opens it with the hamburger button.
 */
function handleResize() {
    const sidebar = document.getElementById('adminSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    const mainContent = document.querySelector('.main-content');

    if (isMobileView()) {
        // On mobile: ALWAYS keep sidebar collapsed unless explicitly opened
        // Never auto-expand based on desktop state
        if (!sidebarMobileOpen) {
            // Sidebar should be hidden
            if (sidebar) sidebar.classList.add('collapsed');
            if (backdrop) backdrop.classList.remove('active');
            document.body.style.overflow = '';
        }
        // Remove desktop-specific classes on mobile
        if (mainContent) mainContent.classList.remove('sidebar-collapsed');
    } else {
        // Switching TO desktop: apply desktop state
        // Close any mobile sidebar state first
        sidebarMobileOpen = false;
        document.body.style.overflow = '';
        if (backdrop) backdrop.classList.remove('active');

        // Apply desktop collapsed state
        if (sidebar) {
            sidebar.classList.toggle('collapsed', sidebarDesktopCollapsed);
        }
        if (mainContent) {
            mainContent.classList.toggle('sidebar-collapsed', sidebarDesktopCollapsed);
        }
    }
}

/* ═══════════════════════════════════════════════════════════════════
   NAV GROUP (DROPDOWN) FUNCTIONALITY
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Toggle a navigation group's expanded state
 * @param {string} groupId - The group identifier
 */
function toggleNavGroup(groupId) {
    const group = document.querySelector(`[data-group="${groupId}"]`);
    if (!group) return;

    // If sidebar is collapsed, don't toggle (use flyout instead)
    if (sidebarCollapsed && window.innerWidth >= 640) return;

    const isExpanded = group.classList.contains('expanded');

    if (isExpanded) {
        group.classList.remove('expanded');
        expandedGroups[groupId] = false;
    } else {
        group.classList.add('expanded');
        expandedGroups[groupId] = true;
    }

    // Persist state
    localStorage.setItem('expandedGroups', JSON.stringify(expandedGroups));
}

/**
 * Auto-expand groups that contain the active page
 */
function autoExpandActiveGroups() {
    const activePage = getCurrentActivePage();

    document.querySelectorAll('.nav-group').forEach(group => {
        const groupId = group.dataset.group;
        const hasActiveItem = group.querySelector(`[data-page="${activePage}"]`);

        if (hasActiveItem) {
            group.classList.add('expanded', 'has-active');
            expandedGroups[groupId] = true;
        } else if (expandedGroups[groupId]) {
            group.classList.add('expanded');
        }
    });

    localStorage.setItem('expandedGroups', JSON.stringify(expandedGroups));
}

/**
 * Initialize nav group event listeners
 */
function initNavGroups() {
    document.querySelectorAll('.nav-group-header').forEach(header => {
        header.addEventListener('click', (e) => {
            e.preventDefault();
            const group = header.closest('.nav-group');
            if (group) {
                toggleNavGroup(group.dataset.group);
            }
        });
    });

    // Auto-expand on page load
    autoExpandActiveGroups();
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE NAVIGATION
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Navigate to a page section
 * @param {string} page - Page name (overview, ctv, hierarchy, etc.)
 */
function navigateTo(page) {
    // Update active states in main sidebar nav
    document.querySelectorAll('.sidebar-nav a[data-page]').forEach(a => {
        a.classList.remove('active');
    });

    // Update active states in flyout menus
    document.querySelectorAll('.nav-flyout a[data-page]').forEach(a => {
        a.classList.remove('active');
    });

    // Set active on clicked item (both in nav and flyout)
    document.querySelectorAll(`[data-page="${page}"]`).forEach(el => {
        if (el.tagName === 'A') {
            el.classList.add('active');
        }
    });

    // Update has-active state on groups
    document.querySelectorAll('.nav-group').forEach(group => {
        const hasActiveChild = group.querySelector(`a.active[data-page]`);
        group.classList.toggle('has-active', !!hasActiveChild);
    });

    // Show corresponding page section
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    const pageSection = document.getElementById(`page-${page}`);
    if (pageSection) {
        pageSection.classList.add('active');
    }

    // Auto-close sidebar on mobile after navigation
    if (isMobileView() && sidebarMobileOpen) {
        closeMobileSidebar();
    }

    // Load page-specific data
    loadPageData(page);
}

/**
 * Load data for a specific page
 * @param {string} page - Page name
 */
function loadPageData(page) {
    switch (page) {
        case 'overview':
            if (typeof initOverview === 'function') {
                initOverview();
            } else if (typeof loadStats === 'function') {
                loadStats();
            }
            break;
        case 'ctv':
            if (typeof loadCTVList === 'function') loadCTVList();
            break;
        case 'registrations':
            if (typeof loadRegistrations === 'function') loadRegistrations();
            break;
        case 'commissions':
            if (typeof loadCommissions === 'function') loadCommissions();
            break;
        case 'settings':
            if (typeof loadCommissionSettings === 'function') loadCommissionSettings();
            break;
        case 'signup-terms':
            if (typeof loadSignupTermsByLanguage === 'function') loadSignupTermsByLanguage();
            break;
        case 'clients':
            if (typeof loadClientsWithServices === 'function') loadClientsWithServices();
            break;
        case 'activity-logs':
            if (typeof loadActivityLogs === 'function') loadActivityLogs(1);
            if (typeof loadActivityStats === 'function') loadActivityStats();
            break;
        case 'hierarchy':
            // Hierarchy page - may have specific init
            break;
    }
}

/**
 * Initialize navigation event listeners
 */
function initNavigation() {
    // Main sidebar nav links
    document.querySelectorAll('.sidebar-nav a[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            navigateTo(page);
        });
    });

    // Flyout menu links
    document.querySelectorAll('.nav-flyout a[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            navigateTo(page);
        });
    });

    // Initialize sidebar collapse
    initSidebarCollapse();

    // Initialize nav groups
    initNavGroups();
}

// Export functions for global access
window.toggleSidebarCollapsed = toggleSidebarCollapsed;
window.openMobileSidebar = openMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;
window.navigateTo = navigateTo;
window.isMobileView = isMobileView;
