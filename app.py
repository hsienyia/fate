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

# --- 1. 網頁基本設定 & CSS 強制不換行 ---
st.set_page_config(page_title="財運與機運", page_icon="🔮", layout="wide")

# 透過 CSS 強制讓 st.metric 並排不換行，並稍微縮小數字字體以適應寬度
st.markdown(
    """
    <style>
    div[data-testid="metric-container"] {
        white-space: nowrap !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.title("🔮 財運與機運")
st.write("先輸入生辰 ➔ 再查詢今日運勢")

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
        day = c3.number_input("出生日", min_value=1, max_value=31, value=1)
        
        hours_map = {
            "子時 (23:00 - 01:00)": "0", "丑時 (01:00 - 03:00)": "2", "寅時 (03:00 - 05:00)": "4",
            "卯時 (05:00 - 07:00)": "6", "辰時 (07:00 - 09:00)": "8", "巳時 (09:00 - 11:00)": "10",
            "午時 (11:00 - 13:00)": "12", "未時 (13:00 - 15:00)": "14", "申時 (15:00 - 17:00)": "16", 
            "酉時 (17:00 - 19:00)": "18", "戌時 (19:00 - 21:00)": "20", "亥時 (21:00 - 23:00)": "22"
        }
        
        c4, c5 = st.columns(2)
        hour_label = c4.selectbox("出生時辰", list(hours_map.keys()), index=8)
        gender_label = c5.radio("性別", ["男", "女"], horizontal=True)
        
        # 第一步按鈕
        if st.button("1️⃣ 開始排本命盤", use_container_width=True):
            hour_val = hours_map[hour_label]
            gender_val = "1" if gender_label == "男" else "0"
            
            with st.spinner("正在破解表單防護並抓取本命盤..."):
                try:
                    session = requests.Session()
                    url = "https://fate.windada.com/cgi-bin/fate"
                    
                    first_page = session.get(url, headers=HEADERS)
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

                    if method == 'post':
                        res_birth = session.post(submit_url, data=payload, headers=HEADERS)
                    else:
                        res_birth = session.get(submit_url, params=payload, headers=HEADERS)
                    
                    res_birth.encoding = 'utf-8'
                    birth_soup = BeautifulSoup(res_birth.text, 'html.parser')
                    
                    st.session_state.cookies = session.cookies.get_dict()
                    
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
                        
                        transit_form = birth_soup.find('form')
                        t_payload = {}
                        if transit_form:
                            st.session_state.transit_form_html = str(transit_form) 
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
                            st.session_state.transit_chart = None 
                            st.rerun() 
                    else:
                        st.error("未能成功解析到命盤表格，可能是防護阻擋，請再試一次。")

                except Exception as e:
                    st.error(f"第一步發生錯誤：{e}")

with col_right:
    st.info("### 步驟二：設定流轉日期")
    with st.container(border=True):
        t_solar_label = st.radio("流轉日期格式", ["國曆", "農曆"], index=0, horizontal=True)
        
        tc1, tc2, tc3 = st.columns(3)
        t_year = tc1.number_input("欲查年份", min_value=1900, max_value=2100, value=2026)
        t_month = tc2.number_input("欲查月份", min_value=1, max_value=12, value=5)
        t_day = tc3.number_input("欲查日期", min_value=1, max_value=31, value=23)
        
        tc4, tc5 = st.columns(2)
        t_hour_label = tc4.selectbox("欲查時辰", list(hours_map.keys()), key="t_hour_select")
        transit_start = tc5.radio("流月起始宮位", ["流年本宮", "流年斗君"], index=0)

        # 第二步按鈕
        if st.button("🚀 一鍵取得四重流轉盤", use_container_width=True):
            with st.spinner("正在向伺服器請求年、月、日、時四個盤 (請稍候幾秒)..."):
                try:
                    session = requests.Session()
                    if st.session_state.cookies:
                        requests.utils.add_dict_to_cookiejar(session.cookies, st.session_state.cookies)
                    
                    targets = {"流年盤": "3", "流月盤": "4", "流日盤": "5", "流時盤": "6"}
                    st.session_state.transit_charts = {} 
                    
                    for title, target_val in targets.items():
                        payload = {
                            "FUNC": "Basic",
                            "Name": "",
                            "Solar": "1", 
                            "Year": str(year),
                            "Month": str(month),
                            "Day": str(day),
                            "Hour": hours_map[hour_label],
                            "Sex": "1" if gender_label == "男" else "0",
                            "Target": target_val, 
                            "SubTarget": "0",
                            "Old": "0",
                            "FateYearType": "0" if transit_start == "流年本宮" else "1",
                            "FateSolar": "1" if t_solar_label == "國曆" else "0", 
                            "FateYear": str(t_year),
                            "FateMonth": str(t_month),
                            "FateDay": str(t_day),
                            "FateHour": hours_map[t_hour_label]
                        }
                        
                        response = session.post("https://fate.windada.com/cgi-bin/fate", data=payload, headers=HEADERS)
                        response.encoding = 'utf-8'
                        
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
                            
                    st.rerun() 
                    
                except Exception as e:
                    st.error(f"錯誤：{e}")

st.markdown("---")

# ==========================================
# 引擎區塊 1：好運指數 (原有)
# ==========================================
def calculate_single_board_score(html_content, mode):
    if not html_content:
        return 50, ["無資料，給予基準分: 50分"]
        
    if mode == "流年盤": html_content = re.sub(r'流[月日時][祿權科忌]', '', html_content)
    elif mode == "流月盤": html_content = re.sub(r'流[日時][祿權科忌]', '', html_content)
    elif mode == "流日盤": html_content = re.sub(r'流時[祿權科忌]', '', html_content)

    soup = BeautifulSoup(html_content, 'html.parser')
    cells = soup.find_all('td', width="25%")
    if len(cells) != 12: return 50, ["格式錯誤，給予基準分: 50分"]

    cell_texts = [cell.get_text() for cell in cells]
    clockwise_indices = [8, 6, 4, 0, 1, 2, 3, 5, 7, 11, 10, 9]
    
    # --- 最強雙重防護定位命宮 ---
    ming_pos = -1
    for i, idx in enumerate(clockwise_indices):
        cell_html = str(cells[idx]).replace(" ", "").upper()
        if "BACKGROUND-COLOR:#FFCC66" in cell_html or "BACKGROUND-COLOR:YELLOW" in cell_html:
            ming_pos = i; break
            
    if ming_pos == -1: 
        for i, idx in enumerate(clockwise_indices):
            if "命宮" in cell_texts[idx] or "命、身" in cell_texts[idx]:
                ming_pos = i; break
                
    if ming_pos == -1: return 50, ["找不到命宮，給予基準分: 50分"]
    # ---------------------------

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

        has_tan = "貪狼" in p_text
        has_huo = "火星" in p_text
        has_ling = "鈴星" in p_text
        has_lu = "祿" in p_text or "祿存" in p_text
        has_kongjie = "地空" in p_text or "地劫" in p_text

        if has_tan and (has_huo or has_ling):
            if has_kongjie:
                score -= 50
                process_log.append(f"⚠️ `{p_name}` 火鈴貪逢空劫，容易橫發橫破，此時追高風險極大 (-50分)")
            elif has_lu:
                score += 40
                process_log.append(f"🔥 `{p_name}` 火/鈴貪逢祿引爆，財源滾滾而來，適合大膽佈局 (+40分)")
            else:
                score += 15
                process_log.append(f"⚡ `{p_name}` 火/鈴貪強勢成格，自帶爆發動能，盤勢震盪不懼回檔 (+15分)")
        
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
            
        has_kong_soft = "旬空" in p_text or "天空" in p_text
        has_kong_hard = "地空" in p_text
        has_jie_hard = "地劫" in p_text
            
        if has_kong_hard and has_jie_hard:
            score -= 100
            process_log.append(f"❌ `{p_name}` 地空地劫同宮重傷 (-100分)")
        elif has_kong_hard:
            score -= 40
            process_log.append(f"❌ `{p_name}` 逢地空星 (-40分)")
        elif has_jie_hard:
            score -= 40
            process_log.append(f"❌ `{p_name}` 逢地劫星 (-40分)")
        elif has_kong_soft:
            score -= 5
            process_log.append(f"❌ `{p_name}` 逢旬空/天空星 (-5分)")
                
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


# ==========================================
# 引擎區塊 2：全新機運指數 (三大模組整合)
# ==========================================
def calculate_opportunity_score(html_content, mode):
    base_score = 0 
    
    sub_scores = {"格局": 0, "社交": 0, "貴人": 0}
    process_logs = {"格局": [], "社交": [], "貴人": []}
    process_logs["格局"].append(f"**✨ {mode}機運起算分: 30 分 (嚴格校準版)**") 
    
    if not html_content: return base_score, sub_scores, process_logs
    
    if mode == "流年盤": html_content = re.sub(r'流[月日時][祿權科忌]', '', html_content)
    elif mode == "流月盤": html_content = re.sub(r'流[日時][祿權科忌]', '', html_content)
    elif mode == "流日盤": html_content = re.sub(r'流時[祿權科忌]', '', html_content)

    soup = BeautifulSoup(html_content, 'html.parser')
    cells = soup.find_all('td', width="25%")
    if len(cells) != 12: return base_score, sub_scores, process_logs

    cell_texts = [cell.get_text() for cell in cells]
    clockwise_indices = [8, 6, 4, 0, 1, 2, 3, 5, 7, 11, 10, 9]
    
    # --- 最強雙重防護定位命宮 ---
    ming_pos = -1
    for i, idx in enumerate(clockwise_indices):
        cell_html = str(cells[idx]).replace(" ", "").upper()
        if "BACKGROUND-COLOR:#FFCC66" in cell_html or "BACKGROUND-COLOR:YELLOW" in cell_html:
            ming_pos = i; break
            
    if ming_pos == -1: 
        for i, idx in enumerate(clockwise_indices):
            if "命宮" in cell_texts[idx] or "命、身" in cell_texts[idx]:
                ming_pos = i; break
                
    if ming_pos == -1: return base_score, sub_scores, process_logs
    # ---------------------------

    ming  = cell_texts[clockwise_indices[ming_pos]]
    fumu  = cell_texts[clockwise_indices[(ming_pos + 1) % 12]]  
    guan  = cell_texts[clockwise_indices[(ming_pos + 4) % 12]]  
    jiao  = cell_texts[clockwise_indices[(ming_pos + 5) % 12]]  
    qian  = cell_texts[clockwise_indices[(ming_pos + 6) % 12]]  
    jie   = cell_texts[clockwise_indices[(ming_pos + 7) % 12]]  # 🔺 夾遷移宮專用
    cai   = cell_texts[clockwise_indices[(ming_pos + 8) % 12]]  
    xiong = cell_texts[clockwise_indices[(ming_pos + 11) % 12]] 
    
    sf_text = ming + cai + guan + qian 
    social_text = ming + fumu + guan + jiao + qian 

    # 🔺 建立一個陣列代表活躍區的獨立宮位 (恢復宮位牆壁)
    active_cells = [ming, cai, guan, qian]

    # ==========================================
    # 模組 1：流轉盤格局與魅力榜 (嚴格鎖定核心活躍區)
    # ==========================================
    
    # 🏆 1. 跨宮位核心大格局 (這個看整體三方四正，所以維持用 sf_text)
    if all(s in sf_text for s in ["天機", "太陰", "天同", "天梁"]):
        sub_scores["格局"] += 25
        process_logs["格局"].append("✨ 活躍區觸發「機月同梁」，團隊協作效率大增 (+25分)")

    # 🌟 2. 雙星同宮 (必須在「同一個宮位 p」內同時出現)
    if any("太陽" in p and "太陰" in p for p in active_cells):
        sub_scores["格局"] += 14; process_logs["格局"].append("☀️🌙 活躍區見日月同宮，磁場和諧吸引好機遇 (+14分)")
    if any("天機" in p and "太陰" in p for p in active_cells):
        sub_scores["格局"] += 12; process_logs["格局"].append("🧠 活躍區見機陰同宮，心思細膩社交進退得宜 (+12分)")
    if any("廉貞" in p and "貪狼" in p for p in active_cells):
        sub_scores["格局"] += 9; process_logs["格局"].append("🏅 活躍區見廉貪同宮，風情萬種擄獲異性目光 (+9分)")
    if any("紫微" in p and "貪狼" in p for p in active_cells):
        sub_scores["格局"] += 7; process_logs["格局"].append("🏅 活躍區見紫貪同宮，高貴得體魅力氣場四溢 (+7分)")
    if any("天機" in p and "巨門" in p for p in active_cells):
        sub_scores["格局"] += 5; process_logs["格局"].append("💬 活躍區見機巨同宮，話題豐富適合知性交流 (+5分)")

    # 🌟 3. 四化專屬爆發 (星曜與四化必須在「同一個宮位 p」內同時出現)
    if any("天同" in p and "祿" in p for p in active_cells):
        sub_scores["格局"] += 15; process_logs["格局"].append("🥇 活躍區見天同化祿，當下自帶極強療癒親和力 (+15分)")
    if any("紫微" in p and "科" in p for p in active_cells):
        sub_scores["格局"] += 15; process_logs["格局"].append("👑 活躍區見紫微化科，帝星閃耀，此時威望極高 (+15分)")
    if any("巨門" in p and "祿" in p for p in active_cells):
        sub_scores["格局"] += 12; process_logs["格局"].append("💬 活躍區見巨門化祿，說服力爆表，極利公關談判 (+12分)")
    if any("太陰" in p and "科" in p for p in active_cells):
        sub_scores["格局"] += 12; process_logs["格局"].append("🌕 活躍區見太陰化科，優雅內斂高冷氣質 (+12分)")
    if any("太陽" in p and "科" in p for p in active_cells):
        sub_scores["格局"] += 12; process_logs["格局"].append("☀️ 活躍區見太陽化科，行走暖陽談吐優雅 (+12分)")
    if any("貪狼" in p and "祿" in p for p in active_cells):
        sub_scores["格局"] += 11; process_logs["格局"].append("🏅 活躍區見貪狼化祿，情商天花板，幽默感大爆發 (+11分)")
    if any("太陽" in p and "權" in p for p in active_cells):
        sub_scores["格局"] += 10; process_logs["格局"].append("🏅 活躍區見太陽化權，霸氣能幹，掌控全局 (+10分)")
    if any("天同" in p and "權" in p for p in active_cells):
        sub_scores["格局"] += 10; process_logs["格局"].append("🥊 活躍區見天同化權，外柔內剛，談判手腕極佳 (+10分)")
    if any("天梁" in p and "科" in p for p in active_cells):
        sub_scores["格局"] += 10; process_logs["格局"].append("🛡️ 活躍區見天梁化科，逢凶化吉，易得長輩救援 (+10分)")

    # 🚶‍♂️ 4. 基礎行動星判定 (這個看整體氣場，維持 sf_text 即可)
    for star in ["天機", "太陰", "天同", "天梁", "巨門"]:
        if star in sf_text:
            brightness = get_star_brightness(star, sf_text)
            if brightness >= 1.1: 
                sub_scores["格局"] += 5
                process_logs["格局"].append(f"🚶‍♂️ 活躍區見 `{star}` (廟旺)，能量順暢 (+5分)")
            else:
                sub_scores["格局"] += 0
                process_logs["格局"].append(f"🚶‍♂️ 活躍區見 `{star}` (平陷)，能量平平 (+0分)")

    has_tan_opp = "貪狼" in sf_text
    has_huo_opp = "火星" in sf_text
    has_ling_opp = "鈴星" in sf_text
    has_lu_opp = "祿" in sf_text or "祿存" in sf_text
    has_kongjie_opp = "地空" in sf_text or "地劫" in sf_text
    
    # 🔺 紀錄是否觸發火貪空劫
    is_huotan_boom = has_tan_opp and (has_huo_opp or has_ling_opp) and has_kongjie_opp

    if has_tan_opp and (has_huo_opp or has_ling_opp):
        if has_kongjie_opp:
            sub_scores["格局"] -= 50
            process_logs["格局"].append("⚠️ 火貪空劫，曇花一現，當心社交圈的突發炎上 (-50分)")
        elif has_lu_opp:
            sub_scores["格局"] += 40
            process_logs["格局"].append("🔥 火鈴貪祿，人氣爆棚，自帶流量的超級發電機 (+40分)")
        else:
            sub_scores["格局"] += 15
            process_logs["格局"].append("⚡ 火鈴貪格，魅力四射，突如其來的社交好機遇 (+15分)")

    breaker_stars = {"擎羊": 15, "陀羅": 15, "地空": 20, "地劫": 20} 
    for star, pts in breaker_stars.items():
        if star in sf_text:
            # 🔺 空劫豁免權發動
            if (star == "地空" or star == "地劫") and is_huotan_boom:
                continue
            sub_scores["格局"] -= pts
            process_logs["格局"].append(f"⚠️ `{star}` 攪局，魅力受到干擾，人際表現打折扣 (-{pts}分)")
            
    if has_huo_opp and not has_tan_opp:
        sub_scores["格局"] -= 10
        process_logs["格局"].append("🔥 `火星` 攪局，情緒急躁，容易瞬間破壞人緣氣場 (-10分)")
    if has_ling_opp and not has_tan_opp:
        sub_scores["格局"] -= 10
        process_logs["格局"].append("🔔 `鈴星` 攪局，陰鬱不滿，讓人覺得難以親近與溝通 (-10分)")

    if "巨門" in sf_text and "忌" in sf_text:
        sub_scores["格局"] -= 20
        process_logs["格局"].append("💬 巨門化忌，口舌是非，無心之言導致人際誤解 (-20分)")

    # ==========================================
    # 模組 2：社交 (活躍度與人際內耗)
    # ==========================================
    peach_stars = ["紅鸞", "天喜", "天姚", "咸池", "沐浴", "貪狼"]
    peach_count = sum(social_text.count(s) for s in peach_stars)
    if peach_count > 0:
        sub_scores["社交"] += (peach_count * 5)
        process_logs["社交"].append(f"🌸 偵測到桃花/人緣星 x{peach_count} (+{peach_count*5}分)")

    for star in ["祿", "權", "科"]:
        count = social_text.count(star)
        if count > 0:
            sub_scores["社交"] += (count * 5)
            process_logs["社交"].append(f"📈 社交面四化 `{star}` x{count} (+{count*5}分)")
            
    ji_count = social_text.count("忌")
    if ji_count > 0:
        sub_scores["社交"] -= (ji_count * 10)
        process_logs["社交"].append(f"📉 社交面化忌 x{ji_count} (-{ji_count*10}分)")

    for p_name, p_text in [("遷移宮", qian), ("交友宮", jiao)]:
        if "馬" in p_text:
            if "陀" in p_text:
                sub_scores["社交"] -= 20
                process_logs["社交"].append(f"⚠️ `{p_name}` 陀羅遇天馬成「拐腳馬」 (-20分)")
            else:
                sub_scores["社交"] += 15
                process_logs["社交"].append(f"🐎 `{p_name}` 見天馬，鼓勵外出 (+15分)")

    isolating_stars = {"孤辰": 15, "寡宿": 15}
    for star, pts in isolating_stars.items():
        if star in social_text:
            sub_scores["社交"] -= pts
            process_logs["社交"].append(f"🏠 `{star}` 發威，傾向內耗或孤獨 (-{pts}分)")

    # ==========================================
    # 模組 3：貴人 (包含夾命宮與夾遷移宮)
    # ==========================================
    if "紫微" in qian:
        sub_scores["貴人"] += 20
        process_logs["貴人"].append("👑 遷移宮見紫微，遇強大貴人提攜 (+20分)")
    if "天府" in qian:
        sub_scores["貴人"] += 20
        process_logs["貴人"].append("🏰 遷移宮見天府，得厚實助力資源 (+20分)")
    if "天梁" in qian:
        process_logs["貴人"].append("👀 遷移宮見天梁，主逢災化吉，不予加分")

    nobility_stars = {"天魁": 10, "天鉞": 10, "左輔": 10, "右弼": 10}
    for star, pts in nobility_stars.items():
        count = social_text.count(star)
        if count > 0:
            sub_scores["貴人"] += (count * pts)
            process_logs["貴人"].append(f"🤝 活躍區見貴人 `{star}` x{count} (+{count*pts}分)")

    for p_name, p_text in [("命宮", ming), ("事業宮", guan), ("父母宮", fumu), ("交友宮", jiao)]:
        if "天梁" in p_text:
            sub_scores["貴人"] += 10
            process_logs["貴人"].append(f"🤝 `{p_name}` 見蔭星 `天梁` (+10分)")
        if "紫微" in p_text:
            sub_scores["貴人"] += 5
            process_logs["貴人"].append(f"🤝 `{p_name}` 見領導星 `紫微` (+5分)")

    # 🧱 夾宮貴人判定：夾命宮 (父母 + 兄弟)
    has_zuoyou_jia_ming = ("左輔" in fumu and "右弼" in xiong) or ("左輔" in xiong and "右弼" in fumu)
    has_kuiyue_jia_ming = ("天魁" in fumu and "天鉞" in xiong) or ("天魁" in xiong and "天鉞" in fumu)
    if has_zuoyou_jia_ming or has_kuiyue_jia_ming:
        sub_scores["貴人"] += 20
        process_logs["貴人"].append("🧱 左右/魁鉞夾命，貴人暗中護體 (+20分)")

    # 🧱 夾宮貴人判定：夾遷移宮 (交友 + 疾厄)
    has_zuoyou_jia_qian = ("左輔" in jiao and "右弼" in jie) or ("左輔" in jie and "右弼" in jiao)
    has_kuiyue_jia_qian = ("天魁" in jiao and "天鉞" in jie) or ("天魁" in jie and "天鉞" in jiao)
    if has_zuoyou_jia_qian or has_kuiyue_jia_qian:
        sub_scores["貴人"] += 20
        process_logs["貴人"].append("🧱 左右/魁鉞夾遷移，出外發展暗藏強大助力 (+20分)")

    # 🔺 最重要的這兩行回來了！
    total_score = base_score + sub_scores["格局"] + sub_scores["社交"] + sub_scores["貴人"]
    return max(0, min(200, total_score)), sub_scores, process_logs

def get_total_opportunity_index(charts_dict):
    if not charts_dict or len(charts_dict) < 4:
        return 0, {}, {}, {}
        
    scores = {}
    sub_scores_dict = {}
    logs = {}
    
    for mode in ["流年盤", "流月盤", "流日盤", "流時盤"]:
        s, sub_s, l = calculate_opportunity_score(charts_dict.get(mode, ""), mode)
        scores[mode] = s
        sub_scores_dict[mode] = sub_s
        logs[mode] = l
    
    total = (scores["流年盤"] * 0.1) + (scores["流月盤"] * 0.1) + (scores["流日盤"] * 0.4) + (scores["流時盤"] * 0.4)
    return round(total, 1), scores, sub_scores_dict, logs
# ==========================================
# 引擎區塊 3：本命盤基礎底蘊 (財運/機運)
# ==========================================
# 亮度權重映射 (廟: 1.2, 旺: 1.1, 地/利: 1.0, 平: 0.8, 陷: 0.5)
BRIGHTNESS_MAP = {"廟": 1.2, "旺": 1.1, "地": 1.0, "利": 1.0, "平": 0.8, "陷": 0.5}

def get_star_brightness(star_name, palace_text):
    """從宮位文字中提取該星曜的亮度"""
    # 正規表達式尋找：星名後緊跟亮度字元
    pattern = f"{star_name}([廟旺地利平陷])"
    match = re.search(pattern, palace_text)
    if match:
        brightness = match.group(1)
        return BRIGHTNESS_MAP.get(brightness, 1.0)
    return 1.0 # 若找不到則視為 1.0

def calculate_birth_wealth(html_content):
    if not html_content: return 50, ["無資料"]
    soup = BeautifulSoup(html_content, 'html.parser')
    cells = soup.find_all('td', width="25%")
    if len(cells) != 12: return 50, ["格式錯誤"]
    
    cell_texts = [cell.get_text() for cell in cells]
    clockwise_indices = [8, 6, 4, 0, 1, 2, 3, 5, 7, 11, 10, 9]
    
    # --- 最強雙重防護定位命宮 ---
    ming_pos = -1
    for i, idx in enumerate(clockwise_indices):
        cell_html = str(cells[idx]).replace(" ", "").upper()
        if "BACKGROUND-COLOR:#FFCC66" in cell_html or "BACKGROUND-COLOR:YELLOW" in cell_html:
            ming_pos = i; break
            
    if ming_pos == -1: 
        for i, idx in enumerate(clockwise_indices):
            if "命宮" in cell_texts[idx] or "命、身" in cell_texts[idx]:
                ming_pos = i; break
                
    if ming_pos == -1: return 50, ["找不到命宮"]
    # ---------------------------

    ming = cell_texts[clockwise_indices[ming_pos]]
    fu   = cell_texts[clockwise_indices[(ming_pos + 2) % 12]]  
    guan = cell_texts[clockwise_indices[(ming_pos + 4) % 12]]  
    qian = cell_texts[clockwise_indices[(ming_pos + 6) % 12]]  
    cai  = cell_texts[clockwise_indices[(ming_pos + 8) % 12]]  
    
    palaces_to_check = [(ming, True, "本命命宮"), (qian, True, "本命遷移"), (fu, True, "本命福德"), (cai, False, "本命財帛"), (guan, False, "本命事業")]
    score = 60
    process_log = ["**🔹 本命財運起算分: 60 分**"]

    # 🔥 全盤掃描：本命 12 宮專屬四化彩蛋 (底蘊基因)
    # ==========================================
    core_wealth_cells = [ming, fu, guan, qian, cai]
    
    for p_text in cell_texts:
        is_core = p_text in core_wealth_cells
        
        # 武曲化祿
        if "武曲" in p_text and "祿" in p_text:
            if is_core:
                score += 30; process_log.append("🌟 核心區見武曲化祿，實打實的無敵本命金庫 (+30分)")
            else:
                score += 15; process_log.append("🌟 命盤藏武曲化祿，具備隱藏暴富底蘊，流轉引爆即發財 (+15分)")
                
        # 破軍化祿
        if "破軍" in p_text and "祿" in p_text:
            if is_core:
                score += 25; process_log.append("🌪️ 核心區見破軍化祿，破繭而出，亂世抄底的暴利推手 (+25分)")
            else:
                score += 10; process_log.append("🌪️ 命盤藏破軍化祿，具備逆轉暴利的隱藏基因 (+10分)")
                
        # 天機化祿
        if "天機" in p_text and "祿" in p_text:
            if is_core:
                score += 20; process_log.append("🧠 核心區見天機化祿，智謀生財，靈活穿梭盤勢的波段神童 (+20分)")
            else:
                score += 10; process_log.append("🧠 命盤藏天機化祿，對數字跳動具備天生敏銳度 (+10分)")
                
        # 武曲化權
        if "武曲" in p_text and "權" in p_text:
            if is_core:
                score += 20; process_log.append("⚖️ 核心區見武曲化權，鐵血紀律，對資金擁有絕對掌控霸氣 (+20分)")
            else:
                score += 10; process_log.append("⚖️ 命盤藏武曲化權，天生自帶嚴謹的資金控管基因 (+10分)")
    # ==========================================
    
    for p_text, is_mqf, p_name in palaces_to_check:
        lu_count = len(re.findall(r'祿', p_text)); quan_count = len(re.findall(r'權', p_text)); ke_count = len(re.findall(r'科', p_text))
        if lu_count > 0: score += (lu_count * 10); process_log.append(f"✅ `{p_name}` 見祿星 x{lu_count} (+{lu_count*10}分)")
        if quan_count > 0 or ke_count > 0: pts = (quan_count + ke_count) * 5; score += pts; process_log.append(f"✅ `{p_name}` 見權/科 (+{pts}分)")

        has_tan = "貪狼" in p_text
        has_huo = "火星" in p_text
        has_ling = "鈴星" in p_text
        has_lu = "祿" in p_text or "祿存" in p_text
        has_kongjie = "地空" in p_text or "地劫" in p_text

        if has_tan and (has_huo or has_ling):
            if has_kongjie:
                score -= 50
                process_log.append(f"⚠️ `{p_name}` 火鈴貪逢空劫，體質易橫發橫破，投資需嚴守停損 (-50分)")
            elif has_lu:
                score += 40
                process_log.append(f"🔥 `{p_name}` 火/鈴貪逢祿引爆，天生自帶暴富基因，適合抓大波段 (+40分)")
            else:
                score += 15
                process_log.append(f"⚡ `{p_name}` 火/鈴貪強勢成格，具備強大爆發力底蘊 (+15分)")

        # 💰 本命專屬四化財運彩蛋
        if "武曲" in p_text and "祿" in p_text:
            score += 30; process_log.append(f"🌟 `{p_name}` 武曲化祿，財神歸位，實打實的無敵本命金庫 (+30分)")
        if "破軍" in p_text and "祿" in p_text:
            score += 25; process_log.append(f"🌪️ `{p_name}` 破軍化祿，破繭而出，亂世抄底的暴利推手 (+25分)")
        if "天機" in p_text and "祿" in p_text:
            score += 20; process_log.append(f"🧠 `{p_name}` 天機化祿，智謀生財，靈活穿梭盤勢的波段神童 (+20分)")
        if "武曲" in p_text and "權" in p_text:
            score += 20; process_log.append(f"⚖️ `{p_name}` 武曲化權，鐵血紀律，對資金擁有絕對的掌控霸氣 (+20分)")
        # --- 新增亮度邏輯：動態計算財星分數 ---
        for star in ["武曲", "太陰", "天府"]:
            if star in p_text:
                brightness = get_star_brightness(star, p_text)
                pts = 5 * brightness
                score += pts
                process_log.append(f"💰 `{p_name}` 財星 `{star}` (亮度: {brightness:.1f}) (+{pts:.1f}分)")
        
        if "貪狼" in p_text and any(s in p_text for s in ["紅鸞", "天喜", "咸池", "天姚", "沐浴"]): 
            score += 5; process_log.append(f"✅ `{p_name}` 貪狼逢桃花財 (+5分)")
        if "天梁" in p_text and "太陽" in p_text: 
            score += 5; process_log.append(f"✅ `{p_name}` 陽梁蔭星財 (+5分)")
        # ----------------------------------------
        
        ma_count = len(re.findall(r'馬', p_text))
        if ma_count > 0:
            score += (ma_count * 5); process_log.append(f"🐎 `{p_name}` 見天馬 (+{ma_count*5}分)")
            if lu_count > 0: score += 15; process_log.append(f"🔥 `{p_name}` 祿馬交馳爆發 (+15分)")
            if "陀" in p_text: score -= 20; process_log.append(f"⚠️ `{p_name}` 陀羅折足馬 (-20分)")
            
        has_kong_soft = "旬空" in p_text or "天空" in p_text
        has_kong_hard = "地空" in p_text
        has_jie_hard = "地劫" in p_text
        if has_kong_hard and has_jie_hard: score -= 100; process_log.append(f"❌ `{p_name}` 地空地劫同宮重傷 (-100分)")
        elif has_kong_hard or has_jie_hard: score -= 40; process_log.append(f"❌ `{p_name}` 逢空/劫星 (-40分)")
        elif has_kong_soft: score -= 5; process_log.append(f"❌ `{p_name}` 逢旬空/天空星 (-5分)")
                
        ji_count = len(re.findall(r'忌', p_text))
        if ji_count > 0:
            if any(f"{star}廟" in p_text or f"{star}旺" in p_text for star in ["武曲", "太陰", "太陽", "天機", "天同"]): process_log.append(f"🛡️ `{p_name}` 逢忌，但廟旺豁免")
            else: score -= (ji_count * 20); process_log.append(f"❌ `{p_name}` 逢忌煞 x{ji_count} (-{ji_count*20}分)")

    return max(0, min(200, score)), process_log

def calculate_birth_opportunity(html_content):
    base_score = 30 
    sub_scores = {"格局": 0, "社交": 0, "貴人": 0}; process_logs = {"格局": ["**✨ 機運起算分: 30 分**"], "社交": [], "貴人": []}
    if not html_content: return base_score, sub_scores, process_logs

    soup = BeautifulSoup(html_content, 'html.parser')
    cells = soup.find_all('td', width="25%")
    if len(cells) != 12: return base_score, sub_scores, process_logs
    
    cell_texts = [cell.get_text() for cell in cells]
    clockwise_indices = [8, 6, 4, 0, 1, 2, 3, 5, 7, 11, 10, 9]
    
    # --- 最強雙重防護定位命宮 ---
    ming_pos = -1
    for i, idx in enumerate(clockwise_indices):
        cell_html = str(cells[idx]).replace(" ", "").upper()
        if "BACKGROUND-COLOR:#FFCC66" in cell_html or "BACKGROUND-COLOR:YELLOW" in cell_html:
            ming_pos = i; break
            
    if ming_pos == -1: 
        for i, idx in enumerate(clockwise_indices):
            if "命宮" in cell_texts[idx] or "命、身" in cell_texts[idx]:
                ming_pos = i; break
                
    if ming_pos == -1: return base_score, sub_scores, process_logs
    # ---------------------------

    ming = cell_texts[clockwise_indices[ming_pos]]
    fumu = cell_texts[clockwise_indices[(ming_pos + 1) % 12]]
    guan = cell_texts[clockwise_indices[(ming_pos + 4) % 12]]
    jiao = cell_texts[clockwise_indices[(ming_pos + 5) % 12]]
    qian = cell_texts[clockwise_indices[(ming_pos + 6) % 12]]
    jie  = cell_texts[clockwise_indices[(ming_pos + 7) % 12]]  # 🔺 新增：疾厄宮 (夾遷移用)
    cai  = cell_texts[clockwise_indices[(ming_pos + 8) % 12]]
    xiong = cell_texts[clockwise_indices[(ming_pos + 11) % 12]]
    
    sf_text = ming + cai + guan + qian; social_text = ming + fumu + guan + jiao + qian 
    
    # 模組 1：格局與魅力榜
    # 🏆 1. 跨宮位核心大格局 (需多星連動，僅限三方四正)
    if all(s in sf_text for s in ["天機", "太陰", "天同", "天梁"]):
        sub_scores["格局"] += 25
        process_logs["格局"].append("✨ 核心三方觸發「機月同梁」，團隊協作效率大增 (+25分)")

    # ==========================================
    # 🕊️ 全盤掃描：12 宮底蘊基因 (5個純社交核心校準版)
    # ==========================================
    # 縮緊防線：僅鎖定 5 大公眾社交與貴人核心宮位
    core_opp_cells = [ming, guan, qian, fumu, jiao]
    
    for p_text in cell_texts:
        is_core = p_text in core_opp_cells
        
        # --- A. 雙星同宮底蘊基因 ---
        if "太陽" in p_text and "太陰" in p_text:
            if is_core: sub_scores["格局"] += 28; process_logs["格局"].append("☀️🌙 核心區見日月同宮，磁場和諧吸引好機遇 (+28分)")
            else: sub_scores["格局"] += 14; process_logs["格局"].append("☀️🌙 命盤藏日月基因，具備隱藏的調和魅力 (+14分)")
            
        if "天機" in p_text and "太陰" in p_text:
            if is_core: sub_scores["格局"] += 25; process_logs["格局"].append("🧠 核心區見機陰同宮，心思細膩社交進退得宜 (+25分)")
            else: sub_scores["格局"] += 12; process_logs["格局"].append("🧠 命盤藏機陰基因，具備隱藏的細膩人際手腕 (+12分)")
            
        if "廉貞" in p_text and "貪狼" in p_text:
            if is_core: sub_scores["格局"] += 18; process_logs["格局"].append("🏅 核心區見廉貪同宮，風情萬種擄獲異性目光 (+18分)")
            else: sub_scores["格局"] += 9; process_logs["格局"].append("🏅 命盤藏廉貪基因，具備隱藏的強大發電機魅力 (+9分)")
            
        if "紫微" in p_text and "貪狼" in p_text:
            if is_core: sub_scores["格局"] += 14; process_logs["格局"].append("🏅 核心區見紫貪同宮，高貴得體魅力氣場四溢 (+14分)")
            else: sub_scores["格局"] += 7; process_logs["格局"].append("🏅 命盤藏紫貪基因，具備隱藏的社交名流氣質 (+7分)")
            
        if "天機" in p_text and "巨門" in p_text:
            if is_core: sub_scores["格局"] += 10; process_logs["格局"].append("💬 核心區見機巨同宮，話題豐富適合知性交流 (+10分)")
            else: sub_scores["格局"] += 5; process_logs["格局"].append("💬 命盤藏機巨基因，具備隱藏的知性對話能力 (+5分)")

        # --- B. 四化專屬底蘊基因 ---
        if "天同" in p_text and "祿" in p_text:
            if is_core: sub_scores["格局"] += 30; process_logs["格局"].append("🥇 核心區見天同化祿，自帶療癒氣場 (+30分)")
            else: sub_scores["格局"] += 15; process_logs["格局"].append("🥇 命盤藏天同化祿，具備隱藏的無害親和基因 (+15分)")
            
        if "紫微" in p_text and "科" in p_text:
            if is_core: sub_scores["格局"] += 30; process_logs["格局"].append("👑 核心區見紫微化科，帝星閃耀威望極高 (+30分)")
            else: sub_scores["格局"] += 15; process_logs["格局"].append("👑 命盤藏紫微化科，自帶隱藏版威望基因 (+15分)")
            
        if "巨門" in p_text and "祿" in p_text:
            if is_core: sub_scores["格局"] += 25; process_logs["格局"].append("💬 核心區見巨門化祿，開口見金收服人心 (+25分)")
            else: sub_scores["格局"] += 12; process_logs["格局"].append("💬 命盤藏巨門化祿，具備潛在的超級說服力 (+12分)")
            
        if "太陰" in p_text and "科" in p_text:
            if is_core: sub_scores["格局"] += 25; process_logs["格局"].append("🌕 核心區見太陰化科，優雅內斂高冷氣質 (+25分)")
            else: sub_scores["格局"] += 12; process_logs["格局"].append("🌕 命盤藏太陰化科，具備隱藏的高質感氣質 (+12分)")
            
        if "太陽" in p_text and "科" in p_text:
            if is_core: sub_scores["格局"] += 25; process_logs["格局"].append("☀️ 核心區見太陽化科，行走暖陽談吐優雅 (+25分)")
            else: sub_scores["格局"] += 12; process_logs["格局"].append("☀️ 命盤藏太陽化科，具備隱藏的名門儒雅基因 (+12分)")
            
        if "貪狼" in p_text and "祿" in p_text:
            if is_core: sub_scores["格局"] += 22; process_logs["格局"].append("🏅 核心區見貪狼化祿，情商天花板幽默魅力 (+22分)")
            else: sub_scores["格局"] += 11; process_logs["格局"].append("🏅 命盤藏貪狼化祿，具備隱藏的公關王者基因 (+11分)")
            
        if "太陽" in p_text and "權" in p_text:
            if is_core: sub_scores["格局"] += 20; process_logs["格局"].append("🏅 核心區見太陽化權，霸氣能幹讓人敬畏 (+20分)")
            else: sub_scores["格局"] += 10; process_logs["格局"].append("🏅 命盤藏太陽化權，具備隱藏的領導大氣基因 (+10分)")
            
        if "天同" in p_text and "權" in p_text:
            if is_core: sub_scores["格局"] += 20; process_logs["格局"].append("🥊 核心區見天同化權，外柔內剛柔性手腕 (+20分)")
            else: sub_scores["格局"] += 10; process_logs["格局"].append("🥊 命盤藏天同化權，具備隱藏的高段柔性手腕 (+10分)")
            
        if "天梁" in p_text and "科" in p_text:
            if is_core: sub_scores["格局"] += 20; process_logs["格局"].append("🛡️ 核心區見天梁化科，逢凶化吉長輩庇蔭 (+20分)")
            else: sub_scores["格局"] += 10; process_logs["格局"].append("🛡️ 命盤藏天梁化科，自帶隱形的逢凶化吉基因 (+10分)")
    # ==========================================

    # 3. 基礎行動星判定 (以核心活躍區 sf_text 為主)
    for star in ["天機", "太陰", "天同", "天梁", "巨門"]:
        if star in sf_text:
            brightness = get_star_brightness(star, sf_text)
            if brightness >= 1.1: 
                sub_scores["格局"] += 5
                process_logs["格局"].append(f"🚶‍♂️ 三方見 `{star}` (廟旺)，能量爆發 (+5分)")
            else:
                sub_scores["格局"] += 0
                process_logs["格局"].append(f"🚶‍♂️ 三方見 `{star}` (平陷)，能量平平 (+0分)")

    # 4. 火鈴貪爆發魅力彩蛋 (聚焦三方四正)
        # 4. 火鈴貪爆發魅力彩蛋 (這段維持你的原樣)
    has_tan_opp = "貪狼" in sf_text
    has_huo_opp = "火星" in sf_text
    has_ling_opp = "鈴星" in sf_text
    has_lu_opp = "祿" in sf_text or "祿存" in sf_text
    has_kongjie_opp = "地空" in sf_text or "地劫" in sf_text
    
    # 🔺 新增一個標籤，紀錄是否已經觸發了核彈級扣分
    is_huotan_boom = has_tan_opp and (has_huo_opp or has_ling_opp) and has_kongjie_opp

    if has_tan_opp and (has_huo_opp or has_ling_opp):
        if has_kongjie_opp:
            sub_scores["格局"] -= 50
            process_logs["格局"].append("⚠️ 火貪空劫，曇花一現，當心社交圈的突發炎上 (-50分)")
        elif has_lu_opp:
            sub_scores["格局"] += 40
            process_logs["格局"].append("🔥 火鈴貪祿，人氣爆棚，自帶流量的超級發電機 (+40分)")
        else:
            sub_scores["格局"] += 15
            process_logs["格局"].append("⚡ 火鈴貪格，魅力四射，突如其來的社交好機遇 (+15分)")

    # 🛡️ 5. 社交魅力防護網
    breaker_stars = {"擎羊": 15, "陀羅": 15, "地空": 20, "地劫": 20} 
    for star, pts in breaker_stars.items():
        if star in sf_text:
            # 🔺 終極修復：如果已經被火貪空劫扣過 50 分了，地空與地劫直接豁免，跳過不扣！
            if (star == "地空" or star == "地劫") and is_huotan_boom:
                continue
                
            sub_scores["格局"] -= pts
            process_logs["格局"].append(f"⚠️ `{star}` 攪局，魅力受到干擾，人際表現打折扣 (-{pts}分)")
            
    # 火星與鈴星的特殊判定：如果「沒有」跟貪狼組隊，才視為破壞星扣分
    if has_huo_opp and not has_tan_opp:
        sub_scores["格局"] -= 10
        process_logs["格局"].append("🔥 `火星` 攪局，情緒急躁，容易瞬間破壞人緣氣場 (-10分)")
    if has_ling_opp and not has_tan_opp:
        sub_scores["格局"] -= 10
        process_logs["格局"].append("🔔 `鈴星` 攪局，陰鬱不滿，讓人覺得難以親近與溝通 (-10分)")

    if "巨門" in sf_text and "忌" in sf_text:
        sub_scores["格局"] -= 20
        process_logs["格局"].append("💬 巨門化忌，口舌是非，無心之言導致人際誤解 (-20分)")
        
    # ----------------------------------------

    # 模組 2：社交 (活躍度與人際內耗)
    peach_count = sum(social_text.count(s) for s in ["紅鸞", "天喜", "天姚", "咸池", "沐浴", "貪狼"])
    if peach_count > 0: 
        sub_scores["社交"] += (peach_count * 5)
        process_logs["社交"].append(f"🌸 桃花/人緣星 x{peach_count} (+{peach_count*5}分)")
        
    for star in ["祿", "權", "科"]:
        c = social_text.count(star)
        if c > 0: 
            sub_scores["社交"] += (c * 5)
            process_logs["社交"].append(f"📈 社交面四化 `{star}` x{c} (+{c*5}分)")
            
    ji_count = social_text.count("忌")
    if ji_count > 0: 
        sub_scores["社交"] -= (ji_count * 10)
        process_logs["社交"].append(f"📉 社交面化忌 x{ji_count} (-{ji_count*10}分)")
        
    for p_name, p_text in [("本命遷移", qian), ("本命交友", jiao)]:
        if "馬" in p_text:
            if "陀" in p_text: 
                sub_scores["社交"] -= 20
                process_logs["社交"].append(f"⚠️ `{p_name}` 拐腳馬，出外社交易有波折 (-20分)")
            else: 
                sub_scores["社交"] += 15
                process_logs["社交"].append(f"🐎 `{p_name}` 見天馬，適合向外拓展人脈 (+15分)")
                
    isolating_stars = {"孤辰": 15, "寡宿": 15}
    for star, pts in isolating_stars.items():
        if star in social_text: 
            sub_scores["社交"] -= pts
            process_logs["社交"].append(f"🏠 `{star}` 發威，性格傾向內收或孤獨 (-{pts}分)")
    
    # 模組 3：貴人
    if "紫微" in qian: sub_scores["貴人"] += 20; process_logs["貴人"].append("👑 本命遷移見紫微 (+20分)")
    if "天府" in qian: sub_scores["貴人"] += 20; process_logs["貴人"].append("🏰 本命遷移見天府 (+20分)")
    for star, pts in {"天魁": 10, "天鉞": 10, "左輔": 10, "右弼": 10}.items():
        c = social_text.count(star)
        if c > 0: sub_scores["貴人"] += (c * pts); process_logs["貴人"].append(f"🤝 活躍區見 `{star}` x{c} (+{c*pts}分)")
    for p_name, p_text in [("本命", ming), ("本命事業", guan), ("本命父母", fumu), ("本命交友", jiao)]:
        if "天梁" in p_text: sub_scores["貴人"] += 10; process_logs["貴人"].append(f"🤝 `{p_name}` 見蔭星天梁 (+10分)")
        if "紫微" in p_text: sub_scores["貴人"] += 5; process_logs["貴人"].append(f"🤝 `{p_name}` 見領導星紫微 (+5分)")
    if ("左輔" in fumu and "右弼" in xiong) or ("左輔" in xiong and "右弼" in fumu) or ("天魁" in fumu and "天鉞" in xiong) or ("天魁" in xiong and "天鉞" in fumu):
        sub_scores["貴人"] += 20; process_logs["貴人"].append("🧱 左右/魁鉞夾命 (+20分)")
        
    # 🧱 夾宮貴人判定：夾遷移宮 (交友 + 疾厄)
    has_zuoyou_jia_qian = ("左輔" in jiao and "右弼" in jie) or ("左輔" in jie and "右弼" in jiao)
    has_kuiyue_jia_qian = ("天魁" in jiao and "天鉞" in jie) or ("天魁" in jie and "天鉞" in jiao)
    if has_zuoyou_jia_qian or has_kuiyue_jia_qian:
        sub_scores["貴人"] += 20
        process_logs["貴人"].append("🧱 左右/魁鉞夾遷移，出外發展暗藏強大助力 (+20分)")

    return max(0, base_score + sub_scores["格局"] + sub_scores["社交"] + sub_scores["貴人"]), sub_scores, process_logs
    
# ==========================================
# 3. 畫面顯示區 (儀表板渲染)
# ==========================================
st.markdown("---")
st.markdown("### 🪐 基礎體質 (初始能力值)")

if st.session_state.birth_chart:
    st.markdown("#### 🧬 基礎底蘊")
    b_wealth_score, b_wealth_logs = calculate_birth_wealth(st.session_state.birth_chart)
    b_opp_score, b_opp_subs, b_opp_logs = calculate_birth_opportunity(st.session_state.birth_chart)
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.metric("💰 財運基礎分", f"{b_wealth_score} 分")
        with st.expander("📝 展開查看本命財運算分明細"):
            for log in b_wealth_logs:
                st.caption(log)
    with b_col2:
        st.metric("🕊️ 社交機運基礎分", f"{b_opp_score} 分")
        with st.expander("📝 展開查看本命機運算分明細"):
            st.write(f"**格局:** `{b_opp_subs['格局']:+d}` | **社交:** `{b_opp_subs['社交']:+d}` | **貴人:** `{b_opp_subs['貴人']:+d}`")
            for cat in ["格局", "社交", "貴人"]:
                for log in b_opp_logs[cat]:
                    st.caption(log)
    
     #隱藏網站抓取到的本命盤，收合於擴展區塊內
    #with st.expander("🗺️ 點此展開查看原始本命盤表格"):
        #components.html(st.session_state.birth_chart, height=550, scrolling=True)
else:
    st.info("請先點擊左側「1️⃣ 開始排本命盤」。")

st.markdown("---")

# 渲染好運指數 (原有)
if hasattr(st.session_state, 'transit_charts') and len(st.session_state.transit_charts) == 4:
    total_luck, individual_scores, process_logs = get_total_luck_index(st.session_state.transit_charts)
    
    st.markdown("### 📊 快樂體操：財運 ")
    
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

    st.markdown("#### 🎯 各維度獨立評分")
    
    # 使用 HTML Flexbox 強制四個分數並排，徹底解決手機斷行問題
    luck_metrics_html = f"""
    <div style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; text-align: left; background: rgba(128,128,128,0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px; overflow-x: auto;">
        <div style="flex: 1; min-width: 70px; border-right: 1px solid rgba(128,128,128,0.2); padding-right: 5px;">
            <div style="font-size: 0.8rem; color: gray;">流年(15%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{individual_scores['流年盤']}</div>
            <div style="font-size: 0.75rem; color: gray;">↑ 貢獻: {round(individual_scores['流年盤']*0.15, 1)}</div>
        </div>
        <div style="flex: 1; min-width: 70px; border-right: 1px solid rgba(128,128,128,0.2); padding-left: 10px; padding-right: 5px;">
            <div style="font-size: 0.8rem; color: gray;">流月(15%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{individual_scores['流月盤']}</div>
            <div style="font-size: 0.75rem; color: gray;">↑ 貢獻: {round(individual_scores['流月盤']*0.15, 1)}</div>
        </div>
        <div style="flex: 1; min-width: 70px; border-right: 1px solid rgba(128,128,128,0.2); padding-left: 10px; padding-right: 5px;">
            <div style="font-size: 0.8rem; color: gray;">流日(30%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{individual_scores['流日盤']}</div>
            <div style="font-size: 0.75rem; color: gray;">↑ 貢獻: {round(individual_scores['流日盤']*0.30, 1)}</div>
        </div>
        <div style="flex: 1; min-width: 70px; padding-left: 10px;">
            <div style="font-size: 0.8rem; color: gray;">流時(40%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{individual_scores['流時盤']}</div>
            <div style="font-size: 0.75rem; color: gray;">↑ 貢獻: {round(individual_scores['流時盤']*0.40, 1)}</div>
        </div>
    </div>
    """
    st.markdown(luck_metrics_html, unsafe_allow_html=True)

    with st.expander("📝 點此展開查看各盤詳細計算過程 (好運指數)"):
        log_c1, log_c2 = st.columns(2)
        log_c3, log_c4 = st.columns(2)
        log_cols = [("流年盤", log_c1), ("流月盤", log_c2), ("流日盤", log_c3), ("流時盤", log_c4)]
        
        for mode, col in log_cols:
            with col:
                st.markdown(f"**【{mode}】算分明細**")
                for line in process_logs[mode]:
                    st.write(line)
                st.markdown("---")

    # ----------------------------------------
    # 渲染全新機運指數 (三大模組整合)
    # ----------------------------------------
    opp_total, opp_scores, opp_subs, opp_logs = get_total_opportunity_index(st.session_state.transit_charts)
    
    st.markdown("---")
    st.markdown("### 🕊️ 快樂體操：機運 ")
    
    c_o1, c_o2, c_o3 = st.columns([1, 2, 1])
    with c_o2:
        opp_color = "purple" if opp_total >= 100 else "blue" if opp_total >= 70 else "gray"
        st.markdown(
            f"""
            <div style="background-color:{opp_color}; padding:20px; border-radius:10px; text-align:center;">
                <h1 style="color:white; font-size:48px; margin:0;">{opp_total} 分</h1>
                <h4 style="color:white; margin:0;">(機運加權總分)</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if opp_total >= 90:
            st.success("🌟 機運爆棚！格局強大且貴人環繞，強力建議出門行動、拓展人脈！")
        elif opp_total >= 60:
            st.info("🚶‍♂️ 能量不錯。適合參加聚會或出外散心，會有正向交流。")
        else:
            st.warning("🏠 能量偏向內收。外在阻礙較多，適合在家沉澱、閱讀充電。")

    # === 新增：機運指數各維度獨立評分 ===
    st.markdown("#### 🎯 機運各維度獨立評分")
    
    # 計算各盤的「主打項目」
    main_features = {}
    for mode in ["流年盤", "流月盤", "流日盤", "流時盤"]:
        subs = opp_subs[mode]
        best_cat = max(subs, key=subs.get)
        best_val = subs[best_cat]
        if best_val > 0:
            main_features[mode] = f" 主打：{best_cat} (+{best_val})"
        else:
            main_features[mode] = "🏠 能量內收"
    
    # 使用 HTML Flexbox 強制四個分數並排，並帶入主打項目取代貢獻分
    opp_metrics_html = f"""
    <div style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; text-align: left; background: rgba(128,128,128,0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px; overflow-x: auto;">
        <div style="flex: 1; min-width: 70px; border-right: 1px solid rgba(128,128,128,0.2); padding-right: 5px;">
            <div style="font-size: 0.8rem; color: gray;">流年(10%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{opp_scores['流年盤']}</div>
            <div style="font-size: 0.75rem; color: gray; font-weight: 500;">{main_features['流年盤']}</div>
        </div>
        <div style="flex: 1; min-width: 70px; border-right: 1px solid rgba(128,128,128,0.2); padding-left: 10px; padding-right: 5px;">
            <div style="font-size: 0.8rem; color: gray;">流月(10%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{opp_scores['流月盤']}</div>
            <div style="font-size: 0.75rem; color: gray; font-weight: 500;">{main_features['流月盤']}</div>
        </div>
        <div style="flex: 1; min-width: 70px; border-right: 1px solid rgba(128,128,128,0.2); padding-left: 10px; padding-right: 5px;">
            <div style="font-size: 0.8rem; color: gray;">流日(40%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{opp_scores['流日盤']}</div>
            <div style="font-size: 0.75rem; color: gray; font-weight: 500;">{main_features['流日盤']}</div>
        </div>
        <div style="flex: 1; min-width: 70px; padding-left: 10px;">
            <div style="font-size: 0.8rem; color: gray;">流時(40%)</div>
            <div style="font-size: 1.6rem; font-weight: 600;">{opp_scores['流時盤']}</div>
            <div style="font-size: 0.75rem; color: gray; font-weight: 500;">{main_features['流時盤']}</div>
        </div>
    </div>
    """
    st.markdown(opp_metrics_html, unsafe_allow_html=True)

    with st.expander("📝 點此展開查看【機運指數】三大項目詳細算分明細"):
        for mode in ["流年盤", "流月盤", "流日盤", "流時盤"]:
            st.markdown(f"#### 🧭 【{mode}】結算總分: {opp_scores[mode]} 分 (基準分: 30)")
            
            col_p, col_s, col_n = st.columns(3)
            
            with col_p:
                st.markdown(f"**🔷 核心格局 ({opp_subs[mode]['格局']:+d}分)**")
                for log in opp_logs[mode]["格局"]:
                    st.caption(log)
                    
            with col_s:
                st.markdown(f"**🔶 社交活躍 ({opp_subs[mode]['社交']:+d}分)**")
                for log in opp_logs[mode]["社交"]:
                    st.caption(log)
                    
            with col_n:
                st.markdown(f"**👑 貴人運勢 ({opp_subs[mode]['貴人']:+d}分)**")
                for log in opp_logs[mode]["貴人"]:
                    st.caption(log)
                    
            st.markdown("---")

# 顯示四個流轉盤
#if hasattr(st.session_state, 'transit_charts') and st.session_state.transit_charts:
#    st.markdown("---")
#    with st.expander("🗺️ 點此展開查看流年/流月/流日/流時真實命盤表格"):
#        col1, col2 = st.columns(2)
#        col3, col4 = st.columns(2)
        
#        grid_mapping = [
#            ("流年盤", col1),
#            ("流月盤", col2),
#            ("流日盤", col3),
#            ("流時盤", col4)
#        ]
        
#        for title, col in grid_mapping:
#            with col:
#                st.markdown(f"<h4 style='text-align: center;'>{title}</h4>", unsafe_allow_html=True)
#                if title in st.session_state.transit_charts:
#                    components.html(st.session_state.transit_charts[title], height=500, scrolling=True)
#                else:
#                    st.warning(f"無法取得{title}資料")
                    
elif st.session_state.step1_done:
    st.info("本命盤已就緒！請設定上方流轉日期後，點擊「🚀 一鍵取得四重流轉盤」。")
