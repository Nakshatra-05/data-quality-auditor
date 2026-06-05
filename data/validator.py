import pandas as pd
import numpy as np


def run_all_checks(df: pd.DataFrame) -> dict:
    return {
        "missing_values": check_missing_values(df),
        "duplicates":     check_duplicates(df),
        "outliers":       check_outliers(df),
        "invalid_values": check_invalid_values(df),
        "type_issues":    check_type_issues(df),
    }


def check_missing_values(df: pd.DataFrame) -> dict:
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    return {
        "count": int(missing.sum()),
        "columns": {col: int(cnt) for col, cnt in missing.items()},
    }


def check_duplicates(df: pd.DataFrame) -> dict:
    dupes = df.duplicated()
    return {
        "count": int(dupes.sum()),
        "rows": df[dupes].index.tolist(),
    }


def check_outliers(df: pd.DataFrame) -> dict:
    results = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue
        Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
        IQR = Q3 - Q1
        lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        outlier_mask = (series < lower) | (series > upper)
        if outlier_mask.any():
            results[col] = {
                "count": int(outlier_mask.sum()),
                "values": series[outlier_mask].tolist(),
                "bounds": {"lower": round(lower, 2), "upper": round(upper, 2)},
            }
    return results


def check_invalid_values(df: pd.DataFrame) -> dict:
    issues = {}

    # Negative numbers in columns that should be positive
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        neg = df[col][df[col] < 0]
        if not neg.empty:
            issues[f"{col}_negative"] = {
                "count": len(neg),
                "rows": neg.index.tolist(),
                "values": neg.tolist(),
            }

    # Email format check
    if "email" in df.columns:
        invalid_emails = df["email"].dropna()
        invalid_emails = invalid_emails[
            ~invalid_emails.str.contains(r"^[^@]+@[^@]+\.[^@]+$", regex=True)
        ]
        if not invalid_emails.empty:
            issues["invalid_emails"] = {
                "count": len(invalid_emails),
                "rows": invalid_emails.index.tolist(),
                "values": invalid_emails.tolist(),
            }

    # Future joining date check
    if "joining_date" in df.columns:
        dates = pd.to_datetime(df["joining_date"], errors="coerce")
        future = dates[dates > pd.Timestamp.today()]
        if not future.empty:
            issues["future_joining_dates"] = {
                "count": len(future),
                "rows": future.index.tolist(),
                "values": future.dt.strftime("%Y-%m-%d").tolist(),
            }

    # Zero age check
    if "age" in df.columns:
        zero_age = df["age"][df["age"] == 0]
        if not zero_age.empty:
            issues["zero_age"] = {
                "count": len(zero_age),
                "rows": zero_age.index.tolist(),
                "values": zero_age.tolist(),
            }

    return issues


def check_type_issues(df: pd.DataFrame) -> dict:
    issues = {}
    for col in df.columns:
        if df[col].dtype == object:
            converted = pd.to_numeric(df[col], errors="coerce")
            failed = converted.isna() & df[col].notna()
            succeeded = converted.notna()
            if failed.any() and succeeded.any():
                issues[col] = {
                    "message": f"Column '{col}' contains mixed types (text and numbers)",
                    "bad_rows": df[col][failed].index.tolist(),
                    "bad_values": df[col][failed].tolist(),
                }
    return issues