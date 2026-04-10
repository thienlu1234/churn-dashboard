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

    # Chuẩn hóa tên cột
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Hiện tên cột thật để debug
    with st.sidebar.expander("Xem tên cột thực tế"):
        st.write(df.columns.tolist())

    # Tự tìm cột gần đúng
    col_tnt = next((c for c in df.columns if "TNT" in c), None)
    col_hdv = next((c for c in df.columns if "HDV" in c), None)
    col_manager = next((c for c in df.columns if "CANBO" in c or "CBQL" in c), None)
    col_phong = next((c for c in df.columns if "PHONG" in c), None)
    col_sp = next((c for c in df.columns if "TOTAL_SPDV" in c or "SPDV" in c or "SPD" in c), None)

    # Tạo TOTAL_VALUE an toàn
    if col_tnt is not None and col_hdv is not None:
        df["TOTAL_VALUE"] = pd.to_numeric(df[col_tnt], errors="coerce").fillna(0) + pd.to_numeric(df[col_hdv], errors="coerce").fillna(0)
    else:
        df["TOTAL_VALUE"] = 0

    menu = st.sidebar.radio("Chọn phân tích", [
        "1. Top khách hàng giá trị",
        "2. Phân nhóm VIP",
        "3. Theo cán bộ quản lý",
        "4. Theo phòng ban",
        "5. Khách ngủ đông",
        "6. Biểu đồ tiền & doanh thu",
        "7. Clustering AI",
        "8. Customer Scoring",
        "9. Dự đoán rời bỏ"
    ])

    # 1
    if menu.startswith("1"):
        st.subheader("Top khách hàng giá trị cao")
        top = df.nlargest(20, "TOTAL_VALUE")
        st.dataframe(top, use_container_width=True)

    # 2
    elif menu.startswith("2"):
        st.subheader("Phân nhóm VIP / thường")
        if "TOTAL_VALUE" not in df.columns:
            st.error("Không tạo được cột TOTAL_VALUE")
        else:
            threshold = df["TOTAL_VALUE"].quantile(0.8)
            df["SEGMENT"] = df["TOTAL_VALUE"].apply(lambda x: "VIP" if x >= threshold else "Thường")
            summary = df["SEGMENT"].value_counts().reset_index()
            summary.columns = ["SEGMENT", "COUNT"]
            fig = px.bar(summary, x="SEGMENT", y="COUNT", text="COUNT")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[[c for c in df.columns if c in ["TOTAL_VALUE", "SEGMENT"]]].head(50), use_container_width=True)

    # 3
    elif menu.startswith("3"):
        st.subheader("Phân tích theo cán bộ quản lý")
        if col_manager is None:
            st.error("Không tìm thấy cột cán bộ quản lý")
        else:
            result = df.groupby(col_manager, dropna=False)["TOTAL_VALUE"].sum().reset_index()
            result = result.sort_values("TOTAL_VALUE", ascending=False)
            fig = px.bar(result, x=col_manager, y="TOTAL_VALUE", text="TOTAL_VALUE")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(result, use_container_width=True)

    # 4
    elif menu.startswith("4"):
        st.subheader("Phân tích theo phòng ban")
        if col_phong is None:
            st.error("Không tìm thấy cột phòng ban")
        else:
            result = df.groupby(col_phong, dropna=False)["TOTAL_VALUE"].sum().reset_index()
            result = result.sort_values("TOTAL_VALUE", ascending=False)
            fig = px.bar(result, x=col_phong, y="TOTAL_VALUE", text="TOTAL_VALUE")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(result, use_container_width=True)

    # 5
    elif menu.startswith("5"):
        st.subheader("Phát hiện khách ngủ đông")
        if col_sp is None:
            st.error("Không tìm thấy cột số sản phẩm/giao dịch")
        else:
            dormant = df[pd.to_numeric(df[col_sp], errors="coerce").fillna(0) <= 1]
            st.write(f"Số khách ngủ đông: {len(dormant):,}")
            st.dataframe(dormant.head(200), use_container_width=True)

    # 6
    elif menu.startswith("6"):
        st.subheader("Biểu đồ tiền gửi & doanh thu")
        c1, c2 = st.columns(2)
        with c1:
            if col_hdv is not None:
                fig1 = px.histogram(df, x=col_hdv, nbins=50, title="Phân bố HDV")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("Không tìm thấy cột HDV")
        with c2:
            if col_tnt is not None:
                fig2 = px.histogram(df, x=col_tnt, nbins=50, title="Phân bố TNT")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Không tìm thấy cột TNT")

    # 7
    elif menu.startswith("7"):
        st.subheader("Cluster khách hàng")
        if col_tnt is None or col_hdv is None or col_sp is None:
            st.error("Thiếu cột để clustering")
        else:
            sample_df = df[[col_tnt, col_hdv, col_sp]].copy()
            sample_df = sample_df.apply(pd.to_numeric, errors="coerce").fillna(0)

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(sample_df)

            kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
            df["CLUSTER"] = kmeans.fit_predict(X_scaled)

            plot_df = df[[col_tnt, col_hdv, "CLUSTER"]].copy()
            plot_df[col_tnt] = pd.to_numeric(plot_df[col_tnt], errors="coerce").fillna(0)
            plot_df[col_hdv] = pd.to_numeric(plot_df[col_hdv], errors="coerce").fillna(0)

            fig = px.scatter(plot_df.sample(min(5000, len(plot_df)), random_state=42),
                             x=col_tnt, y=col_hdv, color="CLUSTER")
            st.plotly_chart(fig, use_container_width=True)

    # 8
    elif menu.startswith("8"):
        st.subheader("Tính điểm khách hàng")
        if col_tnt is None or col_hdv is None or col_sp is None:
            st.error("Thiếu cột để scoring")
        else:
            df["SCORE"] = (
                pd.to_numeric(df[col_tnt], errors="coerce").fillna(0) * 0.5
                + pd.to_numeric(df[col_hdv], errors="coerce").fillna(0) * 0.3
                + pd.to_numeric(df[col_sp], errors="coerce").fillna(0) * 0.2
            )
            st.dataframe(df.nlargest(100, "SCORE"), use_container_width=True)

    # 9
    elif menu.startswith("9"):
        st.subheader("Dự đoán khách rời bỏ")
        if col_sp is None:
            st.error("Thiếu cột để dự đoán rời bỏ")
        else:
            sp_series = pd.to_numeric(df[col_sp], errors="coerce").fillna(0)
            df["CHURN_RISK"] = sp_series.apply(lambda x: "Cao" if x <= 1 else ("Trung bình" if x <= 2 else "Thấp"))
            summary = df["CHURN_RISK"].value_counts().reset_index()
            summary.columns = ["CHURN_RISK", "COUNT"]
            fig = px.pie(summary, names="CHURN_RISK", values="COUNT")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[df["CHURN_RISK"] == "Cao"].head(200), use_container_width=True)

else:
    st.info("Upload file để bắt đầu.")
