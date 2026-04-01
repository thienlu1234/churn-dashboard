import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

df = pd.read_excel("churn_result.xlsx")

manager_list = ["All"] + sorted(df["manager_name"].dropna().unique().tolist())
selected_manager = st.selectbox("Chọn manager", manager_list)

if selected_manager != "All":
    df = df[df["manager_name"] == selected_manager]

risk_list = ["All", "High", "Medium", "Low"]
selected_risk = st.selectbox("Chọn risk level", risk_list)

if selected_risk != "All":
    df = df[df["risk_level"] == selected_risk]

st.title("📊 Customer Churn Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", len(df))
col2.metric("High Risk", (df["risk_level"] == "High").sum())
col3.metric("Medium Risk", (df["risk_level"] == "Medium").sum())
col4.metric("Low Risk", (df["risk_level"] == "Low").sum())

st.subheader("Risk Distribution")
fig = px.pie(df, names="risk_level", title="Risk Distribution")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🔥 Top khách giảm mạnh nhất")
top = df.sort_values("login_drop_pct", ascending=False).head(5)
st.dataframe(
    top[["customer_name", "manager_name", "login_drop_pct", "risk_level"]],
    use_container_width=True
)

st.subheader("⚠️ Khách hàng cần chăm sóc")
alert_df = df[df["risk_level"].isin(["High", "Medium"])]
st.dataframe(
    alert_df[
        [
            "customer_id",
            "customer_name",
            "manager_name",
            "manager_email",
            "login_week_prev",
            "login_week_curr",
            "login_drop_pct",
            "risk_level"
        ]
    ],
    use_container_width=True
)

output_file = "filtered_churn_result.xlsx"
df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download file Excel",
        data=file,
        file_name="filtered_churn_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.subheader("Chi tiết toàn bộ khách hàng")
st.dataframe(df, use_container_width=True)