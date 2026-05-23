import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# =========================
# 工具函式
# =========================
def extract_chart_table(soup):
    """
    自動找出最像命盤的 table
    """
    best_table = None
    max_td = 0

    for table in soup.find_all("table"):
        td_count = len(table.find_all("td"))

        if td_count > max_td:
            max_td = td_count
            best_table = table

    return best_table


def beautify_table(table):
    """
    美化命盤 HTML
    """
    if not table:
        return None

    # 美化中央區塊
    for td in table.find_all('td'):
        if td.get('colspan') == '2' and td.get('rowspan') == '2':
            td['style'] = '''
                background-color: #ffffff !important;
                color: #000000 !important;
                padding: 15px;
            '''

            for font in td.find_all('font'):
                if font.has_attr('color'):
                    del font['color']

    table_html = str(table).replace(
        '<table',
        '<table border="1" style="width:100%; text-align:center; border-collapse: collapse; border-color: #777777; background-color: #ffffff; color: #000000;"'
    )

    return table_html


# =========================
# Streamlit 基本設定
# =========================
st.set_page_config(
    page_title="紫微命盤查詢系統",
    page_icon="🔮",
    layout="wide"
)

st.title("🔮 紫微命盤抓取系統")
st.write("資料來源：windada 算命網")

now = datetime.datetime.now()

# =========================
# 左右輸入區
# =========================
col_left, col_right = st.columns(2)

hours_map = {
    "子時 (23:00 - 01:00)": "0",
    "丑時 (01:00 - 03:00)": "2",
    "寅時 (03:00 - 05:00)": "4",
    "卯時 (05:00 - 07:00)": "6",
    "辰時 (07:00 - 09:00)": "8",
    "巳時 (09:00 - 11:00)": "10",
    "午時 (11:00 - 13:00)": "12",
    "未時 (13:00 - 15:00)": "14",
    "申時 (15:00 - 17:00)": "16",
    "酉時 (17:00 - 19:00)": "18",
    "戌時 (19:00 - 21:00)": "20",
    "亥時 (21:00 - 23:00)": "22"
}

# =========================
# 本命資料
# =========================
with col_left:

    st.markdown("### 👶 本命出生資料")

    with st.container(border=True):

        c1, c2, c3 = st.columns(3)

        with c1:
            year = st.number_input(
                "出生年",
                min_value=1900,
                max_value=2100,
                value=1992
            )

        with c2:
            month = st.number_input(
                "出生月",
                min_value=1,
                max_value=12,
                value=6
            )

        with c3:
            day = st.number_input(
                "出生日",
                min_value=1,
                max_value=31,
                value=18
            )

        c4, c5 = st.columns(2)

        with c4:
            hour_label = st.selectbox(
                "出生時辰",
                list(hours_map.keys()),
                index=8
            )

        with c5:
            gender_label = st.radio(
                "性別",
                ["男", "女"],
                horizontal=True
            )

# =========================
# 流盤資料
# =========================
with col_right:

    st.markdown("### 🗓️ 流盤查詢")

    with st.container(border=True):

        tc1, tc2, tc3 = st.columns(3)

        with tc1:
            t_year = st.number_input(
                "欲查年份",
                min_value=1900,
                max_value=2100,
                value=now.year
            )

        with tc2:
            t_month = st.number_input(
                "欲查月份",
                min_value=1,
                max_value=12,
                value=now.month
            )

        with tc3:
            t_day = st.number_input(
                "欲查日期",
                min_value=1,
                max_value=31,
                value=now.day
            )

        tc4, tc5 = st.columns(2)

        with tc4:
            t_hour_label = st.selectbox(
                "欲查時辰",
                list(hours_map.keys()),
                key="t_hour_select"
            )

        with tc5:
            transit_type = st.radio(
                "查詢模式",
                ["本命盤 (不看流年)", "流年", "流月", "流日", "流時"],
                index=4
            )

st.markdown("---")

# =========================
# 開始排盤
# =========================
if st.button("開始排盤 🚀", use_container_width=True):

    hour_val = hours_map[hour_label]
    t_hour_val = hours_map[t_hour_label]

    gender_val = "1" if gender_label == "男" else "0"

    natal_table = None
    transit_table = None

    with st.spinner("🤖 正在抓取命盤..."):

        try:

            session = requests.Session()

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://fate.windada.com/"
            }

            url = "https://fate.windada.com/cgi-bin/fate"

            # =========================================
            # 第一次 request：本命盤
            # =========================================
            first_page = session.get(url, headers=headers)

            first_page.encoding = 'utf-8'

            soup = BeautifulSoup(first_page.text, 'html.parser')

            form = soup.find('form')

            if not form:
                st.error("找不到輸入表單")
                st.stop()

            payload = {}

            # input
            for input_tag in form.find_all('input'):

                name = input_tag.get('name')

                if name and input_tag.get('type') not in ['submit', 'reset']:

                    payload[name] = input_tag.get('value', '')

            # select
            for select_tag in form.find_all('select'):

                name = select_tag.get('name')

                if name:

                    opts = select_tag.find_all('option')

                    if opts:
                        payload[name] = opts[0].get('value', opts[0].text)

            # 注入出生資料
            for key in payload.keys():

                k_low = key.lower()

                if "year" in k_low or key == "y":
                    payload[key] = str(year)

                elif "month" in k_low or key == "m":
                    payload[key] = str(month)

                elif "day" in k_low or key == "d":
                    payload[key] = str(day)

                elif "hour" in k_low or key == "h" or "time" in k_low:
                    payload[key] = hour_val

                elif "sex" in k_low or "gen" in k_low:
                    payload[key] = gender_val

            action_url = form.get('action')

            submit_url = urljoin(url, action_url) if action_url else url

            method = form.get('method', 'get').lower()

            # 送出本命盤 request
            if method == 'post':

                res = session.post(
                    submit_url,
                    data=payload,
                    headers=headers
                )

            else:

                res = session.get(
                    submit_url,
                    params=payload,
                    headers=headers
                )

            res.encoding = 'utf-8'

            res_soup = BeautifulSoup(res.text, 'html.parser')

            # 保存本命盤
            natal_table = extract_chart_table(res_soup)

            # =========================================
            # 第二次 request：流盤
            # =========================================
            if transit_type != "本命盤 (不看流年)":

                st.toast("🔄 正在計算流盤...", icon="⏳")

                transit_form = res_soup.find('form')

                if transit_form:

                    t_payload = {}

                    # 保留隱藏欄位
                    for input_tag in transit_form.find_all('input'):

                        name = input_tag.get('name')

                        if name and input_tag.get('type') not in [
                            'submit',
                            'reset',
                            'button'
                        ]:

                            t_payload[name] = input_tag.get('value', '')

                    # 注入流盤時間
                    for sel in transit_form.find_all('select'):

                        name = sel.get('name')

                        if not name:
                            continue

                        opts = [
                            o.get('value', o.text)
                            for o in sel.find_all('option')
                        ]

                        try:

                            # 年
                            if any(
                                int(o) > 1900
                                for o in opts
                                if o.isdigit()
                            ):

                                t_payload[name] = str(t_year)

                            # 月
                            elif '12' in opts and len(opts) <= 15:

                                t_payload[name] = str(t_month)

                            # 日
                            elif '31' in opts and len(opts) <= 35:

                                t_payload[name] = str(t_day)

                            # 時
                            elif '23' in opts and len(opts) <= 25:

                                t_payload[name] = t_hour_val

                            else:

                                selected = sel.find(
                                    'option',
                                    selected=True
                                )

                                if selected:
                                    t_payload[name] = selected.get(
                                        'value',
                                        selected.text
                                    )

                        except:
                            pass

                    # 點擊按鈕
                    found_button = False

                    for btn in transit_form.find_all(['input', 'button']):

                        btn_value = btn.get('value', '')

                        if transit_type in btn_value:

                            t_payload[btn.get('name')] = btn_value

                            found_button = True
                            break

                    if not found_button:
                        st.warning("找不到流盤按鈕")

                    t_action = transit_form.get('action')

                    t_submit_url = (
                        urljoin(submit_url, t_action)
                        if t_action else submit_url
                    )

                    t_method = transit_form.get(
                        'method',
                        'get'
                    ).lower()

                    # 送出流盤 request
                    if t_method == 'post':

                        res2 = session.post(
                            t_submit_url,
                            data=t_payload,
                            headers=headers
                        )

                    else:

                        res2 = session.get(
                            t_submit_url,
                            params=t_payload,
                            headers=headers
                        )

                    res2.encoding = 'utf-8'

                    transit_soup = BeautifulSoup(
                        res2.text,
                        'html.parser'
                    )

                    # 保存流盤
                    transit_table = extract_chart_table(transit_soup)

            # =========================================
            # 顯示結果
            # =========================================
            st.success("🎉 命盤抓取成功！")

            col1, col2 = st.columns(2)

            # 本命盤
            with col1:

                st.subheader("👶 本命盤")

                if natal_table:

                    natal_html = beautify_table(natal_table)

                    st.markdown(
                        natal_html,
                        unsafe_allow_html=True
                    )

                else:
                    st.warning("抓不到本命盤")

            # 流盤
            with col2:

                st.subheader(f"🗓️ {transit_type}")

                if transit_table:

                    transit_html = beautify_table(transit_table)

                    st.markdown(
                        transit_html,
                        unsafe_allow_html=True
                    )

                else:

                    if transit_type == "本命盤 (不看流年)":
                        st.info("未選擇流盤")
                    else:
                        st.warning("抓不到流盤")

        except Exception as e:

            st.error(f"發生錯誤：{e}")
