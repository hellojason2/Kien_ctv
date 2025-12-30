/**
 * CTV Portal - Profile Module
 * DOES: Loads and displays user profile and stats
 * INPUTS: API response from /api/ctv/me
 * OUTPUTS: Updates DOM with profile data
 * FLOW: loadProfile -> Update stats cards and user info
 */

// Load Profile
async function loadProfile() {
    const result = await api('/api/ctv/me');
    if (result.status === 'success') {
        setCurrentUser(result.profile);
        document.getElementById('userName').textContent = result.profile.ten;
        
        const levelBadge = document.getElementById('userLevel');
        const capBac = (result.profile.cap_bac || 'Bronze').toLowerCase();
        levelBadge.textContent = result.profile.cap_bac || 'Bronze';
        levelBadge.className = 'user-badge ' + capBac;
        
        // Update stats
        document.getElementById('statTotalEarnings').textContent = formatCurrency(result.stats.total_earnings);
        document.getElementById('statMonthlyEarnings').textContent = formatCurrency(result.stats.monthly_earnings);
        document.getElementById('statNetworkSize').textContent = result.stats.network_size;
        document.getElementById('statMonthlyServices').textContent = result.stats.monthly_services_count || 0;
    }
}

