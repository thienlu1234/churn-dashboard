import streamlit as st
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

st.markdown("""
<h1 style='text-align: center; color: #4A90E2; margin-bottom: 10px;'>
📊 Customer Churn Monitoring System
</h1>
<p style='text-align: center; color: gray; font-size: 18px;'>
Upload file Excel để phân tích churn và gửi email cho quản lý
</p>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx"])

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

        # ===== CALCULATE =====
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
        # ===== FILTER =====
        st.sidebar.header("🔎 Bộ lọc")
        
        selected_manager = st.sidebar.selectbox(
            "Chọn Manager",
            ["All"] + sorted(df["manager_name"].dropna().unique())
        )
        
        selected_risk = st.sidebar.selectbox(
            "Chọn Risk Level",
            ["All", "High", "Medium", "Low"]
        )
        
        filtered_df = df.copy()
        
        if selected_manager != "All":
            filtered_df = filtered_df[
                filtered_df["manager_name"] == selected_manager
            ]
        
        if selected_risk != "All":
            filtered_df = filtered_df[
                filtered_df["risk_level"] == selected_risk
            ]
        # ===== SORT =====
        order_map = {"High": 0, "Medium": 1, "Low": 2}
        df["order"] = df["risk_level"].map(order_map)

        df = df.sort_values(["order", "login_drop_pct"], ascending=[True, False])

        # ===== KPI =====
        total = len(df)
        high = (df["risk_level"] == "High").sum()
        medium = (df["risk_level"] == "Medium").sum()
        low = (df["risk_level"] == "Low").sum()
        churn_rate = (high / total * 100) if total > 0 else 0

        revenue_risk = df.loc[
            df["risk_level"].isin(["High", "Medium"]),
            "revenue_week_prev"
        ].sum()

        st.subheader("📊 KPI Overview")

        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.markdown(f"""
        <div style="background:#f0f2f6;padding:15px;border-radius:12px;text-align:center">
        <h4>Total Customers</h4>
        <h2>{total}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col2.markdown(f"""
        <div style="background:#ffe5e5;padding:15px;border-radius:12px;text-align:center">
        <h4>High Risk</h4>
        <h2>{high}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col3.markdown(f"""
        <div style="background:#fff3cd;padding:15px;border-radius:12px;text-align:center">
        <h4>Medium Risk</h4>
        <h2>{medium}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col4.markdown(f"""
        <div style="background:#e2f0d9;padding:15px;border-radius:12px;text-align:center">
        <h4>Low Risk</h4>
        <h2>{low}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col5.markdown(f"""
        <div style="background:#d9edf7;padding:15px;border-radius:12px;text-align:center">
        <h4>Churn Rate</h4>
        <h2>{churn_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

        st.metric("💰 Revenue At Risk", f"{revenue_risk:,.0f}")

        # ===== CHART =====
        st.subheader("Risk Distribution")
        fig = px.pie(filtered_df, names="risk_level")
        st.plotly_chart(fig, use_container_width=True)

        # ===== TOP =====
        st.subheader("🔥 Top giảm mạnh nhất")
        st.dataframe(df.head(10), use_container_width=True)

        # ===== ALERT =====
        alert_df = filtered_df[filtered_df["risk_level"].isin(["High", "Medium"])]

        def highlight(row):
            if row["risk_level"] == "High":
                return ["background-color:#f8d7da"] * len(row)
            elif row["risk_level"] == "Medium":
                return ["background-color:#fff3cd"] * len(row)
            return [""] * len(row)

        st.subheader("⚠️ Khách cần chăm sóc")
        st.dataframe(alert_df.style.apply(highlight, axis=1), use_container_width=True)
        # ===== SO SÁNH MANAGER =====
        st.subheader("📊 So sánh quản lý")
        
        manager_summary = (
            df.groupby("manager_name")
            .agg(
                total_customers=("customer_id", "count"),
                high_risk=("risk_level", lambda x: (x == "High").sum()),
                medium_risk=("risk_level", lambda x: (x == "Medium").sum())
            )
            .reset_index()
        )
        
        manager_summary["total_risk"] = (
            manager_summary["high_risk"] + manager_summary["medium_risk"]
        )
        
        manager_summary["churn_rate"] = (
            manager_summary["high_risk"] / manager_summary["total_customers"] * 100
        )
        
        # sort manager nguy hiểm nhất lên trên
        manager_summary = manager_summary.sort_values("total_risk", ascending=False)
        
        st.dataframe(manager_summary, use_container_width=True)
        
        # ===== CHART =====
        import plotly.express as px
        
        fig = px.bar(
            manager_summary,
            x="manager_name",
            y="total_risk",
            title="Số khách hàng có nguy cơ rời bỏ theo quản lý"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        # ===== EMAIL CONFIG =====
        st.markdown("## 🔐 Email Config")
        sender_email = st.text_input("Gmail của bạn")
        password = st.text_input("App Password", type="password")

        # ===== SEND MAIL =====
        def send_mail():
            grouped = alert_df.groupby(["manager_name", "manager_email"])

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)

            for (manager_name, manager_email), group in grouped:

                group = group.sort_values("login_drop_pct", ascending=False)

                rows = ""
                for _, row in group.iterrows():
                    color = "#f8d7da" if row["risk_level"] == "High" else "#fff3cd"
                    rows += f"""
                    <tr style="background:{color};">
                        <td>{row['customer_name']}</td>
                        <td>{row['login_week_prev']}</td>
                        <td>{row['login_week_curr']}</td>
                        <td>{round(row['login_drop_pct'],2)}%</td>
                        <td>{row['risk_level']}</td>
                    </tr>
                    """

                html = f"""
                <html>
                <body>
                <h2>🚨 Churn Alert</h2>
                <p>Chào <b>{manager_name}</b>,</p>
                <p>Bạn có <b>{len(group)}</b> khách cần chăm sóc:</p>

                <table border="1" cellpadding="8" style="border-collapse: collapse;">
                    <tr style="background:#d9edf7;">
                        <th>Khách</th>
                        <th>Login trước</th>
                        <th>Login hiện tại</th>
                        <th>% giảm</th>
                        <th>Risk</th>
                    </tr>
                    {rows}
                </table>

                <br>
                <p>-- Churn System --</p>
                </body>
                </html>
                """

                msg = MIMEMultipart()
                msg["Subject"] = f"{len(group)} khách hàng có nguy cơ rời bỏ"
                msg["From"] = sender_email
                msg["To"] = manager_email

                msg.attach(MIMEText(html, "html"))

                server.send_message(msg)

            server.quit()
            st.success("✅ Gửi mail thành công!")

        st.markdown("## 📧 Gửi email")

        if st.button("🚀 Send Alert Email"):
            if sender_email == "" or password == "":
                st.warning("Nhập email + app password")
            else:
                try:
                    send_mail()
                except Exception as e:
                    st.error(e)

        # ===== FULL TABLE =====
        st.subheader("📋 Full Data")
        st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

        # ===== DOWNLOAD =====
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Download CSV", csv, "churn.csv")

else:
    st.info("Upload file để bắt đầu")
