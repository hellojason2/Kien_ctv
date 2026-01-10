/**
 * Admin Dashboard - Overview Page Module
 * Dashboard statistics and top earners
 * 
 * Created: December 30, 2025
 * Updated: January 3, 2026 - Replaced with CTV-style filter buttons with red dot indicators
 * Updated: January 9, 2026 - Added sync worker status indicator with countdown
 */

let overviewDateFilter = {
    preset: 'month', // default to current month
    fromDate: null,
    toDate: null
};

// Sync status state
let syncStatus = {
    lastRun: null,
    interval: 30,
    countdownTimer: null
};

/**
 * Initialize overview page
 */
function initOverview() {
    // Set default to current month
    applyOverviewPreset('month');
    
    // Check which date ranges have data and show red dot indicators
    checkOverviewDateRangesWithData();
    
    // Start the countdown timer
    startSyncCountdown();
}

/**
 * Check which date ranges have data and show red dot indicators
 */
async function checkOverviewDateRangesWithData() {
    try {
        // Wait a bit for the page to be fully rendered
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const result = await api('/api/admin/date-ranges-with-data');
        
        if (result.status === 'success' && result.ranges_with_data) {
            const overviewPage = document.getElementById('page-overview');
            if (!overviewPage) return;
            
            // Update each button based on data availability
            Object.keys(result.ranges_with_data).forEach(preset => {
                const button = overviewPage.querySelector(`.quick-filter-btn[data-preset="${preset}"]`);
                if (button) {
                    if (result.ranges_with_data[preset]) {
                        button.classList.add('has-data');
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
 * Apply overview date preset
 */
function applyOverviewPreset(preset) {
    const today = new Date();
    let fromDate, toDate;
    
    // Ensure translations are applied first
    if (typeof applyTranslations === 'function') {
        applyTranslations();
    }
    
    // Reset all buttons to default text first, then update active button
    const overviewPage = document.getElementById('page-overview');
    if (overviewPage) {
        overviewPage.querySelectorAll('.quick-filter-btn').forEach(btn => {
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
        const customFilter = document.getElementById('overviewCustomDateFilter');
        if (customFilter) customFilter.style.display = 'none';
    }
    
    switch(preset) {
        case 'today':
            fromDate = new Date(today);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today);
            toDate.setHours(23, 59, 59, 999);
            break;
        case '3days':
            fromDate = new Date(today);
            fromDate.setDate(fromDate.getDate() - 2);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today);
            toDate.setHours(23, 59, 59, 999);
            break;
        case 'week':
            fromDate = new Date(today);
            const dayOfWeek = fromDate.getDay();
            fromDate.setDate(fromDate.getDate() - dayOfWeek);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today);
            toDate.setHours(23, 59, 59, 999);
            break;
        case 'month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today);
            toDate.setHours(23, 59, 59, 999);
            break;
        case 'lastmonth':
            fromDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today.getFullYear(), today.getMonth(), 0);
            toDate.setHours(23, 59, 59, 999);
            break;
        case '3months':
            fromDate = new Date(today);
            fromDate.setMonth(fromDate.getMonth() - 2);
            fromDate.setDate(1);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today);
            toDate.setHours(23, 59, 59, 999);
            break;
        case 'year':
            fromDate = new Date(today.getFullYear(), 0, 1);
            fromDate.setHours(0, 0, 0, 0);
            toDate = new Date(today);
            toDate.setHours(23, 59, 59, 999);
            break;
        case 'custom':
            toggleOverviewCustomDateFilter();
            return;
        default:
            return;
    }
    
    overviewDateFilter.preset = preset;
    overviewDateFilter.fromDate = fromDate.toISOString().split('T')[0];
    overviewDateFilter.toDate = toDate.toISOString().split('T')[0];
    
    // Update button text with date range for active button
    if (overviewPage) {
        const activeButton = overviewPage.querySelector(`.quick-filter-btn[data-preset="${preset}"]`);
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
    
    // Show loading state immediately
    showOverviewLoading();
    
    loadStats();
}

/**
 * Toggle custom date filter visibility
 */
function toggleOverviewCustomDateFilter() {
    const customFilter = document.getElementById('overviewCustomDateFilter');
    if (!customFilter) return;
    
    if (customFilter.style.display === 'none' || !customFilter.style.display) {
        customFilter.style.display = 'block';
        overviewDateFilter.preset = 'custom';
    } else {
        customFilter.style.display = 'none';
    }
}

/**
 * Apply custom date range filter
 */
function applyOverviewCustomDateFilter() {
    const fromDateInput = document.getElementById('overviewFromDate');
    const toDateInput = document.getElementById('overviewToDate');
    
    if (!fromDateInput || !toDateInput || !fromDateInput.value || !toDateInput.value) {
        alert(t('please_select_both_dates') || 'Please select both start and end dates');
        return;
    }
    
    if (new Date(fromDateInput.value) > new Date(toDateInput.value)) {
        alert(t('date_from_must_be_before_date_to') || 'Start date must be before end date');
        return;
    }
    
    overviewDateFilter.preset = 'custom';
    overviewDateFilter.fromDate = fromDateInput.value;
    overviewDateFilter.toDate = toDateInput.value;
    
    // Update active button and show date range
    const overviewPage = document.getElementById('page-overview');
    if (overviewPage) {
        overviewPage.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.preset === 'custom') {
                btn.classList.add('active');
            }
        });
        
        // Update button text with date range for custom button
        const customButton = overviewPage.querySelector('.quick-filter-btn[data-preset="custom"]');
        if (customButton && typeof formatDateRangeForButton === 'function') {
            const fromDateObj = new Date(fromDateInput.value);
            const toDateObj = new Date(toDateInput.value);
            const dateRange = formatDateRangeForButton(fromDateObj, toDateObj);
            const translationKey = customButton.getAttribute('data-i18n');
            const translatedText = typeof t === 'function' ? t(translationKey) : translationKey;
            const indicator = customButton.querySelector('.data-indicator');
            
            // Update button text
            customButton.innerHTML = '';
            customButton.appendChild(document.createTextNode(`${translatedText} ${dateRange}`));
            if (indicator) {
                customButton.appendChild(indicator.cloneNode(true));
            }
        }
    }
    
    // Show loading state immediately
    showOverviewLoading();
    
    loadStats();
}

/**
 * Show loading state with skeleton loaders
 */
function showOverviewLoading() {
    const statCards = ['statTotalCTV', 'statMonthlyCommission', 'statMonthlyTx', 'statMonthlyRevenue'];
    statCards.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = '<div class="skeleton-loader medium"></div>';
        }
    });
    
    const topEarnersEl = document.getElementById('topEarnersTableBody');
    if (topEarnersEl) {
        topEarnersEl.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <div class="loading" data-i18n="loading">Loading...</div>
                </td>
            </tr>
        `;
    }
    
    // Disable filter buttons during loading
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.disabled = true;
    });
    const applyBtn = document.querySelector('#overviewCustomDateFilter .btn-filter');
    if (applyBtn) applyBtn.disabled = true;
}

/**
 * Load dashboard statistics with date filter
 */
async function loadStats() {
    // Show loading state immediately
    showOverviewLoading();
    
    // Build query parameters
    const params = new URLSearchParams();
    
    if (overviewDateFilter.fromDate && overviewDateFilter.toDate) {
        params.append('from_date', overviewDateFilter.fromDate);
        params.append('to_date', overviewDateFilter.toDate);
    } else if (overviewDateFilter.preset === 'month') {
        // Default to current month if no dates set
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        params.append('month', `${year}-${month}`);
    }
    
    try {
        const url = '/api/admin/stats' + (params.toString() ? '?' + params.toString() : '');
        console.log('Loading stats with URL:', url);
        console.log('Date filter:', overviewDateFilter);
        
        const result = await api(url);
        console.log('Stats API result:', result);
        console.log('Result status:', result?.status);
        console.log('Result stats:', result?.stats);
        
        // Re-enable buttons after loading
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.disabled = false;
        });
        const applyBtn = document.querySelector('#overviewCustomDateFilter .btn-filter');
        if (applyBtn) applyBtn.disabled = false;
        
        if (!result) {
            throw new Error('No response from API');
        }
        
        if (result.status === 'success' && result.stats) {
            const s = result.stats;
            document.getElementById('statTotalCTV').textContent = s.total_ctv || 0;
            document.getElementById('statMonthlyCommission').textContent = formatCurrency(s.monthly_commission || 0);
            document.getElementById('statMonthlyTx').textContent = s.monthly_transactions || 0;
            document.getElementById('statMonthlyRevenue').textContent = formatCurrency(s.monthly_revenue || 0);
            
            // Update sync worker status
            if (result.system_status) {
                updateSyncStatus(result.system_status);
            }
        
            // Top earners with revenue and commission columns
            const topEarnersEl = document.getElementById('topEarnersTableBody');
            console.log('Top earners data:', s.top_earners);
            if (s.top_earners && Array.isArray(s.top_earners) && s.top_earners.length > 0) {
            topEarnersEl.innerHTML = s.top_earners.map((e, index) => `
                <tr>
                    <td style="font-weight: 500;">
                        ${index < 3 ? `
                            <div style="
                                width: 24px; 
                                height: 24px; 
                                background: ${index === 0 ? 'var(--gradient-gold, linear-gradient(135deg, #fbbf24, #d97706))' : index === 1 ? 'var(--gradient-silver, linear-gradient(135deg, #9ca3af, #4b5563))' : 'var(--gradient-bronze, linear-gradient(135deg, #d97706, #92400e))'}; 
                                color: white; 
                                border-radius: 50%; 
                                display: flex; 
                                align-items: center; 
                                justify-content: center; 
                                font-size: 12px; 
                                font-weight: 700;
                            ">${index + 1}</div>
                        ` : `<span style="margin-left: 8px;">${index + 1}</span>`}
                    </td>
                    <td>
                        <div style="font-weight: 600; color: var(--text-primary);">${e.ten}</div>
                    </td>
                    <td>
                        <div style="font-size: 13px; font-family: 'SF Mono', monospace; color: var(--text-secondary); background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; display: inline-block;">${e.ctv_code}</div>
                    </td>
                    <td style="text-align: right; font-weight: 600;">${formatCurrency(e.total_revenue)}</td>
                    <td style="text-align: right; font-weight: 600; color: var(--accent-green);">${formatCurrency(e.total_commission)}</td>
                </tr>
            `).join('');
            
            // Apply translations to dynamically added elements
            if (typeof applyTranslations === 'function') {
                applyTranslations();
            }
        } else {
            topEarnersEl.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                        <div style="font-style: italic;">${t('no_earnings') || 'No earnings found'}</div>
                    </td>
                </tr>
            `;
        }
        } else {
            console.error('Stats API Error:', result);
            const errorMsg = result?.message || result?.error || 'Unknown error';
            console.error('Error details:', errorMsg);
            // Show error state
            const statCards = ['statTotalCTV', 'statMonthlyCommission', 'statMonthlyTx', 'statMonthlyRevenue'];
            statCards.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = '-';
            });
            const topEarnersEl = document.getElementById('topEarnersTableBody');
            if (topEarnersEl) {
                topEarnersEl.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 40px; color: var(--accent-red);">
                            <div>Error loading data: ${errorMsg}</div>
                        </td>
                    </tr>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        // Re-enable buttons on error
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.disabled = false;
        });
        const applyBtn = document.querySelector('#overviewCustomDateFilter .btn-filter');
        if (applyBtn) applyBtn.disabled = false;
        
        // Show error state
        const statCards = ['statTotalCTV', 'statMonthlyCommission', 'statMonthlyTx', 'statMonthlyRevenue'];
        statCards.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '-';
        });
        const topEarnersEl = document.getElementById('topEarnersTableBody');
        if (topEarnersEl) {
            topEarnersEl.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: var(--accent-red);">
                        <div>Error loading data: ${error.message}</div>
                    </td>
                </tr>
            `;
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// SYNC WORKER STATUS INDICATOR
// ═══════════════════════════════════════════════════════════════════

/**
 * Update the sync worker status indicator
 */
function updateSyncStatus(systemStatus) {
    const dot = document.getElementById('syncStatusDot');
    const text = document.getElementById('syncStatusText');
    
    if (!dot || !text) return;
    
    if (systemStatus.sync_worker_last_run) {
        syncStatus.lastRun = new Date(systemStatus.sync_worker_last_run);
        syncStatus.interval = systemStatus.sync_interval || 30;
        
        // Calculate time elapsed since last run
        const now = new Date();
        const elapsed = Math.floor((now - syncStatus.lastRun) / 1000);
        
        // Buffer: 45 seconds (30s interval + 15s buffer)
        const isOnline = elapsed < 45;
        
        // Update visual status
        dot.className = 'sync-status-dot ' + (isOnline ? 'status-online' : 'status-offline');
        text.className = 'sync-status-text ' + (isOnline ? 'status-online' : 'status-offline');
        
        // Update countdown text
        updateSyncCountdownText();
    } else {
        // No heartbeat found - worker never ran or DB issue
        dot.className = 'sync-status-dot status-offline';
        text.className = 'sync-status-text status-offline';
        text.textContent = 'Offline';
    }
}

/**
 * Update the countdown text display
 */
function updateSyncCountdownText() {
    const text = document.getElementById('syncStatusText');
    const dot = document.getElementById('syncStatusDot');
    
    if (!text || !syncStatus.lastRun) return;
    
    const now = new Date();
    const elapsed = Math.floor((now - syncStatus.lastRun) / 1000);
    
    // Check if still online (within 45 seconds buffer)
    const isOnline = elapsed < 45;
    
    if (isOnline) {
        // Calculate countdown to next sync
        const nextSyncIn = Math.max(0, syncStatus.interval - (elapsed % syncStatus.interval));
        text.textContent = `Syncing in ${nextSyncIn}s`;
        
        // Update status classes
        dot.className = 'sync-status-dot status-online';
        text.className = 'sync-status-text status-online';
    } else {
        // Worker is offline
        const minutesAgo = Math.floor(elapsed / 60);
        if (minutesAgo < 1) {
            text.textContent = `Offline (${elapsed}s ago)`;
        } else if (minutesAgo < 60) {
            text.textContent = `Offline (${minutesAgo}m ago)`;
        } else {
            const hoursAgo = Math.floor(minutesAgo / 60);
            text.textContent = `Offline (${hoursAgo}h ago)`;
        }
        
        // Update status classes
        dot.className = 'sync-status-dot status-offline';
        text.className = 'sync-status-text status-offline';
    }
}

/**
 * Start the countdown timer that updates every second
 */
function startSyncCountdown() {
    // Clear any existing timer
    if (syncStatus.countdownTimer) {
        clearInterval(syncStatus.countdownTimer);
    }
    
    // Update every second
    syncStatus.countdownTimer = setInterval(() => {
        updateSyncCountdownText();
    }, 1000);
}

/**
 * Stop the countdown timer (call when leaving the page)
 */
function stopSyncCountdown() {
    if (syncStatus.countdownTimer) {
        clearInterval(syncStatus.countdownTimer);
        syncStatus.countdownTimer = null;
    }
}
