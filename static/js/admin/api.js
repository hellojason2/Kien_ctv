/**
 * Admin Dashboard - API Module
 * HTTP wrapper with authentication
 * 
 * Created: December 30, 2025
 */

// State - Auth token
let authToken = localStorage.getItem('adminToken');

/**
 * API Helper function
 * @param {string} endpoint - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise} - Response JSON
 */
async function api(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` })
    };
    
    const response = await fetch(endpoint, { ...options, headers });
    return response.json();
}

/**
 * Set auth token
 * @param {string} token - Auth token
 */
function setAuthToken(token) {
    authToken = token;
    if (token) {
        localStorage.setItem('adminToken', token);
    } else {
        localStorage.removeItem('adminToken');
    }
}

/**
 * Get current auth token
 * @returns {string} - Current auth token
 */
function getAuthToken() {
    return authToken;
}

