#!/usr/bin/env python3
"""Quick batch import - imports 2000 records at a time"""
import csv
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 34643,
    'user': 'postgres', 
    'password': 'SEzzSwiBFYIHsnxJyEtorEBOadCZRUtl',
    'database': 'railway'
}

CSV_FILE = 'database/database_check_trung_khach_hang_tham_my.csv'
BATCH_SIZE = 2000

def parse_date(s):
    if not s or not s.strip(): return None
    for fmt in ['%d/%m/%Y', '%d/%m/%y']:
        try: return datetime.strptime(s.strip(), fmt).date()
        except: pass
    return None

def parse_money(s):
    if not s or not s.strip(): return 0
    try: return int(s.strip().replace('.','').replace(',',''))
    except: return 0

# Read CSV
with open(CSV_FILE, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
total = len(rows)

# Get current count
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM khach_hang')
start = cur.fetchone()[0]

print(f'Total rows: {total}, Already imported: {start}')

if start >= total:
    print('All rows already imported!')
else:
    end = min(start + BATCH_SIZE, total)
    print(f'Importing rows {start} to {end}...')
    
    for row in rows[start:end]:
        cur.execute('''INSERT INTO khach_hang 
            (ngay_nhap_don, ten_khach, sdt, co_so, ngay_hen_lam, gio, 
             dich_vu, tong_tien, tien_coc, phai_dong, nguoi_chot, ghi_chu, trang_thai)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (parse_date(row.get('Ngày nhập đơn','')),
             row.get('Tên khách','').strip()[:100],
             row.get('SĐT','').strip()[:15],
             row.get('Cơ Sở','').strip()[:100],
             parse_date(row.get('Ngày hẹn làm','')),
             row.get('Giờ','').strip()[:20],
             row.get('Dịch vụ','').strip()[:500],
             parse_money(row.get('Tổng','')),
             parse_money(row.get('Cọc','')),
             parse_money(row.get('phải đóng','')),
             row.get('Người chốt','').strip()[:50] or None,
             row.get('Ghi Chú','').strip(),
             row.get('Trạng Thái','').strip()[:50] or 'Cho xac nhan'))
    
    conn.commit()
    cur.execute('SELECT COUNT(*) FROM khach_hang')
    new_count = cur.fetchone()[0]
    print(f'Done! Now have {new_count} records')

cur.close()
conn.close()

