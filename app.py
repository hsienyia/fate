import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime
import streamlit.components.v1 as components
import re

# --- 全域設定：確保不會再出現 name 'HEADERS' is not defined ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Referer": "https://fate.windada.com/"
}

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="紫微命盤查詢系統", page_icon="🔮", layout="wide")
st.title("🔮 紫微命盤抓取系統 (兩階段拆解版)")
st.write("完全模擬網站流程：先取得本命盤 ➔ 再疊加流時盤")

# --- 初始化暫存區 (記憶兩階段的資料) ---
if "step1_done" not in st.session_state:
    st.session_state.step1_done = False
if "cookies" not in st.session_state:
    st.session_state.cookies = None
if "birth_chart" not in st.session_state:
    st.session_state.birth_chart = None
if "transit_form_html" not in st.session_state:
    st.session_state.transit_form_html = ""
if "transit_form_data" not in st.session_state:
    st.session_state.transit_form_data = {}
if "submit_url" not in st.session_state:
    st.session_state.submit_url = ""
if "transit_chart" not in st.session_state:
    st.session_state.transit_chart = None
if "transit_header" not in st.session_state:
    st.session_state.transit_header = ""
if "transit_charts" not in st.session_state:
    st.session_state.transit_charts = {}

now = datetime.datetime.now()

# --- 2. 建立網頁輸入介面 ---
col_left, col_right = st.columns(2)

with col_left:
    st.success("### 步驟一：輸入本命資料")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("出生年 (西元)", min_value=1900, max_value=2100, value=1992)
        month = c2.number_input("出生月", min_value=1, max_value=12, value=6)
        day = c3.number_input("出生日", min_value=1, max_value=31, value=18)
        
        hours_map = {
            "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
            "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
            "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
            "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
        }
        
        c4, c5 = st.columns(2)
        hour_label = c4.selectbox("出生時辰", list(hours_map.keys()), index=8)
        gender_label = c5.radio("性別", ["男", "女"], horizontal=True)
        
        # 第一步按鈕：完全還原你之前 100% 成功的寫法，先抓取空表單金鑰再送出！
        if st.button("1️⃣ 開始排本命盤", use_container_width=True):
            hour_val = hours_map[hour_label]
            gender_val = "1" if gender_label == "男" else "0"
            
            with st.spinner("正在破解表單防護並抓取本命盤..."):
                try:
                    session = requests.Session()
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                        "Referer": "https://fate.windada.com/"
                    }
                    url = "https://fate.windada.com/cgi-bin/fate"
                    
                    # 1. 先去拿網頁的隱藏金鑰 (這是成功關鍵！)
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

                    # 2. 注入你的本命資料
                    for key in list(payload.keys()):
                        k_low = key.lower()
                        if "year" in k_low or key == "y": payload[key] = str(year)
                        elif "month" in k_low or key == "m": payload[key] = str(month)
                        elif "day" in k_low or key == "d": payload[key] = str(day)
                        elif "hour" in k_low or key == "h" or "time" in k_low: payload[key] = hour_val
                        elif "sex" in k_low or "gen" in k_low: payload[key] = gender_val

                    action_url = form.get('action')
                    submit_url = urljoin(url, action_url) if action_url else url
                    method = form.get('method', 'get').lower()

                    # 3. 發送取得本命盤
                    if method == 'post':
                        res_birth = session.post(submit_url, data=payload, headers=headers)
                    else:
                        res_birth = session.get(submit_url, params=payload, headers=headers)
                    
                    res_birth.encoding = 'utf-8'
                    birth_soup = BeautifulSoup(res_birth.text, 'html.parser')
                    
                    # 儲存 Session Cookies 供第二步使用 (保持連線狀態)
                    st.session_state.cookies = session.cookies.get_dict()
                    
                    # 4. 尋找真正的本命盤表格
                    birth_table = None
                    max_td_count = 0
                    for table in birth_soup.find_all('table'):
                        text = table.get_text()
                        td_count = len(table.find_all('td'))
                        if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                            birth_table = table
                            max_td_count = td_count
                            
                    if birth_table:
                        st.session_state.birth_chart = str(birth_table)
                        
                        # 5. 攔截第二步的流轉表單金鑰，偷偷存起來
                        transit_form = birth_soup.find('form')
                        t_payload = {}
                        if transit_form:
                            st.session_state.transit_form_html = str(transit_form) # 存下表單結構供第二步找按鈕用
                            for inp in transit_form.find_all('input'):
                                name = inp.get('name')
                                if name and inp.get('type') not in ['submit', 'reset', 'button']:
                                    t_payload[name] = inp.get('value', '')
                            for sel in transit_form.find_all('select'):
                                name = sel.get('name')
                                if name:
                                    selected = sel.find('option', selected=True)
                                    t_payload[name] = selected.get('value', selected.text) if selected else sel.find('option').get('value', '')
                            
                            st.session_state.transit_form_data = t_payload
                            t_action = transit_form.get('action')
                            st.session_state.submit_url = urljoin(submit_url, t_action) if t_action else submit_url
                            
                            st.session_state.step1_done = True
                            st.session_state.transit_chart = None # 重置舊的流時盤
                            st.rerun() # 自動重整網頁顯示右側
                    else:
                        st.error("未能成功解析到命盤表格，可能是防護阻擋，請再試一次。")

                except Exception as e:
                    st.error(f"第一步發生錯誤：{e}")

with col_right:
    st.info("### 步驟二：設定流轉日期")
    with st.container(border=True):
        # 1. 新增：讓你選擇流轉日期是國曆還是農曆
        t_solar_label = st.radio("流轉日期格式", ["國曆", "農曆"], index=0, horizontal=True)
        
        tc1, tc2, tc3 = st.columns(3)
        t_year = tc1.number_input("欲查年份", min_value=1900, max_value=2100, value=2026)
        t_month = tc2.number_input("欲查月份", min_value=1, max_value=12, value=5)
        t_day = tc3.number_input("欲查日期", min_value=1, max_value=31, value=23)
        
        tc4, tc5 = st.columns(2)
        t_hour_label = tc4.selectbox("欲查時辰", list(hours_map.keys()), key="t_hour_select")
        transit_start = tc5.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)
        # transit_type = st.radio("查詢模式", ["流年", "流月", "流日", "流時"], index=3, horizontal=True) # 這行可以刪除，因為已經是一鍵四盤了

        # 第二步按鈕：連續請求四個盤
        if st.button("🚀 一鍵取得四重流轉盤", use_container_width=True):
            with st.spinner("正在向伺服器請求年、月、日、時四個盤 (請稍候幾秒)..."):
                try:
                    # 1. 重新建立 Session 並載入 Cookie
                    session = requests.Session()
                    if st.session_state.cookies:
                        requests.utils.add_dict_to_cookiejar(session.cookies, st.session_state.cookies)
                    
                    # 2. 定義四個盤的 Target 代碼
                    targets = {"流年盤": "3", "流月盤": "4", "流日盤": "5", "流時盤": "6"}
                    st.session_state.transit_charts = {} # 清空舊資料
                    
                    # 3. 迴圈連續發送四次請求
                    for title, target_val in targets.items():
                        payload = {
                            "FUNC": "Basic",
                            "Name": "",
                            "Solar": "1", # 這是本命盤的設定 (固定國曆)
                            "Year": str(year),
                            "Month": str(month),
                            "Day": str(day),
                            "Hour": hours_map[hour_label],
                            "Sex": "1" if gender_label == "男" else "0",
                            "Target": target_val, # 動態替換 3, 4, 5, 6
                            "SubTarget": "0",
                            "Old": "0",
                            "FateYearType": "0" if transit_start == "流年本宮" else "1",
                            
                            # --- 關鍵修改：動態帶入 國曆("1") 或 農曆("0") ---
                            "FateSolar": "1" if t_solar_label == "國曆" else "0", 
                            
                            "FateYear": str(t_year),
                            "FateMonth": str(t_month),
                            "FateDay": str(t_day),
                            "FateHour": hours_map[t_hour_label]
                        }
                        
                        response = session.post("https://fate.windada.com/cgi-bin/fate", data=payload, headers=HEADERS)
                        response.encoding = 'utf-8'
                        
                        # 解析並存入字典
                        transit_soup = BeautifulSoup(response.text, 'html.parser')
                        transit_table = None
                        max_td_count = 0
                        
                        for table in transit_soup.find_all('table'):
                            text = table.get_text()
                            td_count = len(table.find_all('td'))
                            if ("紫微" in text and "天機" in text) and td_count > max_td_count:
                                transit_table = table
                                max_td_count = td_count
                                
                        if transit_table:
                            st.session_state.transit_charts[title] = str(transit_table)
                            
                    st.rerun() # 四個盤都抓完後重整畫面
                    
                except Exception as e:
                    st.error(f"錯誤：{e}")

st.markdown("---")

# --- 升級版：疊加算分引擎與詳細計算過程 (精準鎖定黃色流轉命宮) ---
def calculate_single_board_score(html_content, mode):
    if not html_content:
        return 50, ["無資料，給予基準分: 50分"]
        
    # 時間濾鏡：避免長週期盤受到短週期星曜干擾
    if mode == "流年盤": html_content = re.sub(r'流[月日時][祿權科忌]', '', html_content)
    elif mode == "流月盤": html_content = re.sub(r'流[日時][祿權科忌]', '', html_content)
    elif mode == "流日盤": html_content = re.sub(r'流時[祿權科忌]', '', html_content)

    soup = BeautifulSoup(html_content, 'html.parser')
    cells = soup.find_all('td', width="25%")
    if len(cells) != 12: return 50, ["格式錯誤，給予基準分: 50分"]

    cell_texts = [cell.get_text() for cell in cells]
    clockwise_indices = [8, 6, 4, 0, 1, 2, 3, 5, 7, 11, 10, 9]
    
    # ==========================================
    # 🌟 核心修正：尋找黃色區塊作為「流轉命宮」
    # ==========================================
    ming_pos = -1
    for i, idx in enumerate(clockwise_indices):
        # 將該格子的 HTML 轉大寫並去除空白，精準比對背景顏色
        cell_html = str(cells[idx]).replace(" ", "").upper()
        # Windada 標示流轉命宮的顏色是 #FFCC66 (黃色)
        if "BACKGROUND-COLOR:#FFCC66" in cell_html or "BACKGROUND-COLOR:YELLOW" in cell_html:
            ming_pos = i
            break
            
    # 防呆機制：如果網站改版導致抓不到黃色，才退回找字面上的【命宮】
    if ming_pos == -1: 
        for i, idx in enumerate(clockwise_indices):
            if "【命宮】" in cell_texts[idx]:
                ming_pos = i
                break
                
    if ming_pos == -1: return 50, ["找不到命宮，給予基準分: 50分"]

    # 找到命宮後，依照你的邏輯順時針推算 2(福)、4(官)、6(遷)、8(財)
    ming = cell_texts[clockwise_indices[ming_pos]]
    fu   = cell_texts[clockwise_indices[(ming_pos + 2) % 12]]  
    guan = cell_texts[clockwise_indices[(ming_pos + 4) % 12]]  
    qian = cell_texts[clockwise_indices[(ming_pos + 6) % 12]]  
    cai  = cell_texts[clockwise_indices[(ming_pos + 8) % 12]]  
    
    palaces_to_check = [
        (ming, True, "流轉命宮"), (qian, True, "流轉遷移"), (fu, True, "流轉福德"), 
        (cai, False, "流轉財帛"), (guan, False, "流轉事業")
    ]

    score = 60
    process_log = ["**🔹 基礎起算分: 60 分 (嚴格風控模式)**"]
    
    for p_text, is_mqf, p_name in palaces_to_check:
        # 1. 祿、權、科
        lu_count = len(re.findall(r'祿', p_text))
        quan_count = len(re.findall(r'權', p_text))
        ke_count = len(re.findall(r'科', p_text))
        
        if lu_count > 0:
            pts = lu_count * 10
            score += pts
            process_log.append(f"✅ `{p_name}` 見祿星 x{lu_count} (+{pts}分)")
        
        if quan_count > 0 or ke_count > 0:
            pts = (quan_count + ke_count) * 5
            score += pts
            process_log.append(f"✅ `{p_name}` 見權/科 x{quan_count+ke_count} (+{pts}分)")
        
        # 2. 財星群聚
        wealth_stars = sum(1 for star in ["武曲", "太陰", "天府"] if star in p_text)
        if "貪狼" in p_text and any(s in p_text for s in ["紅鸞", "天喜", "咸池", "天姚", "沐浴"]):
            wealth_stars += 1
            process_log.append(f"✅ `{p_name}` 貪狼逢桃花財 (+加計1財星)")
        if "天梁" in p_text and "太陽" in p_text:
            wealth_stars += 1
            process_log.append(f"✅ `{p_name}` 陽梁蔭星財 (+加計1財星)")
            
        if wealth_stars > 0:
            pts = wealth_stars * 5
            score += pts
            process_log.append(f"💰 `{p_name}` 財星數量 x{wealth_stars} (+{pts}分)")
        
        # 3. 動能：天馬與祿馬交馳
        ma_count = len(re.findall(r'馬', p_text))
        if ma_count > 0:
            pts = ma_count * 5
            score += pts
            process_log.append(f"🐎 `{p_name}` 見天馬 x{ma_count} (+{pts}分)")
            
            if lu_count > 0:
                score += 15
                process_log.append(f"🔥 `{p_name}` 祿馬交馳爆發 (+15分)")
            if "陀" in p_text:
                score -= 20
                process_log.append(f"⚠️ `{p_name}` 陀羅折足馬 (-20分)")
            
        # 4. 嚴格扣分區 (針對流轉命遷福)
            # 定義不同等級的空亡星
        has_kong_soft = "旬空" in p_text or "天空" in p_text
        has_kong_hard = "地空" in p_text
        has_jie_hard = "地劫" in p_text
            
        if has_kong_hard and has_jie_hard:
            score -= 30
            process_log.append(f"❌ `{p_name}` 地空地劫同宮重傷 (-100分)")
        elif has_kong_hard:
            score -= 10
            process_log.append(f"❌ `{p_name}` 逢地空星 (-40分)")
        elif has_jie_hard:
            score -= 10
            process_log.append(f"❌ `{p_name}` 逢地劫星 (-40分)")
        elif has_kong_soft:
            score -= 5
            process_log.append(f"❌ `{p_name}` 逢旬空/天空星 (-20分)")
                
        ji_count = len(re.findall(r'忌', p_text))
        if ji_count > 0:
            is_exempt = any(f"{star}廟" in p_text or f"{star}旺" in p_text for star in ["武曲", "太陰", "太陽", "天機", "天同"])
            if is_exempt:
                process_log.append(f"🛡️ `{p_name}` 逢忌，但廟旺豁免 (不扣分)")
            else:
                pts = ji_count * 20
                score -= pts
                process_log.append(f"❌ `{p_name}` 逢忌煞 x{ji_count} (-{pts}分)")

    final_score = max(0, min(200, score))
    if score != final_score:
        process_log.append(f"📊 結算溢出調整: 原始 {score} 分 ➔ 最終限制在 {final_score} 分")
    return final_score, process_log
    

def get_total_luck_index(charts_dict):
    if not charts_dict or len(charts_dict) < 4:
        return 0, {}, {}
        
    scores = {}
    logs = {}
    for mode in ["流年盤", "流月盤", "流日盤", "流時盤"]:
        s, l = calculate_single_board_score(charts_dict.get(mode, ""), mode)
        scores[mode] = s
        logs[mode] = l
    
    total = (scores["流年盤"] * 0.15) + (scores["流月盤"] * 0.15) + (scores["流日盤"] * 0.3) + (scores["流時盤"] * 0.4)
    return round(total, 1), scores, logs

# --- 3. 畫面顯示區 (上方本命，下方四盤) ---
st.markdown("<h3 style='text-align: center;'>🪐 核心：本命盤</h3>", unsafe_allow_html=True)
if st.session_state.birth_chart:
    # 置中顯示本命盤
    components.html(st.session_state.birth_chart, height=550, scrolling=True)
else:
    st.info("請先點擊左側「1️⃣ 開始排本命盤」。")

st.markdown("---")

# --- 插入好運指數儀表板 ---
if hasattr(st.session_state, 'transit_charts') and len(st.session_state.transit_charts) == 4:
    # 接收更新後的三個回傳值
    total_luck, individual_scores, process_logs = get_total_luck_index(st.session_state.transit_charts)
    
    st.markdown("---")
    st.markdown("### 📊 快樂體操核心：當下好運指數與解析")
    
    # 1. 大總分顯示
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        color = "green" if total_luck >= 70 else "orange" if total_luck >= 50 else "red"
        st.markdown(
            f"""
            <div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center;">
                <h1 style="color:white; font-size:48px; margin:0;">{total_luck} 分</h1>
                <h4 style="color:white; margin:0;">(綜合加權總分)</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if total_luck >= 80:
            st.success("🔥 盤勢極佳！祿馬交馳或財星雲集，空劫無擾，適合積極佈局！")
        elif total_luck >= 60:
            st.info("⚖️ 盤勢中性偏吉。有機會，但需留意短線震盪洗盤。")
        else:
            st.error("⚠️ 盤勢風險高！命遷福受空劫忌重擊，建議空手觀望。")

    # 2. 四盤個別分數與權重貢獻
    st.markdown("#### 🎯 各維度獨立評分")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("流年盤 (佔 15%)", f"{individual_scores['流年盤']} 分", f"貢獻: {round(individual_scores['流年盤']*0.15, 1)}分", delta_color="off")
    sc2.metric("流月盤 (佔 15%)", f"{individual_scores['流月盤']} 分", f"貢獻: {round(individual_scores['流月盤']*0.15, 1)}分", delta_color="off")
    sc3.metric("流日盤 (佔 30%)", f"{individual_scores['流日盤']} 分", f"貢獻: {round(individual_scores['流日盤']*0.30, 1)}分", delta_color="off")
    sc4.metric("流時盤 (佔 40%)", f"{individual_scores['流時盤']} 分", f"貢獻: {round(individual_scores['流時盤']*0.40, 1)}分", delta_color="off")

    # 3. 隱藏式詳細計算過程 (點擊展開)
    with st.expander("📝 點此展開查看各盤詳細計算過程 (演算法軌跡)"):
        log_c1, log_c2 = st.columns(2)
        log_c3, log_c4 = st.columns(2)
        
        log_cols = [
            ("流年盤", log_c1), ("流月盤", log_c2), 
            ("流日盤", log_c3), ("流時盤", log_c4)
        ]
        
        for mode, col in log_cols:
            with col:
                st.markdown(f"**【{mode}】算分明細**")
                # 將陣列中的日誌逐條印出
                for line in process_logs[mode]:
                    st.write(line)
                st.markdown("---")

# 顯示四個流轉盤
if hasattr(st.session_state, 'transit_charts') and st.session_state.transit_charts:
    # 建立 2x2 網格
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    grid_mapping = [
        ("流年盤", col1),
        ("流月盤", col2),
        ("流日盤", col3),
        ("流時盤", col4)
    ]
    
    for title, col in grid_mapping:
        with col:
            st.markdown(f"<h4 style='text-align: center;'>{title}</h4>", unsafe_allow_html=True)
            if title in st.session_state.transit_charts:
                # 渲染網站算好的真實盤面
                components.html(st.session_state.transit_charts[title], height=500, scrolling=True)
            else:
                st.warning(f"無法取得{title}資料")
elif st.session_state.step1_done:
    st.info("本命盤已就緒！請設定上方流轉日期後，點擊「🚀 一鍵取得四重流轉盤」。")
