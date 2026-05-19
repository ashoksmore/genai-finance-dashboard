import pandas as pd


def normalize(df: pd.DataFrame) -> list[dict]:
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    required = ["period", "department", "category", "budget", "actual"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce")
    df["budget"] = df["budget"].fillna(0.0)
    df["actual"] = df["actual"].fillna(0.0)

    for col in ("period", "department", "category"):
        df[col] = df[col].astype(str).str.strip()

    df["department"] = df["department"].str.title()
    df["category"] = df["category"].str.lower()

    df = df[~((df["budget"] == 0) & (df["actual"] == 0))]

    return df[["period", "department", "category", "budget", "actual"]].to_dict(orient="records")


if __name__ == "__main__":
    import pandas as pd

    test_data = {
        "period": ["2025-01", "2025-01", "2025-02"],
        "department": ["  engineering ", "Marketing", "SALES"],
        "category": ["Payroll", "VENDOR", "payroll"],
        "budget": ["380000", "130000", "300000"],
        "actual": ["365000", "128000", "295000"],
    }
    df = pd.DataFrame(test_data)
    result = normalize(df)
    for row in result:
        print(row)
