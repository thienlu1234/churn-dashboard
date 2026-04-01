import os
from churn import run_churn
from send_mail import run_send_mail

def main():
    print("1. Đang tính churn...")
    run_churn(
        input_file="weekly_customer_with_manager.xlsx",
        output_file="churn_result.xlsx"
    )

    print("2. Đang gửi email...")
    run_send_mail(input_file="churn_result.xlsx")

    print("3. Đang mở dashboard...")
    os.system("streamlit run app.py")

if __name__ == "__main__":
    main()