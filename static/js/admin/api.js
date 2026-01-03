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
    
    // Include credentials to send cookies (for session_token)
    const fetchOptions = {
        ...options,
        headers,
        credentials: 'include' // Important: sends cookies with request
    };
    
    try {
        const response = await fetch(endpoint, fetchOptions);
        
        if (!response.ok) {
            // Try to parse error response
            let errorData;
            try {
                errorData = await response.json();
            } catch {
                errorData = { status: 'error', message: `HTTP ${response.status}: ${response.statusText}` };
            }
            return errorData;
        }
        
        return await response.json();
    } catch (error) {
        // Network error or other exception
        console.error('API Error:', error);
        return { status: 'error', message: error.message || 'Network error' };
    }
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

