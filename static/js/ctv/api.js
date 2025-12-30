/**
 * CTV Portal - API Module
 * DOES: Provides authenticated API request helper
 * OUTPUTS: api function for making requests
 * FLOW: Used by all data-fetching modules
 */

// State management
let authToken = localStorage.getItem('ctvToken');
let currentUser = null;

// API Helper
async function api(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` })
    };
    
    const response = await fetch(endpoint, { ...options, headers });
    return response.json();
}

// Getters/Setters for state
function getAuthToken() {
    return authToken;
}

function setAuthToken(token) {
    authToken = token;
}

function getCurrentUser() {
    return currentUser;
}

function setCurrentUser(user) {
    currentUser = user;
}

