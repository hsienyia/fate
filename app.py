import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime
import streamlit.components.v1 as components



def inject_transit_info(original_html, mode, offset):
    soup = BeautifulSoup(original_html, 'html.parser')
    table = soup.find('table')
    if table:
        # 這裡你可以手動標記，或者進行宮位偏移邏輯
        header = soup.new_tag("div", style="color:red; font-weight:bold; text-align:center;")
        # 這裡直接顯示你指定的模式，避開網站後端的參數校驗
        header.string = f"--- 運算中：{mode} ---" 
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

    if st.button("🚀 生成全部流轉盤", key="btn_generate_transit"):
        if st.session_state.birth_chart:
            st.session_state.do_render = True
        else:
            st.error("請先取得本命盤！")
                

with col_right:
    st.info("### 步驟二：設定流轉日期")
    ty = st.number_input("流時年", value=2026)
    tm = st.number_input("流時月", value=5)
    td = st.number_input("流時日", value=23)
    
    

# --- 3. 畫面顯示區 (請用這段替換掉你原來的區塊) ---
st.markdown("---")
st.markdown("### ⚡ 本地端自動生成四盤")

if st.session_state.birth_chart:
    # 這裡必須要有縮排，這就是錯誤訊息指出的地方
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    # 定義模式
    mode_configs = [
        ("流年盤", col1, "流年"), 
        ("流月盤", col2, "流月"), 
        ("流日盤", col3, "流日"), 
        ("流時盤", col4, "流時")
    ]
    
    for title, col, mode_name in mode_configs:
        with col:
            st.markdown(f"#### {title}")
            # 這裡呼叫函式 (確保傳入三個參數：HTML, 模式名, 偏移量)
            transit_html = inject_transit_info(st.session_state.birth_chart, mode_name, 0)
            components.html(transit_html, height=450, scrolling=True)
else:
    # 這裡對應 if 的 else，也需要縮排
    st.info("請先輸入資料並點擊「1️⃣ 取得本命盤」。")
