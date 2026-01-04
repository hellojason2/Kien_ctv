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
    // Always read the latest token from localStorage to ensure we have the current auth state
    const token = localStorage.getItem('ctvToken');
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
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

