import json
import logging
import re
import os
from pathlib import Path
from slugify import slugify

logger = logging.getLogger(__name__)

# Category Mapping to match existing HTML IDs and Icons
CATEGORY_MAP = {
    'FILLER HÀN CƠ BẢN': {'id': 'filler-basic', 'icon': '💉'},
    'FILLER HÀN CAO CẤP': {'id': 'filler-premium', 'icon': '✨'},
    'DỊCH VỤ NÂNG NGỰC': {'id': 'breast', 'icon': '🌸'},
    'TIÊM THON GỌN TỪNG VÙNG': {'id': 'slimming', 'icon': '💫'},
    'THON GỌN HÀM V-LINE PERFECT': {'id': 'vline', 'icon': '✓', 'match_fuzzy': True},
    'THON GỌN HÀM VLINE PERFECT': {'id': 'vline', 'icon': '✓'},  # Variation
    'DỊCH VỤ KHÁC': {'id': 'other', 'icon': '⚡'},
    'NÂNG MŨI': {'id': 'nose', 'icon': '👃'},
    'CÁC DỊCH VỤ VỀ MẮT': {'id': 'eyes', 'icon': '👁'},
    'DỊCH VỤ VỀ MẮT': {'id': 'eyes', 'icon': '👁'} # Variation
}

def clean_price(price):
    if not price: return ""
    # Ensure it ends with 'đ' if it's a number
    p = str(price).strip()
    if p.replace('.', '').replace(',', '').isdigit():
        return f"{p}đ"
    return p

def sync_pricing_sheet(client, sheet_id):
    """
    Sync pricing data from Google Sheet to static JSON file.
    """
    try:
        sheet = client.open_by_key(sheet_id)
        # Use first tab
        worksheet = sheet.get_worksheet(0)
        
        # Get all values
        rows = worksheet.get_all_values()
        
        categories = []
        current_category = None
        
        # Start scanning from row 3 (index 2)
        # Row 1: Empty
        # Row 2: Title
        # Row 3 onwards: Data
        
        for i, row in enumerate(rows):
            if i < 2: continue # Skip first 2 rows
            
            # Safe get columns
            col_b = row[1].strip() if len(row) > 1 else ""
            col_c = row[2].strip() if len(row) > 2 else "" # Price
            col_d = row[3].strip() if len(row) > 3 else "" # Bonus
            
            if not col_b: continue # Skip empty rows
            
            # Detect Category Header
            # Logic: Col B has text, Col C is empty or "GIÁ DỊCH VỤ" header
            is_header = (not col_c or col_c.upper() == "GIÁ DỊCH VỤ") and (col_b.isupper() or "DỊCH VỤ" in col_b.upper() or "FILLER" in col_b.upper())
            
            # Special case for "GIÁ DỊCH VỤ" row - skip it
            if col_c and "GIÁ DỊCH VỤ" in col_c.upper():
                continue
                
            if is_header and col_b not in ["1cc"]: # "1cc" is an item, not a header
                # Normalize header
                header_text = col_b.upper()
                
                # Find mapping
                cat_info = CATEGORY_MAP.get(header_text)
                if not cat_info:
                    # Fuzzy match attempts
                    for k, v in CATEGORY_MAP.items():
                        if v.get('match_fuzzy') and k in header_text:
                            cat_info = v
                            break
                
                # Default if not found
                if not cat_info:
                    cat_id = slugify(header_text)
                    cat_info = {'id': cat_id, 'icon': '🔹'}
                
                current_category = {
                    'id': cat_info['id'],
                    'name': col_b, # Keep original casing if desirable, or use header_text
                    'icon': cat_info['icon'],
                    'items': []
                }
                categories.append(current_category)
            
            elif current_category and col_c: # Item
                # Check for "Premium" or "Hot" keywords in name
                badge = None
                if "PREMIUM" in col_b.upper() or "JUVERDERM" in col_b.upper() or "SỤN MỸ" in col_b.upper() or "SỤN SUGIFORM" in col_b.upper() or "BOTOX MỸ" in col_b.upper():
                    badge = "Premium"
                if "NANO ERGONOMIX" in col_b.upper():
                    badge = "Hot"
                
                item = {
                    'name': col_b,
                    'price': clean_price(col_c),
                    'bonus': col_d,
                    'badge': badge
                }
                current_category['items'].append(item)
                
        # Save to JSON
        output_file = Path(os.getcwd()) / 'static' / 'data' / 'pricing.json'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'categories': categories, 'updated_at': str(import_time())}, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Successfully synced pricing data: {len(categories)} categories")
        return len(categories)
        
    except Exception as e:
        logger.error(f"Error syncing pricing sheet: {e}")
        return 0

def import_time():
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y %H:%M")

if __name__ == "__main__":
    # Test run
    from modules.google_sync import GoogleSheetSync
    logging.basicConfig(level=logging.INFO)
    syncer = GoogleSheetSync()
    client = syncer.get_google_client()
    # Sheet ID from user request
    SHEET_ID = '19YZB-SgpqvI3-hu93xOk0OCDWtUPxrAAfR6CiFpU4GY' 
    sync_pricing_sheet(client, SHEET_ID)
