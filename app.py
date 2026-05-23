import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 全域設定 ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Referer": "https://fate.windada.com/"
}

st.set_page_config(layout="wide")
st.title("🔮 紫微命盤抓取系統 (最終修正版)")

# 初始化 Session (這是確保不會出現 name 'session' is not defined 的關鍵)
if "session" not in st.session_state:
    st.session_state.session = requests.Session()

# 步驟二按鈕邏輯修正
if st.button("🚀 一次執行排盤與流時", use_container_width=True):
    with st.spinner("正在執行完整排盤請求..."):
        try:
            # 必須使用 st.session_state.session
            session = st.session_state.session 
            
            hours_map = {
                "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
                "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
                "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
                "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
            }
            
            # 準備 Payload
            payload = {
                "year": str(year),
                "month": str(month),
                "day": str(day),
                "hour": hours_map[hour_label],
                "sex": "1" if gender_label == "男" else "0",
                "type": "find",
                "place": "1",
                "FateYear": str(t_year),
                "FateMonth": str(t_month),
                "FateDay": str(t_day),
                "FateHour": hours_map[t_hour_label],
                "calday": "流時"
            }
            
            # 發送請求
            response = session.post("https://fate.windada.com/cgi-bin/fate", data=payload, headers=HEADERS)
            
            # 顯示結果
            if "紫微" in response.text:
                st.session_state.transit_chart = response.text
                st.success("排盤成功！")
            else:
                st.error("請求失敗，伺服器未回傳命盤。")
                
        except Exception as e:
            st.error(f"錯誤：{e}")
