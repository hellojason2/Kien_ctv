import os
import json
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

# Config
SHEET_ID = '19YZB-SgpqvI3-hu93xOk0OCDWtUPxrAAfR6CiFpU4GY'
BASE_DIR = Path(__file__).parent.absolute()
CREDENTIALS_FILE = BASE_DIR / 'google_credentials.json'

def check_sheet():
    # Load Credentials
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    if CREDENTIALS_FILE.exists():
        creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
    else:
        print("Credentials file not found.")
        return

    client = gspread.authorize(creds)
    
    try:
        sheet = client.open_by_key(SHEET_ID)
        # Try to find a specific pricing tab or just use the first one
        worksheet = sheet.get_worksheet(0)
        
        print(f"Sheet Title: {sheet.title}")
        print(f"Worksheet Title: {worksheet.title}")
        
        # Read first 10 rows
        all_rows = worksheet.get_all_values()[:10]
        for i, row in enumerate(all_rows):
            print(f"Row {i+1}: {row}")
        
    except Exception as e:
        print(f"Error accessing sheet: {e}")

if __name__ == "__main__":
    check_sheet()
