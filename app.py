import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 全域設定：確保不會再出現 name 'HEADERS' is not defined ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Referer": "https://fate.windada.com/"
}

st.set_page_config(layout="wide")
st.title("🔮 紫微命盤分步抓取系統")

# 初始化 session
if "session" not in st.session_state:
    st.session_state.session = requests.Session()
if "step" not in st.session_state:
    st.session_state.step = 1

# --- 步驟一：輸入本命 ---
if st.session_state.step == 1:
    st.subheader("步驟一：輸入本命資料")
    y = st.number_input("年", value=1992)
    m = st.number_input("月", value=6)
    d = st.number_input("日", value=18)
    if st.button("取得本命盤"):
        data = {"year": str(y), "month": str(m), "day": str(d), "hour": "8", "sex": "1", "type": "find", "place": "1"}
        res = st.session_state.session.post("https://fate.windada.com/cgi-bin/fate", data=data, headers=HEADERS)
        st.session_state.res1 = res.text
        st.session_state.step = 2
        st.rerun()

# --- 步驟二：輸入流時 ---
elif st.session_state.step == 2:
    st.subheader("步驟二：設定流時日期")
    ty = st.number_input("流時年", value=2026)
    tm = st.number_input("流時月", value=5)
    td = st.number_input("流時日", value=23)
    
    if st.button("取得流時命盤"):
        soup = BeautifulSoup(st.session_state.res1, 'html.parser')
        form = soup.find('form')
        
        # 複製原本頁面的所有隱藏欄位
        payload = {inp.get('name'): inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
        
        # 注入流時參數
        payload.update({
            "FateYear": str(ty), "FateMonth": str(tm), "FateDay": str(td), 
            "FateHour": "16", "calday": "流時"
        })
        
        # 強制注入「流時」按鈕觸發
        for btn in form.find_all(['input', 'button']):
            if btn.get('value') == '流時':
                payload[btn.get('name')] = '流時'
                break
        
        action_url = urljoin("https://fate.windada.com/cgi-bin/fate", form.get('action'))
        res2 = st.session_state.session.post(action_url, data=payload, headers=HEADERS)
        st.session_state.res2 = res2.text
        st.session_state.step = 3
        st.rerun()

# --- 步驟三：顯示結果 ---
elif st.session_state.step == 3:
    col1, col2 = st.columns(2)
    s1 = BeautifulSoup(st.session_state.res1, 'html.parser')
    s2 = BeautifulSoup(st.session_state.res2, 'html.parser')
    
    with col1:
        st.markdown("### 本命盤")
        st.markdown(str(s1.find('table')), unsafe_allow_html=True)
    with col2:
        st.markdown("### 流時盤")
        # 直接抓取最後一個表格，通常就是流時盤
        st.markdown(str(s2.find_all('table')[-1]), unsafe_allow_html=True)
        
    if st.button("重新查詢"):
        st.session_state.step = 1
        st.rerun()
