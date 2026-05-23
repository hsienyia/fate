import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微雙盤對照系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微本命 / 流時 雙盤對照系統")

# 初始化暫存區 (Session State)，用來同時保存兩個盤的畫面
if "birth_chart" not in st.session_state:
    st.session_state["birth_chart"] = None
if "transit_chart" not in st.session_state:
    st.session_state["transit_chart"] = None
if "transit_title" not in st.session_state:
    st.session_state["transit_title"] = ""

now = datetime.datetime.now()

# --- 2. 建立網頁輸入介面 ---
col_in_left, col_in_right = st.columns(2)

with col_in_left:
    st.markdown("### 👶 1. 輸入本命出生資料")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1992)
        month = c2.number_input("出生月", min_value=1, max_value=12, value=6)
        day = c3.number_input("出生日", min_value=1, max_value=31, value=18)
        
        # 根據除錯資料修正：網站的出生時辰代碼是用 24 小時制的對應點 (子=0, 丑=2, 寅=4...)
        hours_map = {
            "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
            "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
            "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
            "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
        }
        
        c4, c5 = st.columns(2)
        hour_label = c4.selectbox("出生時辰", list(hours_map.keys()), index=8)
        gender_label = c5.radio("性別", ["男", "女"], horizontal=True)

with col_in_right:
    st.markdown("### 🗓️ 2. 設定欲查詢的流時時間")
    with st.container(border=True):
        tc1, tc2, tc3 = st.columns(3)
        t_year = tc1.number_input("欲查年份", min_value=1900, max_value=2100, value=2026)
        t_month = tc2.number_input("欲查月份", min_value=1, max_value=12, value=5)
        t_day = tc3.number_input("欲查日期", min_value=1, max_value=31, value=23)
        
        tc4, tc5 = st.columns(2)
        # 流時精準選擇小時
        t_hour = tc4.selectbox("欲查小時 (24小時制)", [str(i) for i in range(24)], index=16)
        transit_start = tc5.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)

st.markdown("---")

# --- 3. 核心執行運算 ---
if st.button("同步排盤（自動執行雙層查詢） 🚀", use_container_width=True):
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "0"

    with st.spinner("🔮 正在進行雙層排盤計算，請稍候..."):
        try:
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                "Referer": "https://fate.windada.com/"
            }
            url = "https://fate.windada.com/cgi-bin/fate"
            
            # 【動作一：送出出生資料，攔截本命盤】
            first_page = session.get(url, headers=headers)
            first_page.encoding = 'utf-8'
            soup = BeautifulSoup(first_page.text, 'html.parser')
            form = soup.find('form')
            
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

            payload.update({
                "year": str(year), "month": str(month), "day": str(day),
                "hour": hour_val, "sex": gender_val, "type": "find", "place": "1"
            })

            res_birth = session.post(urljoin(url, form.get('action')), data=payload, headers=headers)
            res_birth.encoding = 'utf-8'
            birth_soup = BeautifulSoup(res_birth.text, 'html.parser')
            
            # 尋找本命盤表格
            birth_table = None
            for table in birth_soup.find_all('table'):
                if "紫微" in table.get_text() and "天機" in table.get_text():
                    birth_table = table
                    break
            
            # 【動作二：直接利用本命盤頁面，注入流時參數發送第二步】
            transit_form = birth_soup.find('form')
            if transit_form:
                t_payload = {}
                for input_tag in transit_form.find_all('input'):
                    name = input_tag.get('name')
                    i_type = input_tag.get('type', 'text').lower()
                    val = input_tag.get('value', '')
                    if not name: continue
                    
                    if i_type in ['radio', 'checkbox']:
                        if ("本宮" in val and "本宮" in transit_start) or ("斗君" in val and "斗君" in transit_start):
                            t_payload[name] = val
                    elif i_type not in ['submit', 'reset', 'button']:
                        t_payload[name] = val
                
                for sel in transit_form.find_all('select'):
                    name = sel.get('name')
                    if name:
                        selected = sel.find('option', selected=True)
                        t_payload[name] = selected.get('value', selected.text) if selected else sel.find('option').text

                # 強制填入除錯驗證過的流時標準格式
                t_payload.update({
                    "FateYear": str(t_year),
                    "FateMonth": str(t_month),
                    "FateDay": str(t_day),
                    "FateHour": str(t_hour),
                    "calday": "流時"
                })

                res_transit = session.post(urljoin(url, transit_form.get('action')), data=t_payload, headers=headers)
                res_transit.encoding = 'utf-8'
                transit_soup = BeautifulSoup(res_transit.text, 'html.parser')
                
                # 尋找流時盤表格
                transit_table = None
                for table in transit_soup.find_all('table'):
                    if "紫微" in table.get_text() and "天機" in table.get_text():
                        transit_table = table
                        break
                
                # 抓取流時盤上方的好運指數標題
                t_title = ""
                for b_tag in transit_soup.find_all(['b', 'font']):
                    txt = b_tag.get_text(strip=True)
                    if "流時：" in txt or "好運指數" in txt:
                        if len(txt) < 40 and txt not in t_title:
                            t_title += f"<h4>{txt}</h4>"

            # 【將結果寫入暫存區】
            if birth_table:
                st.session_state["birth_chart"] = str(birth_table)
            if transit_table:
                st.session_state["transit_chart"] = str(transit_table)
                st.session_state["transit_title"] = t_title

        except Exception as e:
            st.error(f"雙層排盤失敗：{e}")

# --- 4. 畫面顯示區：左右雙盤並列 ---
if st.session_state["birth_chart"] or st.session_state["transit_chart"]:
    out_left, out_right = st.columns(2)
    
    with out_left:
        st.markdown("<h3 style='text-align: center; color: #FF4B4B;'>🪐 原始本命盤</h3>", unsafe_allow_html=True)
        if st.session_state["birth_chart"]:
            # 利用白色背景的 div 容器包裹，完美還原網頁原始配色與字體顏色
            html_content = f"""
            <div style="background-color: #ffffff !important; color: #000000 !important; padding: 15px; border-radius: 8px; border: 2px solid #ddd; min-width: 100%;">
                <style>
                    table {{ width: 100% !important; text-align: center !important; border-collapse: collapse !important; }}
                    td {{ border: 1px solid #aaa !important; color: #000000 !important; }}
                    a {{ color: #0066cc !important; text-decoration: none; }}
                </style>
                {st.session_state["birth_chart"]}
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("暫無本命盤資料")

    with out_right:
        st.markdown("<h3 style='text-align: center; color: #1E90FF;'>⚡ 當前流時盤</h3>", unsafe_allow_html=True)
        if st.session_state["transit_chart"]:
            if st.session_state["transit_title"]:
                st.markdown(f"<div style='text-align: center; color: #1E90FF;'>{st.session_state['transit_title']}</div>", unsafe_allow_html=True)
            
            html_content = f"""
            <div style="background-color: #ffffff !important; color: #000000 !important; padding: 15px; border-radius: 8px; border: 2px solid #ddd; min-width: 100%;">
                <style>
                    table {{ width: 100% !important; text-align: center !important; border-collapse: collapse !important; }}
                    td {{ border: 1px solid #aaa !important; color: #000000 !important; }}
                    a {{ color: #0066cc !important; text-decoration: none; }}
                </style>
                {st.session_state["transit_chart"]}
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("請確認右上方設定並點擊排盤以產生流時結果")
