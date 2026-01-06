/**
 * Admin Dashboard - Clients Module - State
 * 
 * NOTE: If this file approaches 50MB, it must be split into smaller modules.
 * Files larger than 50MB cannot be synchronized or edited safely.
 */

// State
let allClients = [];
let clientsCurrentPage = 1;
let clientsTotalPages = 1;
let currentClientView = localStorage.getItem('clientView') || 'grid';
