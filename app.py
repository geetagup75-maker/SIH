from pathlib import Path
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from database import load_fare_records, load_route_weights, insert_fare_records, ensure_route_weights_table
from preprocessing import clean_fare_data, remove_duplicates, missing_value_summary, data_quality_summary
from statistics import descriptive_statistics, iqr_analysis, zscore_analysis, mad_analysis, coefficient_of_variation
from airfare_index.index_calculator import calculate_dgca_lowe_index, calculate_dynamic_series
from live_demo import build_demo_live_record

st.set_page_config(page_title="India Airfare Price Index", page_icon="✈️", layout="wide")
ensure_route_weights_table()

@st.cache_data
def get_data():
    return clean_fare_data(load_fare_records())

fares = get_data()
fares, duplicate_count = remove_duplicates(fares)
weights = load_route_weights()

with st.sidebar:
    st.header("✈️ Airfare Intelligence")
    page = st.radio("Dashboard", ["Executive Overview","Airfare Price Index","Index Trends","Route Analysis","Airline Analysis","Statistical Analysis","Data Quality","CPI Comparison","CPI Methodology","Live Scrape"])
    st.markdown("### Filters")
    airlines=sorted(fares["carrier_name"].dropna().unique().tolist())
    routes=sorted(fares["route"].dropna().unique().tolist())
    selected_airlines=st.multiselect("Airline", airlines)
    selected_routes=st.multiselect("Route", routes)
    adv_min=int(fares["advance_days"].min()) if not fares.empty else 1
    adv_max=int(fares["advance_days"].max()) if not fares.empty else 30
    advance=st.slider("Advance booking days", adv_min, max(adv_min,adv_max), (adv_min,max(adv_min,adv_max)))

filtered=fares.copy()
if selected_airlines: filtered=filtered[filtered.carrier_name.isin(selected_airlines)]
if selected_routes: filtered=filtered[filtered.route.isin(selected_routes)]
filtered=filtered[filtered.advance_days.between(*advance)]

def money(v): return "N/A" if pd.isna(v) else f"₹{v:,.0f}"
def kpi(label,value,help_text=""): st.metric(label,value,help=help_text)

if page=="Executive Overview":
    st.title("✈️ India Airfare Price Index")
    c=st.columns(4)
    with c[0]: kpi("Average Fare",money(filtered.total_fare.mean()))
    with c[1]: kpi("Median Fare",money(filtered.total_fare.median()))
    with c[2]: kpi("Routes",filtered.route.nunique())
    with c[3]: kpi("Observations",len(filtered))
    daily=filtered.groupby("departure_date",as_index=False).total_fare.mean()
    st.plotly_chart(px.line(daily,x="departure_date",y="total_fare",markers=True),use_container_width=True)

elif page=="Airfare Price Index":
    st.title("Airfare Price Index — DGCA-weighted Lowe/Laspeyres")
    if weights.empty:
        st.warning("Official DGCA route passenger weights are not loaded. Add them to route_weights before presenting this as the official weighted index.")
    idx, detail=calculate_dgca_lowe_index(filtered, route_weights=weights if not weights.empty else None)
    if pd.isna(idx): st.warning("Insufficient comparable observations (N ≥ 5 per route/window is required).")
    else:
        kpi("Current Index",f"{idx:.2f}","Base = 100")
        st.dataframe(detail,use_container_width=True,hide_index=True)

elif page=="Index Trends":
    st.title("📈 Dynamic Time-Series Recalculation")
    series=calculate_dynamic_series(filtered, weights if not weights.empty else None)
    if series.empty: st.warning("Insufficient comparable observations.")
    else:
        fig=px.line(series,x="date",y="index_value",markers=True)
        fig.add_hline(y=100,line_dash="dash",annotation_text="Base = 100")
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(series.sort_values("date",ascending=False),use_container_width=True,hide_index=True)

elif page=="Route Analysis":
    st.title("Route Analysis")
    summary=filtered.groupby("route").total_fare.agg(["mean","median","min","max","count"]).reset_index()
    st.plotly_chart(px.bar(summary.sort_values("mean",ascending=False).head(15),x="route",y="mean"),use_container_width=True)
    st.dataframe(summary,use_container_width=True,hide_index=True)

elif page=="Airline Analysis":
    st.title("Airline Analysis")
    summary=filtered.groupby("carrier_name").total_fare.agg(["mean","median","min","max","count"]).reset_index()
    st.plotly_chart(px.bar(summary,x="carrier_name",y="mean"),use_container_width=True)

elif page=="Statistical Analysis":
    st.title("Statistical Analysis")
    s=filtered.total_fare.dropna()
    if len(s)<5: st.warning("Sample-size check: at least N ≥ 5 observations is required for outlier analysis.")
    else:
        st.json(descriptive_statistics(s))
        st.write("IQR",iqr_analysis(s))
        st.write("Z-score",zscore_analysis(s))
        st.write("MAD",mad_analysis(s))
        st.metric("Coefficient of Variation",f"{coefficient_of_variation(s):.2f}%")

elif page=="Data Quality":
    st.title("Data Quality")
    st.json(data_quality_summary(filtered))
    st.dataframe(missing_value_summary(filtered),use_container_width=True,hide_index=True)

elif page=="CPI Comparison":
    st.title("CPI Comparison")
    st.caption("Load official MOSPI monthly CPI data as a CSV with columns: date,cpi_index. The chart intentionally does not invent official CPI observations.")
    up=st.file_uploader("Upload MOSPI CPI CSV",type=["csv"])
    series=calculate_dynamic_series(filtered,weights if not weights.empty else None)
    if up and not series.empty:
        cpi=pd.read_csv(up)
        cpi["date"]=pd.to_datetime(cpi["date"],errors="coerce")
        cpi["cpi_index"]=pd.to_numeric(cpi["cpi_index"],errors="coerce")
        chart=series[["date","index_value"]].rename(columns={"index_value":"Airfare Index"}).merge(cpi[["date","cpi_index"]],on="date",how="outer").sort_values("date")
        fig=px.line(chart,x="date",y=["Airfare Index","cpi_index"],markers=True,labels={"value":"Index","variable":"Series"})
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("Upload the official MOSPI series to render the comparison.")

elif page=="CPI Methodology":
    st.title("CPI Methodology")
    st.markdown("""
    **Implemented index:** DGCA passenger-weighted Lowe/Laspeyres-style index.

    **Strata:** 1–3, 7–14 and 15–30 advance-booking days are compared before aggregation.

    **Weighting:** route passenger percentages from `route_weights`. Within a route, available booking-window strata receive equal shares because no official booking-window weights are supplied.

    **Quality rule:** each route/window requires N ≥ 5 in both base and target periods.

    Paasche/Fisher are retained only as reference methodology; they are not used in the live production calculation because the fare table has no observed Q₀/Qₜ quantities.
    """)

elif page=="Live Scrape":
    st.title("🔄 Trigger Live Scrape — Demo")
    st.caption("Safe demo: no external request is made. A parsed/fallback record is generated from an existing fare record, inserted into SQLite, and the index is recalculated.")
    if st.button("Trigger Live Scrape"):
        record=build_demo_live_record(fares)
        insert_fare_records(record)
        st.cache_data.clear()
        st.success(f"Inserted 1 demo fallback fare for {record.iloc[0]['route']}.")
        idx,detail=calculate_dgca_lowe_index(clean_fare_data(load_fare_records()), route_weights=(load_route_weights() if not load_route_weights().empty else None))
        st.write("Recomputed index:", None if pd.isna(idx) else round(idx,2))
        st.dataframe(record,use_container_width=True,hide_index=True)
