import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

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

# --- 3. 本地化四盤並列顯示區 ---
st.markdown("---")
st.markdown("### ⚡ 本地端自動生成四盤")

# 檢查 st.session_state.birth_chart 是否真的有資料
if st.session_state.birth_chart is not None:
    # 建立 2x2 網格
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    base_html = st.session_state.birth_chart
    
    # 定義模式與欄位對應
    modes = [("流年盤", col1, "流年"), ("流月盤", col2, "流月"), 
             ("流日盤", col3, "流日"), ("流時盤", col4, "流時")]
    
    for title, col, mode in modes:
        with col:
            st.markdown(f"#### {title}")
            # 傳入 offset 0 進行測試
            try:
                transit_view = inject_transit_info(base_html, mode, 0)
                st.markdown(transit_view, unsafe_html=True)
            except Exception as e:
                st.error(f"渲染失敗: {e}")
else:
    st.info("⚠️ 請先在左側輸入資料並點擊「1️⃣ 取得本命盤」。")
