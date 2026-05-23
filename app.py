import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統 (兩階段拆解版)")
st.write("完全模擬網站流程：先取得本命盤 ➔ 再疊加流時盤")

# --- 初始化暫存區 (用來記憶第一步的資料與連線狀態) ---
if "step1_done" not in st.session_state:
    st.session_state.step1_done = False
if "cookies" not in st.session_state:
    st.session_state.cookies = None
if "birth_chart" not in st.session_state:
    st.session_state.birth_chart = None
if "transit_form_data" not in st.session_state:
    st.session_state.transit_form_data = {}
if "submit_url" not in st.session_state:
    st.session_state.submit_url = "https://fate.windada.com/cgi-bin/fate"
if "transit_chart" not in st.session_state:
    st.session_state.transit_chart = None
if "transit_header" not in st.session_state:
    st.session_state.transit_header = ""

now = datetime.datetime.now()

# --- 2. 建立網頁輸入介面 (分為左右兩大步驟) ---
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
        
        # 第一步的按鈕
        if st.button("1️⃣ 開始排本命盤", use_container_width=True):
            hour_val = hours_map[hour_label]
            gender_val = "1" if gender_label == "男" else "0"
            
            with st.spinner("正在抓取本命盤..."):
                try:
                    session = requests.Session()
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
                    url = "https://fate.windada.com/cgi-bin/fate"
                    
                    # 獲取表單結構
                    res_init = session.get(url, headers=headers)
                    res_init.encoding = 'utf-8'
                    soup_init = BeautifulSoup(res_init.text, 'html.parser')
                    form = soup_init.find('form')
                    
                    payload = {}
                    for inp in form.find_all('input'):
                        if inp.get('name') and inp.get('type') not in ['submit', 'reset']:
                            payload[inp.get('name')] = inp.get('value', '')
                    for sel in form.find_all('select'):
                        if sel.get('name'):
                            opts = sel.find_all('option')
                            if opts: payload[sel.get('name')] = opts[0].get('value', opts[0].text)

                    # 🔥 補回漏掉的關鍵參數：type 和 place
                    payload.update({
                        "year": str(year), "month": str(month), "day": str(day), 
                        "hour": hour_val, "sex": gender_val,
                        "type": "find", "place": "1"
                    })
                    
                    action_url = urljoin(url, form.get('action'))
                    res_birth = session.post(action_url, data=payload, headers=headers)
                    res_birth.encoding = 'utf-8'
                    birth_soup = BeautifulSoup(res_birth.text, 'html.parser')
                    
                    # 儲存連線的 Cookies 給第二步用
                    st.session_state.cookies = session.cookies.get_dict()
                    
                    # 儲存本命盤 HTML
                    for table in birth_soup.find_all('table'):
                        if "紫微" in table.get_text() and "天機" in table.get_text():
                            st.session_state.birth_chart = str(table)
                            break
                            
                    # 把流年表單裡的隱藏金鑰「全部」存下來
                    transit_form = birth_soup.find('form')
                    t_payload = {}
                    if transit_form:
                        for inp in transit_form.find_all('input'):
                            name = inp.get('name')
                            if not name: continue
                            itype = inp.get('type', '').lower()
                            if itype in ['submit', 'reset', 'button']: continue
                            if itype in ['radio', 'checkbox'] and not inp.has_attr('checked'): continue
                            t_payload[name] = inp.get('value', '')
                            
                        for sel in transit_form.find_all('select'):
                            name = sel.get('name')
                            if name:
                                selected = sel.find('option', selected=True)
                                t_payload[name] = selected.get('value', selected.text) if selected else sel.find('option').get('value')
                                
                        st.session_state.transit_form_data = t_payload
                        st.session_state.submit_url = urljoin(action_url, transit_form.get('action'))
                        st.session_state.step1_done = True
                        st.session_state.transit_chart = None # 清空舊的流時盤
                        st.rerun() # 重新整理畫面

                except Exception as e:
                    st.error(f"第一步發生錯誤：{e}")

with col_right:
    st.info("### 步驟二：設定流轉日期")
    with st.container(border=True):
        tc1, tc2, tc3 = st.columns(3)
        t_year = tc1.number_input("欲查年份", min_value=1900, max_value=2100, value=now.year)
        t_month = tc2.number_input("欲查月份", min_value=1, max_value=12, value=now.month)
        t_day = tc3.number_input("欲查日期", min_value=1, max_value=31, value=now.day)
        
        tc4, tc5 = st.columns(2)
        t_hour_label = tc4.selectbox("欲查時辰", list(hours_map.keys()), key="t_hour_select")
        transit_start = tc5.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)
        transit_type = st.radio("查詢模式", ["流年", "流月", "流日", "流時"], index=3, horizontal=True)

        # 第二步的按鈕
        if st.button("2️⃣ 疊加流轉盤", use_container_width=True, disabled=not st.session_state.step1_done):
            t_hour_val = hours_map[t_hour_label]
            
            with st.spinner("正在送出流時參數..."):
                try:
                    session = requests.Session()
                    if st.session_state.cookies:
                        session.cookies.update(st.session_state.cookies)
                    
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
                    
                    # 載入步驟一記憶的隱藏金鑰
                    final_payload = st.session_state.transit_form_data.copy()
                    
                    # 精準覆寫流轉專用參數，保留出生的年份不動！
                    final_payload['FateSolar'] = "1" # 國曆
                    final_payload['FateYear'] = str(t_year)
                    final_payload['FateMonth'] = str(t_month)
                    final_payload['FateDay'] = str(t_day)
                    final_payload['FateHour'] = str(t_hour_val)
                    final_payload['Target'] = "0" if transit_start == "流年本宮" else "1"
                    final_payload['calday'] = transit_type # 例如送出 "流時"
                    
                    res_transit = session.post(st.session_state.submit_url, data=final_payload, headers=headers)
                    res_transit.encoding = 'utf-8'
                    transit_soup = BeautifulSoup(res_transit.text, 'html.parser')
                    
                    # 儲存流時盤 HTML
                    for table in transit_soup.find_all('table'):
                        if "紫微" in table.get_text() and "天機" in table.get_text():
                            st.session_state.transit_chart = str(table)
                            break
                            
                    # 抓取好運指數等標題
                    t_header = ""
                    for center_tag in transit_soup.find_all('center'):
                        if "好運指數" in center_tag.text or transit_type in center_tag.text:
                            for child in center_tag.children:
                                if getattr(child, 'name', None) == 'table': break
                                t_header += str(child)
                            break
                    st.session_state.transit_header = t_header

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
        st.info("請先完成步驟一。")

with out_right:
    st.markdown("<h3 style='text-align: center;'>⚡ 流轉運勢盤</h3>", unsafe_allow_html=True)
    if st.session_state.transit_chart:
        st.markdown(f"<div style='text-align: center;'>{st.session_state.transit_header}</div>", unsafe_allow_html=True)
        st.markdown(st.session_state.transit_chart, unsafe_allow_html=True)
    elif st.session_state.step1_done:
        st.info("請設定上方流轉日期後，點擊「疊加流轉盤」。")
    else:
        st.info("等待步驟一完成。")
