/**
 * CTV Portal - Commissions Module
 * DOES: Loads and displays commission data
 * INPUTS: API responses from /api/ctv/my-commissions
 * OUTPUTS: Renders commission lists and summary tables
 * FLOW: loadRecentCommissions/loadAllCommissions -> Render to DOM
 */

// Earnings date filter state
let earningsDateFilter = {
    preset: 'month',
    fromDate: null,
    toDate: null
};

/**
 * Initialize earnings page
 */
function initEarnings() {
    // Set default to current month
    applyEarningsPreset('month');
    // Load lifetime stats (static, never changes)
    loadEarningsLifetimeStats();
    // Check which date ranges have data and show indicators
    checkDateRangesWithData('earnings');
}

/**
 * Check which date ranges have data and show red dot indicators
 */
async function checkDateRangesWithData(pageType = 'earnings') {
    try {
        // Wait a bit for the page to be fully rendered
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const result = await api('/api/ctv/date-ranges-with-data');
        
        if (result.status === 'success' && result.ranges_with_data) {
            const pageId = pageType === 'earnings' ? 'page-earnings' : 'page-dashboard';
            const page = document.getElementById(pageId);
            if (!page) return;
            
            // Update each button based on data availability
            Object.keys(result.ranges_with_data).forEach(preset => {
                const button = page.querySelector(`.btn-filter-preset[data-preset="${preset}"]`);
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

/**
 * Show loading state on earnings summary card
 */
function showEarningsSummaryLoading() {
    const summaryContainer = document.getElementById('earningsSummary');
    if (summaryContainer) {
        summaryContainer.innerHTML = `
            <div style="padding: 20px;">
                <div class="skeleton-loader" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="skeleton-loader" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="skeleton-loader" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="skeleton-loader" style="height: 20px;"></div>
            </div>
        `;
    }
}

/**
 * Hide loading state on earnings summary card
 */
function hideEarningsSummaryLoading() {
    // Loading is hidden when data is rendered
}

/**
 * Apply earnings date preset
 */
function applyEarningsPreset(preset) {
    const today = new Date();
    let fromDate, toDate;
    
    // Ensure translations are applied first
    if (typeof applyTranslations === 'function') {
        applyTranslations();
    }
    
    // Reset all buttons to default text first, then update active button
    const earningsPage = document.getElementById('page-earnings');
    if (earningsPage) {
        earningsPage.querySelectorAll('.btn-filter-preset').forEach(btn => {
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
    }
    
    // Hide custom date filter if not custom
    if (preset !== 'custom') {
        const customFilter = document.getElementById('earningsCustomDateFilter');
        if (customFilter) customFilter.style.display = 'none';
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
    
    earningsDateFilter.preset = preset;
    earningsDateFilter.fromDate = formatDateForAPI(fromDate);
    earningsDateFilter.toDate = formatDateForAPI(toDate);
    
    // Update date inputs for reference
    const fromInput = document.getElementById('earningsFromDate');
    const toInput = document.getElementById('earningsToDate');
    if (fromInput) fromInput.value = earningsDateFilter.fromDate;
    if (toInput) toInput.value = earningsDateFilter.toDate;
    
    // Update button text with date range for active button
    if (earningsPage) {
        const activeButton = earningsPage.querySelector(`.btn-filter-preset[data-preset="${preset}"]`);
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
    }
    
    // Show loading animation
    showEarningsSummaryLoading();
    
    // Reload commissions with date filter
    loadAllCommissions(earningsDateFilter.fromDate, earningsDateFilter.toDate);
}

/**
 * Toggle custom date filter visibility
 */
function toggleEarningsCustomDateFilter() {
    const customFilter = document.getElementById('earningsCustomDateFilter');
    if (!customFilter) return;
    
    const isVisible = customFilter.style.display !== 'none';
    
    // Update active button
    const earningsPage = document.getElementById('page-earnings');
    if (earningsPage) {
        earningsPage.querySelectorAll('.btn-filter-preset').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.preset === 'custom') {
                btn.classList.add('active');
            }
        });
    }
    
    customFilter.style.display = isVisible ? 'none' : 'block';
}

/**
 * Apply custom date filter
 */
function applyEarningsCustomDateFilter() {
    const fromDate = document.getElementById('earningsFromDate')?.value;
    const toDate = document.getElementById('earningsToDate')?.value;
    
    if (!fromDate || !toDate) {
        alert(t('select_filter_hint') || 'Please select both from and to dates');
        return;
    }
    
    earningsDateFilter.preset = 'custom';
    earningsDateFilter.fromDate = fromDate;
    earningsDateFilter.toDate = toDate;
    
    // Update button text with date range for custom button
    const earningsPage = document.getElementById('page-earnings');
    if (earningsPage) {
        const customButton = earningsPage.querySelector('.btn-filter-preset[data-preset="custom"]');
        if (customButton && typeof formatDateRangeForButton === 'function') {
            const fromDateObj = new Date(fromDate);
            const toDateObj = new Date(toDate);
            const dateRange = formatDateRangeForButton(fromDateObj, toDateObj);
            const translationKey = customButton.getAttribute('data-i18n');
            const translatedText = typeof t === 'function' ? t(translationKey) : translationKey;
            const indicator = customButton.querySelector('.data-indicator');
            
            // Update active state
            earningsPage.querySelectorAll('.btn-filter-preset').forEach(btn => {
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
    }
    
    // Show loading animation
    showEarningsSummaryLoading();
    
    loadAllCommissions(fromDate, toDate);
}

/**
 * Format date for API (YYYY-MM-DD)
 */
function formatDateForAPI(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Set default date filter for earnings page
 */
function setEarningsDefaultDateFilter() {
    applyEarningsPreset('month');
}

/**
 * Show loading state on recent commissions card
 * Mimics the table structure with skeleton loaders
 */
function showRecentCommissionsLoading() {
    const container = document.getElementById('recentCommissions');
    if (container) {
        container.innerHTML = `
            <div style="padding: 20px;">
                <!-- Table header skeleton -->
                <div style="display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1.5fr; gap: 16px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e0e0e0;">
                    <div class="skeleton-loader" style="height: 16px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 16px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 16px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 16px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 16px; border-radius: 4px;"></div>
                </div>
                <!-- Table rows skeleton (5 rows for levels 0-4) -->
                <div style="display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1.5fr; gap: 16px; margin-bottom: 12px; padding: 12px 0;">
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1.5fr; gap: 16px; margin-bottom: 12px; padding: 12px 0;">
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1.5fr; gap: 16px; margin-bottom: 12px; padding: 12px 0;">
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                </div>
                <!-- Total row skeleton -->
                <div style="display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1.5fr; gap: 16px; margin-top: 12px; padding: 12px 0; background: #f8f9fa; border-radius: 8px;">
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                    <div class="skeleton-loader" style="height: 20px; border-radius: 4px;"></div>
                </div>
            </div>
        `;
    }
}

/**
 * Hide loading state on recent commissions card
 */
function hideRecentCommissionsLoading() {
    // Check if the container still has the skeleton loader
    const container = document.getElementById('recentCommissions');
    if (container && container.querySelector('.skeleton-loader')) {
        // If it still has skeleton loaders, it means data load failed or hasn't replaced content yet
        // We should clear it to avoid stuck loading state, but only if we're sure
        // For now, let's just log it
        console.log('Hiding recent commissions loading state');
    }
}

// Load Recent Commissions (Dashboard) with optional date filter
// Shows breakdown by commission level (Level 0, 1, 2, 3, 4) based on selected date filter
// Uses /api/ctv/commission endpoint which returns breakdown by level
async function loadRecentCommissions(fromDate = null, toDate = null) {
    // Show loading animation immediately
    showRecentCommissionsLoading();
    
    // Build URL with query params - use the commission endpoint that provides level breakdown
    let url = '/api/ctv/commission';
    const params = new URLSearchParams();

    // Support both old format (month/day) and new format (fromDate/toDate)
    // Check dashboardDateFilter from profile.js if available
    if (fromDate && toDate) {
        params.append('from', fromDate);
        params.append('to', toDate);
    } else if (typeof dashboardDateFilter !== 'undefined' && dashboardDateFilter && dashboardDateFilter.fromDate && dashboardDateFilter.toDate) {
        params.append('from', dashboardDateFilter.fromDate);
        params.append('to', dashboardDateFilter.toDate);
    }

    if (params.toString()) url += '?' + params.toString();
    
    try {
        const result = await api(url);
        const container = document.getElementById('recentCommissions');
        
        if (!container) return;
        
        if (result.status === 'success') {
            const levelColors = ['#22c55e', '#3b82f6', '#d97706', '#ec4899', '#8b5cf6'];
            
            if (!result.by_level || result.by_level.length === 0) {
                container.innerHTML = `<div class="empty-state">${t('no_commissions_period')}</div>`;
            } else {
                // Display breakdown by level in a table format (same as earnings page)
                container.innerHTML = `
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>${t('level')}</th>
                                <th>${t('revenue')}</th>
                                <th>${t('rate')}</th>
                                <th>${t('count')}</th>
                                <th>${t('total_commission')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.by_level.map(s => `
                                <tr>
                                    <td><span class="level-badge level-${s.level}">Level ${s.level}</span></td>
                                    <td style="color:#22c55e;font-weight:600">${formatCurrency(s.total_revenue)}</td>
                                    <td>${s.rate.toFixed(1)}%</td>
                                    <td>${s.transaction_count}</td>
                                    <td style="color:#22c55e;font-weight:600">${formatCurrency(s.commission)}</td>
                                </tr>
                            `).join('')}
                            <tr class="total-row">
                                <td>${t('all')}</td>
                                <td style="color:#22c55e">${formatCurrency(result.total.revenue || 0)}</td>
                                <td></td>
                                <td>${result.total.transactions || 0}</td>
                                <td style="color:#22c55e">${formatCurrency(result.total.commission || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                `;
            }
            // Hide loading animation
            hideRecentCommissionsLoading();
        } else {
            container.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
            hideRecentCommissionsLoading();
        }
    } catch (error) {
        console.error('Error loading recent commissions:', error);
        const container = document.getElementById('recentCommissions');
        if (container) {
            container.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
        hideRecentCommissionsLoading();
    }
}

// Load Lifetime Statistics (all-time, never changes)
async function loadEarningsLifetimeStats() {
    const result = await api('/api/ctv/lifetime-stats');
    
    if (result.status === 'success') {
        const stats = result.stats;
        const container = document.getElementById('earningsLifetimeStats');
        
        if (!container) return;
        
        // stats.level0 is now available from backend
        // We only show the total row as requested ("show all earnings as one earning")
        
        container.innerHTML = `
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>${t('level')}</th>
                        <th>${t('revenue')}</th>
                        <th>${t('rate')}</th>
                        <th>${t('count')}</th>
                        <th>${t('total_commission')}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="total-row">
                        <td>${t('all')}</td>
                        <td style="color:#22c55e">${formatCurrency(stats.total_revenue || 0)}</td>
                        <td></td>
                        <td>${stats.total_transactions || 0}</td>
                        <td style="color:#22c55e">${formatCurrency(stats.total_commissions || 0)}</td>
                    </tr>
                </tbody>
            </table>
        `;
    } else {
        const container = document.getElementById('earningsLifetimeStats');
        if (container) {
            container.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
    }
}

// Load All Commissions with date filtering - uses /api/ctv/commission endpoint
// which calculates commissions based on khach_hang table with ngay_hen_lam filter
async function loadAllCommissions(fromDate = null, toDate = null) {
    // Build URL with query params - use the commission endpoint that queries khach_hang
    let url = '/api/ctv/commission';
    const params = new URLSearchParams();

    // Support both old format (month/day) and new format (fromDate/toDate)
    // If fromDate/toDate are provided, use them; otherwise check for month/day in earningsDateFilter
    if (fromDate && toDate) {
        params.append('from', fromDate);
        params.append('to', toDate);
    } else if (earningsDateFilter.fromDate && earningsDateFilter.toDate) {
        params.append('from', earningsDateFilter.fromDate);
        params.append('to', earningsDateFilter.toDate);
    }

    if (params.toString()) url += '?' + params.toString();
    
    try {
        const result = await api(url);
        if (result.status === 'success') {
        const levelColors = ['#22c55e', '#3b82f6', '#d97706', '#ec4899', '#8b5cf6'];
        
        // Summary table
        const summaryContainer = document.getElementById('earningsSummary');
        if (!result.by_level || result.by_level.length === 0) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('no_commissions_period')}</div>`;
        } else {
            summaryContainer.innerHTML = `
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>${t('level')}</th>
                            <th>${t('revenue')}</th>
                            <th>${t('rate')}</th>
                            <th>${t('count')}</th>
                            <th>${t('total_commission')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.by_level.map(s => `
                            <tr>
                                <td><span class="level-badge level-${s.level}">Level ${s.level}</span></td>
                                <td style="color:#22c55e;font-weight:600">${formatCurrency(s.total_revenue)}</td>
                                <td>${s.rate.toFixed(1)}%</td>
                                <td>${s.transaction_count}</td>
                                <td style="color:#22c55e;font-weight:600">${formatCurrency(s.commission)}</td>
                            </tr>
                        `).join('')}
                        <tr class="total-row">
                            <td>${t('all')}</td>
                            <td style="color:#22c55e">${formatCurrency(result.total.revenue || 0)}</td>
                            <td></td>
                            <td>${result.total.transactions}</td>
                            <td style="color:#22c55e">${formatCurrency(result.total.commission)}</td>
                        </tr>
                    </tbody>
                </table>
            `;
        }
        // Hide loading animation
        hideEarningsSummaryLoading();
    } else {
        // Show error state
        const summaryContainer = document.getElementById('earningsSummary');
        if (summaryContainer) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
    }
    } catch (error) {
        console.error('Error loading commissions:', error);
        const summaryContainer = document.getElementById('earningsSummary');
        if (summaryContainer) {
            summaryContainer.innerHTML = `<div class="empty-state">${t('error_loading_data') || 'Error loading data'}</div>`;
        }
    }
}


