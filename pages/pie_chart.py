from pathlib import Path

# 修改後的 pie_chart.py 程式內容：支援多欄位合併統計
pie_chart_code = """
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='圓餅圖統計', layout='wide')
st.title('📊 圓餅圖統計分析')

# 上傳 Excel
uploaded_file = st.file_uploader("上傳 Excel 檔案", type=["xlsx", "xls"])
if not uploaded_file:
    st.info("請上傳包含分類欄位的 Excel 檔案。")
    st.stop()

# 選擇工作表與標題列
xls = pd.ExcelFile(uploaded_file)
sheet = st.selectbox("選擇工作表", xls.sheet_names)
header_row = st.number_input("標題列 (row)", min_value=1, value=1)
df = pd.read_excel(uploaded_file, sheet_name=sheet, skiprows=header_row - 1, dtype=str)

if df.empty:
    st.warning("讀取失敗或無資料")
    st.stop()

# 多欄位複選統計
target_cols = st.multiselect("選擇要統計的欄位（可複選）", df.columns)

if not target_cols:
    st.warning("請選擇至少一個欄位以生成圓餅圖。")
    st.stop()

# 抽出所有非空值組合進統一列表
values = []
for _, row in df.iterrows():
    for col in target_cols:
        val = row.get(col, "")
        if pd.notna(val) and str(val).strip():
            values.append(str(val).strip())

# 統計
counts = pd.Series(values).value_counts().reset_index()
counts.columns = ['項目', '數量']

# 繪製圓餅圖
fig = px.pie(counts, names='項目', values='數量', title="選取欄位合併後的分類統計")
st.plotly_chart(fig, use_container_width=True)

# 展示資料表
with st.expander("🔍 查看統計資料表"):
    st.dataframe(counts, use_container_width=True)
"""

# 儲存成 pages/pie_chart.py
output_path = Path("pages/pie_chart.py")
output_path.parent.mkdir(exist_ok=True, parents=True)
output_path.write_text(pie_chart_code.strip(), encoding="utf-8")
output_path.name
