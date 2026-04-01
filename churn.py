import pandas as pd

def run_churn(input_file="weekly_customer_with_manager.xlsx", output_file="churn_result.xlsx"):
    df = pd.read_excel(input_file)

    df["login_drop_pct"] = (
        (df["login_week_prev"] - df["login_week_curr"])
        / df["login_week_prev"]
    ) * 100

    df["login_drop_pct"] = df["login_drop_pct"].replace([float("inf"), -float("inf")], 0)
    df["login_drop_pct"] = df["login_drop_pct"].fillna(0)

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

    df.to_excel(output_file, index=False)
    return df


if __name__ == "__main__":
    result = run_churn()
    print(result.head())