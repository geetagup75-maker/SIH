import numpy as np
import pandas as pd

from database import load_dgca_data


# =========================================================
# BOOKING WINDOWS
# =========================================================

WINDOWS = [
    "1–3 days",
    "7–14 days",
    "15–30 days",
]


# =========================================================
# PRICE RELATIVE
# =========================================================

def price_relative(current_price, base_price):
    """
    Calculate price relative.

    Formula:
        R = (Current Price / Base Price) × 100
    """

    if (
        pd.isna(base_price)
        or base_price == 0
        or pd.isna(current_price)
    ):
        return np.nan

    return current_price / base_price * 100.0


# =========================================================
# LASPEYRES INDEX
# =========================================================

def laspeyres_index(
    current_prices,
    base_prices,
    base_weights
):
    """
    Calculate Laspeyres price index.

    Formula:

        L = Σ(Pt × Q0) / Σ(P0 × Q0) × 100
    """

    current_prices = np.asarray(
        current_prices,
        dtype=float
    )

    base_prices = np.asarray(
        base_prices,
        dtype=float
    )

    base_weights = np.asarray(
        base_weights,
        dtype=float
    )

    mask = (
        np.isfinite(current_prices)
        & np.isfinite(base_prices)
        & np.isfinite(base_weights)
        & (base_prices != 0)
        & (base_weights >= 0)
    )

    current_prices = current_prices[mask]
    base_prices = base_prices[mask]
    base_weights = base_weights[mask]

    if len(current_prices) == 0:
        return np.nan

    denominator = np.sum(
        base_prices * base_weights
    )

    if denominator == 0:
        return np.nan

    numerator = np.sum(
        current_prices * base_weights
    )

    return (
        numerator
        / denominator
        * 100.0
    )


# =========================================================
# WEIGHTED PRICE RELATIVE
# =========================================================

def weighted_price_relative(
    current_prices,
    base_prices,
    weights
):
    """
    Calculate weighted average of price relatives.
    """

    current_prices = np.asarray(
        current_prices,
        dtype=float
    )

    base_prices = np.asarray(
        base_prices,
        dtype=float
    )

    weights = np.asarray(
        weights,
        dtype=float
    )

    mask = (
        np.isfinite(current_prices)
        & np.isfinite(base_prices)
        & np.isfinite(weights)
        & (base_prices != 0)
        & (weights >= 0)
    )

    if not mask.any():
        return np.nan

    current_prices = current_prices[mask]
    base_prices = base_prices[mask]
    weights = weights[mask]

    if weights.sum() == 0:
        return np.nan

    relatives = (
        current_prices
        / base_prices
        * 100.0
    )

    return np.average(
        relatives,
        weights=weights
    )


# =========================================================
# ROUTE WEIGHT MAP
# =========================================================

def _route_weight_map(route_weights):
    """
    Convert route-weight DataFrame into:

        {
            route: weight
        }

    Expected columns:

        route
        passenger_percentage
    """

    if (
        route_weights is None
        or route_weights.empty
    ):
        return {}

    x = route_weights.copy()

    x["passenger_percentage"] = pd.to_numeric(
        x["passenger_percentage"],
        errors="coerce"
    )

    x = x.dropna(
        subset=[
            "route",
            "passenger_percentage"
        ]
    )

    return dict(
        zip(
            x["route"].astype(str).str.strip(),
            x["passenger_percentage"]
        )
    )


# =========================================================
# LOAD DGCA ROUTE WEIGHTS
# =========================================================

def _load_dgca_route_weights():
    """
    Load route weights from the DGCA dataset.

    The DGCA CSV contains:

        Route_Code
        Capacity_Weight

    These are converted into the route-weight structure
    used by the index calculation.
    """

    try:
        dgca_df = load_dgca_data()

    except FileNotFoundError:
        return pd.DataFrame(
            columns=[
                "route",
                "passenger_percentage",
                "source",
                "reference_period",
                "official",
            ]
        )

    if dgca_df.empty:
        return pd.DataFrame(
            columns=[
                "route",
                "passenger_percentage",
                "source",
                "reference_period",
                "official",
            ]
        )

    required_columns = {
        "Route_Code",
        "Capacity_Weight",
    }

    if not required_columns.issubset(
        dgca_df.columns
    ):
        return pd.DataFrame(
            columns=[
                "route",
                "passenger_percentage",
                "source",
                "reference_period",
                "official",
            ]
        )

    weights = dgca_df[
        [
            "Route_Code",
            "Capacity_Weight"
        ]
    ].copy()

    weights["Route_Code"] = (
        weights["Route_Code"]
        .astype(str)
        .str.strip()
    )

    weights["Capacity_Weight"] = pd.to_numeric(
        weights["Capacity_Weight"],
        errors="coerce"
    )

    weights = weights.dropna(
        subset=[
            "Route_Code",
            "Capacity_Weight"
        ]
    )

    # If the same route appears more than once,
    # use its average capacity weight.
    weights = (
        weights
        .groupby(
            "Route_Code",
            as_index=False
        )["Capacity_Weight"]
        .mean()
    )

    weights = weights.rename(
        columns={
            "Route_Code": "route",
            "Capacity_Weight":
                "passenger_percentage",
        }
    )

    weights["source"] = (
        "DGCA weighted airfare dataset"
    )

    if "Date" in dgca_df.columns:
        dates = pd.to_datetime(
            dgca_df["Date"],
            errors="coerce"
        ).dropna()

        if not dates.empty:
            weights["reference_period"] = (
                dates.min().strftime("%Y-%m-%d")
            )
        else:
            weights["reference_period"] = (
                "DGCA dataset"
            )
    else:
        weights["reference_period"] = (
            "DGCA dataset"
        )

    # Keep this as 0 unless the underlying
    # passenger/capacity weights have been
    # independently verified as official.
    weights["official"] = 0

    return weights[
        [
            "route",
            "passenger_percentage",
            "source",
            "reference_period",
            "official",
        ]
    ]


# =========================================================
# GET ROUTE WEIGHTS
# =========================================================

def _get_route_weights(route_weights):
    """
    Priority:

    1. Explicit route_weights supplied by caller.
    2. DGCA CSV dataset.
    3. Empty DataFrame → equal-route fallback.
    """

    # -----------------------------------------------------
    # 1. USER-SUPPLIED ROUTE WEIGHTS
    # -----------------------------------------------------

    if (
        route_weights is not None
        and not route_weights.empty
    ):
        return route_weights.copy()

    # -----------------------------------------------------
    # 2. DGCA DATASET
    # -----------------------------------------------------

    dgca_weights = _load_dgca_route_weights()

    if not dgca_weights.empty:
        return dgca_weights

    # -----------------------------------------------------
    # 3. NO WEIGHTS
    # -----------------------------------------------------

    return pd.DataFrame(
        columns=[
            "route",
            "passenger_percentage",
            "source",
            "reference_period",
            "official",
        ]
    )


# =========================================================
# DGCA LOWE / LASPEYRES INDEX
# =========================================================

def calculate_dgca_lowe_index(
    fares: pd.DataFrame,
    base_date: str = "2026-08-01",
    target_date: str | None = None,
    route_weights: pd.DataFrame | None = None,
    min_group_n: int = 5,
):
    """
    Calculate the DGCA passenger-weighted
    Lowe/Laspeyres-style airfare index.

    Method:

    1. Fare observations are divided into:
       - 1–3 days
       - 7–14 days
       - 15–30 days

    2. Base-period mean fare is calculated.

    3. Current-period mean fare is calculated.

    4. Groups with N < 5 are excluded.

    5. DGCA route weights are applied.

    6. Booking-window strata receive equal
       within-route shares.

    7. Route-level price relatives are
       aggregated into the final index.
    """

    # -----------------------------------------------------
    # COPY DATA
    # -----------------------------------------------------

    df = fares.copy()

    # -----------------------------------------------------
    # DATE CONVERSION
    # -----------------------------------------------------

    df["departure_date"] = pd.to_datetime(
        df["departure_date"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # NUMERIC CONVERSION
    # -----------------------------------------------------

    df["advance_days"] = pd.to_numeric(
        df["advance_days"],
        errors="coerce"
    )

    df["total_fare"] = pd.to_numeric(
        df["total_fare"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # CREATE BOOKING WINDOW
    # -----------------------------------------------------

    if "advance_window" not in df.columns:

        from preprocessing import add_advance_window

        df = add_advance_window(df)

    # -----------------------------------------------------
    # BASE AND TARGET DATE
    # -----------------------------------------------------

    base = pd.Timestamp(
        base_date
    )

    if target_date:

        target = pd.Timestamp(
            target_date
        )

    else:

        target = (
            df["departure_date"]
            .max()
        )

    # -----------------------------------------------------
    # KEEP REQUIRED DATA
    # -----------------------------------------------------

    df = df[
        df["advance_window"].isin(WINDOWS)
        & df["total_fare"].notna()
        & df["departure_date"].notna()
    ].copy()

    if df.empty:
        return np.nan, pd.DataFrame()

    # -----------------------------------------------------
    # BASE PERIOD
    # -----------------------------------------------------

    base_df = df[
        (df["departure_date"].dt.year == base.year)
        &
        (df["departure_date"].dt.month == base.month)
    ].copy()

    # -----------------------------------------------------
    # CURRENT / TARGET PERIOD
    # -----------------------------------------------------

    cur_df = df[
        df["departure_date"].dt.normalize()
        == target.normalize()
    ].copy()

    # -----------------------------------------------------
    # CHECK DATA
    # -----------------------------------------------------

    if base_df.empty or cur_df.empty:
        return np.nan, pd.DataFrame()

    # -----------------------------------------------------
    # BASE PRICE BY ROUTE + WINDOW
    # -----------------------------------------------------

    b = (
        base_df
        .groupby(
            ["route", "advance_window"],
            observed=True
        )["total_fare"]
        .agg(
            base_price="mean",
            base_n="count"
        )
        .reset_index()
    )

    # -----------------------------------------------------
    # CURRENT PRICE BY ROUTE + WINDOW
    # -----------------------------------------------------

    c = (
        cur_df
        .groupby(
            ["route", "advance_window"],
            observed=True
        )["total_fare"]
        .agg(
            current_price="mean",
            current_n="count"
        )
        .reset_index()
    )

    # -----------------------------------------------------
    # MATCH BASE AND CURRENT
    # -----------------------------------------------------

    m = b.merge(
        c,
        on=[
            "route",
            "advance_window"
        ],
        how="inner"
    )

    # -----------------------------------------------------
    # SAMPLE SIZE CHECK
    # N >= 5
    # -----------------------------------------------------

    # Keep only statistically valid route/window groups
    m["valid_group"] = (
        (m["base_n"] >= min_group_n) &
        (m["current_n"] >= min_group_n)
    )

    # If some windows do not have enough observations,
    # exclude only those windows instead of failing the whole index.
    m = m[m["valid_group"]].copy()

    if m.empty:
        return np.nan, m
    # -----------------------------------------------------
    # LOAD ROUTE WEIGHTS
    # -----------------------------------------------------

    effective_weights = _get_route_weights(
        route_weights
    )

    weights = _route_weight_map(
        effective_weights
    )

    # -----------------------------------------------------
    # APPLY DGCA ROUTE WEIGHTS
    # -----------------------------------------------------

    m["route_weight_pct"] = (
        m["route"].astype(str).str.strip().map(weights)
    )

    # -----------------------------------------------------
    # WEIGHT STATUS
    # -----------------------------------------------------

    if m["route_weight_pct"].notna().any():

        # Routes missing from DGCA dataset receive
        # zero weight rather than an invented weight.

        m["route_weight_pct"] = (
            m["route_weight_pct"]
            .fillna(0)
        )

        m["weight_source"] = (
            "DGCA route capacity weight"
        )

    else:

        # No DGCA route matched.
        # Keep a transparent equal-route fallback.

        m["route_weight_pct"] = 1.0

        m["weight_source"] = (
            "Demo equal-route fallback; "
            "DGCA weights not matched"
        )

    # -----------------------------------------------------
    # REMOVE ZERO-WEIGHT ROUTES
    # -----------------------------------------------------

    weighted_m = m[
        m["route_weight_pct"] > 0
    ].copy()

    if weighted_m.empty:

        return np.nan, m

    # -----------------------------------------------------
    # EQUAL SHARE ACROSS AVAILABLE WINDOWS
    # -----------------------------------------------------

    counts = (
        weighted_m
        .groupby("route")["advance_window"]
        .transform("count")
    )

    weighted_m["stratum_weight"] = (
        weighted_m["route_weight_pct"]
        / counts
    )

    # -----------------------------------------------------
    # PRICE RELATIVE
    # -----------------------------------------------------

    weighted_m["price_relative"] = (
        weighted_m["current_price"]
        / weighted_m["base_price"]
        * 100.0
    )

    # -----------------------------------------------------
    # FINAL WEIGHTED INDEX
    # -----------------------------------------------------

    total_weight = (
        weighted_m["stratum_weight"].sum()
    )

    if total_weight == 0:
        return np.nan, weighted_m

    index_value = (
        np.sum(
            weighted_m["price_relative"]
            * weighted_m["stratum_weight"]
        )
        / total_weight
    )

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return (
        float(index_value),
        weighted_m.sort_values(
            [
                "route",
                "advance_window"
            ]
        )
    )


# =========================================================
# DYNAMIC INDEX TIME SERIES
# =========================================================

def calculate_dynamic_series(
    fares,
    route_weights=None,
    min_group_n=5
):
    """
    Recalculate the DGCA-weighted index for
    every available departure date.
    """

    dates = (
        pd.to_datetime(
            fares["departure_date"],
            errors="coerce"
        )
        .dropna()
        .dt.normalize()
        .sort_values()
        .unique()
    )

    if len(dates) == 0:

        return pd.DataFrame(
            columns=[
                "date",
                "index_value",
                "observations",
                "base_value",
                "period",
            ]
        )

    # -----------------------------------------------------
    # FIRST AVAILABLE DATE AS BASE
    # -----------------------------------------------------

    base_date = str(
        pd.Timestamp(
            dates[0]
        ).date()
    )

    rows = []

    # -----------------------------------------------------
    # CALCULATE EACH DATE
    # -----------------------------------------------------

    for d in dates:

        idx, details = (
            calculate_dgca_lowe_index(
                fares,
                base_date=base_date,
                target_date=str(
                    pd.Timestamp(d).date()
                ),
                route_weights=route_weights,
                min_group_n=min_group_n,
            )
        )

        rows.append(
            {
                "date": pd.Timestamp(d),
                "index_value": idx,
                "observations": (
                    int(
                        details["current_n"].sum()
                    )
                    if not details.empty
                    else 0
                ),
            }
        )

    # -----------------------------------------------------
    # CREATE RESULT
    # -----------------------------------------------------

    out = pd.DataFrame(rows)

    out = out.dropna(
        subset=["index_value"]
    )

    if not out.empty:

        out["base_value"] = 100.0

        out["period"] = (
            out["date"]
            .dt.to_period("M")
            .astype(str)
        )

    return out