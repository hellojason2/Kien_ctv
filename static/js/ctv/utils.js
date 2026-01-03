/**
 * CTV Portal - Utilities Module
 * DOES: Provides common utility functions
 * OUTPUTS: formatCurrency, getCtvInitials, escapeHtmlCTV, formatCtvCurrency, debounceCTV
 * FLOW: Used by rendering modules (clients.js, commissions.js)
 */

// Format currency for display
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(amount) + 'd';
}

// Get initials from name
function getCtvInitials(name) {
    if (!name) return '?';
    const words = name.trim().split(/\s+/);
    if (words.length >= 2) {
        return (words[0][0] + words[words.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

// Escape HTML for safe display
function escapeHtmlCTV(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Format currency for CTV display
function formatCtvCurrency(amount) {
    if (!amount && amount !== 0) return '-';
    return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(amount) + 'd';
}

// Debounce function
function debounceCTV(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format date range for display in filter buttons (DD/MM/YY-DD/MM/YYYY)
function formatDateRangeForButton(fromDate, toDate) {
    if (!fromDate || !toDate) return '';
    
    const formatDate = (date) => {
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = String(d.getFullYear()).slice(-2);
        return `${day}/${month}/${year}`;
    };
    
    const formatDateFull = (date) => {
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return `${day}/${month}/${year}`;
    };
    
    const from = formatDate(fromDate);
    const to = formatDateFull(toDate);
    return `${from}-${to}`;
}

