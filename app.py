import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統 (含流年運勢)")
st.write("資料來源自動抓取自 [windada算命網](https://fate.windada.com/cgi-bin/fate)")

# 取得現在的年月，方便作為流年的預設值
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
            # 預設選在申時 (index=8)
            hour_label = st.selectbox("出生時辰", list(hours_map.keys()), index=8)
        with c5:
            gender_label = st.radio("性別", ["男", "女"], horizontal=True)

with col_right:
    st.markdown("### 🗓️ 欲查詢的運勢時間")
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
            t_hour_label = st.selectbox("欲查時辰", list(hours_map.keys()), key="t_hour_select")
        with tc5:
            transit_type = st.radio("查詢模式", ["本命盤 (不看流年)", "流年", "流月", "流日", "流時"], index=0)

st.markdown("---")

# --- 3. 抓取資料與顯示 ---
if st.button("開始排盤 🚀", use_container_width=True):
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "0"
    t_hour_val = hours_map[t_hour_label]

    with st.spinner("🤖 正在與算命伺服器進行多重驗證..."):
        try:
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                "Referer": "https://fate.windada.com/"
            }
            url = "https://fate.windada.com/cgi-bin/fate"
            
            # 【階段一：取得並送出本命資料】
            first_page = session.get(url, headers=headers)
            first_page.encoding = 'utf-8'
            soup = BeautifulSoup(first_page.text, 'html.parser')
            form = soup.find('form')
            
            if not form:
                st.error("無法載入輸入表單。")
                st.stop()
                
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

            # 注入使用者的出生資料
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

            # 【階段二：如果選擇了流年/月/日/時，則攔截第二層表單再次送出】
            if transit_type != "本命盤 (不看流年)":
                st.toast("🔄 正在疊加流年參數，計算運勢中...", icon="⏳")
                transit_form = res_soup.find('form')
                
                if transit_form:
                    t_payload = {}
                    # 抓取第二層表單的隱藏參數 (帶有本命盤的記憶)
                    for input_tag in transit_form.find_all('input'):
                        name = input_tag.get('name')
                        if name and input_tag.get('type') not in ['submit', 'reset', 'button']:
                            t_payload[name] = input_tag.get('value', '')
                    
                    # 智慧判斷哪個下拉選單是年、月、日，並注入使用者想查的時間
                    for sel in transit_form.find_all('select'):
                        name = sel.get('name')
                        if not name: continue
                        opts = [o.get('value', o.text) for o in sel.find_all('option')]
                        
                        # 如果選項裡有年份(大於1900)，就填入欲查年份
                        if any(int(o) > 1900 for o in opts if o.isdigit()):
                            t_payload[name] = str(t_year)
                        # 如果選項最多到12，代表是月份
                        elif '12' in opts and len(opts) <= 15:
                            t_payload[name] = str(t_month)
                        # 如果選項最多到31，代表是日期
                        elif '31' in opts and len(opts) <= 35:
                            t_payload[name] = str(t_day)
                        # 如果選項包含23，代表是時辰
                        elif '23' in opts and len(opts) <= 25:
                            t_payload[name] = t_hour_val
                        else:
                            # 預設值 (例如國曆/農曆選項)
                            selected = sel.find('option', selected=True)
                            t_payload[name] = selected.get('value', selected.text) if selected else opts[0].get('value', opts[0].text)

                    # 找出對應的按鈕並「點擊」它
                    for btn in transit_form.find_all(['input', 'button']):
                        if transit_type in btn.get('value', ''):
                            t_payload[btn.get('name')] = btn.get('value')
                            break
                            
                    t_action = transit_form.get('action')
                    t_submit_url = urljoin(submit_url, t_action) if t_action else submit_url
                    t_method = transit_form.get('method', 'get').lower()

                    if t_method == 'post':
                        res = session.post(t_submit_url, data=t_payload, headers=headers)
                    else:
                        res = session.get(t_submit_url, params=t_payload, headers=headers)
                        
                    res.encoding = 'utf-8'
                    res_soup = BeautifulSoup(res.text, 'html.parser')

            # 【階段三：嚴格尋找最終盤面並美化顯示】
            found_table = None
            max_td_count = 0
            
            for table in res_soup.find_all('table'):
                text = table.get_text()
                td_count = len(table.find_all('td'))
                # 確認有命盤關鍵字才算數
                if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                    found_table = table
                    max_td_count = td_count
            
            if found_table:
                if transit_type == "本命盤 (不看流年)":
                    st.success("🎉 本命盤抓取成功！")
                else:
                    st.success(f"🎉 成功抓取！目標時間：{t_year}年{t_month}月{t_day}日 ({transit_type}盤)")
                    
                # 美化中間文字與格線
                for td in found_table.find_all('td'):
                    if td.get('colspan') == '2' and td.get('rowspan') == '2':
                        td['style'] = 'background-color: #ffffff !important; color: #000000 !important; padding: 15px;'
                        for font in td.find_all('font'):
                            if font.has_attr('color'): del font['color']
                
                table_html = str(found_table).replace('<table', '<table border="1" style="width:100%; text-align:center; border-collapse: collapse; border-color: #777777; background-color: #ffffff; color: #000000;"')
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning("查無符合格式的命盤，可能是網站阻擋或日期格式異常。")

        except Exception as e:
            st.error(f"發生錯誤：{e}")
