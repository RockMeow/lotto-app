import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import re
import time

URL = "https://lottolyzer.com/history/taiwan/daily-cash"

# 加入防快取的 Header
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

def fetch_latest_draw():
    # 加入隨機時間戳記，強制打破 Cloudflare 快取，確保拿到最新開獎
    request_url = f"{URL}?v={int(time.time())}"
    print("🔄 正在連線至 lottolyzer.com 抓取最新開獎資料...")
    response = requests.get(request_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 無法連線至網站，狀態碼：{response.status_code}")
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        table = soup.find('table')
        latest_row = table.find('tbody').find_all('tr')[0]
        columns = latest_row.find_all('td')
        
        # 1. 智慧尋找「日期」 (自動掃描整列，不依賴固定欄位)
        formatted_date = None
        for td in columns:
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', td.text)
            if date_match:
                formatted_date = f"{date_match.group(2)}/{date_match.group(3)}"
                break
                
        if not formatted_date:
            print("❌ 找不到日期格式")
            return None
        
        # 2. 智慧尋找「開獎號碼」 (嚴格過濾 1~39 的數字)
        numbers = []
        for td in columns:
            # 略過剛剛找到日期的那個欄位，以免把月份日期當成號碼
            if date_match.group(0) in td.text:
                continue
                
            # 抓出該欄位內所有數字
            extracted = re.findall(r'\b\d{1,2}\b', td.text)
            
            # 🔴 核心過濾器：必須是 1 到 39 之間的數字，徹底排除 65 或期數
            valid = [n.zfill(2) for n in extracted if n.isdigit() and 1 <= int(n) <= 39]
            
            # 如果這個欄位包含 5 個以上的有效號碼，那這欄絕對就是開獎號碼！
            if len(valid) >= 5:
                numbers = valid[:5]
                break
        
        if len(numbers) != 5:
            print(f"❌ 號碼解析錯誤，找不到 5 個 1~39 的有效號碼。")
            return None
            
        print(f"✅ 成功抓取最新一期！日期：{formatted_date}，號碼：{numbers}")
        return [formatted_date] + numbers
        
    except Exception as e:
        print(f"❌ 解析網頁時發生錯誤：{e}")
        return None

def update_csv(latest_data):
    csv_filename = '539_history_all_sorted.csv'
    
    # 確保 CSV 檔案存在，如果不存在就先建一個並寫入標頭
    if not os.path.exists(csv_filename):
        with open(csv_filename, 'w', encoding='utf-8') as f:
            f.write("Date,N1,N2,N3,N4,N5\n")
            
    # 讀取現有資料
    with open(csv_filename, 'r', encoding='utf-8') as f:
        existing_data = f.read()
        
    latest_date = latest_data[0]
    new_row = ",".join(latest_data)
    
    # 確保日期和號碼的組合完全沒出現過，才寫入檔案
    if new_row not in existing_data:
        with open(csv_filename, 'a', encoding='utf-8') as f:
            # 確保結尾有換行符號再寫入
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