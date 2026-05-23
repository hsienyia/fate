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

hours_map = {
    "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "1", "寅時 (03:00 - 05:00)": "2",
    "卯時 (05:00 - 07:00)": "3", "辰時 (07:00 - 09:00)": "4", "巳時 (09:00 - 11:00)": "5",
    "午時 (11:00 - 13:00)": "6", "未時 (13:00 - 15:00)": "7", "申時 (15:00 - 17:00)": "8",
    "酉時 (17:00 - 19:00)": "9", "戌時 (19:00 - 21:00)": "10", "亥時 (21:00 - 23:00)": "11"
}

hour_label = st.selectbox("請選擇出生時辰", list(hours_map.keys()))
gender_label = st.radio("請選擇性別", ["男", "女"], horizontal=True)

# --- 3. 抓取資料與顯示 ---
if st.button("開始排盤 🚀"):
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "0"

    with st.spinner("🤖 正在啟動智慧偵測模式，分析網站表單結構..."):
        try:
            # 使用 Session 保持連線狀態，讓網站覺得我們是一般使用者
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://fate.windada.com/"
            }
            
            url = "https://fate.windada.com/cgi-bin/fate"
            
            # 【第一步】：先去首頁，抓取它真實的表單
            first_page = session.get(url, headers=headers)
            first_page.encoding = 'utf-8'
            soup = BeautifulSoup(first_page.text, 'html.parser')
            form = soup.find('form')
            
            if not form:
                st.error("無法載入網站的輸入表單，可能被防護擋住了。")
                st.stop()
                
            # 【第二步】：收集表單內所有的預設欄位與隱藏金鑰
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

            # 【第三步】：智慧替換成我們的輸入值
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

            # 【第四步】：判斷要送到哪個網址
            action_url = form.get('action')
            submit_url = urljoin(url, action_url) if action_url else url
            method = form.get('method', 'get').lower()

            # 【第五步】：送出真正的排盤請求
            if method == 'post':
                res = session.post(submit_url, data=payload, headers=headers)
            else:
                res = session.get(submit_url, params=payload, headers=headers)
                
            res.encoding = 'utf-8'
            res_soup = BeautifulSoup(res.text, 'html.parser')
            
            # 【第六步】：嚴格尋找真正的紫微斗數命盤
            found_table = None
            max_td_count = 0
            
            for table in res_soup.find_all('table'):
                text = table.get_text()
                td_count = len(table.find_all('td'))
                
                # ✨ 關鍵條件：一定要有這些星星，才代表是算出來的結果！
                if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                    found_table = table
                    max_td_count = td_count
            
            if found_table:
                st.success("抓取成功！這才是真正的命盤 🎉")
                st.markdown("---")
                # 幫表格加上黑色實線框，看起來更專業
                table_html = str(found_table).replace('<table', '<table border="1" style="width:100%; text-align:center; border-collapse: collapse; border-color: gray;"')
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning("表單已經送出了，但網站還是沒有給出命盤。有可能是性別或時間格式網站有特殊規定。")
                # 💡 這個區塊是給我們抓蟲用的，如果失敗你可以截圖這裡給我看！
                with st.expander("👉 [除錯專用] 展開查看程式到底送了什麼資料給網站"):
                    st.write("送出的方法：", method)
                    st.write("送出的資料：", payload)

        except Exception as e:
            st.error(f"發生錯誤：{e}")
