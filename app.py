import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微雙盤對照系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微本命 / 流時 雙盤對照系統")

# 初始化暫存區 (用來同時顯示兩個盤)
if "birth_chart" not in st.session_state:
    st.session_state["birth_chart"] = None
if "transit_chart" not in st.session_state:
    st.session_state["transit_chart"] = None

now = datetime.datetime.now()

# --- 2. 建立網頁輸入介面 ---
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 👶 1. 輸入本命出生資料")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("年", min_value=1900, max_value=2100, value=1992)
        month = c2.number_input("月", min_value=1, max_value=12, value=6)
        day = c3.number_input("日", min_value=1, max_value=31, value=18)
        
        c4, c5 = st.columns(2)
        # 修正：回歸最單純的 0~11 索引值
        hours_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        hour_label = c4.selectbox("時辰", hours_list, index=8)
        sex_label = c5.radio("性別", ["男", "女"], horizontal=True)

with col_right:
    st.markdown("### 🗓️ 2. 設定欲查詢的流時時間")
    with st.container(border=True):
        tc1, tc2, tc3 = st.columns(3)
        t_year = tc1.number_input("欲查年", min_value=1900, max_value=2100, value=2026)
        t_month = tc2.number_input("欲查月", min_value=1, max_value=12, value=5)
        t_day = tc3.number_input("欲查日", min_value=1, max_value=31, value=23)
        
        tc4, tc5 = st.columns(2)
        t_hour = tc4.selectbox("欲查時 (24小時制)", [str(i) for i in range(24)], index=16)
        transit_start = tc5.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)

st.markdown("---")

# --- 3. 核心執行運算 ---
if st.button("同步排盤 🚀", use_container_width=True):
    # 每次按下按鈕先清空舊畫面
    st.session_state["birth_chart"] = None
    st.session_state["transit_chart"] = None
    
    hour_val = str(hours_list.index(hour_label))
    sex_val = "1" if sex_label == "男" else "0"

    with st.spinner("🔮 正在抓取雙盤資料..."):
        try:
            session = requests.Session()
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
            url = "https://fate.windada.com/cgi-bin/fate"
            
            # 【步驟一：抓本命盤】
            res = session.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            form = soup.find('form')
            
            data = {
                "year": str(year), "month": str(month), "day": str(day),
                "hour": hour_val, "sex": sex_val, "type": "find", "place": "1"
            }
            
            action_url = urljoin("https://fate.windada.com/", form.get('action'))
            res_birth = session.post(action_url, data=data, headers=headers)
            birth_soup = BeautifulSoup(res_birth.text, 'html.parser')
            
            # 儲存本命盤 HTML
            for t in birth_soup.find_all('table'):
                if "紫微" in t.get_text() and "天機" in t.get_text():
                    st.session_state["birth_chart"] = str(t)
                    break
            
            # 【步驟二：抓流時盤】
            fate_form = birth_soup.find('form')
            if fate_form:
                t_data = {}
                for inp in fate_form.find_all('input'):
                    name = inp.get('name')
                    val = inp.get('value', '')
                    i_type = inp.get('type', 'text').lower()
                    
                    if not name: continue
                    if i_type in ['radio', 'checkbox']:
                        if ("本宮" in val and "本宮" in transit_start) or ("斗君" in val and "斗君" in transit_start):
                            t_data[name] = val
                    elif i_type not in ['submit', 'reset', 'button']:
                        t_data[name] = val
                        
                # 補上你的流時設定並模擬按下「流時」按鈕
                t_data.update({
                    "FateYear": str(t_year), 
                    "FateMonth": str(t_month), 
                    "FateDay": str(t_day), 
                    "FateHour": str(t_hour), 
                    "calday": "流時" 
                })
                
                t_action_url = urljoin("https://fate.windada.com/", fate_form.get('action'))
                res_transit = session.post(t_action_url, data=t_data, headers=headers)
                transit_soup = BeautifulSoup(res_transit.text, 'html.parser')
                
                # 儲存流時盤 HTML
                for t in transit_soup.find_all('table'):
                    if "紫微" in t.get_text() and "天機" in t.get_text():
                        st.session_state["transit_chart"] = str(t)
                        break
                            
        except Exception as e:
            st.error(f"發生錯誤：{e}")

# --- 4. 畫面顯示區：左右雙盤並列 (原汁原味) ---
if st.session_state["birth_chart"] or st.session_state["transit_chart"]:
    col_out1, col_out2 = st.columns(2)
    
    with col_out1:
        st.markdown("### 🪐 本命盤")
        if st.session_state["birth_chart"]:
            # 完全不改顏色，直接輸出原始 HTML
            st.markdown(st.session_state["birth_chart"], unsafe_allow_html=True)
        else:
            st.error("無法取得本命盤，請確認出生資料。")
            
    with col_out2:
        st.markdown("### ⚡ 流時盤")
        if st.session_state["transit_chart"]:
            # 完全不改顏色，直接輸出原始 HTML
            st.markdown(st.session_state["transit_chart"], unsafe_allow_html=True)
        else:
            st.error("無法取得流時盤。")
