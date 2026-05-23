import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮")
st.title("🔮 紫微命盤抓取系統")
st.write("資料來源自動抓取自 [windada算命網](https://fate.windada.com/cgi-bin/fate)")

# --- 2. 建立網頁輸入介面 ---
col1, col2, col3 = st.columns(3)
with col1:
    year = st.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1990)
with col2:
    month = st.number_input("出生月", min_value=1, max_value=12, value=10)
with col3:
    day = st.number_input("出生日", min_value=1, max_value=31, value=10)

hours_map = {
    "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "1", "寅時 (03:00 - 05:00)": "2",
    "卯時 (05:00 - 07:00)": "3", "辰時 (07:00 - 09:00)": "4", "巳時 (09:00 - 11:00)": "5",
    "午時 (11:00 - 13:00)": "6", "未時 (13:00 - 15:00)": "7", "申時 (15:00 - 17:00)": "8",
    "酉時 (17:00 - 19:00)": "9", "戌時 (19:00 - 21:00)": "10", "亥時 (21:00 - 23:00)": "11"
}

hour_label = st.selectbox("請選擇出生時辰", list(hours_map.keys()))
gender_label = st.radio("請選擇性別", ["男", "女"], horizontal=True)

# --- 3. 抓取資料與顯示 ---
if st.button("開始排盤 🚀"):
    hour_val = hours_map[hour_label]
    # 修正：通常算命網站男生代碼是1，女生是0
    gender_val = "1" if gender_label == "男" else "0"
    
    url = "https://fate.windada.com/cgi-bin/fate"
    # 增加 submit 參數，更真實模擬人類按下送出按鈕
    payload = {
        "year": str(year), "month": str(month), "day": str(day),
        "hour": hour_val, "sex": gender_val, "type": "find", "place": "1",
        "submit": "送出"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://fate.windada.com/cgi-bin/fate"
    }

    with st.spinner("正在連線至伺服器抓取資料..."):
        try:
            res = requests.post(url, data=payload, headers=headers)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 🔥 關鍵修改：放寬條件，尋找紫微斗數的命盤表格
            found_table = None
            max_td_count = 0
            
            for table in soup.find_all('table'):
                text = table.get_text()
                td_count = len(table.find_all('td'))
                
                # 紫微命盤特徵：一定有「命宮」或「農曆」這些字，而且因為是 12 宮格，格子(td)數量會很多
                if ("命宮" in text or "農曆" in text) and td_count > max_td_count:
                    found_table = table
                    max_td_count = td_count
            
            if found_table:
                st.success("抓取成功！")
                st.markdown("---")
                st.subheader(f"📅 {year}年{month}月{day}日 的紫微命盤")
                
                # 幫抓下來的表格加上框線，讓 12 宮格更好看
                table_html = str(found_table).replace('<table', '<table border="1" style="width:100%; text-align:center; border-collapse: collapse;"')
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning("有連上網站，但找不到標準格式的命盤表格，請確認輸入日期。")
                with st.expander("👉 點我查看網站實際回傳的內容"):
                    st.code(res.text[:3000], language="html")
                
        except Exception as e:
            st.error(f"連線失敗，發生錯誤：{e}")
