import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統 (流年完整版)")
st.write("資料來源自動抓取自 [windada算命網](https://fate.windada.com/cgi-bin/fate)")

now = datetime.datetime.now()

# --- 2. 建立網頁輸入介面 ---
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 👶 本命出生資料")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            year = st.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1992)
        with c2:
            month = st.number_input("出生月", min_value=1, max_value=12, value=6)
        with c3:
            day = st.number_input("出生日", min_value=1, max_value=31, value=18)
        
        hours_map = {
            "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
            "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
            "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
            "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
        }
        
        c4, c5 = st.columns(2)
        with c4:
            hour_label = st.selectbox("出生時辰", list(hours_map.keys()), index=8)
        with c5:
            gender_label = st.radio("性別", ["男", "女"], horizontal=True)

with col_right:
    st.markdown("### 🗓️ 欲查詢的運勢時間 (對應網站左上角)")
    with st.container(border=True):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            t_year = st.number_input("欲查年份", min_value=1900, max_value=2100, value=now.year)
        with tc2:
            t_month = st.number_input("欲查月份", min_value=1, max_value=12, value=now.month)
        with tc3:
            t_day = st.number_input("欲查日期", min_value=1, max_value=31, value=now.day)
            
        tc4, tc5 = st.columns(2)
        with tc4:
            t_hour_label = st.selectbox("欲查時辰", list(hours_map.keys()), index=0, key="t_hour_select")
        with tc5:
            # 補上截圖中漏掉的「流月起始宮位」設定
            transit_start = st.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)

        transit_type = st.radio("查詢模式 (按下排盤時會自動點擊該按鈕)", ["本命盤 (不看流年)", "流年", "流月", "流日", "流時"], index=4, horizontal=True)

st.markdown("---")

# --- 3. 抓取資料與顯示 ---
if st.button("開始排盤 🚀", use_container_width=True):
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "0"
    t_hour_val = hours_map[t_hour_label]

    with st.spinner("🤖 正在破解伺服器雙層表單，計算星盤中..."):
        try:
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                "Referer": "https://fate.windada.com/"
            }
            url = "https://fate.windada.com/cgi-bin/fate"
            
            # 【階段一：取得本命資料與隱藏金鑰】
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

            for key in payload.keys():
                k_low = key.lower()
                if "year" in k_low or key == "y": payload[key] = str(year)
                elif "month" in k_low or key == "m": payload[key] = str(month)
                elif "day" in k_low or key == "d": payload[key] = str(day)
                elif "hour" in k_low or key == "h" or "time" in k_low: payload[key] = hour_val
                elif "sex" in k_low or "gen" in k_low: payload[key] = gender_val

            action_url = form.get('action')
            submit_url = urljoin(url, action_url) if action_url else url
            method = form.get('method', 'get').lower()

            if method == 'post':
                res = session.post(submit_url, data=payload, headers=headers)
            else:
                res = session.get(submit_url, params=payload, headers=headers)
            
            res.encoding = 'utf-8'
            res_soup = BeautifulSoup(res.text, 'html.parser')

            # 【階段二：精準攔截第二層表單，注入流年時間並模擬點擊】
            t_payload = {}
            if transit_type != "本命盤 (不看流年)":
                transit_form = res_soup.find('form')
                
                if transit_form:
                    for input_tag in transit_form.find_all('input'):
                        name = input_tag.get('name')
                        i_type = input_tag.get('type', 'text').lower()
                        val = input_tag.get('value', '')
                        if not name: continue
                        
                        # 處理流年本宮/斗君的選項
                        if i_type in ['radio', 'checkbox']:
                            if ("本宮" in val and "本宮" in transit_start) or ("斗君" in val and "斗君" in transit_start):
                                t_payload[name] = val
                        elif i_type not in ['submit', 'reset', 'button']:
                            t_payload[name] = val
                    
                    for sel in transit_form.find_all('select'):
                        name = sel.get('name')
                        if not name: continue
                        opts = sel.find_all('option')
                        opts_vals = [o.get('value', o.text).strip() for o in opts]
                        
                        # 聰明辨識年月日下拉選單
                        if any(str(t_year) in v for v in opts_vals) and len(opts_vals) > 20:
                            t_payload[name] = str(t_year)
                        elif '12' in opts_vals and '1' in opts_vals and len(opts_vals) <= 13:
                            t_payload[name] = str(t_month)
                        elif '31' in opts_vals and '1' in opts_vals and len(opts_vals) <= 32:
                            t_payload[name] = str(t_day)
                        elif '23' in opts_vals and '0' in opts_vals and len(opts_vals) <= 25:
                            t_payload[name] = str(t_hour_val)
                        else:
                            selected = sel.find('option', selected=True)
                            t_payload[name] = selected.get('value', selected.text) if selected else opts_vals[0]

                    # 最關鍵的一步：找出對應的按鈕名稱並確實送出
                    clicked = False
                    for btn in transit_form.find_all(['input', 'button']):
                        val = btn.get('value', '')
                        if transit_type in val:
                            b_name = btn.get('name')
                            if b_name:
                                t_payload[b_name] = val
                            else:
                                t_payload['submit'] = val # 防呆機制
                            clicked = True
                            break
                            
                    if not clicked:
                        t_payload['submit'] = transit_type

                    t_action = transit_form.get('action')
                    t_submit_url = urljoin(submit_url, t_action) if t_action else submit_url
                    t_method = transit_form.get('method', 'get').lower()

                    if t_method == 'post':
                        res = session.post(t_submit_url, data=t_payload, headers=headers)
                    else:
                        res = session.get(t_submit_url, params=t_payload, headers=headers)
                        
                    res.encoding = 'utf-8'
                    res_soup = BeautifulSoup(res.text, 'html.parser')

            # 【階段三：抓取最終盤面、標題與好運指數】
            found_table = None
            max_td_count = 0
            
            for table in res_soup.find_all('table'):
                text = table.get_text()
                td_count = len(table.find_all('td'))
                if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                    found_table = table
                    max_td_count = td_count
            
            if found_table:
                # 抓取網頁上方的「好運指數」等大標題
                header_text = ""
                for b_tag in res_soup.find_all(['b', 'font', 'h2', 'h3']):
                    txt = b_tag.get_text(strip=True)
                    if "好運指數" in txt or "本命：" in txt or "流" in txt:
                        # 避免抓到表格內的文字
                        if len(txt) < 30 and txt not in header_text:
                            header_text += f"### {txt} \n"
                
                st.success("🎉 排盤成功！已切換至目標運勢盤。")
                st.markdown("---")
                
                # 顯示標題與好運指數
                if header_text:
                    st.markdown(f"<div style='text-align: center; color: #1E90FF;'>{header_text}</div>", unsafe_allow_html=True)
                    
                # 美化表格，同時「保留流年星星的專屬顏色」！
                for td in found_table.find_all('td'):
                    if td.get('colspan') == '2' and td.get('rowspan') == '2':
                        td['style'] = 'background-color: #ffffff !important; color: #000000 !important; padding: 15px;'
                        # 只把中間看不見的白色字變黑，保留其他顏色
                        for font in td.find_all('font'):
                            if font.has_attr('color') and font['color'].lower() in ['#ffffff', 'white']:
                                font['color'] = '#000000'
                    else:
                        td['style'] = td.get('style', '') + '; background-color: #fdfdfd; color: #000;'
                
                table_html = str(found_table).replace('<table', '<table border="1" style="width:100%; text-align:center; border-collapse: collapse; border-color: #aaaaaa; background-color: #ffffff;"')
                st.markdown(table_html, unsafe_allow_html=True)
                
                # 隱藏除錯面板，萬一失敗可以打開看
                with st.expander("👉 [除錯專用] 若盤面錯誤，點此查看送出的參數"):
                    st.write("這是程式代替你按下的表單內容：", t_payload)
            else:
                st.warning("查無符合格式的命盤，可能是網站阻擋或日期格式異常。")

        except Exception as e:
            st.error(f"發生錯誤：{e}")
