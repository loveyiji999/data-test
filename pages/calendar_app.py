import streamlit as st
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- Helpers ---
def parse_roc_date(roc_str):
    """
    把 ROC 格式日期 'YYY/MM/DD' 轉成 datetime.date
    例如 '110/05/15' -> datetime.date(2021, 5, 15)
    """
    try:
        parts = roc_str.split('/')
        if len(parts) == 3:
            year = int(parts[0]) + 1911
            month = int(parts[1])
            day = int(parts[2])
            return datetime.date(year, month, day)
    except:
        return None
    return None

@st.cache_data
def load_data(file, sheet_name, header_row):
    """讀取 Excel，將所有欄位轉為字串"""
    return pd.read_excel(
        file,
        sheet_name=sheet_name,
        skiprows=header_row-1,
        dtype=str
    )

# --- Streamlit UI ---
st.set_page_config(page_title='日曆視圖', layout='wide')
st.title('日曆視圖')

# 上傳與載入資料
df = None
uploaded = st.file_uploader('上傳 Excel 檔案', type=['xlsx','xls'])
if uploaded:
    xls = pd.ExcelFile(uploaded)
    sheet = st.selectbox('選擇工作表', xls.sheet_names)
    header = st.number_input('標題列 (row)', min_value=1, value=1)
    df = load_data(uploaded, sheet, header)
    if df.empty:
        st.error('讀取後無資料，請檢查標題列設定。')
        st.stop()
else:
    st.info('請先上傳 Excel 檔案。')
    st.stop()

# 欄位對應表單
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
with st.form('cfg'):
    date_col = st.selectbox('日期欄位 (事件定位)', df.columns)
    title_col = st.selectbox('標題欄位 (事件名稱)', df.columns)
    detail_cols = st.multiselect(
        '詳情欄位 (懸停顯示)',
        [c for c in df.columns if c not in (date_col, title_col)]
    )
    if st.form_submit_button('生成日曆'):
        st.session_state.submitted = True

if not st.session_state.submitted:
    st.info('請設定欄位後按「生成日曆」。')
    st.stop()

# 建立事件資料字典: 日期 -> HTML 片段
events = {}
for _, row in df.iterrows():
    date = parse_roc_date(row.get(date_col, ''))
    if not date:
        continue
    title = str(row.get(title_col, ''))
    tip_lines = [f"{col}: {row[col]}" for col in detail_cols]
    tip_html = '<br>'.join(tip_lines)
    evt_html = (
        f"<div class='event'>{title}"
        f"<div class='tip'>{tip_html}</div>"
        f"</div>"
    )
    events.setdefault(date, []).append(evt_html)

# 事件統計: 各年與各月
events_by_year = {}
events_by_month = {}
for date, lst in events.items():
    events_by_year[date.year] = events_by_year.get(date.year, 0) + len(lst)
    events_by_month.setdefault((date.year, date.month), 0)
    events_by_month[(date.year, date.month)] += len(lst)

# 年度、月份選擇與統計
today = datetime.date.today()
col_y, col_yc = st.columns([3,1])
with col_y:
    year = st.number_input('年度', value=today.year, step=1, key='year')
with col_yc:
    st.write(f"{events_by_year.get(year, 0)} 筆")

if 'month' not in st.session_state:
    st.session_state.month = today.month
col_m1, col_m2, col_m3 = st.columns([1,5,1])
with col_m1:
    if st.button('←', key='month_dec') and st.session_state.month > 1:
        st.session_state.month -= 1
with col_m2:
    options = [f"{m}月 ({events_by_month.get((year, m),0)} 筆)" for m in range(1,13)]
    sel = st.selectbox('月份', options, index=st.session_state.month-1, key='month_sel')
    st.session_state.month = options.index(sel) + 1
with col_m3:
    if st.button('→', key='month_inc') and st.session_state.month < 12:
        st.session_state.month += 1
month = st.session_state.month

days = (datetime.date(year + (month // 12), (month % 12) + 1, 1) - datetime.timedelta(days=1)).day
first_weekday = datetime.date(year, month, 1).weekday()  # Mon=0

# Generate both table and list views
calendar_html = f"""
<style>
  .calendar-wrapper {{ overflow-x:auto; }}

  .calendar {{
    border-collapse: collapse;
    width: 100%;
    min-width: 600px;
  }}

  .calendar th,
  .calendar td {{
    border: 1px solid #ccc;
    width: 14%;
    height: 90px;
    padding: 4px;
    position: relative;
    overflow: visible;
  }}

  .calendar th {{
    background: #f0f0f0;
  }}

  .date {{
    position: absolute;
    top: 2px;
    right: 4px;
    font-size: 0.8em;
    color: #666;
  }}

  .event {{
    background: #3174ad;
    color: #fff;
    margin: 2px 0;
    padding: 1px 3px;
    border-radius: 3px;
    font-size: 0.75em;
    cursor: default;
    display: inline-block;
    position: relative;
  }}

  .event .tip {{
    visibility: hidden;
    opacity: 0;
    position: fixed;  /* ✅ 改為浮動定位 */
    background: rgba(0, 0, 0, 0.85);
    color: #fff;
    padding: 6px;
    border-radius: 4px;
    white-space: pre-wrap;
    font-size: 0.75em;
    transition: opacity 0.2s;
    z-index: 9999;
    max-width: 300px;
    pointer-events: none;
  }}

  .event:hover .tip {{
    visibility: visible;
    opacity: 1;
  }}

  .calendar-list {{
    display: none;
  }}

  @media (max-width:768px) {{
    .calendar-wrapper {{
      display: none;
    }}

    .calendar-list {{
      display: block;
    }}

    .day-card {{
      margin-bottom: 12px;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      position: relative;
      overflow: visible;  /* ✅ 解除截斷 */
    }}

    .day-card .date-header {{
      font-weight: bold;
      margin-bottom: 4px;
    }}

    .day-card ul {{
      margin: 0;
      padding-left: 16px;
    }}

    .day-card li {{
      margin-bottom: 2px;
      font-size: 0.85em;
    }}
  }}
</style>

<script>
document.querySelectorAll('.event').forEach(evt => {{
  const tip = evt.querySelector('.tip');
  if (!tip) return;
  evt.addEventListener('mousemove', e => {{
    tip.style.top = (e.clientY + 10) + 'px';
    tip.style.left = (e.clientX + 10) + 'px';
  }});
}});
</script>
"""
# Table View
table_html = ["<div class='calendar-wrapper'><table class='calendar'>",
              "<tr><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Sun</th></tr>"]

day=1
for week in range(6):
    row = '<tr>'
    for wd in range(7):
        if week==0 and wd<first_weekday:
            cell=''
        elif day>days:
            cell=''
        else:
            d = datetime.date(year, month, day)
            evs = events.get(d, [])
            cell = f"<div class='date'>{day}</div>" + ''.join(evs)
            day += 1
        row += f"<td>{cell}</td>"
    row += '</tr>'
    table_html.append(row)
    if day>days: break

table_html.append('</table></div>')

# List View with Tooltip support
# 在窄螢幕下使用清單模式，並保留.tooltip
from html import escape

# 生成清單視圖 HTML
day_list_html = ['<div class="calendar-list">']
for d in range(1, days+1):
    date_obj = datetime.date(year, month, d)
    items = events.get(date_obj, [])
    if not items:
        continue
    day_list_html.append('<div class="day-card">')
    day_list_html.append(f'<div class="date-header">{d}日</div>')
    day_list_html.append('<ul>')
    for evt in items:
        # evt 已包含<div class='event'>以及內部<div class='tip'>，可直接使用
        day_list_html.append(f'<li>{evt}</li>')
    day_list_html.append('</ul></div>')

# 結束清單容器
day_list_html.append('</div>')

# 合併 HTML 片段並呈現
full_html_list = [calendar_html] + table_html + day_list_html
full_html = ''.join(full_html_list)

# 在 List View 上加入點擊切換 Tooltip 的 JS
toggle_script = '''
<script>
// 點擊事件切換詳細提示
const eventsList = document.querySelectorAll('.calendar-list .event');
eventsList.forEach(el => {
  el.addEventListener('click', e => {
    e.stopPropagation();
    const tip = el.querySelector('.tip');
    if (!tip) return;
    if (tip.style.visibility === 'visible') {
      tip.style.visibility = 'hidden';
      tip.style.opacity = '0';
    } else {
      tip.style.visibility = 'visible';
      tip.style.opacity = '1';
    }
  });
});
</script>
'''
full_html += toggle_script

# ✅ 正確的嵌入方式
components.html(full_html, height=650, scrolling=True)