import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(layout="wide")

st.title("📊 Dashboard Phân Tích Khách Hàng")

uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx"])

@st.cache_data
def load_data(file):
    return pd.read_excel(file)

if uploaded_file is not None:
    df = load_data(uploaded_file).copy()
    df = df.fillna(0)

    # =========================
    # FIX CỘT
    # =========================
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Debug xem cột
    with st.sidebar.expander("📌 Xem tên cột"):
        st.write(df.columns.tolist())

    # =========================
    # AUTO DETECT CỘT
    # =========================
    col_tnt = next((c for c in df.columns if "TNT" in c), None)
    col_hdv = next((c for c in df.columns if "HDV" in c), None)
    col_manager = next((c for c in df.columns if "CANBO" in c or "CBQL" in c), None)
    col_phong = next((c for c in df.columns if "PHONG" in c), None)
    col_sp = next((c for c in df.columns if "SPD" in c or "SPDV" in c), None)

    # =========================
    # TẠO TOTAL_VALUE AN TOÀN
    # =========================
    if col_tnt and col_hdv:
        df["TOTAL_VALUE"] = (
            pd.to_numeric(df[col_tnt], errors="coerce").fillna(0) +
            pd.to_numeric(df[col_hdv], errors="coerce").fillna(0)
        )
    else:
        st.error("❌ Không tìm thấy TNT hoặc HDV → kiểm tra file")
        st.stop()

    # =========================
    # MENU
    # =========================
    menu = st.sidebar.radio("Chọn phân tích", [
        "1. Top khách hàng",
        "2. Phân nhóm VIP",
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
        st.subheader("🏆 Top khách hàng")
        top = df.nlargest(20, "TOTAL_VALUE")
        st.dataframe(top, use_container_width=True)

    # =========================
    # 2. VIP
    # =========================
    elif menu.startswith("2"):
        st.subheader("🎯 Phân nhóm VIP")

        df["TOTAL_VALUE"] = pd.to_numeric(df["TOTAL_VALUE"], errors="coerce").fillna(0)

        if df["TOTAL_VALUE"].sum() == 0:
            st.error("❌ TOTAL_VALUE = 0 → file sai cột TNT/HDV")
        else:
            threshold = df["TOTAL_VALUE"].quantile(0.8)

            df["SEGMENT"] = df["TOTAL_VALUE"].apply(
                lambda x: "VIP" if x >= threshold else "Thường"
            )

            summary = df["SEGMENT"].value_counts().reset_index()
            summary.columns = ["SEGMENT", "COUNT"]

            fig = px.bar(summary, x="SEGMENT", y="COUNT", text="COUNT")
            st.plotly_chart(fig, use_container_width=True)

    # =========================
    # 3. CÁN BỘ
    # =========================
    elif menu.startswith("3"):
        st.subheader("👨‍💼 Theo cán bộ")

        if col_manager:
            result = df.groupby(col_manager)["TOTAL_VALUE"].sum().reset_index()
            result = result.sort_values(by="TOTAL_VALUE", ascending=False)

            fig = px.bar(result, x=col_manager, y="TOTAL_VALUE")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("❌ Không tìm thấy cột cán bộ")

    # =========================
    # 4. PHÒNG BAN
    # =========================
    elif menu.startswith("4"):
        st.subheader("🏢 Theo phòng ban")

        if col_phong:
            result = df.groupby(col_phong)["TOTAL_VALUE"].sum().reset_index()

            fig = px.pie(result, names=col_phong, values="TOTAL_VALUE")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("❌ Không tìm thấy cột phòng")

    # =========================
    # 5. NGỦ ĐÔNG
    # =========================
    elif menu.startswith("5"):
        st.subheader("😴 Khách ngủ đông")

        if col_sp:
            dormant = df[pd.to_numeric(df[col_sp], errors="coerce").fillna(0) <= 1]
            st.write(f"Số lượng: {len(dormant)}")
            st.dataframe(dormant.head(100))
        else:
            st.error("❌ Không tìm thấy cột SPDV")

    # =========================
    # 6. BIỂU ĐỒ
    # =========================
    elif menu.startswith("6"):
        st.subheader("📊 Biểu đồ")

        if col_hdv:
            fig1 = px.histogram(df, x=col_hdv)
            st.plotly_chart(fig1)

        if col_tnt:
            fig2 = px.histogram(df, x=col_tnt)
            st.plotly_chart(fig2)

    # =========================
    # 7. CLUSTER
    # =========================
    elif menu.startswith("7"):
        st.subheader("🤖 Clustering")

        if col_sp:
            X = df[[col_tnt, col_hdv, col_sp]].apply(pd.to_numeric, errors="coerce").fillna(0)

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            kmeans = KMeans(n_clusters=3, n_init=10)
            df["CLUSTER"] = kmeans.fit_predict(X_scaled)

            fig = px.scatter(df, x=col_tnt, y=col_hdv, color="CLUSTER")
            st.plotly_chart(fig)
        else:
            st.error("❌ Không đủ dữ liệu")

    # =========================
    # 8. SCORING
    # =========================
    elif menu.startswith("8"):
        st.subheader("📊 Scoring")

        if col_sp:
            df["SCORE"] = (
                pd.to_numeric(df[col_tnt], errors="coerce").fillna(0)*0.5 +
                pd.to_numeric(df[col_hdv], errors="coerce").fillna(0)*0.3 +
                pd.to_numeric(df[col_sp], errors="coerce").fillna(0)*0.2
            )

            st.dataframe(df.nlargest(50, "SCORE"))
        else:
            st.error("❌ Không đủ dữ liệu")

    # =========================
    # 9. CHURN
    # =========================
    elif menu.startswith("9"):
        st.subheader("⚠️ Churn")

        if col_sp:
            sp = pd.to_numeric(df[col_sp], errors="coerce").fillna(0)

            df["CHURN"] = sp.apply(lambda x: "Cao" if x <= 1 else "Thấp")

            st.dataframe(df[df["CHURN"] == "Cao"].head(100))
        else:
            st.error("❌ Không đủ dữ liệu")

else:
    st.info("Upload file để bắt đầu")
