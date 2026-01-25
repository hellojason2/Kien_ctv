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
        // Only send Authorization header if token exists and is not the placeholder 'cookie-auth'
        ...(authToken && authToken !== 'cookie-auth' && { 'Authorization': `Bearer ${authToken}` })
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
            // Handle 401 Unauthorized globally
            if (response.status === 401) {
                window.dispatchEvent(new CustomEvent('auth:unauthorized'));
            }

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
 * API Helper for long-running operations with extended timeout
 * @param {string} endpoint - API endpoint
 * @param {object} options - Fetch options
 * @param {number} timeoutMs - Timeout in milliseconds (default: 5 minutes)
 * @returns {Promise} - Response JSON
 */
async function apiLong(endpoint, options = {}, timeoutMs = 300000) {
    const headers = {
        'Content-Type': 'application/json',
        ...(authToken && authToken !== 'cookie-auth' && { 'Authorization': `Bearer ${authToken}` })
    };

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const fetchOptions = {
        ...options,
        headers,
        credentials: 'include',
        signal: controller.signal
    };

    try {
        const response = await fetch(endpoint, fetchOptions);
        clearTimeout(timeoutId);

        if (!response.ok) {
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
        clearTimeout(timeoutId);
        console.error('API Long Error:', error);

        if (error.name === 'AbortError') {
            return {
                status: 'error',
                message: 'Request timed out. The operation may still be running on the server. Please wait a moment and refresh the page to check the results.'
            };
        }
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

