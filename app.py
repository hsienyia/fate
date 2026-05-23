import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 工具函式 ---
def inject_transit_info(original_html, mode, offset):
    soup = BeautifulSoup(original_html, 'html.parser')
    table = soup.find('table')
    if table:
        header = soup.new_tag("div", style="color:red; font-weight:bold; text-align:center; margin-top:20px;")
        header.string = f"--- {mode}運勢顯示中 ---"
        table.insert_before(header)
    return str(soup)

# --- 全域設定 ---
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0", "Referer": "https://fate.windada.com/"}

st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取與流轉系統")

# 初始化 session
if "session" not in st.session_state: st.session_state.session = requests.Session()
if "birth_chart" not in st.session_state: st.session_state.birth_chart = None

# --- UI 介面 ---
col_left, col_right = st.columns(2)

with col_left:
    st.success("### 步驟一：輸入本命資料")
    y = st.number_input("出生年", value=1992)
    m = st.number_input("出生月", value=6)
    d = st.number_input("出生日", value=18)
    hours_map = {"子時": "0", "丑時": "2", "寅時": "4", "卯時": "6", "辰時": "8", "巳時": "10", "午時": "12", "未時": "14", "申時": "16", "酉時": "18", "戌時": "20", "亥時": "22"}
    h_label = st.selectbox("時辰", list(hours_map.keys()), index=8)
    sex = st.radio("性別", ["男", "女"], horizontal=True)

    if st.button("1️⃣ 取得本命盤"):
        data = {"year": str(y), "month": str(m), "day": str(d), "hour": hours_map[h_label], "sex": "1" if sex=="男" else "0", "type": "find", "place": "1"}
        res = st.session_state.session.post("https://fate.windada.com/cgi-bin/fate", data=data, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find_all('table')[-1]
        st.session_state.birth_chart = str(table)
        st.rerun()

with col_right:
    st.info("### 步驟二：設定流轉日期")
    ty = st.number_input("流時年", value=2026)
    tm = st.number_input("流時月", value=5)
    td = st.number_input("流時日", value=23)
    
    if st.button("🚀 生成全部流轉盤"):
        if st.session_state.birth_chart:
            st.session_state.do_render = True
        else:
            st.error("請先取得本命盤！")

# --- 結果顯示區 ---
if st.session_state.birth_chart:
    st.markdown("---")
    st.markdown("### 🪐 本地端生成四盤對照")
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    modes = [("流年盤", c1, "流年"), ("流月盤", c2, "流月"), ("流日盤", c3, "流日"), ("流時盤", c4, "流時")]
    for title, col, mode in modes:
        with col:
            st.markdown(f"#### {title}")
            st.markdown(inject_transit_info(st.session_state.birth_chart, mode, 0), unsafe_html=True)
