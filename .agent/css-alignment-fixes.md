# Common CSS Alignment Issues & Fixes

## 1. Mobile Navigation Icon Vertical Misalignment

**Problem:** Icons in mobile bottom navigation are not vertically centered.

**Root Cause:** Desktop CSS uses `margin-top: auto` or `margin-bottom: auto` which pushes elements to edges. Mobile media queries may not override these with `!important`.

**Fix Pattern:**
```css
@media (max-width: 600px) {
    .sidebar-icon {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        align-self: center !important;
    }
}
```

**File:** `templates/dashboard.html` (lines 659-690)

---

## 2. Floating Button Overlapping Header Content

**Problem:** Fixed-position buttons (like Home button) overlap with header text.

**Symptoms:**
- Button covers brand name/logo
- Header content not visible on mobile

**Fix Pattern:**
```css
/* Push header content to make room for fixed button */
div[class*="lg:hidden"][class*="fixed"][class*="top-0"] {
    padding-left: 140px !important;
}

/* Position button at correct vertical center */
.mobile-home-btn {
    position: fixed;
    top: 12px;  /* (header_height - button_height) / 2 */
    left: 12px;
}
```

**File:** `static/catalogue/index.html` (mobile media query)

---

## 3. CSS Selector Not Working on React Components

**Problem:** Standard class selectors like `.fixed.top-0` don't work on React-generated elements.

**Fix Pattern:** Use attribute selectors instead:
```css
/* ❌ Won't work */
.fixed.top-0.left-0 { }

/* ✅ Works */
div[class*="fixed"][class*="top-0"][class*="left-0"] { }
```

---

## 4. Browser Cache Not Updating

**Problem:** Users don't see CSS changes without hard refresh.

**Fix Pattern:** Add Cache-Control headers in Flask:
```python
@app.route('/your-page')
def your_page():
    response = send_file('path/to/file.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
```

**File:** `backend.py` (line 95-103)

---

## 5. Hiding Elements in React Apps

**Problem:** Need to hide specific elements (like logos/icons) in a React app.

**Fix Pattern:**
```css
/* Hide first child (usually logo) of header container */
div[class*="lg:hidden"][class*="fixed"][class*="top-0"] > div:first-child > div:first-child {
    display: none !important;
}
```

---

## Quick Reference: Perfect Vertical Centering

**Formula:** `top = (container_height - element_height) / 2`

| Container Height | Element Height | Top Position |
|-----------------|----------------|--------------|
| 64px | 40px | 12px |
| 64px | 44px | 10px |
| 60px | 44px | 8px |
