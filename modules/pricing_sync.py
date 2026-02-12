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
    
    # Dental services - 🦷 tooth icon
    'DỊCH VỤ NHA KHOA': {'id': 'dental', 'icon': '🦷'},
    'NHA KHOA': {'id': 'dental', 'icon': '🦷'},
    'IMPLANT': {'id': 'implant', 'icon': '🦷'},
    'MẮC CÀI KIM LOẠI TIÊU CHUẨN': {'id': 'braces-metal', 'icon': '🦷'},
    'MẮC CÀI KIM LOẠI TỰ ĐÓNG': {'id': 'braces-self', 'icon': '🦷'},
    'MẮC CÀI SỨ TIÊU CHUẨN': {'id': 'braces-ceramic', 'icon': '🦷'},
    'MẮC CÀI SỨ TỰ ĐÓNG': {'id': 'braces-ceramic-self', 'icon': '🦷'},
    'MẮC CÀI KIM LOẠI TỰ ĐÓNG DAMON ULTIMA (MỚI)': {'id': 'braces-damon', 'icon': '🦷'},
    'RĂNG SỨ': {'id': 'porcelain', 'icon': '🦷'},
    'TRÁM RĂNG': {'id': 'filling', 'icon': '🦷'},
    'TẨY TRẮNG RĂNG': {'id': 'whitening', 'icon': '🦷'},
    'NHỔ RĂNG': {'id': 'extraction', 'icon': '🦷'},
}

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

            is_header = (not col_c or col_c.upper() == "GIÁ DỊCH VỤ") and (col_b.isupper() or "DỊCH VỤ" in col_b.upper() or "FILLER" in col_b.upper())
            
            if col_c and "GIÁ DỊCH VỤ" in col_c.upper():
                continue
                
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
        
        # === POST-PROCESSING: Extract dental items into separate category ===
        DENTAL_KEYWORDS = [
            'IMPLANT', 'MẮC CÀI', 'VENEER', 'RĂNG SỨ', 'RĂNG', 'NHA KHOA',
            'TRÁM', 'TẨY TRẮNG', 'NHỔ', 'NIỀNG', 'CHỈ NHA', 'SỨ'
        ]
        
        dental_category = {
            'id': 'dental',
            'name': 'DỊCH VỤ NHA KHOA',
            'icon': '🦷',
            'items': []
        }
        
        for cat in categories:
            items_to_keep = []
            for item in cat['items']:
                item_upper = item['name'].upper()
                is_dental = any(kw in item_upper for kw in DENTAL_KEYWORDS)
                
                if is_dental:
                    dental_category['items'].append(item)
                else:
                    items_to_keep.append(item)
            
            cat['items'] = items_to_keep
        
        categories = [c for c in categories if len(c['items']) > 0]
        
        if len(dental_category['items']) > 0:
            categories.append(dental_category)
                
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
