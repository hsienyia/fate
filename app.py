import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統 (兩階段拆解版)")
st.write("完全模擬網站流程：先取得本命盤 ➔ 再疊加流時盤")

# --- 初始化暫存區 (記憶兩階段的資料) ---
if "step1_done" not in st.session_state:
    st.session_state.step1_done = False
if "cookies" not in st.session_state:
    st.session_state.cookies = None
if "birth_chart" not in st.session_state:
    st.session_state.birth_chart = None
if "transit_form_html" not in st.session_state:
    st.session_state.transit_form_html = ""
if "transit_form_data" not in st.session_state:
    st.session_state.transit_form_data = {}
if "submit_url" not in st.session_state:
    st.session_state.submit_url = ""
if "transit_chart" not in st.session_state:
    st.session_state.transit_chart = None
if "transit_header" not in st.session_state:
    st.session_state.transit_header = ""

now = datetime.datetime.now()

# --- 2. 建立網頁輸入介面 ---
col_left, col_right = st.columns(2)

with col_left:
    st.success("### 步驟一：輸入本命資料")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1992)
        month = c2.number_input("出生月", min_value=1, max_value=12, value=6)
        day = c3.number_input("出生日", min_value=1, max_value=31, value=18)
        
        hours_map = {
            "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
            "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
            "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
            "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
        }
        
        c4, c5 = st.columns(2)
        hour_label = c4.selectbox("出生時辰", list(hours_map.keys()), index=8)
        gender_label = c5.radio("性別", ["男", "女"], horizontal=True)
        
        # 第一步按鈕：完全還原你之前 100% 成功的寫法，先抓取空表單金鑰再送出！
        if st.button("1️⃣ 開始排本命盤", use_container_width=True):
            hour_val = hours_map[hour_label]
            gender_val = "1" if gender_label == "男" else "0"
            
            with st.spinner("正在破解表單防護並抓取本命盤..."):
                try:
                    session = requests.Session()
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                        "Referer": "https://fate.windada.com/"
                    }
                    url = "https://fate.windada.com/cgi-bin/fate"
                    
                    # 1. 先去拿網頁的隱藏金鑰 (這是成功關鍵！)
                    first_page = session.get(url, headers=headers)
                    first_page.encoding = 'utf-8'
                    soup = BeautifulSoup(first_page.text, 'html.parser')
                    form = soup.find('form')
                    
                    if not form:
                        st.error("無法載入輸入表單。")
                        st.stop()
                        
                    payload = {}
                    for input_tag in form.find_all('input'):
                        name = input_tag.get('name')
                        if name and input_tag.get('type') not in ['submit', 'reset']:
                            payload[name] = input_tag.get('value', '')
                            
                    for select_tag in form.find_all('select'):
                        name = select_tag.get('name')
                        if name:
                            opts = select_tag.find_all('option')
                            if opts: payload[name] = opts[0].get('value', opts[0].text)

                    # 2. 注入你的本命資料
                    for key in list(payload.keys()):
                        k_low = key.lower()
                        if "year" in k_low or key == "y": payload[key] = str(year)
                        elif "month" in k_low or key == "m": payload[key] = str(month)
                        elif "day" in k_low or key == "d": payload[key] = str(day)
                        elif "hour" in k_low or key == "h" or "time" in k_low: payload[key] = hour_val
                        elif "sex" in k_low or "gen" in k_low: payload[key] = gender_val

                    action_url = form.get('action')
                    submit_url = urljoin(url, action_url) if action_url else url
                    method = form.get('method', 'get').lower()

                    # 3. 發送取得本命盤
                    if method == 'post':
                        res_birth = session.post(submit_url, data=payload, headers=headers)
                    else:
                        res_birth = session.get(submit_url, params=payload, headers=headers)
                    
                    res_birth.encoding = 'utf-8'
                    birth_soup = BeautifulSoup(res_birth.text, 'html.parser')
                    
                    # 儲存 Session Cookies 供第二步使用 (保持連線狀態)
                    st.session_state.cookies = session.cookies.get_dict()
                    
                    # 4. 尋找真正的本命盤表格
                    birth_table = None
                    max_td_count = 0
                    for table in birth_soup.find_all('table'):
                        text = table.get_text()
                        td_count = len(table.find_all('td'))
                        if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                            birth_table = table
                            max_td_count = td_count
                            
                    if birth_table:
                        st.session_state.birth_chart = str(birth_table)
                        
                        # 5. 攔截第二步的流轉表單金鑰，偷偷存起來
                        transit_form = birth_soup.find('form')
                        t_payload = {}
                        if transit_form:
                            st.session_state.transit_form_html = str(transit_form) # 存下表單結構供第二步找按鈕用
                            for inp in transit_form.find_all('input'):
                                name = inp.get('name')
                                if name and inp.get('type') not in ['submit', 'reset', 'button']:
                                    t_payload[name] = inp.get('value', '')
                            for sel in transit_form.find_all('select'):
                                name = sel.get('name')
                                if name:
                                    selected = sel.find('option', selected=True)
                                    t_payload[name] = selected.get('value', selected.text) if selected else sel.find('option').get('value', '')
                            
                            st.session_state.transit_form_data = t_payload
                            t_action = transit_form.get('action')
                            st.session_state.submit_url = urljoin(submit_url, t_action) if t_action else submit_url
                            
                            st.session_state.step1_done = True
                            st.session_state.transit_chart = None # 重置舊的流時盤
                            st.rerun() # 自動重整網頁顯示右側
                    else:
                        st.error("未能成功解析到命盤表格，可能是防護阻擋，請再試一次。")

                except Exception as e:
                    st.error(f"第一步發生錯誤：{e}")

with col_right:
    st.info("### 步驟二：設定流轉日期")
    with st.container(border=True):
        tc1, tc2, tc3 = st.columns(3)
        t_year = tc1.number_input("欲查年份", min_value=1900, max_value=2100, value=2026)
        t_month = tc2.number_input("欲查月份", min_value=1, max_value=12, value=5)
        t_day = tc3.number_input("欲查日期", min_value=1, max_value=31, value=23)
        
        tc4, tc5 = st.columns(2)
        t_hour_label = tc4.selectbox("欲查時辰", list(hours_map.keys()), key="t_hour_select")
        transit_start = tc5.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)
        transit_type = st.radio("查詢模式", ["流年", "流月", "流日", "流時"], index=3, horizontal=True)

        # 第二步按鈕：精準發送流轉設定，且不覆蓋本命資料
        if st.button("2️⃣ 疊加流轉盤", use_container_width=True, disabled=not st.session_state.step1_done):
            t_hour_val = hours_map[t_hour_label]
            
            with st.spinner("正在計算..."):
                try:
                    # --- DEBUG 模式：印出目前的表單結構 ---
                    st.write("--- 偵錯：目前的 Payload ---")
                    
                    # 複製一份原本的數據
                    final_payload = st.session_state.transit_form_data.copy()
                    
                    # 注入時間參數
                    final_payload['FateYear'] = str(t_year)
                    final_payload['FateMonth'] = str(t_month)
                    final_payload['FateDay'] = str(t_day)
                    final_payload['FateHour'] = t_hour_val
                    
                    # 關鍵點：找出網站判定流時的那個按鈕的值 (例如 'caltime')
                    # 這裡我們強行印出來看看它到底是什麼
                    st.write(final_payload) 
                    
                    # 執行請求 (保持不變)
                    session = requests.Session()
                    if st.session_state.cookies: session.cookies.update(st.session_state.cookies)
                    
                    # ... (發送請求後) ...
                    
                    # --- DEBUG 模式：檢查伺服器回傳的真實 URL ---
                    st.write(f"送出網址: {st.session_state.submit_url}")
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                        "Referer": "https://fate.windada.com/"
                    }
                    
                    # 載入步驟一偷存的隱藏金鑰
                    final_payload = st.session_state.transit_form_data.copy()
                    
                    # 1. 精準覆寫流轉專用參數，使用防呆大小寫比對
                    for key in list(final_payload.keys()):
                        k_low = key.lower()
                        if k_low == 'fatesolar': final_payload[key] = "1"  # 1為國曆
                        elif k_low == 'fateyear': final_payload[key] = str(t_year)
                        elif k_low == 'fatemonth': final_payload[key] = str(t_month)
                        elif k_low == 'fateday': final_payload[key] = str(t_day)
                        elif k_low == 'fatehour': final_payload[key] = str(t_hour_val)
                        elif k_low == 'target': final_payload[key] = "0" if transit_start == "流年本宮" else "1"
                    
                    # 2. 智慧尋找網頁上真正的「按鈕名稱」並點擊
                    transit_soup = BeautifulSoup(st.session_state.transit_form_html, 'html.parser')
                    btn_found = False
                    for btn in transit_soup.find_all(['input', 'button']):
                        if btn.get('type') in ['submit', 'button'] and transit_type in btn.get('value', ''):
                            final_payload[btn.get('name')] = btn.get('value')
                            btn_found = True
                            break
                            
                    # 若動態尋找失敗的備用方案
                    if not btn_found:
                        btn_mapping = {"流年": "calyear", "流月": "calmonth", "流日": "calday", "流時": "caltime"}
                        final_payload[btn_mapping.get(transit_type, 'calday')] = transit_type
                    
                    # 3. 發送請求
                    res_transit = session.post(st.session_state.submit_url, data=final_payload, headers=headers)
                    res_transit.encoding = 'utf-8'
                    transit_soup_res = BeautifulSoup(res_transit.text, 'html.parser')
                    
                    # 4. 尋找並儲存第二頁的流時盤表格
                    transit_table = None
                    max_td_count = 0
                    for table in transit_soup_res.find_all('table'):
                        text = table.get_text()
                        td_count = len(table.find_all('td'))
                        if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                            transit_table = table
                            max_td_count = td_count
                            
                    # 5. 抓取好運指數等標題
                    t_header = ""
                    for center_tag in transit_soup_res.find_all('center'):
                        if "好運指數" in center_tag.text or transit_type in center_tag.text:
                            for child in center_tag.children:
                                if getattr(child, 'name', None) == 'table': break
                                t_header += str(child)
                            break
                    
                    if transit_table:
                        st.session_state.transit_chart = str(transit_table)
                        st.session_state.transit_header = t_header
                        st.rerun()
                    else:
                        st.error("未能成功抓取到流時盤，請確認參數。")

                except Exception as e:
                    st.error(f"第二步發生錯誤：{e}")

st.markdown("---")

# --- 3. 畫面顯示區 (原汁原色雙盤並列) ---
out_left, out_right = st.columns(2)

with out_left:
    st.markdown("<h3 style='text-align: center;'>🪐 本命盤</h3>", unsafe_allow_html=True)
    if st.session_state.birth_chart:
        st.markdown(st.session_state.birth_chart, unsafe_allow_html=True)
    else:
        st.info("請先點擊左側「1️⃣ 開始排本命盤」。")

with out_right:
    st.markdown("<h3 style='text-align: center;'>⚡ 流轉運勢盤</h3>", unsafe_allow_html=True)
    if st.session_state.transit_chart:
        st.markdown(f"<div style='text-align: center;'>{st.session_state.transit_header}</div>", unsafe_allow_html=True)
        st.markdown(st.session_state.transit_chart, unsafe_allow_html=True)
    elif st.session_state.step1_done:
        st.info("本命盤已就緒！請設定上方流轉日期後，點擊「2️⃣ 疊加流轉盤」。")
    else:
        st.info("等待步驟一完成。")
