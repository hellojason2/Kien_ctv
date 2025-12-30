/**
 * Admin Dashboard - Excel Export Module
 * DOES: Handles Excel file exports for various data tables
 * INPUTS: Export button clicks, current filter values
 * OUTPUTS: Downloaded Excel files
 * FLOW: User clicks export -> Build URL with filters -> Trigger download
 */

// Generic export function for simple endpoints
function exportToExcel(endpoint) {
    const token = getAuthToken();
    if (!token) {
        alert('Please login first');
        return;
    }
    
    // Create download link
    const link = document.createElement('a');
    link.href = endpoint;
    link.click();
}

// Export commissions with month filter
function exportCommissionsExcel() {
    const month = document.getElementById('commissionMonth')?.value || '';
    let url = '/api/admin/commissions/summary/export';
    if (month) {
        url += `?month=${month}`;
    }
    exportToExcel(url);
}

// Export clients with search filter
function exportClientsExcel() {
    const search = document.getElementById('clientSearch')?.value || '';
    let url = '/api/admin/clients/export';
    if (search) {
        url += `?search=${encodeURIComponent(search)}`;
    }
    exportToExcel(url);
}

// Export activity logs with all filters
function exportActivityLogsExcel() {
    const eventType = document.getElementById('logEventFilter')?.value || '';
    const userType = document.getElementById('logUserTypeFilter')?.value || '';
    const fromDate = document.getElementById('logFromDate')?.value || '';
    const toDate = document.getElementById('logToDate')?.value || '';
    const search = document.getElementById('logSearch')?.value || '';
    
    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (userType) params.append('user_type', userType);
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (search) params.append('search', search);
    
    let url = '/api/admin/activity-logs/export-xlsx';
    if (params.toString()) {
        url += '?' + params.toString();
    }
    exportToExcel(url);
}

