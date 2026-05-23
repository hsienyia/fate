import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime
import streamlit.components.v1 as components



def inject_transit_info(original_html, mode, offset): # 補上 offset 參數
    soup = BeautifulSoup(original_html.encode('latin1').decode('utf-8'), 'html.parser')
    table = soup.find('table')
    if table:
        header = soup.new_tag("div", style="color:red; font-weight:bold; text-align:center; margin-top:20px;")
        header.string = f"--- {mode}運勢顯示中 (偏移:{offset}) ---"
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
        with st.spinner("正在執行高權限連線..."):
            try:
                # 1. 建立 Session
                session = st.session_state.session
                
                # 2. 獲取頁面以取得 Cookie 和隱藏表單欄位
                # 這是最關鍵的一步：先讀取頁面中的 <input type="hidden">
                init_res = session.get("https://fate.windada.com/cgi-bin/fate", headers=HEADERS)
                soup = BeautifulSoup(init_res.text, 'html.parser')
                form = soup.find('form')
                
                # 抓取所有隱藏欄位 (這是防止被判斷為機器人的關鍵)
                payload = {}
                if form:
                    for input_tag in form.find_all('input'):
                        if input_tag.get('name'):
                            payload[input_tag.get('name')] = input_tag.get('value', '')
                
                # 3. 填入你的資料 (覆蓋掉原始值)
                payload.update({
                    "year": str(y), 
                    "month": str(m), 
                    "day": str(d), 
                    "hour": hours_map[h_label], 
                    "sex": "1" if sex=="男" else "0", 
                    "type": "find", 
                    "place": "1"
                })
                
                # 4. 發送請求
                # 使用剛才抓到的 form action URL，確保路徑正確
                post_url = urljoin("https://fate.windada.com/cgi-bin/fate", form.get('action', '')) if form else "https://fate.windada.com/cgi-bin/fate"
                res = session.post(post_url, data=payload, headers=HEADERS)
                
                # 5. 解析與儲存
                result_soup = BeautifulSoup(res.text, 'html.parser')
                tables = result_soup.find_all('table')
                
                if tables:
                    # 判斷是否抓到真的盤：通常有效的命盤表格裡會有「命宮」或特定中文字
                    st.session_state.birth_chart = str(tables[-1])
                    st.rerun()
                else:
                    st.error("未找到有效的命盤表格，網站可能已拒絕請求。")
                    
            except Exception as e:
                st.error(f"錯誤細節: {e}")
                

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

# --- 3. 畫面顯示區 (修正重複渲染問題) ---
# --- 修正後的顯示區塊 ---
if st.session_state.birth_chart:
    st.markdown("---")
    st.markdown("### ⚡ 本地端自動生成四盤")
    
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    # 模式與欄位對應
    mode_configs = [
        ("流年盤", col1, "流年"), 
        ("流月盤", col2, "流月"), 
        ("流日盤", col3, "流日"), 
        ("流時盤", col4, "流時")
    ]
    
    for title, col, mode_name in mode_configs:
        with col:
            st.markdown(f"#### {title}")
            # 這裡傳入三個參數：(html, mode, 0)
            transit_html = inject_transit_info(st.session_state.birth_chart, mode_name, 0)
            # 使用 components.html 而不是 st.markdown
            components.html(transit_html, height=450, scrolling=True)
            try:
                # 呼叫 inject_transit_info
                # 注意：你定義的 inject_transit_info 參數是 (html, mode, offset)，請補上第三個參數 0
                transit_html = inject_transit_info(st.session_state.birth_chart, mode_name, 0)
                components.html(transit_html, height=450, scrolling=True)
            except Exception as e:
                st.error(f"渲染錯誤: {e}")
else:
    st.info("請先輸入資料並點擊「1️⃣ 取得本命盤」。")
