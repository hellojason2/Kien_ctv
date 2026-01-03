/**
 * CTV Portal - Profile Module
 * DOES: Loads and displays user profile and stats
 * INPUTS: API response from /api/ctv/me
 * OUTPUTS: Updates DOM with profile data
 * FLOW: loadProfile -> Update stats cards and user info
 */

// Current dashboard date filter state
let dashboardDateFilter = {
    preset: 'month',
    fromDate: null,
    toDate: null
};

// Show loading state on stat cards
function showStatsLoading() {
    const statCards = ['statTotalEarnings', 'statMonthlyEarnings', 'statNetworkSize', 'statMonthlyServices'];
    statCards.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = '<span class="skeleton-loader"></span>';
        }
    });
}

// Update period labels based on preset
function updatePeriodLabels(preset) {
    const periodEarningsLabel = document.getElementById('periodEarningsLabel');
    const periodServicesLabel = document.getElementById('periodServicesLabel');
    
    if (periodEarningsLabel) {
        const earningsLabels = {
            'today': t('earnings_period_today'),
            '3days': t('earnings_period_3days'),
            'week': t('earnings_period_week'),
            'month': t('earnings_period_month'),
            'lastmonth': t('earnings_period_lastmonth'),
            '3months': t('earnings_period_3months'),
            'year': t('earnings_period_year'),
            'custom': t('earnings_period_custom')
        };
        periodEarningsLabel.textContent = earningsLabels[preset] || t('earnings_period_month');
    }
    
    if (periodServicesLabel) {
        const servicesLabels = {
            'today': t('services_period_today'),
            '3days': t('services_period_3days'),
            'week': t('services_period_week'),
            'month': t('services_period_month'),
            'lastmonth': t('services_period_lastmonth'),
            '3months': t('services_period_3months'),
            'year': t('services_period_year'),
            'custom': t('services_period_custom')
        };
        periodServicesLabel.textContent = servicesLabels[preset] || t('services_period_month');
    }
}

// Load Profile with optional date filter
async function loadProfile(fromDate = null, toDate = null) {
    let url = '/api/ctv/me';
    if (fromDate && toDate) {
        url += `?from_date=${fromDate}&to_date=${toDate}`;
    }
    
    const result = await api(url);
    if (result.status === 'success') {
        setCurrentUser(result.profile);
        document.getElementById('userName').textContent = result.profile.ten;
        
        const levelBadge = document.getElementById('userLevel');
        const capBac = (result.profile.cap_bac || 'Bronze').toLowerCase();
        levelBadge.textContent = result.profile.cap_bac || 'Bronze';
        levelBadge.className = 'user-badge ' + capBac;
        
        // Update stats
        document.getElementById('statTotalEarnings').textContent = formatCurrency(result.stats.total_earnings);
        document.getElementById('statMonthlyEarnings').textContent = formatCurrency(result.stats.monthly_earnings);
        document.getElementById('statNetworkSize').textContent = result.stats.network_size;
        document.getElementById('statMonthlyServices').textContent = result.stats.monthly_services_count || 0;
    }
}

// Apply dashboard date preset
function applyDashboardPreset(preset) {
    const today = new Date();
    let fromDate, toDate;
    
    // Update active button
    document.querySelectorAll('.btn-filter-preset').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.preset === preset) {
            btn.classList.add('active');
        }
    });
    
    // Hide custom date filter if not custom
    if (preset !== 'custom') {
        document.getElementById('customDateFilter').style.display = 'none';
    }
    
    switch(preset) {
        case 'today':
            fromDate = today;
            toDate = today;
            break;
        case '3days':
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - 3);
            toDate = today;
            break;
        case 'week':
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - today.getDay()); // Start of week (Sunday)
            toDate = today;
            break;
        case 'month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = today;
            break;
        case 'lastmonth':
            fromDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            toDate = new Date(today.getFullYear(), today.getMonth(), 0); // Last day of previous month
            break;
        case '3months':
            fromDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
            toDate = today;
            break;
        case 'year':
            fromDate = new Date(today.getFullYear(), 0, 1);
            toDate = today;
            break;
        case 'custom':
            return; // Don't load, wait for custom filter
        default:
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            toDate = today;
    }
    
    dashboardDateFilter.preset = preset;
    dashboardDateFilter.fromDate = formatDateForAPI(fromDate);
    dashboardDateFilter.toDate = formatDateForAPI(toDate);
    
    // Update date inputs for reference
    const fromInput = document.getElementById('dashFromDate');
    const toInput = document.getElementById('dashToDate');
    if (fromInput) fromInput.value = dashboardDateFilter.fromDate;
    if (toInput) toInput.value = dashboardDateFilter.toDate;
    
    // Update period labels
    updatePeriodLabels(preset);
    
    // Show loading animation
    showStatsLoading();
    
    // Reload profile with date filter
    loadProfile(dashboardDateFilter.fromDate, dashboardDateFilter.toDate);
    loadRecentCommissions(dashboardDateFilter.fromDate, dashboardDateFilter.toDate);
}

// Toggle custom date filter visibility
function toggleCustomDateFilter() {
    const customFilter = document.getElementById('customDateFilter');
    const isVisible = customFilter.style.display !== 'none';
    
    // Update active button
    document.querySelectorAll('.btn-filter-preset').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.preset === 'custom') {
            btn.classList.add('active');
        }
    });
    
    customFilter.style.display = isVisible ? 'none' : 'block';
}

// Apply custom date filter
function applyCustomDateFilter() {
    const fromDate = document.getElementById('dashFromDate').value;
    const toDate = document.getElementById('dashToDate').value;
    
    if (!fromDate || !toDate) {
        alert(t('select_filter_hint'));
        return;
    }
    
    dashboardDateFilter.preset = 'custom';
    dashboardDateFilter.fromDate = fromDate;
    dashboardDateFilter.toDate = toDate;
    
    // Update period labels
    updatePeriodLabels('custom');
    
    // Show loading animation
    showStatsLoading();
    
    loadProfile(fromDate, toDate);
    loadRecentCommissions(fromDate, toDate);
}

// Format date for API (YYYY-MM-DD)
function formatDateForAPI(date) {
    return date.toISOString().split('T')[0];
}

// Initialize dashboard date filter on page load
function initDashboardDateFilter() {
    // Set default to current month
    updatePeriodLabels('month');
    applyDashboardPreset('month');
}

// Load Lifetime Statistics (all-time data)
async function loadLifetimeStats() {
    const result = await api('/api/ctv/lifetime-stats');
    if (result.status === 'success') {
        const stats = result.stats;
        
        // Update lifetime stats table
        document.getElementById('lifetimeTotalCommissions').textContent = formatCurrency(stats.total_commissions || 0);
        document.getElementById('lifetimeTotalTransactions').textContent = stats.total_transactions || 0;
        document.getElementById('lifetimeNetworkSize').textContent = stats.network_size || 0;
        document.getElementById('lifetimeDirectReferrals').textContent = stats.direct_referrals || 0;
        document.getElementById('lifetimeTotalServices').textContent = stats.total_services || 0;
        document.getElementById('lifetimeTotalRevenue').textContent = formatCurrency(stats.total_revenue || 0);
    } else {
        // Fallback: use data from profile endpoint
        const profileResult = await api('/api/ctv/me');
        if (profileResult.status === 'success') {
            document.getElementById('lifetimeTotalCommissions').textContent = formatCurrency(profileResult.stats.total_earnings || 0);
            document.getElementById('lifetimeNetworkSize').textContent = profileResult.stats.network_size || 0;
            
            // Set placeholders for other stats
            document.getElementById('lifetimeTotalTransactions').textContent = '-';
            document.getElementById('lifetimeDirectReferrals').textContent = profileResult.stats.network_by_level?.[1] || '-';
            document.getElementById('lifetimeTotalServices').textContent = '-';
            document.getElementById('lifetimeTotalRevenue').textContent = '-';
        }
    }
}

