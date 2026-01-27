/**
 * TMV Tam Pricing Page - JavaScript
 * Handles navigation, collapse/expand, mobile interactions, and auto-refresh
 */

// Track last update time
let lastUpdateTime = new Date();

document.addEventListener('DOMContentLoaded', function () {
    initCategoryNavigation();
    initScrollSpy();
    initScrollToTop();
    initMobileSidebar();
    initCollapsibleSections();
    initAutoRefresh();
    updateLastUpdatedBadge();
});

/**
 * Auto-Refresh - Reload page every 30 seconds to get fresh data
 */
function initAutoRefresh() {
    const REFRESH_INTERVAL = 30000; // 30 seconds

    // Update the badge immediately
    updateLastUpdatedBadge();

    // Set up countdown and refresh
    setInterval(function () {
        refreshPricingData();
    }, REFRESH_INTERVAL);

    // Update the badge every second for live countdown
    setInterval(function () {
        updateLastUpdatedBadge();
    }, 1000);
}

/**
 * Refresh pricing data by reloading the page
 */
function refreshPricingData() {
    const badge = document.getElementById('lastUpdatedBadge');
    if (badge) {
        badge.classList.add('syncing');
    }

    // Save scroll position
    const scrollPos = window.scrollY;
    sessionStorage.setItem('pricingScrollPos', scrollPos);

    // Reload the page to get fresh data
    location.reload();
}

/**
 * Update the last updated badge with current time
 */
function updateLastUpdatedBadge() {
    const badge = document.getElementById('lastUpdatedBadge');
    const timeSpan = document.getElementById('updateTime');

    if (!timeSpan) return;

    // Calculate seconds since page load
    const now = new Date();
    const secondsSinceUpdate = Math.floor((now - lastUpdateTime) / 1000);
    const secondsUntilRefresh = 30 - (secondsSinceUpdate % 30);

    // Format as time ago
    if (secondsSinceUpdate < 60) {
        timeSpan.textContent = `${secondsSinceUpdate}s`;
    } else {
        const minutes = Math.floor(secondsSinceUpdate / 60);
        timeSpan.textContent = `${minutes}m`;
    }

    // Show countdown indicator when close to refresh
    if (secondsUntilRefresh <= 5) {
        badge.classList.add('syncing');
    } else {
        badge.classList.remove('syncing');
    }
}

/**
 * Restore scroll position after reload
 */
window.addEventListener('load', function () {
    const savedPos = sessionStorage.getItem('pricingScrollPos');
    if (savedPos) {
        window.scrollTo(0, parseInt(savedPos));
        sessionStorage.removeItem('pricingScrollPos');
    }
});

/**
 * Category Navigation - Smooth scroll to sections
 */
function initCategoryNavigation() {
    const categoryLinks = document.querySelectorAll('.category-link');

    categoryLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');

            // Skip if it's an external link (not starting with #)
            if (!href.startsWith('#')) {
                return;
            }

            e.preventDefault();

            const targetId = href.substring(1);
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                // Calculate offset (minimal since no header)
                const targetPosition = targetSection.offsetTop - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Close mobile sidebar if open
                closeMobileSidebar();
            }
        });
    });
}

/**
 * Scroll Spy - Highlight active category on scroll
 */
function initScrollSpy() {
    const sections = document.querySelectorAll('.pricing-section');
    const categoryLinks = document.querySelectorAll('.category-link[data-category]');

    function updateActiveLink() {
        let currentSection = '';
        const scrollPosition = window.scrollY + 100;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;

            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });

        categoryLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-category') === currentSection) {
                link.classList.add('active');
            }
        });
    }

    // Throttle scroll event for performance
    let ticking = false;
    window.addEventListener('scroll', function () {
        if (!ticking) {
            window.requestAnimationFrame(function () {
                updateActiveLink();
                ticking = false;
            });
            ticking = true;
        }
    });

    // Initial call
    updateActiveLink();
}

/**
 * Scroll to Top Button
 */
function initScrollToTop() {
    const scrollTopBtn = document.getElementById('scrollTopBtn');

    window.addEventListener('scroll', function () {
        if (window.scrollY > 500) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Mobile Sidebar Toggle
 */
function initMobileSidebar() {
    const toggleBtn = document.getElementById('mobileCategoryToggle');
    const sidebar = document.getElementById('pricingSidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.add('open');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeMobileSidebar);
    }
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('pricingSidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (sidebar) {
        sidebar.classList.remove('open');
    }
    if (overlay) {
        overlay.classList.remove('active');
    }
    document.body.style.overflow = '';
}

/**
 * Collapsible Sections
 */
function initCollapsibleSections() {
    // All sections start expanded by default
}

function toggleSection(header) {
    const section = header.closest('.pricing-section');
    const content = section.querySelector('.section-content');

    header.classList.toggle('collapsed');
    content.classList.toggle('collapsed');
}

/**
 * Utility: Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Format price for display (utility for future dynamic use)
 */
function formatPrice(amount) {
    return new Intl.NumberFormat('vi-VN').format(amount) + 'đ';
}
