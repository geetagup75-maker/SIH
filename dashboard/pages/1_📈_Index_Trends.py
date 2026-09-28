import sys
from pathlib import Path

import streamlit as st
import plotly.express as px

# =========================================================
# PROJECT ROOT
# =========================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =========================================================
# IMPORTS
# =========================================================

from database import (
    load_fare_records,
    load_dgca_data,
)

from preprocessing import clean_fare_data

from airfare_index.index_calculator import (
    calculate_dynamic_series,
)


# =========================================================
# PAGE TITLE
# =========================================================

st.title("📈 Dynamic Airfare Index Trends")

st.caption(
    "DGCA-weighted Lowe/Laspeyres-style airfare index "
    "using route weights and advance-booking windows."
)


# =========================================================
# LOAD AIRFARE DATA
# =========================================================

try:

    fares = load_fare_records()

    fares = clean_fare_data(fares)

except Exception as e:

    st.error(
        f"Unable to load airfare data: {e}"
    )

    st.stop()


# =========================================================
# LOAD DGCA DATA
# =========================================================

try:

    dgca_data = load_dgca_data()

except FileNotFoundError:

    dgca_data = None

    st.warning(
        "DGCA dataset was not found. "
        "The index cannot use DGCA route weights."
    )

except Exception as e:

    dgca_data = None

    st.error(
        f"Unable to load DGCA dataset: {e}"
    )


# =========================================================
# DGCA DATA STATUS
# =========================================================

if dgca_data is not None and not dgca_data.empty:

    st.success(
        f"✅ DGCA dataset loaded: "
        f"{len(dgca_data):,} observations"
    )

    # -----------------------------------------------------
    # SHOW DGCA DATASET INFORMATION
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "DGCA Observations",
            f"{len(dgca_data):,}"
        )

    with col2:

        routes = dgca_data[
            "Route_Code"
        ].nunique()

        st.metric(
            "DGCA Routes",
            f"{routes:,}"
        )

    with col3:

        weight_sum = dgca_data[
            "Capacity_Weight"
        ].sum()

        st.metric(
            "Total Capacity Weight",
            f"{weight_sum:.4f}"
        )

else:

    st.warning(
        "⚠️ DGCA dataset is empty or unavailable. "
        "The index calculation will not have DGCA route weights."
    )


# =========================================================
# CALCULATE DYNAMIC INDEX
# =========================================================

try:

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # route_weights=None tells index_calculator.py
    # to automatically load the DGCA CSV.
    # -----------------------------------------------------

    series = calculate_dynamic_series(
        fares,
        route_weights=None,
        min_group_n=5,
    )

except Exception as e:

    st.error(
        f"Unable to calculate dynamic airfare index: {e}"
    )

    st.stop()


# =========================================================
# CHECK RESULT
# =========================================================

if series.empty:

    st.warning(
        "Not enough comparable observations to "
        "calculate the dynamic index."
    )

    st.info(
        "Each route and advance-booking window requires "
        "at least N ≥ 5 observations in both the base "
        "and target periods."
    )

    st.stop()


# =========================================================
# INDEX SUMMARY
# =========================================================

latest = series.sort_values(
    "date"
).iloc[-1]

latest_index = latest["index_value"]

latest_date = latest["date"]

# ---------------------------------------------------------
# BASE VALUE
# ---------------------------------------------------------

BASE_VALUE = 100.0


# =========================================================
# METRICS
# =========================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Current Index",
        f"{latest_index:.2f}"
    )


with col2:

    st.metric(
        "Base Index",
        f"{BASE_VALUE:.2f}"
    )


with col3:

    change_from_base = (
        latest_index - BASE_VALUE
    )

    st.metric(
        "Change from Base",
        f"{change_from_base:+.2f}"
    )


with col4:

    st.metric(
        "Comparable Observations",
        f"{int(latest['observations']):,}"
    )


st.caption(
    f"Latest calculated index date: "
    f"{latest_date:%Y-%m-%d}"
)


# =========================================================
# INDEX INTERPRETATION
# =========================================================

if latest_index > 100:

    st.info(
        f"The latest index is {latest_index:.2f}, "
        f"which is above the base value of 100."
    )

elif latest_index < 100:

    st.info(
        f"The latest index is {latest_index:.2f}, "
        f"which is below the base value of 100."
    )

else:

    st.info(
        "The latest index is equal to the base value of 100."
    )


# =========================================================
# CHART
# =========================================================

st.subheader("📊 Airfare Index Trend")


fig = px.line(
    series.sort_values("date"),
    x="date",
    y="index_value",
    markers=True,
    labels={
        "date": "Departure Date",
        "index_value":
            "DGCA-Weighted Lowe/Laspeyres-Style Index",
    },
    title="Dynamic DGCA-Weighted Airfare Index",
)


# ---------------------------------------------------------
# BASE LINE
# ---------------------------------------------------------

fig.add_hline(
    y=100,
    line_dash="dash",
    annotation_text="Base = 100",
)


fig.update_layout(
    hovermode="x unified",
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# DATA TABLE
# =========================================================

st.subheader("📋 Calculated Index Values")


display_series = series.sort_values(
    "date",
    ascending=False
).copy()


display_series["date"] = (
    display_series["date"]
    .dt.strftime("%Y-%m-%d")
)


display_series["index_value"] = (
    display_series["index_value"]
    .round(2)
)


display_series["base_value"] = (
    display_series["base_value"]
    .round(2)
)


st.dataframe(
    display_series,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# METHODOLOGY INFORMATION
# =========================================================

with st.expander(
    "ℹ️ Index Methodology"
):

    st.markdown(
        """
### DGCA-Weighted Lowe/Laspeyres-Style Index

The dynamic index uses:

- Route-level airfare observations
- DGCA dataset route weights
- Base-period mean fares
- Current-period mean fares
- Advance-booking windows
- Minimum sample size of **N ≥ 5**

### Advance-booking windows

| Window | Days |
|---|---:|
| 1–3 days | Near-departure |
| 7–14 days | Short-term advance |
| 15–30 days | Medium-term advance |

### Price Relative

\[
R_t = \\frac{P_t}{P_0} \\times 100
\]

The route-level price relatives are aggregated using the available route weights.

### Base

The base index is:

\[
100
\]

A value above 100 represents a level above the base-period value, while a value below 100 represents a level below the base-period value.

### Sample-size rule

A route/window combination must have at least:

\[
N \\geq 5
\]

observations in both the base and target periods to enter the calculation.
"""
    )


# =========================================================
# DGCA DATA PREVIEW
# =========================================================

if dgca_data is not None and not dgca_data.empty:

    with st.expander(
        "✈️ DGCA Dataset Preview"
    ):

        st.dataframe(
            dgca_data.head(100),
            use_container_width=True,
            hide_index=True,
        )