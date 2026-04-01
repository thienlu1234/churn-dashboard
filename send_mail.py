import pandas as pd
import smtplib
from email.mime.text import MIMEText

SENDER_EMAIL = "mpecplus197@gmail.com"
PASSWORD = "nqtroizxyekzhnbi"

def run_send_mail(input_file="churn_result.xlsx"):
    df = pd.read_excel(input_file)

    alert_df = df[df["risk_level"].isin(["High", "Medium"])]

    if alert_df.empty:
        print("Không có khách hàng cần gửi email.")
        return

    grouped = alert_df.groupby(["manager_name", "manager_email"])

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, PASSWORD)

    for (manager_name, manager_email), group in grouped:
        content = f"Chào {manager_name},\n\nCác khách hàng cần chăm sóc:\n\n"

        for _, row in group.iterrows():
            content += (
                f"- {row['customer_name']} | "
                f"Prev Login: {row['login_week_prev']} | "
                f"Curr Login: {row['login_week_curr']} | "
                f"Drop: {round(row['login_drop_pct'], 2)}% | "
                f"Risk: {row['risk_level']}\n"
            )

        content += "\nVui lòng kiểm tra sớm.\n"

        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = "Cảnh báo khách hàng có nguy cơ rời bỏ"
        msg["From"] = SENDER_EMAIL
        msg["To"] = manager_email

        try:
            server.send_message(msg)
            print(f"Đã gửi email tới {manager_email}")
        except Exception as e:
            print(f"Lỗi gửi mail tới {manager_email}: {e}")

    server.quit()


if __name__ == "__main__":
    run_send_mail()