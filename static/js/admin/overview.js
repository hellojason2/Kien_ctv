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
    countdownTimer: null,
    newRecords: 0
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

    // Load row count indicators (DB vs Google Sheets)
    loadRowCounts();

    // Check Google Sheet Variables
    checkGoogleStatus();

    // Attach click handler to Sync Status
    const syncStatusContainer = document.getElementById('syncStatusContainer');
    if (syncStatusContainer) {
        syncStatusContainer.style.cursor = 'pointer';
        syncStatusContainer.onclick = function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (typeof showSyncWorkerLogs === 'function') {
                showSyncWorkerLogs();
            } else {
                console.error('showSyncWorkerLogs is not defined');
            }
        };
    }
}

/**
 * Check Google Sheet Variables Status
 */
async function checkGoogleStatus() {
    const dot = document.getElementById('googleStatusDot');
    const text = document.getElementById('googleStatusText');
    const container = document.getElementById('googleStatusContainer');

    if (!dot || !text) return;

    try {
        const result = await api('/api/admin/check-google-creds');

        if (result.valid) {
            // GREEN - Found
            dot.style.backgroundColor = '#22c55e'; // Green
            text.textContent = 'Variables: OK';
            text.style.color = '#15803d'; // Dark green text
            container.style.backgroundColor = '#dcfce7'; // Light green bg
            container.style.borderColor = '#bbf7d0';
            container.title = `Source: ${result.source}`;
        } else {
            // RED - Missing
            dot.style.backgroundColor = '#ef4444'; // Red
            text.textContent = 'Variables: Missing';
            text.style.color = '#b91c1c'; // Dark red text
            container.style.backgroundColor = '#fee2e2'; // Light red bg
            container.style.borderColor = '#fecaca';
            container.title = result.message;
        }
    } catch (error) {
        console.error('Error checking Google status:', error);
        dot.style.backgroundColor = '#ef4444';
        text.textContent = 'Check Failed';
        text.style.color = '#b91c1c';
        container.style.backgroundColor = '#fee2e2';
    }
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

    switch (preset) {
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

            // Refresh row count indicators
            loadRowCounts();

            // Top earners with revenue and commission columns
            const topEarnersEl = document.getElementById('topEarnersTableBody');
            console.log('Top earners data:', s.top_earners);
            if (s.top_earners && Array.isArray(s.top_earners) && s.top_earners.length > 0) {
                const labelRank = t('id') || '#';
                const labelName = t('ctv_name') || 'Name';
                const labelCode = t('ctv_code') || 'Code';
                const labelRev = t('total_revenue') || 'Total Revenue';
                const labelComm = t('total_commission') || 'Total Commission';

                topEarnersEl.innerHTML = s.top_earners.map((e, index) => `
                <tr>
                    <td data-label="${labelRank}" style="font-weight: 500;">
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
                    <td data-label="${labelName}">
                        <div style="font-weight: 600; color: var(--text-primary);">${e.ten}</div>
                    </td>
                    <td data-label="${labelCode}">
                        <div style="font-size: 13px; font-family: 'SF Mono', monospace; color: var(--text-secondary); background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; display: inline-block;">${e.ctv_code}</div>
                    </td>
                    <td data-label="${labelRev}" style="text-align: right; font-weight: 600;">${formatCurrency(e.total_revenue)}</td>
                    <td data-label="${labelComm}" style="text-align: right; font-weight: 600; color: var(--accent-green);">${formatCurrency(e.total_commission)}</td>
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
    const badge = document.getElementById('syncBadge');

    if (!dot || !text) return;

    // Always show as online with countdown
    syncStatus.interval = systemStatus?.sync_interval || 30;

    // If we have a last run time, use it; otherwise start fresh
    if (systemStatus?.sync_worker_last_run) {
        syncStatus.lastRun = new Date(systemStatus.sync_worker_last_run);
    } else if (!syncStatus.lastRun) {
        // Start countdown from now if no heartbeat exists yet
        syncStatus.lastRun = new Date();
    }

    // Update new records count
    syncStatus.newRecords = systemStatus?.new_records || 0;

    // Update badge display
    if (badge) {
        if (syncStatus.newRecords > 0) {
            badge.textContent = syncStatus.newRecords > 99 ? '99+' : syncStatus.newRecords;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }

    // Always show as online
    dot.className = 'sync-status-dot status-online';
    text.className = 'sync-status-text status-online';

    // Update countdown text
    updateSyncCountdownText();
}

/**
 * Update the countdown text display
 */
function updateSyncCountdownText() {
    const text = document.getElementById('syncStatusText');
    const dot = document.getElementById('syncStatusDot');

    if (!text) return;

    // If no lastRun set yet, initialize it
    if (!syncStatus.lastRun) {
        syncStatus.lastRun = new Date();
    }

    const now = new Date();
    const elapsed = Math.floor((now - syncStatus.lastRun) / 1000);

    // Calculate countdown to next sync (cycles every 30 seconds)
    const nextSyncIn = Math.max(0, syncStatus.interval - (elapsed % syncStatus.interval));

    // Show "Online" with countdown
    text.textContent = `Online • ${nextSyncIn}s`;

    // Keep status as online
    if (dot) dot.className = 'sync-status-dot status-online';
    text.className = 'sync-status-text status-online';
}

/**
 * Start the countdown timer that updates every second
 */
function startSyncCountdown() {
    // Clear any existing timer
    if (syncStatus.countdownTimer) {
        clearInterval(syncStatus.countdownTimer);
    }

    // Initialize lastRun if not set
    if (!syncStatus.lastRun) {
        syncStatus.lastRun = new Date();
    }

    // Update immediately
    updateSyncCountdownText();

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

// ═══════════════════════════════════════════════════════════════════
// ROW COUNT INDICATORS (DB vs Google Sheets)
// ═══════════════════════════════════════════════════════════════════

/**
 * Load and display row counts comparing DB to Google Sheets
 */
async function loadRowCounts() {
    try {
        const result = await api('/api/admin/sync/row-counts');

        if (result.status === 'success' && result.row_counts) {
            updateRowCountDisplay('TM', result.row_counts.tham_my);
            updateRowCountDisplay('NK', result.row_counts.nha_khoa);
            updateRowCountDisplay('GT', result.row_counts.gioi_thieu);
        } else {
            // Show error state
            ['TM', 'NK', 'GT'].forEach(label => {
                const valueEl = document.getElementById(`rowCount${label}Value`);
                if (valueEl) valueEl.textContent = '-/-';
            });
        }
    } catch (error) {
        console.error('Error loading row counts:', error);
        ['TM', 'NK', 'GT'].forEach(label => {
            const valueEl = document.getElementById(`rowCount${label}Value`);
            if (valueEl) valueEl.textContent = 'Error';
        });
    }
}

/**
 * Update a single row count display box
 */
function updateRowCountDisplay(label, counts) {
    const boxEl = document.getElementById(`rowCount${label}`);
    const valueEl = document.getElementById(`rowCount${label}Value`);

    if (!valueEl || !boxEl) return;

    const dbCount = counts?.db ?? 0;
    const sheetCount = counts?.sheet;

    // Format numbers with commas for readability
    const formatNum = (n) => n != null ? n.toLocaleString() : '-';

    if (sheetCount != null) {
        const diff = sheetCount - dbCount;

        // Format: DB / Sheet (Diff)
        // diff > 0: Sheet has more = NEW rows waiting to be added = RED
        // diff < 0: DB has more than sheet = duplicates removed = GREEN
        if (diff > 0) {
            // NEW rows waiting to be added → RED
            valueEl.innerHTML = `${formatNum(dbCount)} / ${formatNum(sheetCount)} <span style="font-size: 0.8em; font-weight: 700; color: #dc2626;">(-${formatNum(diff)})</span>`;
        } else if (diff < 0) {
            // Duplicates removed from sync → GREEN
            valueEl.innerHTML = `${formatNum(dbCount)} / ${formatNum(sheetCount)} <span style="font-size: 0.8em; font-weight: 700; color: #16a34a;">(+${formatNum(Math.abs(diff))})</span>`;
        } else {
            // Perfectly synced
            valueEl.innerHTML = `${formatNum(dbCount)} / ${formatNum(sheetCount)} <span style="font-size: 0.8em; font-weight: 700; color: #16a34a;">✓</span>`;
        }

        // Color coding based on sync status
        boxEl.classList.remove('status-synced', 'status-missing', 'status-error');

        if (dbCount === sheetCount) {
            // Fully synced - green
            boxEl.classList.add('status-synced');
        } else if (dbCount < sheetCount) {
            // Missing rows - waiting to sync - yellow warning border
            boxEl.classList.add('status-synced');
            boxEl.style.borderColor = '#fbbf24'; // Yellow tint
        } else {
            // DB > Sheet (duplicates handled)
            boxEl.classList.add('status-synced');
        }
    } else {
        // Sheet count unavailable
        valueEl.textContent = `${formatNum(dbCount)}/-`;
        boxEl.classList.remove('status-synced', 'status-missing');
        boxEl.classList.add('status-error');
    }
}

/**
 * Refresh row counts (can be called manually)
 */
function refreshRowCounts() {
    loadRowCounts();
}

/**
 * Manual Sync - Pull new records from Google Sheets (Step by Step)
 */
async function manualSync() {
    const syncBtn = document.getElementById('syncNowBtn');
    if (!syncBtn) return;

    // Show the sync modal
    const modal = document.getElementById('syncModal');
    const logEntries = document.getElementById('syncLogEntries');
    const statusDisplay = document.getElementById('syncStatusDisplay');
    const summary = document.getElementById('syncSummary');
    const currentStep = document.getElementById('syncCurrentStep');

    if (modal) {
        modal.style.display = 'flex';
        logEntries.innerHTML = '';
        statusDisplay.style.display = 'block';
        summary.style.display = 'none';
        if (currentStep) currentStep.textContent = 'Connecting...';
    }

    // Disable button
    syncBtn.disabled = true;
    const originalText = syncBtn.innerHTML;
    syncBtn.innerHTML = '<span style="font-weight: bold;">⟳</span> <span>Syncing...</span>';
    syncBtn.style.opacity = '0.7';

    function addSyncLog(message, level = 'info') {
        if (logEntries) {
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = `sync-log-entry ${level}`;
            entry.innerHTML = `<span style="color:#9ca3af;margin-right:8px;">[${time}]</span>${message}`;
            logEntries.appendChild(entry);
            logEntries.scrollTop = logEntries.scrollHeight;
        }
    }

    function updateStep(text) {
        if (currentStep) currentStep.textContent = text;
    }

    try {
        const authToken = localStorage.getItem('adminToken');
        const headers = {
            'Content-Type': 'application/json',
            ...(authToken && authToken !== 'cookie-auth' && { 'Authorization': `Bearer ${authToken}` })
        };

        const response = await fetch('/api/admin/sync/manual', {
            method: 'POST',
            headers: headers,
            credentials: 'include'
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n\n');

            lines.forEach(line => {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.substring(6);
                        if (!jsonStr.trim()) return;

                        const data = JSON.parse(jsonStr);

                        // Log message
                        if (data.message) {
                            addSyncLog(data.message, data.level || 'info');
                            if (data.level !== 'error') {
                                updateStep(data.message.length > 50 ? 'Processing...' : data.message);
                            }
                        }

                        // Completion
                        if (data.done) {
                            // Show summary
                            statusDisplay.style.display = 'none';
                            summary.style.display = 'block';

                            const stats = data.stats;
                            const totalNew = data.total_new;
                            const totalUpdated = data.total_updated;

                            // Safe fallbacks for stats
                            const tm = stats.tham_my || { inserted: 0, updated: 0 };
                            const nk = stats.nha_khoa || { inserted: 0, updated: 0 };
                            const gt = stats.gioi_thieu || { inserted: 0, updated: 0 };

                            const summaryHtml = `
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;">
                                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb;">
                                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase;">Thẩm Mỹ</div>
                                        <div style="font-weight: 600; color: #166534;">+${tm.inserted}</div>
                                        <div style="font-size: 11px; color: #3b82f6;">↻ ${tm.updated}</div>
                                    </div>
                                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb;">
                                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase;">Nha Khoa</div>
                                        <div style="font-weight: 600; color: #166534;">+${nk.inserted}</div>
                                        <div style="font-size: 11px; color: #3b82f6;">↻ ${nk.updated}</div>
                                    </div>
                                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb;">
                                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase;">Giới Thiệu</div>
                                        <div style="font-weight: 600; color: #166534;">+${gt.inserted}</div>
                                        <div style="font-size: 11px; color: #3b82f6;">↻ ${gt.updated}</div>
                                    </div>
                                </div>
                                <div style="text-align: center; color: #374151; font-weight: 500;">
                                    Total: ${totalNew} new, ${totalUpdated} updated
                                </div>
                            `;

                            document.getElementById('syncSummaryStats').innerHTML = summaryHtml;
                            refreshRowCounts();

                            // Refresh overall stats if function exists
                            if (typeof loadStats === 'function') {
                                loadStats();
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data', e, line);
                    }
                }
            });
        }

    } catch (error) {
        addSyncLog(`Connection failed: ${error.message}`, 'error');
        console.error('Manual sync error:', error);
        if (statusDisplay) {
            statusDisplay.innerHTML = `
                <div style="color: #b91c1c; font-size: 48px; margin-bottom: 12px;">✗</div>
                <div style="color: #b91c1c; font-weight: 600;">Sync Failed</div>
                <div style="color: #6b7280; margin-top: 8px;">${error.message}</div>
            `;
        }
    } finally {
        syncBtn.disabled = false;
        syncBtn.innerHTML = originalText;
        syncBtn.style.opacity = '1';
    }
}

/**
 * Close the sync modal
 */
function closeSyncModal() {
    const modal = document.getElementById('syncModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Hard Reset Progress Controller
 */
const resetProgress = {
    steps: ['read', 'delete', 'beauty', 'dental', 'referral', 'commission'],
    currentStep: 0,
    progressIntervals: {},
    dbCounts: null,
    logs: []
};

/**
 * Add entry to the activity log
 */
function addLogEntry(message, type = 'info') {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });

    resetProgress.logs.push({ time: timeStr, message, type });

    const logEntries = document.getElementById('logEntries');
    if (logEntries) {
        const entry = document.createElement('div');
        entry.className = `log - entry ${type} `;
        entry.innerHTML = `< span class="log-time" > [${timeStr}]</span > <span class="log-message">${message}</span>`;
        logEntries.appendChild(entry);
        logEntries.scrollTop = logEntries.scrollHeight;
    }

    // Also log to console
    console.log(`[HardReset ${type.toUpperCase()}] ${message} `);
}

/**
 * Toggle log panel visibility
 */
function toggleLogPanel() {
    const logContent = document.getElementById('logContent');
    const logToggle = document.getElementById('logToggle');
    if (logContent && logToggle) {
        const isHidden = logContent.style.display === 'none';
        logContent.style.display = isHidden ? 'block' : 'none';
        logToggle.classList.toggle('expanded', isHidden);
    }
}

/**
 * Show the progress modal
 */
function showHardResetModal() {
    const modal = document.getElementById('hardResetModal');
    if (modal) {
        modal.style.display = 'flex';

        // Clear previous logs
        resetProgress.logs = [];
        const logEntries = document.getElementById('logEntries');
        if (logEntries) logEntries.innerHTML = '';

        // Hide database counts
        const dbCounts = document.getElementById('dbCounts');
        if (dbCounts) dbCounts.style.display = 'none';

        // Reset all steps to initial state
        resetProgress.steps.forEach(step => {
            const stepEl = document.getElementById(`step - ${step} `);
            if (stepEl) {
                stepEl.classList.remove('active', 'complete', 'error');
            }
            const progressBar = document.getElementById(`step - ${step} -progress`);
            if (progressBar) {
                progressBar.style.width = '0%';
            }
            const status = document.getElementById(`step - ${step} -status`);
            if (status) {
                status.textContent = 'Waiting...';
            }
        });

        // Reset detail texts
        document.getElementById('step-read-detail').textContent = 'Counting existing records...';
        document.getElementById('step-delete-detail').textContent = 'Preparing to delete existing records...';
        document.getElementById('step-beauty-detail').textContent = 'Extracting from Thẩm Mỹ sheet...';
        document.getElementById('step-dental-detail').textContent = 'Extracting from Nha Khoa sheet...';
        document.getElementById('step-referral-detail').textContent = 'Extracting from Giới Thiệu sheet...';
        document.getElementById('step-commission-detail').textContent = 'Recalculating all commission levels...';

        // Hide summary
        const summary = document.getElementById('progressSummary');
        if (summary) {
            summary.style.display = 'none';
        }

        // Show progress steps
        const steps = document.querySelector('.progress-steps');
        if (steps) {
            steps.style.display = 'flex';
        }

        // Show log panel
        const logPanel = document.querySelector('.progress-log-panel');
        if (logPanel) {
            logPanel.style.display = 'block';
        }

        // Reset modal header
        const icon = document.querySelector('.progress-modal-icon');
        if (icon) {
            icon.style.animation = 'spin-slow 3s linear infinite';
            icon.style.background = 'linear-gradient(135deg, #fee2e2, #fecaca)';
            icon.innerHTML = `< svg viewBox = "0 0 24 24" fill = "none" stroke = "currentColor" stroke - width="2" >
        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg > `;
            icon.querySelector('svg').style.stroke = '#b91c1c';
        }
        const header = document.querySelector('.progress-modal-header h3');
        if (header) header.textContent = t('hard_reset_progress') || 'Hard Reset In Progress';
        const subtitle = document.querySelector('.progress-modal-subtitle');
        if (subtitle) subtitle.textContent = t('hard_reset_subtitle') || 'Please wait while we sync your data...';
    }
}

/**
 * Close the progress modal
 */
function closeHardResetModal() {
    const modal = document.getElementById('hardResetModal');
    if (modal) {
        modal.style.display = 'none';
    }
    // Stop all progress animations
    Object.keys(resetProgress.progressIntervals).forEach(key => {
        clearInterval(resetProgress.progressIntervals[key]);
    });
    resetProgress.progressIntervals = {};

    // Reload page to refresh data
    window.location.reload();
}

/**
 * Update a step's progress
 */
function updateStepProgress(stepId, status, progress, detail) {
    const stepEl = document.getElementById(`step - ${stepId} `);
    const progressBar = document.getElementById(`step - ${stepId} -progress`);
    const statusEl = document.getElementById(`step - ${stepId} -status`);
    const detailEl = document.getElementById(`step - ${stepId} -detail`);

    if (stepEl) {
        stepEl.classList.remove('active', 'complete', 'error', 'pending');
        if (status === 'active') stepEl.classList.add('active');
        else if (status === 'complete') stepEl.classList.add('complete');
        else if (status === 'error') stepEl.classList.add('error');
        else if (status === 'pending') stepEl.classList.add('pending');
    }

    if (progressBar) {
        if (progress !== undefined && progress !== null) {
            progressBar.style.width = `${progress}% `;
        } else if (status === 'active') {
            // Indeterminate progress - show pulsing bar
            progressBar.style.width = '100%';
            progressBar.classList.add('indeterminate');
        } else if (status === 'complete') {
            progressBar.style.width = '100%';
            progressBar.classList.remove('indeterminate');
        } else {
            progressBar.style.width = '0%';
            progressBar.classList.remove('indeterminate');
        }
    }

    if (statusEl) {
        if (status === 'active') {
            statusEl.textContent = progress !== null ? `${Math.round(progress)}% ` : 'Processing...';
        } else if (status === 'complete') {
            statusEl.textContent = '✓ Done';
        } else if (status === 'error') {
            statusEl.textContent = '✗ Failed';
        } else if (status === 'pending') {
            statusEl.textContent = 'Waiting...';
        } else {
            statusEl.textContent = 'Waiting...';
        }
    }

    if (detailEl && detail) {
        detailEl.textContent = detail;
    }
}

/**
 * Animate a step's progress bar
 */
function animateStepProgress(stepId, duration, detailMessages) {
    return new Promise((resolve) => {
        const startTime = Date.now();
        let messageIndex = 0;

        updateStepProgress(stepId, 'active', 0, detailMessages[0]);

        const interval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min((elapsed / duration) * 100, 95);

            const newMessageIndex = Math.floor((progress / 100) * detailMessages.length);
            if (newMessageIndex !== messageIndex && newMessageIndex < detailMessages.length) {
                messageIndex = newMessageIndex;
                addLogEntry(detailMessages[messageIndex]);
            }

            updateStepProgress(stepId, 'active', progress, detailMessages[messageIndex]);

            if (progress >= 95) {
                clearInterval(interval);
                resolve();
            }
        }, 100);

        resetProgress.progressIntervals[stepId] = interval;
    });
}

/**
 * Show completion summary
 */
function showResetSummary(stats) {
    // Hide progress steps
    const steps = document.querySelector('.progress-steps');
    if (steps) {
        steps.style.display = 'none';
    }

    // Stop the spinning icon
    const icon = document.querySelector('.progress-modal-icon');
    if (icon) {
        icon.style.animation = 'none';
        icon.innerHTML = `< svg viewBox = "0 0 24 24" fill = "none" stroke = "currentColor" stroke - width="2" >
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg > `;
        icon.style.background = 'linear-gradient(135deg, #dcfce7, #bbf7d0)';
        icon.querySelector('svg').style.stroke = '#16a34a';
    }

    // Update header
    const header = document.querySelector('.progress-modal-header h3');
    if (header) {
        header.textContent = t('hard_reset_complete') || 'Hard Reset Complete!';
    }
    const subtitle = document.querySelector('.progress-modal-subtitle');
    if (subtitle) {
        subtitle.textContent = t('data_synced_successfully') || 'All data has been synced successfully.';
    }

    // Show summary with before/after comparison
    const summary = document.getElementById('progressSummary');
    const summaryStats = document.getElementById('summaryStats');
    if (summary && summaryStats) {
        const beforeTotal = resetProgress.dbCounts?.total || 0;
        const afterTotal = (stats.tham_my?.processed || 0) + (stats.nha_khoa?.processed || 0) + (stats.gioi_thieu?.processed || 0);

        summaryStats.innerHTML = `
        < div class="summary-stat" >
                <div class="summary-stat-value">${stats.tham_my?.processed || 0}</div>
                <div class="summary-stat-label">Thẩm Mỹ</div>
            </div >
            <div class="summary-stat">
                <div class="summary-stat-value">${stats.nha_khoa?.processed || 0}</div>
                <div class="summary-stat-label">Nha Khoa</div>
            </div>
            <div class="summary-stat">
                <div class="summary-stat-value">${stats.gioi_thieu?.processed || 0}</div>
                <div class="summary-stat-label">Giới Thiệu</div>
            </div>
    `;
        summary.style.display = 'block';
    }

    addLogEntry(`Reset complete! Imported ${(stats.tham_my?.processed || 0) + (stats.nha_khoa?.processed || 0) + (stats.gioi_thieu?.processed || 0)} total records.`, 'success');
}

/**
 * Confirm and trigger Hard Reset with detailed progress
 */
async function confirmHardReset() {
    if (!confirm(t('confirm_hard_reset') || 'WARNING: This will DELETE all Client Service data (Beauty, Dental, Referral) and re-import everything from Google Sheets.\n\nThis process may take a minute. Are you sure you want to proceed?')) {
        return;
    }

    const btn = document.getElementById('hardResetBtn');
    const originalText = btn.innerHTML;

    // Disable button
    btn.disabled = true;
    btn.style.opacity = '0.5';
    btn.innerHTML = '<span style="font-weight: bold;">↻</span> In Progress...';

    // Show progress modal
    showHardResetModal();

    addLogEntry('Hard Reset initiated by user', 'info');
    addLogEntry('Starting database analysis...', 'info');

    // STEP 0: Read database counts first
    updateStepProgress('read', 'active', 10, 'Connecting to database...');

    try {
        // Fetch current database counts
        addLogEntry('Fetching current record counts from database...', 'info');
        const previewResponse = await api('/api/admin/reset-data/preview');

        if (previewResponse.status === 'success') {
            resetProgress.dbCounts = previewResponse.counts;

            // Update the counts display
            document.getElementById('count-tham-my').textContent = previewResponse.counts.tham_my.toLocaleString();
            document.getElementById('count-nha-khoa').textContent = previewResponse.counts.nha_khoa.toLocaleString();
            document.getElementById('count-gioi-thieu').textContent = previewResponse.counts.gioi_thieu.toLocaleString();
            document.getElementById('count-commissions').textContent = previewResponse.counts.commissions.toLocaleString();
            document.getElementById('count-total').textContent = previewResponse.counts.total.toLocaleString();

            // Show the counts panel
            document.getElementById('dbCounts').style.display = 'block';

            addLogEntry(`Found ${previewResponse.counts.tham_my.toLocaleString()} Beauty records`, 'info');
            addLogEntry(`Found ${previewResponse.counts.nha_khoa.toLocaleString()} Dental records`, 'info');
            addLogEntry(`Found ${previewResponse.counts.gioi_thieu.toLocaleString()} Referral records`, 'info');
            addLogEntry(`Found ${previewResponse.counts.commissions.toLocaleString()} Commission records`, 'info');
            addLogEntry(`TOTAL: ${previewResponse.counts.total.toLocaleString()} records will be deleted`, 'warning');

            updateStepProgress('read', 'complete', 100, `Found ${previewResponse.counts.total.toLocaleString()} records`);
        } else {
            throw new Error('Failed to get database counts');
        }

        // Small delay before starting
        await new Promise(r => setTimeout(r, 500));

        addLogEntry('Starting step-by-step data reset process...', 'info');

        // Initialize all steps
        updateStepProgress('delete', 'pending', null, 'Waiting...');
        updateStepProgress('beauty', 'pending', null, 'Waiting...');
        updateStepProgress('dental', 'pending', null, 'Waiting...');
        updateStepProgress('referral', 'pending', null, 'Waiting...');
        updateStepProgress('commission', 'pending', null, 'Waiting...');

        const stats = {
            tham_my: { processed: 0, errors: 0 },
            nha_khoa: { processed: 0, errors: 0 },
            gioi_thieu: { processed: 0, errors: 0 }
        };

        // ═══════════════════════════════════════════════════════════════
        // STEP 1: Delete all records
        // ═══════════════════════════════════════════════════════════════
        addLogEntry('', 'info');
        addLogEntry('--- STEP 1: Deleting existing records ---', 'info');
        updateStepProgress('delete', 'active', null, 'Deleting records...');

        const deleteResponse = await api('/api/admin/reset-data/step/delete', { method: 'POST' });

        if (deleteResponse.status !== 'success') {
            throw new Error(deleteResponse.message || 'Failed to delete records');
        }

        addLogEntry(`✓ Deleted ${deleteResponse.deleted_khach_hang?.toLocaleString() || 0} client records`, 'success');
        addLogEntry(`✓ Deleted ${deleteResponse.deleted_commissions?.toLocaleString() || 0} commission records`, 'success');
        updateStepProgress('delete', 'complete', 100, `✓ Deleted ${(deleteResponse.deleted_khach_hang || 0).toLocaleString()} records`);

        // ═══════════════════════════════════════════════════════════════
        // STEP 2: Import Thẩm Mỹ (Beauty)
        // ═══════════════════════════════════════════════════════════════
        addLogEntry('', 'info');
        addLogEntry('--- STEP 2: Importing Thẩm Mỹ (Beauty) ---', 'info');
        updateStepProgress('beauty', 'active', null, 'Importing...');

        const beautyResponse = await apiLong('/api/admin/reset-data/step/import/tham_my', { method: 'POST' }, 180000);

        if (beautyResponse.status !== 'success') {
            throw new Error(beautyResponse.message || 'Failed to import beauty data');
        }

        stats.tham_my = { processed: beautyResponse.processed || 0, errors: beautyResponse.errors || 0 };
        addLogEntry(`✓ Imported ${stats.tham_my.processed.toLocaleString()} beauty records`, 'success');
        if (stats.tham_my.errors > 0) addLogEntry(`⚠ ${stats.tham_my.errors} errors`, 'warning');
        updateStepProgress('beauty', 'complete', 100, `✓ ${stats.tham_my.processed.toLocaleString()} records`);

        // ═══════════════════════════════════════════════════════════════
        // STEP 3: Import Nha Khoa (Dental)
        // ═══════════════════════════════════════════════════════════════
        addLogEntry('', 'info');
        addLogEntry('--- STEP 3: Importing Nha Khoa (Dental) ---', 'info');
        updateStepProgress('dental', 'active', null, 'Importing...');

        const dentalResponse = await apiLong('/api/admin/reset-data/step/import/nha_khoa', { method: 'POST' }, 180000);

        if (dentalResponse.status !== 'success') {
            throw new Error(dentalResponse.message || 'Failed to import dental data');
        }

        stats.nha_khoa = { processed: dentalResponse.processed || 0, errors: dentalResponse.errors || 0 };
        addLogEntry(`✓ Imported ${stats.nha_khoa.processed.toLocaleString()} dental records`, 'success');
        if (stats.nha_khoa.errors > 0) addLogEntry(`⚠ ${stats.nha_khoa.errors} errors`, 'warning');
        updateStepProgress('dental', 'complete', 100, `✓ ${stats.nha_khoa.processed.toLocaleString()} records`);

        // ═══════════════════════════════════════════════════════════════
        // STEP 4: Import Giới Thiệu (Referral)
        // ═══════════════════════════════════════════════════════════════
        addLogEntry('', 'info');
        addLogEntry('--- STEP 4: Importing Giới Thiệu (Referral) ---', 'info');
        updateStepProgress('referral', 'active', null, 'Importing...');

        const referralResponse = await apiLong('/api/admin/reset-data/step/import/gioi_thieu', { method: 'POST' }, 180000);

        if (referralResponse.status !== 'success') {
            throw new Error(referralResponse.message || 'Failed to import referral data');
        }

        stats.gioi_thieu = { processed: referralResponse.processed || 0, errors: referralResponse.errors || 0 };
        addLogEntry(`✓ Imported ${stats.gioi_thieu.processed.toLocaleString()} referral records`, 'success');
        if (stats.gioi_thieu.errors > 0) addLogEntry(`⚠ ${stats.gioi_thieu.errors} errors`, 'warning');
        updateStepProgress('referral', 'complete', 100, `✓ ${stats.gioi_thieu.processed.toLocaleString()} records`);

        // ═══════════════════════════════════════════════════════════════
        // STEP 5: Recalculate Commissions
        // ═══════════════════════════════════════════════════════════════
        addLogEntry('', 'info');
        addLogEntry('--- STEP 5: Recalculating Commissions ---', 'info');
        updateStepProgress('commission', 'active', null, 'Calculating...');

        const commissionResponse = await api('/api/admin/reset-data/step/commissions', { method: 'POST' });

        if (commissionResponse.status !== 'success') {
            addLogEntry(`⚠ Commission calculation warning: ${commissionResponse.message} `, 'warning');
        } else {
            addLogEntry('✓ Commission calculation complete', 'success');
        }
        updateStepProgress('commission', 'complete', 100, '✓ Commissions calculated');

        // ═══════════════════════════════════════════════════════════════
        // COMPLETE
        // ═══════════════════════════════════════════════════════════════
        addLogEntry('', 'info');
        addLogEntry('═══════════════════════════════════════', 'info');
        addLogEntry('HARD RESET COMPLETE', 'success');
        addLogEntry('═══════════════════════════════════════', 'info');

        const totalImported = stats.tham_my.processed + stats.nha_khoa.processed + stats.gioi_thieu.processed;
        const totalErrors = stats.tham_my.errors + stats.nha_khoa.errors + stats.gioi_thieu.errors;

        addLogEntry(`Total imported: ${totalImported.toLocaleString()} records`, 'success');
        if (totalErrors > 0) {
            addLogEntry(`Total errors: ${totalErrors} `, 'warning');
        }

        // Show summary after short delay
        setTimeout(() => {
            showResetSummary(stats);
        }, 800);

    } catch (error) {
        console.error('Hard reset error:', error);
        addLogEntry(`✗ ERROR: ${error.message} `, 'error');

        // Stop all animations
        Object.keys(resetProgress.progressIntervals).forEach(key => {
            clearInterval(resetProgress.progressIntervals[key]);
        });

        // Mark current step as error
        const currentActiveStep = resetProgress.steps.find(step => {
            const el = document.getElementById(`step - ${step} `);
            return el && el.classList.contains('active');
        });
        if (currentActiveStep) {
            updateStepProgress(currentActiveStep, 'error', 0, `Error: ${error.message} `);
        }

        addLogEntry('Hard reset failed. Check logs above for details.', 'error');
        addLogEntry('You may need to restart the server and try again.', 'warning');

        // Re-enable button after delay
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            btn.style.opacity = '1';
        }, 2000);
    }
}

// ═══════════════════════════════════════════════════════════════════
// WORKER LOGS VIEWER (Replaces resetSyncCounter)
// ═══════════════════════════════════════════════════════════════════

let workerLogInterval = null;

// Override the function called by the "Online" pill
window.resetSyncCounter = function () {
    showSyncWorkerLogs();
};

async function showSyncWorkerLogs() {
    const modal = document.getElementById('syncModal');
    if (!modal) return;

    // UI Elements
    const title = modal.querySelector('h3');
    const subtitle = modal.querySelector('.progress-modal-subtitle');
    const logEntries = document.getElementById('syncLogEntries');
    const statusDisplay = document.getElementById('syncStatusDisplay');
    const summary = document.getElementById('syncSummary');

    // Reset State
    modal.style.display = 'flex';
    if (statusDisplay) statusDisplay.style.display = 'none';
    if (summary) summary.style.display = 'none';

    // Hijack Title (Translation safe-ish)
    if (title) title.textContent = 'Background Worker Logs';
    if (subtitle) subtitle.textContent = 'Live activity from the autonomous sync process';

    // Add Close Button if not exists
    let closeBtn = modal.querySelector('.worker-logs-close-btn');
    if (!closeBtn) {
        const modalContent = modal.querySelector('.progress-modal-content') || modal.firstElementChild;
        if (modalContent) {
            closeBtn = document.createElement('button');
            closeBtn.className = 'worker-logs-close-btn';
            closeBtn.innerHTML = '✕';
            closeBtn.style.cssText = `
                position: absolute;
                top: 16px;
                right: 16px;
                width: 36px;
                height: 36px;
                border: none;
                background: #f1f5f9;
                border-radius: 8px;
                font-size: 18px;
                cursor: pointer;
                color: #64748b;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                z-index: 10;
            `;
            closeBtn.onmouseover = () => { closeBtn.style.background = '#ef4444'; closeBtn.style.color = 'white'; };
            closeBtn.onmouseout = () => { closeBtn.style.background = '#f1f5f9'; closeBtn.style.color = '#64748b'; };
            closeBtn.onclick = () => {
                if (workerLogInterval) clearInterval(workerLogInterval);
                modal.style.display = 'none';
            };
            modalContent.style.position = 'relative';
            modalContent.insertBefore(closeBtn, modalContent.firstChild);
        }
    }

    // Also close when clicking outside the modal content
    modal.onclick = (e) => {
        if (e.target === modal) {
            if (workerLogInterval) clearInterval(workerLogInterval);
            modal.style.display = 'none';
        }
    };

    // Initial Loading State
    if (logEntries) {
        logEntries.innerHTML = '<div style="padding:20px;text-align:center;color:#9ca3af;">Fetching logs...</div>';
    }

    // Start Polling
    fetchWorkerLogs();
    if (workerLogInterval) clearInterval(workerLogInterval);
    workerLogInterval = setInterval(fetchWorkerLogs, 3000);
}

async function fetchWorkerLogs() {
    const logEntries = document.getElementById('syncLogEntries');
    // Stop if modal is closed
    if (document.getElementById('syncModal').style.display === 'none') {
        clearInterval(workerLogInterval);
        return;
    }

    try {
        const result = await api('/api/admin/sync/worker-logs');
        if (result.status === 'success') {
            const logs = result.logs;
            if (!logs || logs.length === 0) {
                logEntries.innerHTML = '<div style="padding:20px;text-align:center;color:#9ca3af;">No logs found yet.</div>';
                return;
            }

            const html = logs.map(log => {
                let color = '#9ca3af'; // default/info
                let icon = 'ℹ️';

                if (log.level === 'WARNING') { color = '#f59e0b'; icon = '⚠️'; }
                if (log.level === 'ERROR') { color = '#ef4444'; icon = '❌'; }
                if (log.message.includes('Success') || log.message.includes('Complete')) { color = '#10b981'; icon = '✅'; }
                if (log.message.includes('Connecting')) { color = '#3b82f6'; icon = '🔌'; }
                if (log.message.includes('Processing')) { color = '#8b5cf6'; icon = '⚙️'; }
                if (log.message.includes('Sleeping')) { color = '#6b7280'; icon = '💤'; }

                // Vietnamese time format: "2026-01-27 11:41:12 (VN)"
                // Extract just the time with VN marker
                let timeDisplay = '';
                if (log.created_at) {
                    const parts = log.created_at.split(' ');
                    if (parts.length >= 2) {
                        timeDisplay = parts[1] + ' ' + (parts[2] || '');
                    } else {
                        timeDisplay = log.created_at;
                    }
                }

                return `
                    <div style="font-family:'SF Mono', monospace; font-size:11px; padding:4px 0; border-bottom:1px solid rgba(0,0,0,0.05); color:${color}">
                        <span style="color:#0369a1; margin-right:8px; font-weight:600;">[${timeDisplay}]</span>
                        <span style="margin-right:4px;">${icon}</span>
                        <span>${log.message}</span>
                    </div>
                `;
            }).join('');

            logEntries.innerHTML = html;
        }
    } catch (e) {
        console.error("Worker Log Fetch Error", e);
    }
}

// Hook into existing close function (if accessible) or rewrite it
const originalCloseSyncModal = window.closeSyncModal;
window.closeSyncModal = function () {
    if (workerLogInterval) clearInterval(workerLogInterval);
    if (originalCloseSyncModal) originalCloseSyncModal();
};
