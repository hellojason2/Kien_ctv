/**
 * CTV Portal - Navigation Module
 * DOES: Handles sidebar navigation between pages
 * INPUTS: Click events on sidebar icons
 * OUTPUTS: Page transitions and data loading
 * FLOW: User clicks -> Update active state -> Load page data
 */

// Initialize navigation
function initNavigation() {
    document.querySelectorAll('.sidebar-icon[data-page]').forEach(icon => {
        icon.addEventListener('click', () => {
            const page = icon.dataset.page;
            
            // Update active states
            document.querySelectorAll('.sidebar-icon[data-page]').forEach(i => i.classList.remove('active'));
            icon.classList.add('active');
            
            document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
            document.getElementById(`page-${page}`).classList.add('active');
            
            // Load page data
            if (page === 'earnings') {
                setEarningsDefaultDateFilter();
                filterCommissions();
            }
            if (page === 'network') loadNetwork();
            if (page === 'clients') {
                switchToCardView();
            }
        });
    });
}

