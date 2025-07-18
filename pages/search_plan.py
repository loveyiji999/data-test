import streamlit as st
import pandas as pd
import math
from io import BytesIO
import re

# -------------------------------------
# 1. 快取資料
# -------------------------------------
@st.cache_data(show_spinner=False)
def load_data(uploaded_file, sheet_name, header_row):
    try:
        df = pd.read_excel(
            uploaded_file,
            sheet_name=sheet_name,
            skiprows=header_row - 1,
            dtype=str
        )
    except Exception as e:
        st.error(f"讀取 Excel 檔案時發生錯誤：{e}")
        return pd.DataFrame()
    return df

# -------------------------------------
# 2. 輸出 Excel 的輔助函式
# -------------------------------------
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="搜尋結果")
    return output.getvalue()

# -------------------------------------
# 3. 頁面設定
# -------------------------------------
st.set_page_config(page_title="分項計畫搜尋工具", layout="wide")
st.title("分項計畫搜尋工具")

# -------------------------------------
# 4. 分頁與搜尋狀態初始化
# -------------------------------------
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1
if 'search_clicked' not in st.session_state:
    st.session_state.search_clicked = False

# -------------------------------------
# 5. 上傳與載入資料
# -------------------------------------
uploaded_file = st.file_uploader("上傳 Excel 檔案", type=["xlsx", "xls"])
if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_name = st.selectbox("選擇工作表", xls.sheet_names)
    header_row = st.number_input("標題列 (row)", min_value=1, value=8)
    df = load_data(uploaded_file, sheet_name, header_row)

    if not df.empty:
        cols = df.columns.tolist()
        search_cols = st.multiselect("選擇要搜尋的欄位（可多選）", cols, default=cols[:1])
        keyword = st.text_input("搜尋關鍵字")
        return_cols = st.multiselect("選擇要回傳的欄位", cols, default=cols[:3])
        page_size = st.number_input("每頁顯示筆數", min_value=1, value=20)

        # 搜尋按鈕：觸發搜尋
        if st.button("搜尋"):
            st.session_state.search_clicked = True
            st.session_state.page_number = 1

        # 若已點過搜尋，則執行搜尋和分頁顯示
        if st.session_state.search_clicked:
            if not search_cols:
                st.warning("請至少選擇一個搜尋欄位")
            elif not keyword:
                st.warning("請先輸入搜尋關鍵字")
            else:
                with st.spinner("搜尋中…"):
                    try:
                        mask = (
                            df[search_cols]
                            .apply(lambda col: col.str.contains(keyword, case=False, na=False))
                            .any(axis=1)
                        )
                        result = df.loc[mask, return_cols]
                    except Exception as e:
                        st.error(f"搜尋過程中發生錯誤：{e}")
                        result = pd.DataFrame()

                if result.empty:
                    st.error("未找到符合的項目，請更換關鍵字或欄位。")
                else:
                    total_pages = math.ceil(len(result) / page_size)
                    st.success(f"共找到 {len(result)} 筆結果，分 {total_pages} 頁顯示")

                    # 關鍵字高亮
                    def highlight(text):
                        return re.sub(f"(?i)({re.escape(keyword)})", r"<mark>\1</mark>", str(text))

                    highlighted = result.astype(str).applymap(highlight)

                    # 分頁按鈕
                    col1, _, col3 = st.columns([1, 6, 1])
                    with col1:
                        if st.button("← 上一頁") and st.session_state.page_number > 1:
                            st.session_state.page_number -= 1
                    with col3:
                        if st.button("下一頁 →") and st.session_state.page_number < total_pages:
                            st.session_state.page_number += 1

                    # 計算並顯示當前頁面資料
                    start = (st.session_state.page_number - 1) * page_size
                    end = start + page_size
                    page_data = highlighted.iloc[start:end]
                    st.markdown(page_data.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # 下載按鈕
                    excel_bytes = to_excel_bytes(result)
                    st.download_button(
                        label="下載結果為 Excel", data=excel_bytes,
                        file_name="搜尋結果.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    csv = result.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="下載結果為 CSV", data=csv,
                        file_name="搜尋結果.csv", mime="text/csv"
                    )
    else:
        st.info("請確認上傳的檔案及設定的標題列是否正確。")
else:
    st.info("請先上傳 Excel 檔案。")
