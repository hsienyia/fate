import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統")

# --- 2. 介面 ---
col_left, col_right = st.columns(2)
with col_left:
    st.markdown("### 1. 本命出生資料")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("年", value=1992)
        month = c2.number_input("月", value=6)
        day = c3.number_input("日", value=18)
        hour = st.selectbox("時辰", ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"], index=8)
        sex = st.radio("性別", ["男", "女"], horizontal=True)

with col_right:
    st.markdown("### 2. 流轉日期設定")
    with st.container(border=True):
        t1, t2, t3 = st.columns(3)
        t_year = t1.number_input("欲查年", value=2026)
        t_month = t2.number_input("欲查月", value=5)
        t_day = t3.number_input("欲查日", value=23)
        t_hour = st.selectbox("欲查時", ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"], index=16)

if st.button("開始排盤 🚀", use_container_width=True):
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    
    # 步驟一：獲取初始表單並送出本命資料
    res = session.get("https://fate.windada.com/cgi-bin/fate", headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    form = soup.find('form')
    
    # 這裡直接利用網站的參數結構填入
    data = {
        "year": str(year), "month": str(month), "day": str(day),
        "hour": str(["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"].index(hour)),
        "sex": "1" if sex == "男" else "0", "type": "find", "place": "1"
    }
    
    # 送出本命查詢
    res_fate = session.post(urljoin("https://fate.windada.com/", form.get('action')), data=data, headers=headers)
    
    # 步驟二：送出流轉參數 (根據你設定的日期)
    fate_soup = BeautifulSoup(res_fate.text, 'html.parser')
    fate_form = fate_soup.find('form')
    
    # 收集流轉表單參數 (如：FateYear, FateMonth, FateDay, calday 等)
    t_data = {input_tag.get('name'): input_tag.get('value', '') for input_tag in fate_form.find_all('input') if input_tag.get('name')}
    t_data.update({"FateYear": str(t_year), "FateMonth": str(t_month), "FateDay": str(t_day), "FateHour": str(t_hour), "calday": "流時"})
    
    # 送出流轉查詢
    res_final = session.post(urljoin("https://fate.windada.com/", fate_form.get('action')), data=t_data, headers=headers)
    final_soup = BeautifulSoup(res_final.text, 'html.parser')

    # 顯示結果
    st.success("以下顯示本命盤與流轉盤：")
    
    # 顯示本命盤
    with st.expander("👉 查看本命盤 (原始格式)", expanded=True):
        st.markdown(str(fate_soup.find_all('table')[0]), unsafe_allow_html=True)
        
    # 顯示流轉盤
    with st.expander("👉 查看流時盤 (原始格式)", expanded=True):
        st.markdown(str(final_soup.find_all('table')[0]), unsafe_allow_html=True)
