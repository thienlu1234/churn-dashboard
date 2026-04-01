import streamlit as st
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

st.title("📊 Customer Churn Dashboard")
st.write("Upload file Excel để phân tích churn và gửi email cho quản lý")

uploaded_file = st.file_uploader("Chọn file Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    required_cols = [
        "customer_id",
        "customer_name",
        "manager_name",
        "manager_email",
        "revenue_week_prev",
        "revenue_week_curr",
        "login_week_prev",
        "login_week_curr"
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Thiếu cột: {missing_cols}")
    else:
        df["login_drop_pct"] = (
            (df["login_week_prev"] - df["login_week_curr"])
            / df["login_week_prev"]
        ) * 100

        df["login_drop_pct"] = df["login_drop_pct"].replace([float("inf"), -float("inf")], 0)
        df["login_drop_pct"] = df["login_drop_pct"].fillna(0)

        df["revenue_drop_pct"] = (
            (df["revenue_week_prev"] - df["revenue_week_curr"])
            / df["revenue_week_prev"]
        ) * 100

        df["revenue_drop_pct"] = df["revenue_drop_pct"].replace([float("inf"), -float("inf")], 0)
        df["revenue_drop_pct"] = df["revenue_drop_pct"].fillna(0)

        def classify(row):
            if row["login_week_prev"] > 0 and row["login_week_curr"] == 0:
                return "High"
            if row["login_drop_pct"] >= 50:
                return "High"
            elif row["login_drop_pct"] >= 30:
                return "Medium"
            else:
                return "Low"

        df["risk_level"] = df.apply(classify, axis=1)

        risk_order_map = {"High": 0, "Medium": 1, "Low": 2}
        df["risk_order"] = df["risk_level"].map(risk_order_map)

        manager_list = ["All"] + sorted(df["manager_name"].dropna().unique().tolist())
        selected_manager = st.selectbox("Chọn manager", manager_list)

        filtered_df = df.copy()

        if selected_manager != "All":
            filtered_df = filtered_df[filtered_df["manager_name"] == selected_manager]

        risk_list = ["All", "High", "Medium", "Low"]
        selected_risk = st.selectbox("Chọn risk level", risk_list)

        if selected_risk != "All":
            filtered_df = filtered_df[filtered_df["risk_level"] == selected_risk]

        filtered_df = filtered_df.sort_values(
            by=["risk_order", "login_drop_pct"],
            ascending=[True, False]
        )

        total_customers = len(filtered_df)
        high_count = (filtered_df["risk_level"] == "High").sum()
        medium_count = (filtered_df["risk_level"] == "Medium").sum()
        low_count = (filtered_df["risk_level"] == "Low").sum()
        churn_rate = ((filtered_df["risk_level"] == "High").mean() * 100) if len(filtered_df) > 0 else 0
        revenue_at_risk = filtered_df.loc[
            filtered_df["risk_level"].isin(["High", "Medium"]),
            "revenue_week_prev"
        ].sum()

        st.subheader("Tổng quan")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", total_customers)
        col2.metric("High Risk", high_count)
        col3.metric("Medium Risk", medium_count)
        col4.metric("Low Risk", low_count)
        col5.metric("Churn Rate", f"{churn_rate:.1f}%")

        st.metric("Revenue At Risk", f"{revenue_at_risk:,.0f}")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("Risk Distribution")
            fig = px.pie(filtered_df, names="risk_level", title="Risk Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            st.subheader("Top manager có nhiều khách rủi ro")
            manager_risk = (
                filtered_df[filtered_df["risk_level"].isin(["High", "Medium"])]
                .groupby("manager_name")
                .size()
                .reset_index(name="num_customers")
                .sort_values("num_customers", ascending=False)
            )
            if len(manager_risk) > 0:
                fig_manager = px.bar(
                    manager_risk,
                    x="manager_name",
                    y="num_customers",
                    title="At-risk customers by manager"
                )
                st.plotly_chart(fig_manager, use_container_width=True)
            else:
                st.info("Không có dữ liệu manager rủi ro")

        st.subheader("🔥 Top khách giảm mạnh nhất")
        top = filtered_df.sort_values("login_drop_pct", ascending=False).head(10)
        st.dataframe(
            top[
                [
                    "customer_id",
                    "customer_name",
                    "manager_name",
                    "login_week_prev",
                    "login_week_curr",
                    "login_drop_pct",
                    "risk_level"
                ]
            ],
            use_container_width=True
        )

        st.subheader("⚠️ Khách hàng cần chăm sóc")
        alert_df = filtered_df[filtered_df["risk_level"].isin(["High", "Medium"])]

        def highlight_risk(row):
            if row["risk_level"] == "High":
                return ["background-color: #f8d7da"] * len(row)
            elif row["risk_level"] == "Medium":
                return ["background-color: #fff3cd"] * len(row)
            else:
                return [""] * len(row)

        alert_show = alert_df[
            [
                "customer_id",
                "customer_name",
                "manager_name",
                "manager_email",
                "revenue_week_prev",
                "revenue_week_curr",
                "revenue_drop_pct",
                "login_week_prev",
                "login_week_curr",
                "login_drop_pct",
                "risk_level"
            ]
        ]

        st.dataframe(
            alert_show.style.apply(highlight_risk, axis=1),
            use_container_width=True
        )

        st.markdown("## 🔐 Cấu hình gửi email")
        sender_email = st.text_input("Nhập Gmail của bạn")
        password = st.text_input("Nhập App Password", type="password")

        def send_mail():
            if alert_df.empty:
                st.warning("Không có khách cần gửi mail")
                return

            grouped = alert_df.groupby(["manager_name", "manager_email"])

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)

            for (manager_name, manager_email), group in grouped:
                content = f"Chào {manager_name},\n\nDanh sách khách hàng cần chăm sóc:\n\n"

                for _, row in group.iterrows():
                    content += (
                        f"- {row['customer_name']} | "
                        f"Doanh thu tuần trước: {row['revenue_week_prev']:,.0f} | "
                        f"Doanh thu tuần này: {row['revenue_week_curr']:,.0f} | "
                        f"Login tuần trước: {row['login_week_prev']} | "
                        f"Login tuần này: {row['login_week_curr']} | "
                        f"Giảm login: {round(row['login_drop_pct'], 2)}% | "
                        f"Risk: {row['risk_level']}\n"
                    )

                content += "\nVui lòng kiểm tra sớm.\n"

                msg = MIMEText(content, "plain", "utf-8")
                msg["Subject"] = "Cảnh báo khách hàng có nguy cơ rời bỏ"
                msg["From"] = sender_email
                msg["To"] = manager_email

                server.send_message(msg)

            server.quit()
            st.success("✅ Đã gửi email thành công!")

        st.markdown("## 📧 Gửi email")
        if st.button("🚀 Gửi email cho tất cả manager"):
            if sender_email == "" or password == "":
                st.warning("Vui lòng nhập Gmail và App Password")
            else:
                try:
                    send_mail()
                except Exception as e:
                    st.error(f"Gửi email thất bại: {e}")

        st.subheader("Chi tiết toàn bộ khách hàng")

        full_show = filtered_df[
            [
                "customer_id",
                "customer_name",
                "manager_name",
                "manager_email",
                "revenue_week_prev",
                "revenue_week_curr",
                "revenue_drop_pct",
                "login_week_prev",
                "login_week_curr",
                "login_drop_pct",
                "risk_level"
            ]
        ]

        st.dataframe(
            full_show.style.apply(highlight_risk, axis=1),
            use_container_width=True
        )

        csv_data = full_show.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Download kết quả",
            data=csv_data,
            file_name="churn_result.csv",
            mime="text/csv"
        )

else:
    st.info("Hãy upload file Excel để bắt đầu.")
