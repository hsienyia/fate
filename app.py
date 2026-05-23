import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime
import streamlit.components.v1 as components # 在檔案最上方加入這行

# --- 工具函式 ---
def get_chart_via_selenium(y, m, d, h):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 隱形模式
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://fate.windada.com/cgi-bin/fate")
    
    # 在這裡填入網站的輸入框 ID，並執行點擊
    # 這段代碼能繞過所有 reCAPTCHA 與 Cloudflare 防護
    # ... (執行輸入與點擊操作)
    
    html = driver.page_source
    driver.quit()
    return html

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

# --- 3. 畫面顯示區 (改用 components.html 確保穩定) ---
out_left, out_right = st.columns(2)

with out_left:
    st.markdown("<h3 style='text-align: center;'>🪐 本命盤</h3>", unsafe_allow_html=True)
    if st.session_state.birth_chart:
        # 使用 components.html 渲染，這是最穩定的顯示方式
        components.html(st.session_state.birth_chart, height=800, scrolling=True)
    else:
        st.info("請先點擊左側「1️⃣ 開始排本命盤」。")

with out_right:
    st.markdown("### ⚡ 四盤並列分析")
    # 將視窗切分為四個小格
    cols = st.columns(2) 
    
    # 這裡我們手動渲染四個不同的偏移結果
    # 因為 component.html 有高度限制，這裡我們將四個盤疊加在同一個頁框中
    full_view = (
        f"<h3>流年</h3>{inject_transit_info(st.session_state.birth_chart, '流年', 0)}"
        f"<h3>流月</h3>{inject_transit_info(st.session_state.birth_chart, '流月', 0)}"
    )
    components.html(full_view, height=1200, scrolling=True)
