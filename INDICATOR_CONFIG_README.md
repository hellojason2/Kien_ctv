# Data Indicator Configuration Guide

The data availability indicators on date filter buttons can be easily customized for holidays, events, or special occasions.

## Quick Start

### Option 1: Use a Preset (Easiest)

Open `static/js/ctv/indicator_config.js` and change the `indicatorType` at the top:

```javascript
// For Christmas
setIndicatorPreset('christmas');

// For Chinese New Year
setIndicatorPreset('chineseNewYear');

// For New Year
setIndicatorPreset('newYear');

// Back to default red dot
setIndicatorPreset('default');
```

### Option 2: Custom Emoji

```javascript
setCustomIndicator('emoji', '🎄', '18px'); // Christmas tree
setCustomIndicator('emoji', '🐉', '20px'); // Dragon for Chinese New Year
setCustomIndicator('emoji', '🎊', '16px'); // Party popper
setCustomIndicator('emoji', '❤️', '14px'); // Heart for Valentine's
```

### Option 3: Custom Icon (if using Font Awesome or similar)

```javascript
setCustomIndicator('icon', 'fa fa-star', '16px');
```

### Option 4: Custom HTML

```javascript
setCustomIndicator('custom', '<img src="/static/images/christmas-hat.png" style="width: 16px; height: 16px;">');
```

## Available Presets

- `default` - Red dot (10px)
- `christmas` - 🎄 Christmas tree (16px)
- `chineseNewYear` - 🐉 Dragon (18px)
- `newYear` - 🎊 Party popper (16px)
- `valentine` - ❤️ Heart (14px)
- `halloween` - 🎃 Pumpkin (16px)

## How to Change for Holidays

### Example: Christmas

1. Open `static/js/ctv/indicator_config.js`
2. At the bottom of the file, add this code (or call it from browser console):

```javascript
// Set Christmas indicator
setIndicatorPreset('christmas');
```

Or modify the config directly:

```javascript
const INDICATOR_CONFIG = {
    indicatorType: 'emoji',
    indicatorContent: '🎄',
    indicatorSize: '16px',
    // ... rest of config
};
```

### Example: Chinese New Year

```javascript
setIndicatorPreset('chineseNewYear');
// or
setCustomIndicator('emoji', '🐉', '20px');
```

## Programmatic Usage

You can also change indicators dynamically from the browser console:

```javascript
// Check current config
getIndicatorConfig();

// Set to Christmas
setIndicatorPreset('christmas');

// Set custom emoji
setCustomIndicator('emoji', '🎄', '18px');

// Update all indicators on page
updateAllIndicators();
```

## File Location

- Configuration: `static/js/ctv/indicator_config.js`
- CSS Styles: `static/css/ctv/components.css`
- Initialization: `static/js/ctv/main.js`

## Notes

- Changes take effect immediately when `updateAllIndicators()` is called
- Indicators are automatically updated when pages load
- The indicator appears on the top-right corner of date filter buttons that have data
- Emoji indicators support animation (bounce effect)
- Custom HTML indicators can include images, SVGs, or any HTML

## Examples for Different Occasions

```javascript
// Christmas
setCustomIndicator('emoji', '🎄', '18px');

// Chinese New Year
setCustomIndicator('emoji', '🐉', '20px');

// Vietnamese New Year (Tet)
setCustomIndicator('emoji', '🌸', '16px');

// Valentine's Day
setCustomIndicator('emoji', '❤️', '14px');

// Halloween
setCustomIndicator('emoji', '🎃', '16px');

// Birthday/Anniversary
setCustomIndicator('emoji', '🎉', '16px');

// Back to default
setIndicatorPreset('default');
```

