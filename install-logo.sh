#!/bin/bash

# Logo Installation Helper Script
# This script helps you place the logo file in the correct location

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Tâm Thẩm Mỹ Viện Logo Installation Helper            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Required Location:"
echo "   /Users/thuanle/Documents/Ctv/static/images/tam-logo.png"
echo ""
echo "📋 Steps to Install:"
echo "   1. Save your logo image as 'tam-logo.png'"
echo "   2. Place it in: /Users/thuanle/Documents/Ctv/static/images/"
echo "   3. Refresh your browser to see the logo"
echo ""
echo "✨ Logo Specifications:"
echo "   • Format: PNG (with transparent background preferred)"
echo "   • Minimum Size: 200x200 pixels"
echo "   • Recommended: 400x400 pixels or higher"
echo "   • Color: The gold/tan colors will complement the theme"
echo ""
echo "📍 Where the Logo Appears:"
echo "   • Sidebar: 50x50px (left navigation panel)"
echo "   • Header: 80x80px (top of main content)"
echo "   • Responsive: Auto-scales on mobile/tablet"
echo ""
echo "✅ Checking if logo exists..."

if [ -f "/Users/thuanle/Documents/Ctv/static/images/tam-logo.png" ]; then
    echo "   ✓ Logo file found! You're all set."
    echo ""
    echo "   File details:"
    ls -lh "/Users/thuanle/Documents/Ctv/static/images/tam-logo.png"
else
    echo "   ✗ Logo file not found yet."
    echo "   ℹ  Please add tam-logo.png to the images directory."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
