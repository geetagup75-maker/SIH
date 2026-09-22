import numpy as np
import pandas as pd

ADVANCE_WINDOWS = {
    "1–3 days": (1, 3),
    "7–14 days": (7, 14),
    "15–30 days": (15, 30),
}

def add_advance_window(df):
    df = df.copy()
    bins = [0, 3, 6, 14, 30, np.inf]
    labels = ["1–3 days", "4–6 days", "7–14 days", "15–30 days", "31+ days"]
    df["advance_window"] = pd.cut(
        pd.to_numeric(df["advance_days"], errors="coerce"),
        bins=bins, labels=labels, include_lowest=True
    ).astype("string")
    return df

def clean_fare_data(df):
    df = df.copy()
    for col in ["departure_date","booking_date","scraped_at"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["advance_days","base_fare","taxes","convenience_fee","total_fare"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["origin","destination","carrier_code","carrier_name","fare_class","source"]:
        if col in df:
            df[col] = df[col].astype("string").str.strip()
    df["route"] = df["origin"].astype(str) + " → " + df["destination"].astype(str)
    df["month"] = df["departure_date"].dt.to_period("M").astype(str)
    df["year"] = df["departure_date"].dt.year
    df["month_name"] = df["departure_date"].dt.month_name()
    df["day_of_week"] = df["departure_date"].dt.day_name()
    df["tax_percentage"] = np.where(df["total_fare"] > 0, df["taxes"] / df["total_fare"] * 100, np.nan)
    df["fee_percentage"] = np.where(df["total_fare"] > 0, df["convenience_fee"] / df["total_fare"] * 100, np.nan)
    return add_advance_window(df)

def remove_duplicates(df):
    duplicate_columns = ["origin","destination","carrier_code","departure_date","booking_date","fare_class","source"]
    existing = [c for c in duplicate_columns if c in df.columns]
    before = len(df)
    out = df.drop_duplicates(subset=existing)
    return out, before-len(out)

def missing_value_summary(df):
    return pd.DataFrame({
        "column": df.columns,
        "missing_count": df.isna().sum().values,
        "missing_percentage": (df.isna().mean()*100).round(2).values
    }).sort_values("missing_percentage", ascending=False)

def data_quality_summary(df):
    total = df.shape[0]*df.shape[1]
    missing = int(df.isna().sum().sum())
    return {
        "rows": len(df), "columns": len(df.columns),
        "duplicates": int(df.duplicated().sum()),
        "missing_cells": missing,
        "missing_percentage": missing/total*100 if total else 0,
    }
