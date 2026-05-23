import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="八字命盤查詢系統", page_icon="🔮")
st.title("🔮 八字命盤抓取系統")
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
    gender_val = "1" if gender_label == "男" else "2"
    
    url = "https://fate.windada.com/cgi-bin/fate"
    payload = {
        "year": str(year), "month": str(month), "day": str(day),
        "hour": hour_val, "sex": gender_val, "type": "find", "place": "1"
    }

    # 🔥 關鍵修改：加上瀏覽器偽裝 (User-Agent)，騙過網站防護機制
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://fate.windada.com/cgi-bin/fate"
    }

    with st.spinner("正在連線至伺服器抓取資料..."):
        try:
            # 這裡把 headers 傳送出去
            res = requests.post(url, data=payload, headers=headers)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 尋找網頁中的命盤表格
            found_table = None
            for table in soup.find_all('table'):
                # 放寬搜尋條件，只要有年柱和日柱就算數
                if "年柱" in table.get_text() and "日柱" in table.get_text():
                    found_table = table
                    break
            
            if found_table:
                st.success("抓取成功！")
                st.markdown("---")
                st.subheader(f"📅 {year}年{month}月{day}日 的命盤")
                st.markdown(str(found_table), unsafe_allow_html=True)
            else:
                st.warning("有連上網站，但找不到標準格式的命盤表格，請確認輸入日期。")
                # 🔥 新增除錯模式：如果失敗，讓你看網站到底給了什麼畫面
                with st.expander("👉 點我查看網站實際回傳的內容 (看看是否被擋住了)"):
                    st.code(res.text[:3000], language="html")
                
        except Exception as e:
            st.error(f"連線失敗，發生錯誤：{e}")
