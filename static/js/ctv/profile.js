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

// Update Recent Commissions title based on preset
function updateRecentCommissionsTitle(preset) {
    // Find the Recent Commissions header - it's the h3 inside the card-header
    const recentCommissionsCard = document.querySelector('#page-dashboard .card:nth-of-type(2) .card-header h3') ||
        document.querySelector('#page-dashboard .card-header h3[data-i18n="recent_commissions"]') ||
        document.querySelector('#page-dashboard .card-header h3');

    if (recentCommissionsCard && preset) {
        const periodLabels = {
            'today': t('today'),
            '3days': t('three_days'),
            'week': t('week'),
            'month': t('this_month'),
            'lastmonth': t('last_month'),
            '3months': t('three_months'),
            'year': t('this_year'),
            'custom': t('custom_range')
        };
        const periodLabel = periodLabels[preset] || t('this_month');
        const baseTitle = t('recent_commissions');
        // Remove data-i18n to prevent applyTranslations from overwriting
        recentCommissionsCard.removeAttribute('data-i18n');
        recentCommissionsCard.textContent = `${baseTitle} - ${periodLabel}`;
    }
}

// Update period labels based on preset
function updatePeriodLabels(preset) {
    // Update Total Earnings label (shows revenue for the period)
    // Use a selector that doesn't depend on data-i18n since we remove it
    const statsGrid = document.querySelector('#page-dashboard .stats-grid');
    const totalEarningsLabel = statsGrid ? statsGrid.querySelector('.stat-card.green .label') :
        document.querySelector('#page-dashboard .stat-card.green .label') ||
        document.querySelector('.stat-card.green .label');

    if (totalEarningsLabel) {
        const revenueLabels = {
            'today': t('total_revenue_today'),
            '3days': t('total_revenue_3days'),
            'week': t('total_revenue_week'),
            'month': t('total_revenue_month'),
            'lastmonth': t('total_revenue_lastmonth'),
            '3months': t('total_revenue_3months'),
            'year': t('total_revenue_year'),
            'custom': t('total_revenue_custom')
        };
        const labelText = revenueLabels[preset] || t('total_revenue_month');
        // Remove data-i18n to prevent applyTranslations from overwriting
        totalEarningsLabel.removeAttribute('data-i18n');
        totalEarningsLabel.textContent = labelText;
    }

    // Update Commission label (shows commission for the period)
    const periodEarningsLabel = document.getElementById('periodEarningsLabel');
    if (periodEarningsLabel) {
        const commissionLabels = {
            'today': t('commission_period_today'),
            '3days': t('commission_period_3days'),
            'week': t('commission_period_week'),
            'month': t('commission_period_month'),
            'lastmonth': t('commission_period_lastmonth'),
            '3months': t('commission_period_3months'),
            'year': t('commission_period_year'),
            'custom': t('commission_period_custom')
        };
        periodEarningsLabel.textContent = commissionLabels[preset] || t('commission_period_month');
    }

    // Update Services label
    const periodServicesLabel = document.getElementById('periodServicesLabel');
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

    // Update Recent Commissions title
    updateRecentCommissionsTitle(preset);
}

/**
 * Check which date ranges have data and show red dot indicators
 */
async function checkDashboardDateRangesWithData() {
    try {
        // Wait a bit for the page to be fully rendered
        await new Promise(resolve => setTimeout(resolve, 100));

        const result = await api('/api/ctv/date-ranges-with-data');

        if (result.status === 'success' && result.ranges_with_data) {
            const dashboardPage = document.getElementById('page-dashboard');
            if (!dashboardPage) return;

            // Update each button based on data availability
            Object.keys(result.ranges_with_data).forEach(preset => {
                const button = dashboardPage.querySelector(`.btn-filter-preset[data-preset="${preset}"]`);
                if (button) {
                    if (result.ranges_with_data[preset]) {
                        button.classList.add('has-data');
                        // Update indicator element if it exists
                        const indicator = button.querySelector('.data-indicator');
                        if (indicator && typeof updateIndicatorElement === 'function') {
                            updateIndicatorElement(indicator);
                        }
                    } else {
                        button.classList.remove('has-data');
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error checking date ranges with data:', error);
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

        // Helper to get role class based on keywords
        const getRoleClass = (role) => {
            if (!role) return 'bronze';
            const lowerRole = role.toLowerCase();

            // High level roles
            if (lowerRole.includes('giám đốc') || lowerRole.includes('director') || lowerRole.includes('ceo')) return 'director';
            if (lowerRole.includes('trưởng phòng') || lowerRole.includes('manager') || lowerRole.includes('head')) return 'manager';
            if (lowerRole.includes('trưởng nhóm') || lowerRole.includes('leader')) return 'leader';

            // Standard levels
            if (lowerRole.includes('gold')) return 'gold';
            if (lowerRole.includes('silver')) return 'silver';
            if (lowerRole.includes('bronze')) return 'bronze';

            return 'bronze'; // Default
        };

        const roleClass = getRoleClass(result.profile.cap_bac);
        levelBadge.textContent = result.profile.cap_bac || 'Bronze';
        levelBadge.className = 'user-badge ' + roleClass;

        // Update stats
        // Total Earnings card should show period revenue (total transaction revenue) for the selected date filter
        // The API always calculates period_revenue based on the date filter (or defaults to current month)
        const totalEarningsValue = (result.stats.period_revenue !== undefined && result.stats.period_revenue !== null)
            ? result.stats.period_revenue
            : (result.stats.total_earnings || 0);
        document.getElementById('statTotalEarnings').textContent = formatCurrency(totalEarningsValue);
        document.getElementById('statMonthlyEarnings').textContent = formatCurrency(result.stats.monthly_earnings);
        document.getElementById('statNetworkSize').textContent = result.stats.network_size;
        document.getElementById('statMonthlyServices').textContent = result.stats.monthly_services_count || 0;

        // Update referral badge notification (show customer count, not network size)
        const referralBadge = document.getElementById('referralBadge');
        if (referralBadge) {
            const customerCount = parseInt(result.stats.customer_count) || 0;
            if (customerCount > 0) {
                referralBadge.textContent = customerCount;
                referralBadge.style.display = 'flex';
            } else {
                referralBadge.style.display = 'none';
            }
        }

        // Update booking referrer phone if booking form exists
        if (typeof updateBookingReferrerPhone === 'function') {
            updateBookingReferrerPhone();
        }
    }
}

// Apply dashboard date preset
function applyDashboardPreset(preset) {
    const today = new Date();
    let fromDate, toDate;

    // Reset all buttons to default text first, then update active button
    document.querySelectorAll('.btn-filter-preset').forEach(btn => {
        btn.classList.remove('active');
        // Reset button text to translation only (remove date range)
        const translationKey = btn.getAttribute('data-i18n');
        if (translationKey) {
            // Get translation - use translations object directly if t() not available
            let translatedText = translationKey;
            if (typeof t === 'function') {
                translatedText = t(translationKey);
            } else if (typeof translations !== 'undefined' && typeof getCurrentLang === 'function') {
                const currentLang = getCurrentLang();
                if (translations[currentLang] && translations[currentLang][translationKey]) {
                    translatedText = translations[currentLang][translationKey];
                }
            }

            // Only update if we got a valid translation (not the key itself)
            if (translatedText && translatedText !== translationKey) {
                // Save indicator before clearing
                const existingIndicator = btn.querySelector('.data-indicator');
                btn.innerHTML = '';
                btn.appendChild(document.createTextNode(translatedText));
                // Restore indicator if it existed
                if (existingIndicator) {
                    const indicatorClone = existingIndicator.cloneNode(true);
                    btn.appendChild(indicatorClone);
                }
            }
        }
        btn.removeAttribute('data-date-range');
    });

    // Hide custom date filter if not custom
    if (preset !== 'custom') {
        document.getElementById('customDateFilter').style.display = 'none';
    }

    switch (preset) {
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

    // Update button text with date range for active button
    const activeButton = document.querySelector(`.btn-filter-preset[data-preset="${preset}"]`);
    if (activeButton && typeof formatDateRangeForButton === 'function') {
        activeButton.classList.add('active');
        const dateRange = formatDateRangeForButton(fromDate, toDate);
        const translationKey = activeButton.getAttribute('data-i18n');

        // Get translation - ensure we get the actual translated text, not the key
        let translatedText = translationKey;
        if (typeof t === 'function') {
            translatedText = t(translationKey);
        } else if (typeof translations !== 'undefined' && typeof getCurrentLang === 'function') {
            const currentLang = getCurrentLang();
            if (translations[currentLang] && translations[currentLang][translationKey]) {
                translatedText = translations[currentLang][translationKey];
            }
        }

        // Only proceed if we have a valid translation (not the key itself)
        if (translatedText && translatedText !== translationKey) {
            const indicator = activeButton.querySelector('.data-indicator');

            // Store date range in data attribute for translation preservation
            activeButton.setAttribute('data-date-range', dateRange);

            // Update button text: show translation + date range
            activeButton.innerHTML = '';
            activeButton.appendChild(document.createTextNode(`${translatedText} ${dateRange}`));
            if (indicator) {
                activeButton.appendChild(indicator.cloneNode(true));
            }
        }
    }

    // Update period labels AFTER button updates
    updatePeriodLabels(preset);

    // Apply translations (but our labels won't be overwritten since we removed data-i18n)
    if (typeof applyTranslations === 'function') {
        applyTranslations();
    }

    // Update labels again after translations to ensure they're correct
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

    // Update button text with date range for custom button
    const customButton = document.querySelector('.btn-filter-preset[data-preset="custom"]');
    if (customButton && typeof formatDateRangeForButton === 'function') {
        const fromDateObj = new Date(fromDate);
        const toDateObj = new Date(toDate);
        const dateRange = formatDateRangeForButton(fromDateObj, toDateObj);
        const translationKey = customButton.getAttribute('data-i18n');
        const translatedText = typeof t === 'function' ? t(translationKey) : translationKey;
        const indicator = customButton.querySelector('.data-indicator');

        // Update active state
        document.querySelectorAll('.btn-filter-preset').forEach(btn => {
            btn.classList.remove('active');
        });
        customButton.classList.add('active');

        // Update button text
        customButton.innerHTML = '';
        customButton.appendChild(document.createTextNode(`${translatedText} ${dateRange}`));
        if (indicator) {
            customButton.appendChild(indicator.cloneNode(true));
        }
    }

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
    // Check which date ranges have data and show indicators
    checkDashboardDateRangesWithData();
}

// Lifetime Statistics section removed - function kept as stub to prevent errors
async function loadLifetimeStats() {
    // Section removed from UI
    return;
}

