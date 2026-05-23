import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統")
st.write("資料來源自動抓取自 [windada算命網](https://fate.windada.com/cgi-bin/fate)")

# 定義時辰對應表
hours_map = {
    "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
    "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
    "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
    "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
}

# --- 2. 建立網頁輸入介面 ---
st.markdown("### 👤 第一步：本命資料")
col1, col2, col3 = st.columns(3)
with col1:
    year = st.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1992)
with col2:
    month = st.number_input("出生月", min_value=1, max_value=12, value=6)
with col3:
    day = st.number_input("出生日", min_value=1, max_value=31, value=18)

col4, col5 = st.columns(2)
with col4:
    hour_label = st.selectbox("請選擇出生時辰", list(hours_map.keys()), index=8) # 預設申時
with col5:
    gender_label = st.radio("請選擇性別", ["男", "女"], horizontal=True)

st.markdown("---")
st.markdown("### ⏳ 第二步：運勢 (流年/流月) 設定")
st.write("若只想看本命盤，請保持預設「本命盤」。若要看運勢，請設定下方時間並選擇模式：")

col6, col7, col8 = st.columns(3)
with col6:
    t_year = st.number_input("查詢年 (西元)", min_value=1900, max_value=2100, value=2026)
with col7:
    t_month = st.number_input("查詢月", min_value=1, max_value=12, value=5)
with col8:
    t_day = st.number_input("查詢日", min_value=1, max_value=31, value=1)

col9, col10 = st.columns(2)
with col9:
    t_hour_label = st.selectbox("查詢時辰", list(hours_map.keys()), index=0, key="target_hour")
with col10:
    query_type = st.radio("排盤模式", ["本命盤", "流年", "流月", "流日", "流時"], horizontal=True)


# --- 共用函式：負責美化並顯示命盤 ---
def display_chart(soup_data, title_text):
    found_table = None
    max_td_count = 0
    for table in soup_data.find_all('table'):
        text = table.get_text()
        td_count = len(table.find_all('td'))
        if ("紫微" in text and "天機" in text) and td_count > max_td_count:
            found_table = table
            max_td_count = td_count
            
    if found_table:
        st.success(f"抓取成功！目前顯示：{title_text} 🎉")
        
        # 強制把中間格子的背景塗白、文字塗黑
        for td in found_table.find_all('td'):
            if td.get('colspan') == '2' and td.get('rowspan') == '2':
                td['style'] = 'background-color: #ffffff !important; color: #000000 !important; padding: 15px;'
                for font in td.find_all('font'):
                    if font.has_attr('color'):
                        del font['color']
        
        table_html = str(found_table).replace('<table', '<table border="1" style="width:100%; text-align:center; border-collapse: collapse; border-color: #555555; background-color: #ffffff; color: #000000;"')
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.error("抓取失敗：找不到符合格式的命盤，請確認日期是否輸入正確。")


# --- 3. 抓取資料主邏輯 ---
if st.button("開始排盤 🚀"):
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "0"

    with st.spinner("🤖 正在模擬操作，計算命盤中..."):
        try:
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://fate.windada.com/"
            }
            url = "https://fate.windada.com/cgi-bin/fate"
            
            # 【階段一：取得並送出本命表單】
            first_page = session.get(url, headers=headers)
            first_page.encoding = 'utf-8'
            soup = BeautifulSoup(first_page.text, 'html.parser')
            form = soup.find('form')
            
            payload = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name and input_tag.get('type') not in ['submit', 'reset']:
                    payload[name] = value
                    
            for select_tag in form.find_all('select'):
                name = select_tag.get('name')
                if name:
                    options = select_tag.find_all('option')
                    if options:
                        payload[name] = options[0].get('value', options[0].text)

            for key in payload.keys():
                k_low = key.lower()
                if "year" in k_low or key == "y": payload[key] = str(year)
                elif "month" in k_low or key == "m": payload[key] = str(month)
                elif "day" in k_low or key == "d": payload[key] = str(day)
                elif "hour" in k_low or key == "h" or "time" in k_low: payload[key] = hour_val
                elif "sex" in k_low or "gen" in k_low: payload[key] = gender_val

            action_url = form.get('action')
            submit_url = urljoin(url, action_url) if action_url else url
            
            # 送出本命盤請求
            res1 = session.post(submit_url, data=payload, headers=headers) if form.get('method', 'get').lower() == 'post' else session.get(submit_url, params=payload, headers=headers)
            res1.encoding = 'utf-8'
            res1_soup = BeautifulSoup(res1.text, 'html.parser')
            
            # 如果只要本命盤，到這裡就可以直接顯示了
            if query_type == "本命盤":
                display_chart(res1_soup, f"{year}年{month}月{day}日 本命盤")
                st.stop()
                
            # 【階段二：解析流年表單並送出】
            fortune_form = None
            for f in res1_soup.find_all('form'):
                # 尋找有「流年」按鈕的那個表單
                if f.find('input', value=lambda v: v and '流年' in v):
                    fortune_form = f
                    break
                    
            if not fortune_form:
                st.error("已算出本命盤，但找不到流年設定表單！網站格式可能已更改。")
                st.stop()

            # 智慧收集流年表單的隱藏參數與 Radio 選項
            fortune_payload = {}
            radio_names = set()
            for inp in fortune_form.find_all('input'):
                name = inp.get('name')
                t = inp.get('type', '').lower()
                if not name or t in ['submit', 'button', 'reset']: continue
                
                if t == 'radio':
                    radio_names.add(name)
                    if inp.has_attr('checked'): fortune_payload[name] = inp.get('value', '')
                else:
                    fortune_payload[name] = inp.get('value', '')
                    
            # 確保 Radio 有預設值 (流年本宮)
            for rn in radio_names:
                if rn not in fortune_payload:
                    first_radio = fortune_form.find('input', {'type': 'radio', 'name': rn})
                    if first_radio: fortune_payload[rn] = first_radio.get('value', '')

            # 智慧配對下拉選單 (農曆/年/月/日/時)
            for s in fortune_form.find_all('select'):
                name = s.get('name')
                options = s.find_all('option')
                if not options or not name: continue
                
                opt_texts = [opt.text.strip() for opt in options]
                opt_values = [opt.get('value', opt.text) for opt in options]
                
                if "曆" in opt_texts[0]: 
                    fortune_payload[name] = opt_values[0] # 預設農曆
                elif any(str(t_year) in text for text in opt_texts): 
                    idx = next((i for i, text in enumerate(opt_texts) if str(t_year) in text), 0)
                    fortune_payload[name] = opt_values[idx]
                elif len(options) == 12 and "1" in opt_texts[0]: 
                    idx = next((i for i, text in enumerate(opt_texts) if str(t_month) == text), 0)
                    fortune_payload[name] = opt_values[idx]
                elif len(options) >= 28 and "1" in opt_texts[0]: 
                    idx = next((i for i, text in enumerate(opt_texts) if str(t_day) == text), 0)
                    fortune_payload[name] = opt_values[idx]
                elif len(options) >= 12: 
                    t_hour_index = list(hours_map.keys()).index(t_hour_label)
                    fortune_payload[name] = opt_values[t_hour_index] if t_hour_index < len(options) else opt_values[0]
                else:
                    fortune_payload[name] = opt_values[0]

            # 模擬點擊「流年/流月/流日/流時」的按鈕
            target_btn = fortune_form.find('input', value=query_type)
            if target_btn and target_btn.get('name'):
                fortune_payload[target_btn.get('name')] = target_btn.get('value')

            f_action = fortune_form.get('action')
            f_url = urljoin(url, f_action) if f_action else url
            
            # 送出第二階段的流年請求
            res2 = session.post(f_url, data=fortune_payload, headers=headers) if fortune_form.get('method', 'get').lower() == 'post' else session.get(f_url, params=fortune_payload, headers=headers)
            res2.encoding = 'utf-8'
            res2_soup = BeautifulSoup(res2.text, 'html.parser')
            
            display_chart(res2_soup, f"{t_year}年 {query_type}命盤")

        except Exception as e:
            st.error(f"連線或解析時發生錯誤：{e}")
