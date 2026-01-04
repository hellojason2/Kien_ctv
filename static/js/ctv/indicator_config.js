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
    indicatorContent: `<svg width="18" height="24" viewBox="0 0 18 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
        <!-- Main envelope body (elongated rectangle) -->
        <rect x="2" y="4" width="14" height="18" rx="2" fill="#DC2626" stroke="#B91C1C" stroke-width="1.2"/>
        <!-- Top flap (triangular) -->
        <path d="M2 4L9 10L16 4" fill="#EF4444" stroke="#B91C1C" stroke-width="1.2" stroke-linejoin="round"/>
        <!-- Flap fold line -->
        <line x1="2" y1="4" x2="16" y2="4" stroke="#B91C1C" stroke-width="0.8" opacity="0.6"/>
        <!-- Decorative gold elements (like traditional lì xì) -->
        <circle cx="5" cy="10" r="0.8" fill="#FCD34D" opacity="0.9"/>
        <circle cx="13" cy="10" r="0.8" fill="#FCD34D" opacity="0.9"/>
        <!-- Gold Chinese Character "Fortune" (福) -->
        <text x="9" y="16" fill="#FCD34D" font-size="6.5" font-family="serif" text-anchor="middle" font-weight="bold" style="text-shadow: 0 0.5px 0.5px rgba(0,0,0,0.3);">福</text>
        <!-- Vertical decorative line (center) -->
        <line x1="9" y1="18" x2="9" y2="20" stroke="#FCD34D" stroke-width="0.5" opacity="0.4"/>
    </svg>`, // Elongated red envelope SVG with gold Chinese character for New Year
    
    // Size settings (only applies to emoji/icon types)
    indicatorSize: '24px', // Size for emoji/icon indicators (height for elongated envelope)
    
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
            content: `<svg width="18" height="24" viewBox="0 0 18 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
                <!-- Main envelope body (elongated rectangle) -->
                <rect x="2" y="4" width="14" height="18" rx="2" fill="#DC2626" stroke="#B91C1C" stroke-width="1.2"/>
                <!-- Top flap (triangular) -->
                <path d="M2 4L9 10L16 4" fill="#EF4444" stroke="#B91C1C" stroke-width="1.2" stroke-linejoin="round"/>
                <!-- Flap fold line -->
                <line x1="2" y1="4" x2="16" y2="4" stroke="#B91C1C" stroke-width="0.8" opacity="0.6"/>
                <!-- Decorative gold elements (like traditional lì xì) -->
                <circle cx="5" cy="10" r="0.8" fill="#FCD34D" opacity="0.9"/>
                <circle cx="13" cy="10" r="0.8" fill="#FCD34D" opacity="0.9"/>
                <!-- Gold Chinese Character "Fortune" (福) -->
                <text x="9" y="16" fill="#FCD34D" font-size="6.5" font-family="serif" text-anchor="middle" font-weight="bold" style="text-shadow: 0 0.5px 0.5px rgba(0,0,0,0.3);">福</text>
                <!-- Vertical decorative line (center) -->
                <line x1="9" y1="18" x2="9" y2="20" stroke="#FCD34D" stroke-width="0.5" opacity="0.4"/>
            </svg>`,
            size: '24px'
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
    
    // Clear existing content and inline styles
    element.innerHTML = '';
    element.className = 'data-indicator';
    element.removeAttribute('style'); // Clear any inline styles to let CSS control display
    
    // Apply type-specific styling (only non-display properties)
    switch(config.indicatorType) {
        case 'emoji':
            element.textContent = config.indicatorContent;
            element.style.fontSize = config.indicatorSize;
            element.classList.add('indicator-emoji');
            break;
            
        case 'icon':
            element.innerHTML = `<i class="${config.indicatorContent}"></i>`;
            element.style.fontSize = config.indicatorSize;
            element.classList.add('indicator-icon');
            break;
            
        case 'custom':
            element.innerHTML = config.indicatorContent;
            element.classList.add('indicator-custom');
            break;
            
        case 'dot':
        default:
            // Use default red dot styling (handled by CSS)
            element.classList.add('indicator-dot');
            break;
    }
    
    // Apply position
    element.style.top = config.indicatorPosition.top;
    element.style.right = config.indicatorPosition.right;
    element.style.position = 'absolute'; // Ensure position is set
}

