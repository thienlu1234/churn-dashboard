import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(layout="wide")

st.title("📊 Dashboard Phân Tích Khách Hàng")

file = st.file_uploader("Upload file Excel", type=["xlsx"])

@st.cache_data
def load_data(file):
    return pd.read_excel(file)

if file is not None:
    df = load_data(file)
    df = df.fillna(0)

    # =========================
    # 🔥 FIX CỘT (QUAN TRỌNG)
    # =========================
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.upper()

    # Debug (có thể comment lại sau)
    st.sidebar.write("📌 Columns:")
    st.sidebar.write(df.columns)

    # =========================
    # 🔥 AUTO DETECT CỘT
    # =========================
    col_manager = next((c for c in df.columns if "CANBO" in c), None)
    col_phong = next((c for c in df.columns if "PHONG" in c), None)
    col_tnt = next((c for c in df.columns if "TNT" in c), None)
    col_hdv = next((c for c in df.columns if "HDV" in c), None)
    col_sp = next((c for c in df.columns if "SPD" in c or "SPDV" in c), None)

    # =========================
    # 🔥 TẠO TOTAL VALUE
    # =========================
    if col_tnt and col_hdv:
        df["TOTAL_VALUE"] = df[col_tnt] + df[col_hdv]
    else:
        st.error("❌ Không tìm thấy cột TNT hoặc HDV")
        st.stop()

    # =========================
    # MENU
    # =========================
    menu = st.sidebar.radio("Chọn phân tích", [
        "1. Top khách hàng",
        "2. VIP / thường",
        "3. Theo cán bộ",
        "4. Theo phòng ban",
        "5. Khách ngủ đông",
        "6. Biểu đồ",
        "7. Clustering",
        "8. Scoring",
        "9. Churn"
    ])

    # =========================
    # 1. TOP KHÁCH
    # =========================
    if menu.startswith("1"):
        top = df.nlargest(20, "TOTAL_VALUE")
        st.subheader("🏆 Top khách hàng")
        st.dataframe(top)

    # =========================
    # 2. VIP
    # =========================
    elif menu.startswith("2"):
        threshold = df["TOTAL_VALUE"].quantile(0.8)
        df["SEGMENT"] = df["TOTAL_VALUE"].apply(
            lambda x: "VIP" if x >= threshold else "Thường"
        )

        st.subheader("🎯 Phân nhóm khách hàng")
        st.bar_chart(df["SEGMENT"].value_counts())

    # =========================
    # 3. THEO CÁN BỘ
    # =========================
    elif menu.startswith("3"):
        if col_manager:
            result = df.groupby(col_manager)["TOTAL_VALUE"].sum().reset_index()

            fig = px.bar(
                result.sort_values(by="TOTAL_VALUE", ascending=False),
                x=col_manager,
                y="TOTAL_VALUE"
            )
            st.plotly_chart(fig)
        else:
            st.error("❌ Không tìm thấy cột cán bộ")

    # =========================
    # 4. THEO PHÒNG BAN
    # =========================
    elif menu.startswith("4"):
        if col_phong:
            result = df.groupby(col_phong)["TOTAL_VALUE"].sum().reset_index()

            fig = px.pie(result, names=col_phong, values="TOTAL_VALUE")
            st.plotly_chart(fig)
        else:
            st.error("❌ Không tìm thấy cột phòng ban")

    # =========================
    # 5. KHÁCH NGỦ ĐÔNG
    # =========================
    elif menu.startswith("5"):
        if col_sp:
            dormant = df[df[col_sp] <= 1]
            st.subheader(f"😴 Khách ngủ đông: {len(dormant)}")
            st.dataframe(dormant.head(100))
        else:
            st.error("❌ Không tìm thấy cột sản phẩm")

    # =========================
    # 6. BIỂU ĐỒ
    # =========================
    elif menu.startswith("6"):
        fig1 = px.histogram(df, x=col_hdv, title="Tiền gửi")
        fig2 = px.histogram(df, x=col_tnt, title="Doanh thu")

        st.plotly_chart(fig1)
        st.plotly_chart(fig2)

    # =========================
    # 7. CLUSTERING
    # =========================
    elif menu.startswith("7"):
        if col_sp:
            X = df[[col_tnt, col_hdv, col_sp]]

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            kmeans = KMeans(n_clusters=3, n_init=10)
            df["CLUSTER"] = kmeans.fit_predict(X_scaled)

            fig = px.scatter(df, x=col_tnt, y=col_hdv, color="CLUSTER")
            st.plotly_chart(fig)
        else:
            st.error("❌ Không đủ cột để clustering")

    # =========================
    # 8. SCORING
    # =========================
    elif menu.startswith("8"):
        if col_sp:
            df["SCORE"] = (
                df[col_tnt]*0.5 +
                df[col_hdv]*0.3 +
                df[col_sp]*0.2
            )

            st.dataframe(df.nlargest(50, "SCORE"))
        else:
            st.error("❌ Không đủ cột để scoring")

    # =========================
    # 9. CHURN
    # =========================
    elif menu.startswith("9"):
        if col_sp:
            df["CHURN"] = df[col_sp].apply(lambda x: 1 if x <= 1 else 0)
            churn = df[df["CHURN"] == 1]

            st.subheader(f"⚠️ Khách có nguy cơ rời: {len(churn)}")
            st.dataframe(churn.head(100))
        else:
            st.error("❌ Không đủ dữ liệu churn")

else:
    st.info("Upload file để bắt đầu")
