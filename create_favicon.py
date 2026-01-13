#!/usr/bin/env python3
"""
Favicon Creator Script
This script converts an image to favicon formats (ICO and PNG)

Usage:
    python3 create_favicon.py path/to/image.png

Requirements:
    pip install Pillow
"""

import sys
from PIL import Image
import os

def create_favicon(input_path, output_dir='static/images'):
    """Convert an image to favicon formats"""
    
    if not os.path.exists(input_path):
        print(f"❌ Error: File not found: {input_path}")
        return False
    
    try:
        # Open the image
        print(f"📂 Opening image: {input_path}")
        img = Image.open(input_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            print("🎨 Converting RGBA to RGB...")
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        elif img.mode != 'RGB':
            print(f"🎨 Converting {img.mode} to RGB...")
            img = img.convert('RGB')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save as PNG (32x32 for web use)
        png_path = os.path.join(output_dir, 'favicon.png')
        print(f"💾 Creating PNG favicon (32x32): {png_path}")
        img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
        img_32.save(png_path, format='PNG')
        
        # Save as ICO with multiple sizes
        ico_path = os.path.join(output_dir, 'favicon.ico')
        print(f"💾 Creating ICO favicon (16x16, 32x32, 48x48): {ico_path}")
        img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
        
        print(f"\n✅ Success! Favicon files created:")
        print(f"   - {png_path}")
        print(f"   - {ico_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating favicon: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 create_favicon.py path/to/image.png")
        print("\nExample:")
        print("  python3 create_favicon.py dragonfly.png")
        sys.exit(1)
    
    input_image = sys.argv[1]
    create_favicon(input_image)
