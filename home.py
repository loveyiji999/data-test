import streamlit as st

# 設定主頁面標題與配置
st.set_page_config(page_title="分項計畫工具 主介面", layout="wide")

# 主標題
st.title("分項計畫工具 主介面!")

# 功能選單說明
st.markdown(
    """
    歡迎使用「分項計畫工具」。請從左側導覽列選擇您要使用的功能子頁面：

    - **搜尋工具**：上傳 Excel 並以關鍵字搜尋，支援多欄位、分頁展示與結果下載。
    - **日曆視圖**：上傳 Excel 並將指定日期欄位事件顯示於月曆，懸停事件即可查看詳細資訊。
    """
)

# 可以在此加入常見問題、聯絡方式等
with st.expander("📖 使用說明 / FAQ"):
    st.write(
        """
        **Q1. 如何切換功能？**
        - 請點擊左側選單中的「搜尋工具」或「日曆視圖」。

        **Q2. 為何需要欄位對應？**
        - 因為 Excel 中的欄位名稱可能不同，需手動對應以正確識別日期與顯示內容。

        **Q3. 如何回報問題？**
        - 歡迎聯絡開發團隊或在 GitHub Issue 提出需求。  
        """
    )

# 底部版權等資訊
st.markdown("---")
st.caption("© 2025 皆豪資訊中心")
