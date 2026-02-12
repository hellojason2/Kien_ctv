import json
import logging
import re
import os
import time
from pathlib import Path
from slugify import slugify

logger = logging.getLogger(__name__)

# Resolve project root from this file's location (modules/pricing_sync.py -> project root)
BASE_DIR = Path(__file__).parent.parent.absolute()

# Retry config for transient Google API errors
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5  # seconds
RETRYABLE_CODES = [429, 500, 503]

# Category Mapping to match existing HTML IDs and Icons
# These map to the exact headers found in the Google Sheet
CATEGORY_MAP = {
    # Cosmetic/Beauty services
    'FILLER HÀN CƠ BẢN': {'id': 'filler-basic', 'icon': '💉'},
    'FILLER HÀN CAO CẤP': {'id': 'filler-premium', 'icon': '✨'},
    'DỊCH VỤ NÂNG NGỰC': {'id': 'breast', 'icon': '🌸'},
    'TIÊM THON GỌN TỪNG VÙNG': {'id': 'slimming', 'icon': '💫'},
    'THON GỌN HÀM V-LINE PERFECT': {'id': 'vline', 'icon': '✓', 'match_fuzzy': True},
    'THON GỌN HÀM VLINE PERFECT': {'id': 'vline', 'icon': '✓'},
    'DỊCH VỤ KHÁC': {'id': 'other', 'icon': '⚡'},
    'NÂNG MŨI': {'id': 'nose', 'icon': '👃'},
    'CÁC DỊCH VỤ VỀ MẮT': {'id': 'eyes', 'icon': '👁'},
    'DỊCH VỤ VỀ MẮT': {'id': 'eyes', 'icon': '👁'},
    'THẨM MỸ CÔ BÉ': {'id': 'intimate', 'icon': '🌺'},
    'CĂNG DA MEDI LIFT': {'id': 'facelift', 'icon': '✨'},
    'THẨM MỸ CÔNG NGHỆ CAO': {'id': 'high-tech', 'icon': '🔬'},
    
    # Nâng cơ (mixed case in sheet)
    'NÂNG CƠ TÁO': {'id': 'apple-lift', 'icon': '🍎', 'match_fuzzy': True},
    
    # Dental services - 🦷 tooth icon (exact headers from Google Sheet)
    'RĂNG SỨ THẨM MỸ': {'id': 'porcelain', 'icon': '🦷'},
    'TRỒNG RĂNG IMPLANT': {'id': 'implant', 'icon': '🦷'},
    'NIỀNG RĂNG MẮC CÀI KIM LOẠI': {'id': 'braces-metal', 'icon': '🦷'},
    'NIỀNG RĂNG MẮC CÀI SỨ': {'id': 'braces-ceramic', 'icon': '🦷'},
}

# Keywords that indicate a row is a category header even if not fully uppercase
HEADER_KEYWORDS = [
    'FILLER', 'DỊCH VỤ', 'NÂNG MŨI', 'NÂNG NGỰC', 'THON GỌN', 'VLINE',
    'THẨM MỸ', 'CĂNG DA', 'NÂNG CƠ', 'CÔNG NGHỆ',
    'RĂNG SỨ', 'IMPLANT', 'MẮC CÀI', 'NIỀNG RĂNG', 'TRỒNG RĂNG',
]

# Sub-section labels in the sheet that should NOT be treated as categories
# These are visual dividers with no price, just formatting text
SUB_SECTION_SKIP = [
    'MẮC CÀI KIM LOẠI TIÊU CHUẨN', 'MẮC CÀI KIM LOẠI TỰ ĐÓNG',
    'MẮC CÀI KIM LOẠI TỰ ĐÓNG DAMON ULTIMA', 
    'MẮC CÀI SỨ TIÊU CHUẨN', 'MẮC CÀI SỨ TỰ ĐÓNG',
    'BẢNG GIÁ THẨM MỸ VIỆN TẤM',
]

def clean_price(price):
    if not price: return ""
    p = str(price).strip()
    if p.replace('.', '').replace(',', '').isdigit():
        return f"{p}đ"
    return p


def _is_retryable_error(error):
    """Check if an error is a transient Google API error worth retrying."""
    error_str = str(error)
    for code in RETRYABLE_CODES:
        if f'[{code}]' in error_str:
            return True
    if 'RemoteDisconnected' in error_str or 'Connection aborted' in error_str:
        return True
    if 'ServiceUnavailable' in error_str or 'Internal error' in error_str:
        return True
    return False


def _fetch_sheet_data_with_retry(client, sheet_id):
    """Fetch data from Google Sheet with retry logic for transient errors."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.get_worksheet(0)
            rows = worksheet.get_all_values()
            if attempt > 1:
                logger.info(f"  Pricing sheet fetch succeeded on attempt {attempt}")
            return rows
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES and _is_retryable_error(e):
                delay = RETRY_BASE_DELAY * (3 ** (attempt - 1))  # 5s, 15s, 45s
                logger.warning(f"  Pricing fetch attempt {attempt}/{MAX_RETRIES} failed: {e}")
                logger.warning(f"  Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise last_error


def sync_pricing_sheet(client, sheet_id):
    """
    Sync pricing data from Google Sheet to static JSON file.
    Includes retry logic for transient Google API errors.
    """
    try:
        rows = _fetch_sheet_data_with_retry(client, sheet_id)
        
        categories = []
        current_category = None
        
        for i, row in enumerate(rows):
            if i < 2: continue

            col_b = row[1].strip() if len(row) > 1 else ""
            col_c = row[2].strip() if len(row) > 2 else ""
            col_d = row[3].strip() if len(row) > 3 else ""
            
            if not col_b: continue

            has_price = bool(col_c) and col_c.upper() != "GIÁ DỊCH VỤ"
            col_b_upper = col_b.upper()
            
            # Skip "GIÁ DỊCH VỤ" price-header rows
            if col_c and "GIÁ DỊCH VỤ" in col_c.upper():
                continue
            
            # Skip sub-section labels (visual dividers, not real categories)
            if not has_price and any(skip in col_b_upper for skip in SUB_SECTION_SKIP):
                continue
            
            # Skip note/disclaimer rows (long text without price)
            if not has_price and len(col_b) > 80:
                continue
            
            # Detect category headers: no price + (uppercase OR contains known keyword)
            has_keyword = any(kw in col_b_upper for kw in HEADER_KEYWORDS)
            is_header = not has_price and (col_b.isupper() or has_keyword)
                
            if is_header and col_b not in ["1cc"]:
                header_text = col_b.upper()
                
                cat_info = CATEGORY_MAP.get(header_text)
                if not cat_info:
                    for k, v in CATEGORY_MAP.items():
                        if v.get('match_fuzzy') and k in header_text:
                            cat_info = v
                            break
                
                if not cat_info:
                    cat_id = slugify(header_text)
                    cat_info = {'id': cat_id, 'icon': '🔹'}
                
                current_category = {
                    'id': cat_info['id'],
                    'name': col_b,
                    'icon': cat_info['icon'],
                    'items': []
                }
                categories.append(current_category)
            
            elif current_category and col_c:
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
        
        # Keep categories exactly as they appear in the Google Sheet
        categories = [c for c in categories if len(c['items']) > 0]
                
        # Save to JSON using __file__-based path (reliable in production)
        output_file = BASE_DIR / 'static' / 'data' / 'pricing.json'
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
    from modules.google_sync import GoogleSheetSync
    logging.basicConfig(level=logging.INFO)
    syncer = GoogleSheetSync()
    client = syncer.get_google_client()
    SHEET_ID = '19YZB-SgpqvI3-hu93xOk0OCDWtUPxrAAfR6CiFpU4GY' 
    sync_pricing_sheet(client, SHEET_ID)
