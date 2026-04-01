import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

# đọc file gốc
df = pd.read_excel("weekly_customer_with_manager.xlsx")

# tính % giảm login
df["login_drop_pct"] = (
    (df["login_week_prev"] - df["login_week_curr"])
    / df["login_week_prev"]
) * 100

# xử lý chia 0
df["login_drop_pct"] = df["login_drop_pct"].replace([float("inf"), -float("inf")], 0)
df["login_drop_pct"] = df["login_drop_pct"].fillna(0)

# phân loại churn
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

# filter manager
manager_list = ["All"] + sorted(df["manager_name"].dropna().unique().tolist())
selected_manager = st.selectbox("Chọn manager", manager_list)

if selected_manager != "All":
    df = df[df["manager_name"] == selected_manager]

# filter risk
risk_list = ["All", "High", "Medium", "Low"]
selected_risk = st.selectbox("Chọn risk level", risk_list)

if selected_risk != "All":
    df = df[df["risk_level"] == selected_risk]

st.title("📊 Customer Churn Dashboard")

# metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", len(df))
col2.metric("High Risk", (df["risk_level"] == "High").sum())
col3.metric("Medium Risk", (df["risk_level"] == "Medium").sum())
col4.metric("Low Risk", (df["risk_level"] == "Low").sum())

# biểu đồ phân bố risk
st.subheader("Risk Distribution")
fig = px.pie(df, names="risk_level", title="Risk Distribution")
st.plotly_chart(fig, use_container_width=True)

# top khách giảm mạnh nhất
st.subheader("🔥 Top khách giảm mạnh nhất")
top = df.sort_values("login_drop_pct", ascending=False).head(5)
st.dataframe(
    top[["customer_name", "manager_name", "login_drop_pct", "risk_level"]],
    use_container_width=True
)

# khách cần chăm sóc
st.subheader("⚠️ Khách hàng cần chăm sóc")
alert_df = df[df["risk_level"].isin(["High", "Medium"])]
st.dataframe(
    alert_df[
        [
            "customer_id",
            "customer_name",
            "manager_name",
            "manager_email",
            "revenue_week_prev",
            "revenue_week_curr",
            "login_week_prev",
            "login_week_curr",
            "login_drop_pct",
            "risk_level"
        ]
    ],
    use_container_width=True
)

# download excel
output_file = "filtered_churn_result.xlsx"
df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download file Excel",
        data=file,
        file_name="filtered_churn_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# bảng chi tiết
st.subheader("Chi tiết toàn bộ khách hàng")
st.dataframe(df, use_container_width=True)
