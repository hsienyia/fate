import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮")
st.title("🔮 紫微命盤抓取系統")
st.write("資料來源自動抓取自 [windada算命網](https://fate.windada.com/cgi-bin/fate)")

# --- 2. 建立網頁輸入介面 ---
col1, col2, col3 = st.columns(3)
with col1:
    year = st.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1990)
with col2:
    month = st.number_input("出生月", min_value=1, max_value=12, value=10)
with col3:
    day = st.number_input("出生日", min_value=1, max_value=31, value=10)

# 🔥 修正1：將時辰傳遞的數值改為「實際 24 小時制代表的小時數」
hours_map = {
    "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
    "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
    "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
    "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
}

hour_label = st.selectbox("請選擇出生時辰", list(hours_map.keys()))
gender_label = st.radio("請選擇性別", ["男", "女"], horizontal=True)

# --- 3. 抓取資料與顯示 ---
if st.button("開始排盤 🚀"):
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "0"

    with st.spinner("🤖 正在啟動智慧偵測模式，分析網站表單結構..."):
        try:
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://fate.windada.com/"
            }
            
            url = "https://fate.windada.com/cgi-bin/fate"
            
            first_page = session.get(url, headers=headers)
            first_page.encoding = 'utf-8'
            soup = BeautifulSoup(first_page.text, 'html.parser')
            form = soup.find('form')
            
            if not form:
                st.error("無法載入網站的輸入表單，可能被防護擋住了。")
                st.stop()
                
            payload = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name and input_tag.get('type') not in ['submit', 'reset']:
                    payload[name] = value
                    
            for select_tag in form.find_all('select'):
                name = select_tag.get('name')
                if name:
                    options = select_tag.find_all('option')
                    if options:
                        payload[name] = options[0].get('value', options[0].text)

            for key in payload.keys():
                k_low = key.lower()
                if "year" in k_low or key == "y":
                    payload[key] = str(year)
                elif "month" in k_low or key == "m":
                    payload[key] = str(month)
                elif "day" in k_low or key == "d":
                    payload[key] = str(day)
                elif "hour" in k_low or key == "h" or "time" in k_low:
                    payload[key] = hour_val
                elif "sex" in k_low or "gen" in k_low:
                    payload[key] = gender_val

            action_url = form.get('action')
            submit_url = urljoin(url, action_url) if action_url else url
            method = form.get('method', 'get').lower()

            if method == 'post':
                res = session.post(submit_url, data=payload, headers=headers)
            else:
                res = session.get(submit_url, params=payload, headers=headers)
                
            res.encoding = 'utf-8'
            res_soup = BeautifulSoup(res.text, 'html.parser')
            
            found_table = None
            max_td_count = 0
            
            for table in res_soup.find_all('table'):
                text = table.get_text()
                td_count = len(table.find_all('td'))
                
                if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                    found_table = table
                    max_td_count = td_count
            
            if found_table:
                st.success("抓取成功！這才是真正的命盤 🎉")
                st.markdown("---")
                
                # 🔥 修正2：解決中間文字隱形的問題
                # 紫微命盤的正中間通常是一個大儲存格 (橫跨2格、直跨2格)
                for td in found_table.find_all('td'):
                    if td.get('colspan') == '2' and td.get('rowspan') == '2':
                        # 強制把中間格子的背景塗白、文字塗黑
                        td['style'] = 'background-color: #ffffff !important; color: #000000 !important; padding: 15px;'
                        # 拔掉原本網站自帶的顏色設定
                        for font in td.find_all('font'):
                            if font.has_attr('color'):
                                del font['color']
                
                # 幫整個表格加上乾淨的框線設計
                table_html = str(found_table).replace('<table', '<table border="1" style="width:100%; text-align:center; border-collapse: collapse; border-color: #555555; background-color: #ffffff; color: #000000;"')
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning("表單已經送出了，但網站還是沒有給出命盤。")

        except Exception as e:
            st.error(f"發生錯誤：{e}")
