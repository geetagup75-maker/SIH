from datetime import datetime
import numpy as np
import pandas as pd

def build_demo_live_record(fares: pd.DataFrame) -> pd.DataFrame:
    if fares.empty:
        raise ValueError("No fare records available for demo scrape.")
    row = fares.sample(1, random_state=None).iloc[0].copy()
    row["departure_date"] = pd.Timestamp(row["departure_date"])
    row["booking_date"] = pd.Timestamp.now().normalize()
    row["advance_days"] = max(1, int((row["departure_date"] - row["booking_date"]).days))
    multiplier = float(np.random.uniform(0.97, 1.03))
    row["base_fare"] = round(float(row["base_fare"]) * multiplier, 2)
    row["taxes"] = round(float(row["taxes"]) * multiplier, 2)
    row["convenience_fee"] = round(float(row["convenience_fee"]), 2)
    row["total_fare"] = round(row["base_fare"] + row["taxes"] + row["convenience_fee"], 2)
    row["source"] = "demo_live_fallback"
    row["scraped_at"] = datetime.now().isoformat()
    return pd.DataFrame([row])
