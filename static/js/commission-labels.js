/**
 * Commission Labels Utility
 * Provides global access to custom commission level labels
 * 
 * Created: January 14, 2026
 */

// Global cache for commission labels
window.commissionLabels = null;

/**
 * Load commission labels from API
 */
async function loadCommissionLabels() {
    if (window.commissionLabels) {
        return window.commissionLabels;
    }
    
    try {
        const result = await api('/api/commission-labels');
        if (result.status === 'success') {
            window.commissionLabels = result.labels;
            return window.commissionLabels;
        }
    } catch (error) {
        console.error('Failed to load commission labels:', error);
    }
    
    // Return default labels if API fails
    return {
        0: 'Level 0',
        1: 'Level 1',
        2: 'Level 2',
        3: 'Level 3',
        4: 'Level 4'
    };
}

/**
 * Get label for a specific level
 */
function getCommissionLabel(level) {
    if (!window.commissionLabels) {
        return `Level ${level}`;
    }
    return window.commissionLabels[level] || `Level ${level}`;
}

/**
 * Format level badge with custom label
 */
function formatLevelBadge(level) {
    const label = getCommissionLabel(level);
    return `<span class="level-badge level-${level}">${label}</span>`;
}
