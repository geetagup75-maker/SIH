import numpy as np
import pandas as pd

WINDOWS = ["1–3 days", "7–14 days", "15–30 days"]

def price_relative(current_price, base_price):
    if pd.isna(base_price) or base_price == 0 or pd.isna(current_price):
        return np.nan
    return current_price / base_price * 100.0

def laspeyres_index(current_prices, base_prices, base_weights):
    current_prices = np.asarray(current_prices, dtype=float)
    base_prices = np.asarray(base_prices, dtype=float)
    base_weights = np.asarray(base_weights, dtype=float)
    mask = np.isfinite(current_prices) & np.isfinite(base_prices) & np.isfinite(base_weights)
    current_prices, base_prices, base_weights = current_prices[mask], base_prices[mask], base_weights[mask]
    den = np.sum(base_prices * base_weights)
    return np.nan if den == 0 else np.sum(current_prices * base_weights) / den * 100.0

def weighted_price_relative(current_prices, base_prices, weights):
    cur, base, w = map(np.asarray, (current_prices, base_prices, weights))
    mask = np.isfinite(cur) & np.isfinite(base) & np.isfinite(w) & (base != 0) & (w >= 0)
    if not mask.any() or w[mask].sum() == 0:
        return np.nan
    return np.average((cur[mask] / base[mask]) * 100.0, weights=w[mask])

def _route_weight_map(route_weights):
    if route_weights is None or route_weights.empty:
        return {}
    x = route_weights.copy()
    x["passenger_percentage"] = pd.to_numeric(x["passenger_percentage"], errors="coerce")
    x = x.dropna(subset=["route","passenger_percentage"])
    return dict(zip(x["route"], x["passenger_percentage"]))

def calculate_dgca_lowe_index(
    fares: pd.DataFrame,
    base_date: str = "2026-08-01",
    target_date: str | None = None,
    route_weights: pd.DataFrame | None = None,
    min_group_n: int = 5,
):
    """
    DGCA passenger-weighted Lowe/Laspeyres-style index.

    - Prices are stratified into the requested advance-booking windows.
    - Base-period stratum mean fares are fixed as the price reference.
    - Current-period stratum mean fares are compared with base means.
    - DGCA passenger percentages weight routes.
    - Booking-window strata receive equal within-route shares unless separate
      official window weights are supplied.
    """
    df = fares.copy()
    df["departure_date"] = pd.to_datetime(df["departure_date"], errors="coerce")
    df["advance_days"] = pd.to_numeric(df["advance_days"], errors="coerce")
    df["total_fare"] = pd.to_numeric(df["total_fare"], errors="coerce")
    if "advance_window" not in df:
        from preprocessing import add_advance_window
        df = add_advance_window(df)

    base = pd.Timestamp(base_date)
    target = pd.Timestamp(target_date) if target_date else df["departure_date"].max()
    df = df[df["advance_window"].isin(WINDOWS) & df["total_fare"].notna()].copy()

    # Fixed base-period basket: the calendar month containing base_date.
    # This avoids accidentally allowing later observations into the base.
    base_df = df[
        (df["departure_date"].dt.year == base.year) &
        (df["departure_date"].dt.month == base.month)
    ].copy()
    if target_date:
        cur_df = df[df["departure_date"].dt.normalize() == target.normalize()].copy()
    else:
        cur_df = df[df["departure_date"].dt.normalize() == target.normalize()].copy()

    if base_df.empty or cur_df.empty:
        return np.nan, pd.DataFrame()

    b = (base_df.groupby(["route","advance_window"], observed=True)["total_fare"]
         .agg(base_price="mean", base_n="count").reset_index())
    c = (cur_df.groupby(["route","advance_window"], observed=True)["total_fare"]
         .agg(current_price="mean", current_n="count").reset_index())
    m = b.merge(c, on=["route","advance_window"], how="inner")
    m = m[(m["base_n"] >= min_group_n) & (m["current_n"] >= min_group_n)].copy()
    if m.empty:
        return np.nan, m

    weights = _route_weight_map(route_weights)
    m["route_weight_pct"] = m["route"].map(weights)
    if m["route_weight_pct"].isna().all():
        m["route_weight_pct"] = 1.0
        m["weight_source"] = "demo equal-route fallback; official DGCA weights not loaded"
    else:
        m["route_weight_pct"] = m["route_weight_pct"].fillna(0)
        m["weight_source"] = "DGCA route passenger percentage"
    # Equal allocation across available windows within each route.
    counts = m.groupby("route")["advance_window"].transform("count")
    m["stratum_weight"] = m["route_weight_pct"] / counts
    m["price_relative"] = m["current_price"] / m["base_price"] * 100.0
    index_value = np.average(m["price_relative"], weights=m["stratum_weight"])
    return float(index_value), m.sort_values(["route","advance_window"])

def calculate_dynamic_series(fares, route_weights=None, min_group_n=5):
    dates = pd.to_datetime(fares["departure_date"], errors="coerce").dropna().dt.normalize().sort_values().unique()
    if len(dates) == 0:
        return pd.DataFrame(columns=["date","index_value","observations"])
    base_date = str(pd.Timestamp(dates[0]).date())
    rows = []
    for d in dates:
        idx, details = calculate_dgca_lowe_index(
            fares, base_date=base_date, target_date=str(pd.Timestamp(d).date()),
            route_weights=route_weights, min_group_n=min_group_n
        )
        rows.append({
            "date": pd.Timestamp(d),
            "index_value": idx,
            "observations": int(details["current_n"].sum()) if not details.empty else 0
        })
    out = pd.DataFrame(rows).dropna(subset=["index_value"])
    if not out.empty:
        out["base_value"] = 100.0
        out["period"] = out["date"].dt.to_period("M").astype(str)
    return out
