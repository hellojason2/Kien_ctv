/**
 * CTV Portal - Data Indicator Configuration
 * DOES: Configures the appearance of data availability indicators on date filter buttons
 * USAGE: Change the indicatorType and indicatorContent to customize for holidays/events
 * 
 * QUICK CHANGE EXAMPLES:
 * 
 * For Christmas:
 *   setIndicatorPreset('christmas');
 *   OR: indicatorType: 'emoji', indicatorContent: '🎄'
 * 
 * For Chinese New Year:
 *   setIndicatorPreset('chineseNewYear');
 *   OR: indicatorType: 'emoji', indicatorContent: '🐉'
 * 
 * For Custom Emoji:
 *   setCustomIndicator('emoji', '🎊', '16px');
 * 
 * Back to Default Red Dot:
 *   setIndicatorPreset('default');
 *   OR: indicatorType: 'dot'
 * 
 * To change the indicator:
 * 1. Set indicatorType to 'emoji', 'icon', 'custom', or 'dot'
 * 2. Update indicatorContent with your emoji/icon/custom HTML
 * 3. Optionally update indicatorSize and indicatorPosition
 * 4. Call updateAllIndicators() to apply changes
 */

const INDICATOR_CONFIG = {
    // Type: 'emoji' | 'icon' | 'custom' | 'dot'
    indicatorType: 'custom', // Using custom for red envelope SVG
    
    // Content based on type:
    // - 'emoji': Use emoji characters (e.g., '🎄', '🐉', '🎊')
    // - 'icon': Use icon class names (e.g., 'fa fa-star')
    // - 'custom': Use custom HTML (e.g., '<img src="...">')
    // - 'dot': Use default red dot (ignores indicatorContent)
    indicatorContent: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
        <path d="M20 6H4C2.9 6 2 6.9 2 8V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6Z" fill="#DC2626" stroke="#B91C1C" stroke-width="1.5"/>
        <path d="M12 12L8 8H16L12 12Z" fill="#FEE2E2"/>
        <path d="M4 8L12 12L20 8" stroke="#B91C1C" stroke-width="1.5" stroke-linecap="round"/>
        <circle cx="7" cy="11" r="1" fill="#FEE2E2" opacity="0.8"/>
        <circle cx="17" cy="11" r="1" fill="#FEE2E2" opacity="0.8"/>
    </svg>`, // Red envelope SVG for Chinese New Year
    
    // Size settings (only applies to emoji/icon types)
    indicatorSize: '20px', // Size for emoji/icon indicators
    
    // Position offset (adjusts position from top-right corner)
    indicatorPosition: {
        top: '-4px',
        right: '-4px'
    },
    
    // Holiday presets (easy switching)
    presets: {
        default: {
            type: 'dot',
            content: '',
            size: '10px'
        },
        christmas: {
            type: 'emoji',
            content: '🎄',
            size: '16px'
        },
        chineseNewYear: {
            type: 'custom',
            content: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
                <path d="M20 6H4C2.9 6 2 6.9 2 8V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6Z" fill="#DC2626" stroke="#B91C1C" stroke-width="1.5"/>
                <path d="M12 12L8 8H16L12 12Z" fill="#FEE2E2"/>
                <path d="M4 8L12 12L20 8" stroke="#B91C1C" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="7" cy="11" r="1" fill="#FEE2E2" opacity="0.8"/>
                <circle cx="17" cy="11" r="1" fill="#FEE2E2" opacity="0.8"/>
            </svg>`,
            size: '20px'
        },
        newYear: {
            type: 'emoji',
            content: '🎊',
            size: '16px'
        },
        valentine: {
            type: 'emoji',
            content: '❤️',
            size: '14px'
        },
        halloween: {
            type: 'emoji',
            content: '🎃',
            size: '16px'
        }
    }
};

/**
 * Get current indicator configuration
 * Can be called to check current settings
 */
function getIndicatorConfig() {
    return INDICATOR_CONFIG;
}

/**
 * Set indicator to a preset
 * @param {string} presetName - Name of preset (e.g., 'christmas', 'chineseNewYear')
 */
function setIndicatorPreset(presetName) {
    if (INDICATOR_CONFIG.presets[presetName]) {
        const preset = INDICATOR_CONFIG.presets[presetName];
        INDICATOR_CONFIG.indicatorType = preset.type;
        INDICATOR_CONFIG.indicatorContent = preset.content;
        INDICATOR_CONFIG.indicatorSize = preset.size;
        updateAllIndicators();
    }
}

/**
 * Set custom indicator
 * @param {string} type - 'emoji' | 'icon' | 'custom' | 'dot'
 * @param {string} content - Content based on type
 * @param {string} size - Size (optional, defaults to 16px)
 */
function setCustomIndicator(type, content, size = '16px') {
    INDICATOR_CONFIG.indicatorType = type;
    INDICATOR_CONFIG.indicatorContent = content;
    INDICATOR_CONFIG.indicatorSize = size;
    updateAllIndicators();
}

/**
 * Update all indicators on the page with current config
 */
function updateAllIndicators() {
    document.querySelectorAll('.data-indicator').forEach(indicator => {
        updateIndicatorElement(indicator);
    });
}

/**
 * Update a single indicator element based on config
 * @param {HTMLElement} element - The indicator element
 */
function updateIndicatorElement(element) {
    const config = INDICATOR_CONFIG;
    
    // Clear existing content
    element.innerHTML = '';
    element.className = 'data-indicator';
    
    // Apply type-specific styling
    switch(config.indicatorType) {
        case 'emoji':
            element.textContent = config.indicatorContent;
            element.style.fontSize = config.indicatorSize;
            element.style.width = 'auto';
            element.style.height = 'auto';
            element.style.background = 'transparent';
            element.style.border = 'none';
            element.style.boxShadow = 'none';
            element.style.lineHeight = '1';
            element.classList.add('indicator-emoji');
            break;
            
        case 'icon':
            element.innerHTML = `<i class="${config.indicatorContent}"></i>`;
            element.style.fontSize = config.indicatorSize;
            element.style.width = 'auto';
            element.style.height = 'auto';
            element.style.background = 'transparent';
            element.style.border = 'none';
            element.style.boxShadow = 'none';
            element.classList.add('indicator-icon');
            break;
            
        case 'custom':
            element.innerHTML = config.indicatorContent;
            element.style.width = 'auto';
            element.style.height = 'auto';
            element.style.display = 'flex';
            element.style.alignItems = 'center';
            element.style.justifyContent = 'center';
            element.classList.add('indicator-custom');
            // Add cute animation for red envelope
            element.style.animation = 'envelope-wiggle 2s ease-in-out infinite';
            break;
            
        case 'dot':
        default:
            // Use default red dot styling (handled by CSS)
            element.style.width = '10px';
            element.style.height = '10px';
            element.style.background = '#ef4444';
            element.style.border = '2px solid #ffffff';
            element.style.borderRadius = '50%';
            element.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.2)';
            element.classList.add('indicator-dot');
            break;
    }
    
    // Apply position
    element.style.top = config.indicatorPosition.top;
    element.style.right = config.indicatorPosition.right;
    
    // Ensure custom indicators are visible when has-data class is present
    if (element.closest('.has-data')) {
        element.style.display = 'flex';
    }
}

