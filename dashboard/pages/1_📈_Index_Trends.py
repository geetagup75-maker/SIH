import sys
from pathlib import Path
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from database import load_fare_records, load_route_weights
from preprocessing import clean_fare_data
from airfare_index.index_calculator import calculate_dynamic_series

st.title("📈 Dynamic Airfare Index Trends")
fares = clean_fare_data(load_fare_records())
weights = load_route_weights()
if weights.empty:
    st.warning("No official DGCA route weights are loaded. The chart can show a demo equal-route fallback, not an official weighted index.")

series = calculate_dynamic_series(fares, weights if not weights.empty else None)
if series.empty:
    st.info("Not enough comparable observations to calculate the dynamic index.")
else:
    fig = px.line(series, x="date", y="index_value", markers=True,
                  labels={"date":"Departure date","index_value":"DGCA-weighted Lowe/Laspeyres-style index"})
    fig.add_hline(y=100, line_dash="dash", annotation_text="Base = 100")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(series.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
