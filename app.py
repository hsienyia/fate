import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="八字命盤查詢系統", page_icon="🔮")
st.title("🔮 八字命盤抓取系統")
st.write("資料來源自動抓取自 [windada算命網](https://fate.windada.com/cgi-bin/fate)")

# --- 2. 建立網頁輸入介面 ---
# 把年月日分成三個直行
col1, col2, col3 = st.columns(3)
with col1:
    year = st.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1990)
with col2:
    month = st.number_input("出生月", min_value=1, max_value=12, value=10)
with col3:
    day = st.number_input("出生日", min_value=1, max_value=31, value=10)

# 時辰對應表 (讓網頁顯示中文，程式偷偷傳數字給伺服器)
hours_map = {
    "子時 (23:00 - 01:00)": "0",
    "丑時 (01:00 - 03:00)": "1",
    "寅時 (03:00 - 05:00)": "2",
    "卯時 (05:00 - 07:00)": "3",
    "辰時 (07:00 - 09:00)": "4",
    "巳時 (09:00 - 11:00)": "5",
    "午時 (11:00 - 13:00)": "6",
    "未時 (13:00 - 15:00)": "7",
    "申時 (15:00 - 17:00)": "8",
    "酉時 (17:00 - 19:00)": "9",
    "戌時 (19:00 - 21:00)": "10",
    "亥時 (21:00 - 23:00)": "11"
}

# 下拉選單與單選按鈕
hour_label = st.selectbox("請選擇出生時辰", list(hours_map.keys()))
gender_label = st.radio("請選擇性別", ["男", "女"], horizontal=True)

# --- 3. 抓取資料與顯示 ---
if st.button("開始排盤 🚀"):
    # 轉換資料格式給目標網站
    hour_val = hours_map[hour_label]
    gender_val = "1" if gender_label == "男" else "2"
    
    url = "https://fate.windada.com/cgi-bin/fate"
    payload = {
        "year": str(year),
        "month": str(month),
        "day": str(day),
        "hour": hour_val,
        "sex": gender_val,
        "type": "find",
        "place": "1"
    }

    # 顯示轉圈圈的讀取動畫
    with st.spinner("正在連線至伺服器抓取資料..."):
        try:
            res = requests.post(url, data=payload)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            st.success("抓取成功！")
            st.markdown("---")
            st.subheader(f"📅 {year}年{month}月{day}日 的命盤")
            
            # 尋找網頁中的命盤表格
            found_table = None
            for table in soup.find_all('table'):
                # 判斷這個表格是不是包含命盤關鍵字
                if "時柱" in table.get_text() and "日柱" in table.get_text():
                    found_table = table
                    break
            
            if found_table:
                # 直接將抓到的 HTML 表格顯示在 Streamlit 上，這樣最整齊！
                st.markdown(str(found_table), unsafe_allow_html=True)
            else:
                st.warning("有連上網站，但找不到標準格式的命盤表格，請確認輸入日期。")
                
        except Exception as e:
            st.error(f"連線失敗，發生錯誤：{e}")
