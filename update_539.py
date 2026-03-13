import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import re

# Lottolyzer 台灣今彩539 的歷史頁面網址
URL = "https://lottolyzer.com/history/taiwan/daily-cash"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_latest_draw():
    print("🔄 正在連線至 lottolyzer.com 抓取最新開獎資料...")
    response = requests.get(URL, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 無法連線至網站，狀態碼：{response.status_code}")
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        # Lottolyzer 的開獎號碼通常放在 class="table" 裡面的 tbody 的第一個 tr
        table = soup.find('table')
        latest_row = table.find('tbody').find_all('tr')[0]
        columns = latest_row.find_all('td')
        
        # 1. 取得日期並轉換格式為 MM/DD
        raw_date = columns[1].text.strip()
        date_obj = datetime.strptime(raw_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%m/%d')
        
        # 2. 取得 5 個號碼 (使用正規表達式暴力萃取)
        raw_numbers_text = columns[2].text 
        extracted_numbers = re.findall(r'\d+', raw_numbers_text)
        numbers = [n.zfill(2) for n in extracted_numbers][:5] 
        
        if len(numbers) != 5:
            print(f"❌ 號碼解析錯誤，抓到的數量不正確：{numbers}")
            print(f"🔍 程式看到的原始文字為：{raw_numbers_text.strip()}")
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
        
    # 將最新資料組合成一行字串 (例如: 03/13,05,12,23,34,39)
    new_row = ",".join(latest_data)
    
    # 🔴 核心修改：同時檢查「日期」與「號碼」組合是否已經存在
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