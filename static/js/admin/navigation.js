/**
 * Admin Dashboard - Navigation Module
 * Sidebar navigation, page switching, collapsible groups, and responsive behavior
 * 
 * Created: December 30, 2025
 * Updated: January 24, 2026 - Collapsible Sidebar with Animations
 */

/* ═══════════════════════════════════════════════════════════════════
   STATE MANAGEMENT
   ═══════════════════════════════════════════════════════════════════ */

// Sidebar state
let sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

// Expanded groups state (persisted)
let expandedGroups = JSON.parse(localStorage.getItem('expandedGroups') || '{}');

/**
 * Get current active page from URL or DOM
 */
function getCurrentActivePage() {
    const activeLink = document.querySelector('.sidebar-nav a.active[data-page]');
    return activeLink ? activeLink.dataset.page : 'overview';
}

/* ═══════════════════════════════════════════════════════════════════
   SIDEBAR COLLAPSE FUNCTIONALITY
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Toggle sidebar collapsed state
 */
function toggleSidebarCollapsed() {
    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.main-content');
    const backdrop = document.getElementById('sidebarBackdrop');

    sidebarCollapsed = !sidebarCollapsed;

    if (sidebar) {
        sidebar.classList.toggle('collapsed', sidebarCollapsed);
    }

    if (mainContent) {
        mainContent.classList.toggle('sidebar-collapsed', sidebarCollapsed);
    }

    if (backdrop) {
        backdrop.classList.toggle('active', !sidebarCollapsed && window.innerWidth < 640);
    }

    // Persist state (only on desktop)
    if (window.innerWidth >= 640) {
        localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
    }
}

/**
 * Initialize sidebar collapse state on load
 */
function initSidebarCollapse() {
    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.main-content');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const backdrop = document.getElementById('sidebarBackdrop');

    // On mobile, always start collapsed
    if (window.innerWidth < 640) {
        sidebarCollapsed = true;
    }

    // Apply initial state
    if (sidebar && sidebarCollapsed) {
        sidebar.classList.add('collapsed');
    }

    if (mainContent && sidebarCollapsed) {
        mainContent.classList.add('sidebar-collapsed');
    }

    // Collapse button click handler
    if (collapseBtn) {
        collapseBtn.addEventListener('click', toggleSidebarCollapsed);
    }

    // Backdrop click handler (close sidebar on mobile)
    if (backdrop) {
        backdrop.addEventListener('click', () => {
            if (!sidebarCollapsed) {
                toggleSidebarCollapsed();
            }
        });
    }

    // Handle window resize
    window.addEventListener('resize', handleResize);
}

/**
 * Handle window resize for responsive behavior
 */
function handleResize() {
    const backdrop = document.getElementById('sidebarBackdrop');

    // On desktop, hide backdrop
    if (window.innerWidth >= 640 && backdrop) {
        backdrop.classList.remove('active');
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
    if (window.innerWidth < 640 && !sidebarCollapsed) {
        toggleSidebarCollapsed();
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

/* ═══════════════════════════════════════════════════════════════════
   MOBILE MENU TOGGLE (for header hamburger if needed)
   ═══════════════════════════════════════════════════════════════════ */

/**
 * Open sidebar on mobile
 */
function openMobileSidebar() {
    if (sidebarCollapsed) {
        toggleSidebarCollapsed();
    }
}

/**
 * Close sidebar on mobile
 */
function closeMobileSidebar() {
    if (!sidebarCollapsed && window.innerWidth < 640) {
        toggleSidebarCollapsed();
    }
}

// Export functions for global access
window.toggleSidebarCollapsed = toggleSidebarCollapsed;
window.openMobileSidebar = openMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;
window.navigateTo = navigateTo;
