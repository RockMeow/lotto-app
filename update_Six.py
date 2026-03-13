import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import re
import time

# Lottolyzer 香港六合彩的歷史頁面網址
URL = "https://lottolyzer.com/history/hong-kong/mark-six"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

def fetch_latest_draw():
    request_url = f"{URL}?v={int(time.time())}"
    print("🔄 正在連線至 lottolyzer.com 抓取最新六合彩開獎資料...")
    response = requests.get(request_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 無法連線至網站，狀態碼：{response.status_code}")
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        table = soup.find('table')
        latest_row = table.find('tbody').find_all('tr')[0]
        columns = latest_row.find_all('td')
        
        # 🔍 透視眼：印出網站給我們的原始字串
        print(f"🔍 網站給的原始資料：{latest_row.get_text(separator=' | ').strip()}")
        
        # 1. 智慧尋找「日期」，並記錄它在哪一個欄位
        formatted_date = None
        date_col_idx = -1
        
        for idx, td in enumerate(columns):
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', td.text)
            if date_match:
                formatted_date = f"{date_match.group(2)}/{date_match.group(3)}"
                date_col_idx = idx
                break
                
        if not formatted_date:
            print("❌ 找不到日期格式")
            return None
        
        # 2. 跨欄位地毯式搜索：掃描日期「之後」的所有欄位
        numbers = []
        for idx in range(date_col_idx + 1, len(columns)):
            # stripped_strings 會無視 HTML 結構，把每個文字片段分開，完美解決號碼黏在一起的問題
            for string_piece in columns[idx].stripped_strings:
                extracted = re.findall(r'\d+', string_piece)
                for n in extracted:
                    if 1 <= int(n) <= 49:
                        numbers.append(n.zfill(2))
                        
        # 只要集滿 7 顆有效號碼 (6 正碼 + 1 特別號) 即可
        if len(numbers) >= 7:
            numbers = numbers[:7]
        else:
            print(f"❌ 號碼解析錯誤，只找到 {len(numbers)} 個 1~49 的有效號碼。抓到的號碼：{numbers}")
            return None
            
        print(f"✅ 成功抓取最新一期！日期：{formatted_date}，正碼：{numbers[:6]}，特別號：{numbers[6]}")
        return [formatted_date] + numbers
        
    except Exception as e:
        print(f"❌ 解析網頁時發生錯誤：{e}")
        return None

def update_csv(latest_data):
    csv_filename = 'Six_history_all_sorted.csv'
    
    if not os.path.exists(csv_filename):
        with open(csv_filename, 'w', encoding='utf-8') as f:
            f.write("Date,N1,N2,N3,N4,N5,N6,Special\n")
            
    with open(csv_filename, 'r', encoding='utf-8') as f:
        existing_data = f.read()
        
    new_row = ",".join(latest_data)
    
    if new_row not in existing_data:
        with open(csv_filename, 'a', encoding='utf-8') as f:
            if existing_data and not existing_data.endswith('\n'):
                f.write('\n')
            f.write(new_row + '\n')
        print(f"💾 檔案寫入成功！已新增：【{new_row}】")
    else:
        print(f"⚡ 開獎紀錄 【{new_row}】 已經存在 CSV 中，略過更新。")

if __name__ == '__main__':
    latest_data = fetch_latest_draw()
    if latest_data:
        update_csv(latest_data)